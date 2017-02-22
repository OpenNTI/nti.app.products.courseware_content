#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators for providing access to the various course pieces.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.location.interfaces import ILocation

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.contenttypes.courses.legacy_catalog import ILegacyCourseInstance

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseContentPackageBundle

from nti.coremetadata.interfaces import IPublishable

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS


@component.adapter(ICourseInstance)
@interface.implementer(IExternalMappingDecorator)
class _CourseLibraryLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Provide a course `Library` rel to editors.
    """

    def _predicate(self, context, result):
        return  self._is_authenticated \
            and not ILegacyCourseInstance.providedBy(context) \
            and has_permission(ACT_CONTENT_EDIT, context, self.request)

    def _do_decorate_external(self, context, result):
        _links = result.setdefault(LINKS, [])
        link = Link(context,
                    rel=VIEW_COURSE_LIBRARY,
                    elements=(VIEW_COURSE_LIBRARY,))
        interface.alsoProvides(link, ILocation)
        link.__name__ = ''
        link.__parent__ = context
        _links.append(link)


@component.adapter(ICourseContentPackageBundle)
@interface.implementer(IExternalObjectDecorator)
class _CourseContentPackageBundleDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Suppress packcages w/o acesss
    """

    def _predicate(self, context, result):
        return  self._is_authenticated \
            and not ILegacyCourseInstance.providedBy(context) \
            and has_permission(ACT_READ, context, self.request)

    def _is_published(self, unit):
        return not IPublishable.providedBy(unit) or unit.is_published()

    def _check_publication_view(self, context):
        return self._is_published(context) \
            or has_permission(ACT_CONTENT_EDIT, context, self.request)

    def _do_decorate_external(self, context, result):
        keeper = list()
        ext_obj = result.get('ContentPackages') or ()
        for idx, package in enumerate(context.ContentPackages or ()):
            if self._check_publication_view(package):
                keeper.append(ext_obj[idx])
        if len(keeper) < len(ext_obj):
            result['ContentPackages'] = keeper
