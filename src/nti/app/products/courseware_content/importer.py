#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import site as current_site

from zope.event import notify

from zope.security.interfaces import IPrincipal

from nti.app.authentication import get_remote_user

from nti.app.products.courseware.resources.utils import get_course_filer

from nti.app.products.courseware.utils import transfer_resource_from_filer

from nti.cabinet.filer import transfer_to_native_file

from nti.coremetadata.utils import current_principal

from nti.contentlibrary.interfaces import IFilesystemBucket
from nti.contentlibrary.interfaces import IEditableContentPackage
from nti.contentlibrary.interfaces import IContentPackageImporterUpdater

from nti.contentlibrary.mixins import ContentPackageImporterMixin

from nti.contenttypes.courses.interfaces import NTI_COURSE_FILE_SCHEME

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionImporter
from nti.contenttypes.courses.interfaces import CourseBundleWillUpdateEvent

from nti.contenttypes.courses.importer import BaseSectionImporter

from nti.contenttypes.courses.utils import get_course_subinstances

from nti.externalization.interfaces import StandardExternalFields

from nti.site.interfaces import IHostPolicyFolder

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICourseSectionImporter)
class CourseContentPackagesImporter(ContentPackageImporterMixin,
                                    BaseSectionImporter):

    CONTENT_PACKAGE_INDEX = "content_packages.json"

    @Lazy
    def current_principal(self):
        remoteUser = IPrincipal(get_remote_user(), None)
        if remoteUser is None:
            remoteUser = current_principal()
        return remoteUser

    def handle_packages(self, items, course, source_filer=None, target_filer=None):
        result = ContentPackageImporterMixin.handle_packages(self, items, course, 
                                                             source_filer=source_filer,
                                                             target_filer=target_filer)
        added, _ = result
        if added:
            notify(CourseBundleWillUpdateEvent(course, added_packages=added))
        return added

    def process_source(self, course, source, source_filer=None, target_filer=None):
        source = self.load(source)
        items = source.get(ITEMS)
        # want to make sure pkgs are registered in the course site
        with current_site(IHostPolicyFolder(course)):
            self.handle_packages(items, course, source_filer, target_filer)

    def do_import(self, course, source_filer, writeout=True):
        href = self.course_bucket_path(course) + self.CONTENT_PACKAGE_INDEX
        source = self.safe_get(source_filer, href)
        if source is not None:
            target_filer = get_course_filer(course)
            self.process_source(course, source, source_filer, target_filer)
            # save source
            if writeout and IFilesystemBucket.providedBy(course.root):
                source = self.safe_get(source_filer, href)  # reload
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
    

@component.adapter(IEditableContentPackage)
@interface.implementer(IContentPackageImporterUpdater)
class EditableContentPackageImporterUpdater(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def updateFromExternalObject(self, package, external, *unused_args, **kwargs):
        icon = external.get('icon')
        source_filer = kwargs.get('source_filer')
        target_filer = kwargs.get('target_filer')
        if      isinstance(icon, six.string_types) \
            and icon.startswith(NTI_COURSE_FILE_SCHEME) \
            and source_filer is not None and target_filer is not None:
            href, unused = transfer_resource_from_filer(icon, package,
                                                        source_filer, target_filer)
            package.icon = href
