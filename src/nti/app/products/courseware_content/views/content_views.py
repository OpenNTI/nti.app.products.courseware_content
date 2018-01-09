#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.event import notify

from zope.cachedescriptors.property import Lazy

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.contentlibrary.views import LIBRARY_ADAPTER

from nti.app.contentlibrary.views.edit_views import LibraryPostView

from nti.app.products.courseware_content.views import CourseLibraryPathAdapter

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import CourseBundleWillUpdateEvent

from nti.contenttypes.courses.utils import get_parent_course

from nti.dataserver import authorization as nauth

logger = __import__('logging').getLogger(__name__)


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

    @Lazy
    def course(self):
        # pylint: disable=no-member
        return self.context.course

    def get_library(self, unused_context=None):
        """
        Override to install the new content in the course site library.
        """
        course = self.course
        return super(CourseLibraryPostView, self).get_library(context=course)

    def _do_call(self):
        course = self.course
        package = super(CourseLibraryPostView, self)._do_call()
        # Now we should have our package in our library, store it on our
        # course and fire events.
        # pylint: disable=no-member
        bundle = course.ContentPackageBundle
        bundle.updateLastMod()
        # Not sure we can guarantee this is a set...
        bundle.add(package)
        # Since the bundle is shared between all course hierarchy members,
        # let's fire the event for the root course.
        root_course = get_parent_course(course)
        notify(CourseBundleWillUpdateEvent(root_course, (package,)))
        return package


@view_config(context=ICourseCatalogEntry)
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               name=LIBRARY_ADAPTER,
               request_method='POST',
               permission=nauth.ACT_CONTENT_EDIT)
class CatalogEntryLibraryPostView(CourseLibraryPostView):

    @Lazy
    def course(self):
        return ICourseInstance(self.context)
