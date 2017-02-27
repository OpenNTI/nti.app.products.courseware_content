#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.interfaces import IEditableContentPackage

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionExporter

from nti.contenttypes.courses.exporter import BaseSectionExporter

from nti.contenttypes.courses.utils import get_course_hierarchy

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.proxy import removeAllProxies

ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID


@interface.implementer(ICourseSectionExporter)
class ContentPacakgesExporter(BaseSectionExporter):

    def _output(self, course, filer=None, backup=True, salt=None):
        result = []
        try:
            packages = course.ContentPackageBundle.ContentPackages or ()
            for package in packages:
                package = removeAllProxies(package)
                if not IEditableContentPackage.providedBy(self, package):
                    continue
                ext_obj = to_external_object(package,
                                             name="exporter",
                                             decorate=False)
                if not backup:
                    for name in (NTIID, NTIID.lower()):
                        ext_obj.pop(name, None)
                result.append(ext_obj)
        except AttributeError:
            pass
        return result

    def externalize(self, context, filer=None, backup=True, salt=None):
        result = LocatedExternalDict()
        course = ICourseInstance(context)
        items = self._output(course,
                             filer=filer,
                             backup=backup,
                             salt=salt)
        if items:  # check
            result[ITEMS] = items
        return result

    def export(self, context, filer, backup=True, salt=None):
        course = ICourseInstance(context)
        courses = get_course_hierarchy(course)
        for course in courses:
            bucket = self.course_bucket(course)
            result = self.externalize(course, filer, backup, salt)
            if result: # check
                source = self.dump(result)
                filer.save("content_pacakges.json", source, bucket=bucket,
                           contentType="application/json", overwrite=True)
        return result
