#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.location.interfaces import IContained

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY


@interface.implementer(IPathAdapter, IContained)
class CourseLibraryPathAdapter(object):

    __name__ = VIEW_COURSE_LIBRARY

    def __init__(self, context):
        self.context = self.__parent__ = self.course = context
