#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from zope import interface

from docutils import nodes

from docutils.parsers.rst import directives

from docutils.parsers.rst.directives.images import Figure

from nti.app.contentfile.view_mixins import is_oid_external_link
from nti.app.contentfile.view_mixins import get_file_from_oid_external_link

from nti.app.contentfolder.utils import is_cf_io_href
from nti.app.contentfolder.utils import get_file_from_cf_io_url

from nti.app.products.courseware_content.docutils.nodes import course_asset

from nti.cabinet.filer import transfer_to_native_file

COURSE_ASSETS = 'Images/CourseAssets'


def is_course_asset(uri):
    return is_cf_io_href(uri) or is_oid_external_link(uri)


def get_course_asset(uri):
    if is_cf_io_href(uri):
        return get_file_from_cf_io_url(uri)
    return get_file_from_oid_external_link(uri)


def save_to_disk(asset, out_dir=None):
    out_dir = out_dir or os.getcwd()
    out_dir = os.path.join(out_dir, COURSE_ASSETS)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    path = os.path.join(out_dir, asset.filename)
    transfer_to_native_file(asset, path)
    result = os.path.join(COURSE_ASSETS, asset.filename)
    return result


class CourseAsset(Figure):

    option_spec = dict(Figure.option_spec)
    option_spec.pop('target', None)
    option_spec.pop('figclass', None)

    def run(self):
        reference = directives.uri(self.arguments[0]) or u''
        if not reference or not is_course_asset(reference):
            raise self.error(
                'Error in "%s" directive: "%s" is not a valid href value for '
                'a course asset.' % (self.name, reference))

        figwidth = self.options.pop('figwidth', None)
        if figwidth == 'image':
            raise self.error(
                'Error in "%s" directive: image is not a valid value for '
                'the "figwidth" option.' % self.name)

        asset = get_course_asset(reference)
        if asset is None:
            raise self.error(
                'Error in "%s" directive: course asset "%" is missing'
                % (self.name, reference))

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
        course_asset_node = course_asset('', 
                                         *fig_children[1:],
                                         **node_attributes)

        # when this directive runs the we assume the directory 
        # to save the resource has been set
        course_asset_node['uri'] = save_to_disk(asset)
        return [course_asset_node]


def register_directives():
    directives.register_directive("course-asset", CourseAsset)
register_directives()

from nti.contentlibrary_rendering.docutils.interfaces import IDirectivesModule
interface.moduleProvides(IDirectivesModule)
