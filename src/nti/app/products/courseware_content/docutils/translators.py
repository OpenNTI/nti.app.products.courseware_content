#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from docutils.nodes import Text
from docutils.nodes import TextElement

from plone.namedfile.file import getImageInfo

from nti.base._compat import text_

from nti.app.contentlibrary_rendering.docutils.utils import process_rst_figure
from nti.app.contentlibrary_rendering.docutils.utils import get_dataserver_asset
from nti.app.contentlibrary_rendering.docutils.utils import save_to_course_assets

from nti.contentlibrary_rendering.docutils.translators import build_nodes
from nti.contentlibrary_rendering.docutils.translators import TranslatorMixin

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator


@interface.implementer(IRSTToPlastexNodeTranslator)
class CourseFigureToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "course_figure"

    supported_local_types = ('image/jpeg', 'image/png')

    @classmethod
    def is_supported_local_type(cls, asset, rst_node):
        if hasattr(asset, 'data'):
            content_type, width, height = getImageInfo(asset.data)
            result = content_type in cls.supported_local_types
            if not result and width and height:
                rst_node['width'] = width
                rst_node['height'] = height
            return result
        return False

    def save_local(self, rst_node):
        uri = rst_node['uri']
        asset = get_dataserver_asset(uri)
        if asset is None:
            logger.error("%s course asset is missing", uri)
        elif self.is_supported_local_type(asset, rst_node):
            rst_node['uri'] = save_to_course_assets(asset)
        return rst_node

    def do_translate(self, rst_node, tex_doc, tex_parent):
        if rst_node['local']:
            self.save_local(rst_node)
        # start pushing the rst_nodes
        tex_doc.px_toggle_skip()
        result, _ = process_rst_figure(rst_node, tex_doc)
        return result

    def do_legend(self, rst_node, figure, caption, tex_doc):
        # XXX: in rst, a figure legend can be multiple paragraph
        # We  will interpret it as a caption
        # http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure
        all_text = []
        if caption is None:
            caption = tex_doc.createElement('caption')
            figure.append(caption)
        for node in rst_node.children or ():
            if node.tagname == 'paragraph':
                par = build_nodes(node, None, tex_doc=tex_doc)
                for child in par.childNodes or ():
                    caption.append(child)
                all_text.append(text_(node.astext()))
        return u' '.join(all_text)

    def do_caption(self, rst_node, figure):
        # XXX: in rst, a figure caption is a single paragraph.
        # We  will interpret it as the caption title
        # http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure
        all_text = []
        tex_doc = figure.ownerDocument
        caption = tex_doc.createElement('caption')
        figure.append(caption)
        for node in rst_node.children or ():
            if isinstance(node, (Text, TextElement)):
                data = text_(node.astext())
                all_text.append(data)
        caption.title = u' '.join(all_text)
        return caption

    def do_depart(self, rst_node, tex_node, tex_doc):
        # Allow processing
        tex_doc.px_toggle_skip()
        # process children nodes
        caption_node = None
        for node in tex_doc.px_store():
            if node.tagname == 'caption':
                caption_node = self.do_caption(node, tex_node)
            elif node.tagname == 'legend':
                self.do_legend(node, tex_node,
                               caption_node, tex_doc)
        # set image caption
        if caption_node is not None:
            for child in tex_node.childNodes or ():
                if child != caption_node:
                    child.title = caption_node
                    frag = tex_doc.createDocumentFragment()
                    frag.parentNode = child
                    frag.ownerDocument = tex_doc.ownerDocument
                    frag.appendChild(caption_node)
                    child.caption = frag
                    break
        # clean up
        tex_doc.px_clear()
