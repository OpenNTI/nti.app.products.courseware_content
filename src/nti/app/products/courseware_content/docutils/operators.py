#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re

from docutils import statemachine

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from nti.app.products.courseware.resources.utils import is_internal_file_link

from nti.app.products.courseware.utils.exporter import save_resource_to_filer

from nti.base._compat import text_
from nti.base._compat import bytes_

from nti.contentlibrary.interfaces import IContentOperator
from nti.contentlibrary.interfaces import IRenderableContentPackage


@interface.implementer(IContentOperator)
@component.adapter(IRenderableContentPackage)
class RenderablePackageContentOperator(object):

    def __init__(self, *args):
        pass

    @Lazy
    def _figure_pattern(self):
        pattern = r'\.\.[ ]+%s\s?::\s?(.+)' % 'course-figure'
        pattern = re.compile(pattern, re.VERBOSE | re.UNICODE)
        return pattern

    def _process_course_figure(self, input_lines, filer, idx, result):
        line = input_lines[idx]
        m = self._figure_pattern.match(line)
        if m is None:
            return False
        reference = m.groups()[0]
        if is_internal_file_link(reference):    
            internal = save_resource_to_filer(reference, filer, False)
            line = re.sub(reference, internal, line)
            result.append(line)
            return True
        return False
    
    def replace_all(self, content, filer):
        idx = 0
        result = []
        input_lines = statemachine.string2lines(content)
        input_lines = statemachine.StringList(input_lines, '<string>')
        while idx < len(input_lines):
            matched = self._process_course_figure(input_lines, filer, idx, result)
            if not matched:
                result.append(input_lines[idx])
            idx += 1
        return u'\n'.join(result)

    def operate(self, content, unused_context=None, **kwargs):
        if not content:
            return content
        filer = kwargs.get('filer')
        if filer is None:
            return content
        is_bytes = isinstance(content, bytes)
        content = text_(content) if is_bytes else content
        try:
            content = self.replace_all(content, filer)
        except Exception:
            logger.exception("Cannot operate on content")
        return bytes_(content) if is_bytes else content
