#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import copy
import time

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.event import notify

from zope.security.interfaces import IPrincipal

from nti.app.authentication import get_remote_user

from nti.cabinet.filer import transfer_to_native_file

from nti.coremetadata.utils import current_principal

from nti.contentlibrary.interfaces import IContentUnit
from nti.contentlibrary.interfaces import IContentPackage
from nti.contentlibrary.interfaces import IFilesystemBucket
from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IEditableContentPackage

from nti.contentlibrary.library import register_content_units

from nti.contentlibrary.utils import make_content_package_ntiid

from nti.contentlibrary_rendering import RST_MIMETYPE

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionImporter
from nti.contenttypes.courses.interfaces import CourseBundleUpdatedEvent

from nti.contenttypes.courses.importer import BaseSectionImporter

from nti.contenttypes.courses.utils import get_course_subinstances

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.property.property import Lazy

from nti.recorder.interfaces import TRX_TYPE_IMPORT

from nti.recorder.utils import record_transaction

ITEMS = StandardExternalFields.ITEMS


def copy_attributes(source, target, names):
    for name in names or ():
        value = getattr(source, name, None)
        if value is not None:
            setattr(target, name, value)


@interface.implementer(ICourseSectionImporter)
class CourseContentPackagesImporter(BaseSectionImporter):

    CONTENT_PACKAGE_INDEX = "content_pacakges.json"

    @Lazy
    def current_principal(self):
        remoteUser = IPrincipal(get_remote_user(), None)
        if remoteUser is None:
            remoteUser = current_principal()
        return remoteUser

    @Lazy
    def library(self):
        return component.getUtility(IContentPackageLibrary)

    def get_ntiid(self, obj):
        return getattr(obj, 'ntiid', None)

    def is_new(self, obj, course=None):
        ntiid = self.get_ntiid(obj) or u''
        return component.queryUtility(IContentPackage, name=ntiid)

    def handle_package(self, the_object, source, course,
                       check_locked=False, filer=None):
        result = the_object
        stored = self.is_new(the_object, course)
        if stored is not None:
            result = stored # replace
            assert IEditableContentPackage.providedBy(result)
            # copy all new content package attributes
            copy_attributes(the_object, result, IContentPackage.names())
            # copy content unit attributes
            attributes = set(IContentUnit.names()) - {'children', 'ntiid'}
            copy_attributes(the_object, result, attributes)
            # copy contents
            result.contents = the_object.contents
            result.contentType = the_object.contentType or RST_MIMETYPE
            # record trx
            record_transaction(result, type_=TRX_TYPE_IMPORT,
                               ext_value={
                                    'contents': result.contents,
                                    'contentType': result.contentType,
                                    'version': str(int(time.time()))
                               })
        else:
            register_content_units(course, result)
            result.ntiid = make_content_package_ntiid(result)
            self.library.add(result, event=False)

        is_published = source.get('isPublished')
        if is_published and (not check_locked or not result.is_locked()):
            result.publish()  # event trigger render job

        locked = source.get('isLocked')
        if locked and (not check_locked or not result.is_locked()):
            the_object.lock(event=False)
        # update indexes
        lifecycleevent.modified(result)
        return result, (stored is None)

    def handle_packages(self, items, course, check_locked=False, filer=None):
        added = []
        for ext_obj in items or ():
            source = copy.deepcopy(ext_obj)
            factory = find_factory_for(ext_obj)
            the_object = factory()  # create object
            assert IEditableContentPackage.providedBy(the_object)
            update_from_external_object(the_object, ext_obj, notify=False)
            package, is_new = self.handle_package(the_object,
                                                  filer=filer,
                                                  source=source,
                                                  course=course,
                                                  check_locked=check_locked)
            if is_new:
                added.append(package)

        if added:
            notify(CourseBundleUpdatedEvent(course, added_packages=added))
        return added

    def process_source(self, course, source, check_locked=True, filer=None):
        source = self.load(source)
        items = source.get(ITEMS)
        self.handle_packages(items, course, check_locked, filer)

    def do_import(self, course, filer, writeout=True):
        href = self.course_bucket_path(course) + self.CONTENT_PACKAGE_INDEX
        source = self.safe_get(filer, href)
        if source is not None:
            self.process_source(course, source, False, filer)
            # save source
            if writeout and IFilesystemBucket.providedBy(course.root):
                source = self.safe_get(filer, href)  # reload
                self.makedirs(course.root.absolute_path)  # create
                new_path = os.path.join(course.root.absolute_path,
                                        self.CONTENT_PACKAGE_INDEX)
                transfer_to_native_file(source, new_path)
            return True
        return False

    def process(self, context, filer, writeout=True):
        course = ICourseInstance(context)
        result = self.do_import(course, filer, writeout)
        for subinstance in get_course_subinstances(course):
            result = self.do_import(subinstance, filer, writeout) or result
        return result
