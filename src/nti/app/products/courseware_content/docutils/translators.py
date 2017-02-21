#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.base._compat import unicode_

from nti.contentlibrary_rendering.docutils.translators import build_nodes
from nti.contentlibrary_rendering.docutils.translators import TranslatorMixin

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentrendering.plastexpackages.ntilatexmacros import ntiincludeannotationgraphics


@interface.implementer(IRSTToPlastexNodeTranslator)
class CourseAssetToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "course_asset"

    def do_translate(self, rst_node, tex_doc, tex_parent):
        # start pushing the rst_nodes
        tex_doc.px_toggle_skip()
        result = tex_doc.createElement('figure')

        # attribute settings
        options = dict()
        grphx = ntiincludeannotationgraphics()
        grphx.setAttribute('file', rst_node['uri'])
        grphx.setAttribute('options', options)

        # alternative text settings
        value = rst_node.attributes.get('alt', None)
        if value:  # alttext
            grphx.setAttribute('alttext', value)
            result.setAttribute('title', value)

        # dimension settings
        value = rst_node.attributes.get('scale', None)
        if value:
            options['scale'] = value if value <= 1 else value / 100.0
        else:
            for name in ('height', 'width'):
                value = rst_node.attributes.get(name, None)
                if value:
                    try:
                        float(value)  # unitless
                        options[name] = '%spx' % (value)
                    except (ValueError):
                        options[name] = value

        # add to set lineage
        result.append(grphx)

        # process image and return
        grphx.process_image()
        return result

    def do_legend(self, rst_node, figure, caption, tex_doc):
        # XXX: in rst, a figure legend can be multiple paragraph
        # We  will interpret it as a caption
        # http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure
        if caption is None:
            caption = tex_doc.createElement('caption')
            figure.append(caption)
        for node in rst_node.children or ():
            if node.tagname == 'paragraph':
                par = build_nodes(node, None, tex_doc=tex_doc)
                for child in par.childNodes or ():
                    caption.append(child)

    def do_caption(self, rst_node, figure):
        # XXX: in rst, a figure caption is a single paragraph.
        # We  will interpret it as the caption title
        # http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure
        tex_doc = figure.ownerDocument
        caption = tex_doc.createElement('caption')
        figure.append(caption)
        for node in rst_node.children or ():
            if node.tagname == '#text':
                caption.title = unicode_(node.astext())
                break
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
                self.do_legend(node, tex_node, caption_node, tex_doc)
        # clean up
        tex_doc.px_clear()
