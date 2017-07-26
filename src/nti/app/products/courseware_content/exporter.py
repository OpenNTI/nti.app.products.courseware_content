#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary.interfaces import IEditableContentPackage

from nti.contenttypes.courses.common import get_course_content_packages

from nti.contenttypes.courses.interfaces import ICourseSectionExporter
from nti.contenttypes.courses.interfaces import IContentCourseInstance

from nti.contenttypes.courses.exporter import BaseSectionExporter

from nti.contenttypes.courses.utils import get_course_subinstances

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.proxy import removeAllProxies

OID = StandardExternalFields.OID
ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID


try:
    from nti.app.assessment.evaluations.exporter import EvaluationsExporterMixin
except ImportError:
    class EvaluationsExporterMixin(object):
        def export_evaluations(self, context, filer, backup, salt):
            pass


@interface.implementer(ICourseSectionExporter)
class CourseContentPackagesExporter(EvaluationsExporterMixin, BaseSectionExporter):

    def _do_externalize(self, course, filer=None, backup=True, salt=None):
        result = []
        packages = get_course_content_packages(course)
        for package in packages:
            package = removeAllProxies(package)
            if not IEditableContentPackage.providedBy(package):
                continue
            ext_obj = to_external_object(package,
                                         name="exporter",
                                         decorate=False)
            if not backup:
                ext_obj.pop(OID, None)
                for name in (NTIID, NTIID.lower()):
                    ntiid = ext_obj.get(name)
                    if ntiid:
                        ext_obj[name] = self.hash_ntiid(ntiid, salt)
            evaluations = self.export_evaluations(package, filer, backup, salt)
            if evaluations:
                ext_obj['Evaluations'] = evaluations
            result.append(ext_obj)
        return result

    def externalize(self, context, filer=None, backup=True, salt=None):
        result = LocatedExternalDict()
        course = IContentCourseInstance(context)
        items = self._do_externalize(course, filer, backup, salt)
        if items:  # check
            result[ITEMS] = items
        return result

    def do_export(self, course, filer, backup=True, salt=None):
        bucket = self.course_bucket(course)
        result = self.externalize(course, filer, backup, salt)
        if result:  # check
            source = self.dump(result)
            filer.save("content_pacakges.json", source, bucket=bucket,
                       contentType="application/json", overwrite=True)

    def export(self, context, filer, backup=True, salt=None):
        course = IContentCourseInstance(context, None)
        if course is None:
            return
        self.do_export(course, filer, backup, salt)
        for instance in get_course_subinstances(course):
            if course.ContentPackageBundle is not instance.ContentPackageBundle:
                self.do_export(instance, filer, backup, salt)
