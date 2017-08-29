#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component
from zope import interface

from nti.app.products.courseware.resources.utils import is_internal_file_link

from nti.app.products.courseware.utils.exporter import save_resource_to_filer

from nti.contentlibrary.interfaces import IEditableContentPackage
from nti.contentlibrary.interfaces import IContentPackageExporterDecorator

from nti.contentlibrary.utils import export_content_package

from nti.contenttypes.courses.common import get_course_content_packages

from nti.contenttypes.courses.interfaces import ICourseSectionExporter
from nti.contenttypes.courses.interfaces import IContentCourseInstance

from nti.contenttypes.courses.exporter import BaseSectionExporter

from nti.contenttypes.courses.utils import get_course_subinstances

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.proxy import removeAllProxies

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


@interface.implementer(ICourseSectionExporter)
class CourseContentPackagesExporter(BaseSectionExporter):

    def _do_externalize(self, course, backup=True, salt=None, filer=None):
        result = []
        packages = get_course_content_packages(course)
        for package in packages:
            package = removeAllProxies(package)
            if not IEditableContentPackage.providedBy(package):
                continue
            ext_obj = export_content_package(package, backup, salt, filer)
            result.append(ext_obj)
        return result

    def externalize(self, context, filer=None, backup=True, salt=None):
        result = LocatedExternalDict()
        course = IContentCourseInstance(context)
        items = self._do_externalize(course, backup, salt, filer)
        if items:  # check
            result[ITEMS] = items
            result[TOTAL] = result[ITEM_COUNT] = len(items)
        return result

    def do_export(self, course, filer, backup=True, salt=None):
        filer.default_bucket = bucket = self.course_bucket(course)
        result = self.externalize(course, filer, backup, salt)
        if result:  # check
            source = self.dump(result)
            filer.save("content_packages.json", source, bucket=bucket,
                       contentType="application/json", overwrite=True)

    def export(self, context, filer, backup=True, salt=None):
        course = IContentCourseInstance(context, None)
        if course is None:
            return
        self.do_export(course, filer, backup, salt)
        for instance in get_course_subinstances(course):
            if course.ContentPackageBundle is not instance.ContentPackageBundle:
                self.do_export(instance, filer, backup, salt)


@component.adapter(IEditableContentPackage)
@interface.implementer(IContentPackageExporterDecorator)
class EditableContentPackageExporterDecorator(object):

    __slots__ = ()

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, package, external, unused_backup=True,
                               unused_salt=None, filer=None):
        icon = package.icon
        if      filer is not None \
            and isinstance(icon, six.string_types) \
            and is_internal_file_link(icon):
            href = save_resource_to_filer(icon, filer, True, package)
            external['icon'] = href
