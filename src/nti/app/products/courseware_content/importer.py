#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import copy

from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.event import notify

from zope.security.interfaces import IPrincipal

from nti.app.authentication import get_remote_user

from nti.cabinet.filer import transfer_to_native_file

from nti.coremetadata.utils import current_principal

from nti.contentlibrary.interfaces import IFilesystemBucket
from nti.contentlibrary.interfaces import IEditableContentPackage

from nti.contentlibrary.mixins import ContentPackageImporterMixin

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionImporter
from nti.contenttypes.courses.interfaces import CourseBundleWillUpdateEvent

from nti.contenttypes.courses.importer import BaseSectionImporter

from nti.contenttypes.courses.utils import get_course_subinstances

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

ITEMS = StandardExternalFields.ITEMS


@interface.implementer(ICourseSectionImporter)
class CourseContentPackagesImporter(ContentPackageImporterMixin, 
                                    BaseSectionImporter):

    CONTENT_PACKAGE_INDEX = "content_pacakges.json"

    @Lazy
    def current_principal(self):
        remoteUser = IPrincipal(get_remote_user(), None)
        if remoteUser is None:
            remoteUser = current_principal()
        return remoteUser

    def handle_packages(self, items, course, unused_filer=None):
        added = []
        for ext_obj in items or ():
            source = copy.deepcopy(ext_obj)
            factory = find_factory_for(ext_obj)
            the_object = factory()  # create object
            assert IEditableContentPackage.providedBy(the_object)
            update_from_external_object(the_object, ext_obj, notify=False)
            package, is_new = self.handle_package(the_object, source,
                                                  course,)
            if is_new:
                added.append(package)

        if added:
            notify(CourseBundleWillUpdateEvent(course, added_packages=added))
        return added

    def process_source(self, course, source, filer=None):
        source = self.load(source)
        items = source.get(ITEMS)
        self.handle_packages(items, course, filer)

    def do_import(self, course, filer, writeout=True):
        href = self.course_bucket_path(course) + self.CONTENT_PACKAGE_INDEX
        source = self.safe_get(filer, href)
        if source is not None:
            self.process_source(course, source, filer)
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
