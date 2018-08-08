#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.component.hooks import site as current_site

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IEditableContentPackage

from nti.contenttypes.courses.common import get_course_packages

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSubInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry

from nti.site.interfaces import IHostPolicyFolder
from nti.contenttypes.courses.utils import get_parent_course

logger = __import__('logging').getLogger(__name__)


def _get_library(context):
    library = None
    if context is None:
        library = component.queryUtility(IContentPackageLibrary)
    else:
        # If context is given, attempt to use the site the given context
        # is stored in. This is necessary to avoid data loss during sync.
        folder = IHostPolicyFolder(context, None)
        if folder is not None:
            with current_site(folder):
                library = component.queryUtility(IContentPackageLibrary)
    return library


@component.adapter(ICourseInstance, IObjectRemovedEvent)
def _clear_course_packages(course, unused_event):
    """
    Clean up any editable content packages in this course (these authored
    packages are currently only available in the course where they were
    created).
    """
    count = 0
    if ICourseSubInstance.providedBy(course):
        # If we share bundles, we do not want to remove
        # IEditableContentPackages that belong to the parent course
        parent_course = get_parent_course(course)
        child_bundle = getattr(course, 'ContentPackageBundle', '')
        parent_bundle = getattr(parent_course, 'ContentPackageBundle', '')
        if child_bundle is parent_bundle:
            return
    packages = get_course_packages(course)
    for package in packages:
        if IEditableContentPackage.providedBy(package):
            library = _get_library(package)
            if library is not None:
                library.remove(package)
                count += 1
    logger.info('Deleted %s editable content packages (course=%s) (total_package_count=%s)',
                count,
                ICourseCatalogEntry(course).ntiid,
                len(packages))
