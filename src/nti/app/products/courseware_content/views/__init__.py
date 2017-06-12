#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.container.contained import Contained

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY


@interface.implementer(IPathAdapter)
class CourseLibraryPathAdapter(Contained):

    __name__ = 'Library'

    def __init__(self, context):
        self.context = self.__parent__ = self.course = context
