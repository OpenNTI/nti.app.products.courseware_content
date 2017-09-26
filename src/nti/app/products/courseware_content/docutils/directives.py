#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from docutils import nodes

from docutils.parsers.rst import directives

from docutils.parsers.rst.directives.images import Figure

from nti.app.contentlibrary_rendering.docutils.utils import is_dataserver_asset

from nti.app.products.courseware_content.docutils.nodes import course_figure

from nti.common.string import is_true

from nti.contenttypes.courses.interfaces import NTI_COURSE_FILE_SCHEME

logger = __import__('logging').getLogger(__name__)


def true_value(argument):
    return is_true(argument)


class CourseFigure(Figure):

    option_spec = dict(Figure.option_spec)
    option_spec.pop('target', None)
    option_spec['local'] = true_value

    def _is_valid_reference(self, reference):
        return is_dataserver_asset(reference) \
            or reference.startswith(NTI_COURSE_FILE_SCHEME)

    def run(self):
        reference = directives.uri(self.arguments[0])
        if not reference or not self._is_valid_reference(reference):
            raise self.error(
                'Error in "%s" directive: "%s" is not a valid href value for '
                'a course asset.' % (self.name, reference))

        figwidth = self.options.pop('figwidth', None)
        if figwidth == 'image':
            raise self.error(
                'Error in "%s" directive: image is not a valid value for '
                'the "figwidth" option.' % self.name)

        (figure_node,) = Figure.run(self)
        if isinstance(figure_node, nodes.system_message):
            return [figure_node]

        # first children is an image
        fig_children = figure_node.children

        # merge image and figure attributes
        img_attributes = fig_children[0].attributes
        node_attributes = dict(img_attributes)
        node_attributes.update(figure_node.attributes)

        # creates the course asset, don't include the image node
        result = course_figure(self.block_text,
                               *fig_children[1:],
                               **node_attributes)
        result['uri'] = reference
        result['local'] = is_true(self.options.get('local'))
        return [result]


def register_directives():
    directives.register_directive("course-figure", CourseFigure)
register_directives()

from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
