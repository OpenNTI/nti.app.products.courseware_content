#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.location.interfaces import ILocation

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.contenttypes.courses.legacy_catalog import ILegacyCourseInstance

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseInstance)
@interface.implementer(IExternalMappingDecorator)
class _CourseLibraryLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Provide a course `Library` rel to editors.
    """

    def _predicate(self, context, unused_result):
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

