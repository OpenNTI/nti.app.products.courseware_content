#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.event import notify

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.contentlibrary.views.edit_views import LibraryPostView

from nti.app.products.courseware_content.views import CourseLibraryPathAdapter

from nti.contenttypes.courses.interfaces import CourseBundleUpdatedEvent

from nti.dataserver import authorization as nauth


@view_config(context=CourseLibraryPathAdapter)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               request_method='POST',
               permission=nauth.ACT_CONTENT_EDIT)
class CourseLibraryPostView(LibraryPostView):
    """
    A view to attach a brand new :class:`IContentPackage` to a course
    after first placing it in the site :class:`IContentPackageLibrary`.
    """

    def _do_call(self):
        course = self.context.course
        package = super(CourseLibraryPostView, self)._do_call()
        # Now we should have our package in our library, store it on our
        # course and fire events.
        bundle = course.ContentPackageBundle
        bundle.updateLastMod()
        # Not sure we can guarantee this is a set...
        bundle.add(package)
        notify(CourseBundleUpdatedEvent(course, (package,)))
        return package
