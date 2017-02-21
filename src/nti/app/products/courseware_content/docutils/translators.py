#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.contentlibrary_rendering.docutils.translators import TranslatorMixin

from nti.contentlibrary_rendering.docutils.interfaces import IRSTToPlastexNodeTranslator

from nti.contentrendering.plastexpackages.ntilatexmacros import ntiincludeannotationgraphics


@interface.implementer(IRSTToPlastexNodeTranslator)
class CourseAssetToPlastexNodeTranslator(TranslatorMixin):

    __name__ = "course_asset"

    def translate(self, rst_node, tex_doc, tex_parent):
        result = tex_doc.createElement('figure')
        # process include graphics
        options = dict()  # graphics settings
        grphx = ntiincludeannotationgraphics()
        grphx.setAttribute('file', rst_node['uri'])
        grphx.setAttribute('options', options)
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
