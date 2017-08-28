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

from nti.app.products.courseware.utils import transfer_resource_from_filer

from nti.app.products.courseware.utils.exporter import save_resource_to_filer

from nti.base._compat import text_
from nti.base._compat import bytes_

from nti.contentlibrary.interfaces import IContentOperator
from nti.contentlibrary.interfaces import IRenderableContentPackage
from nti.contentlibrary.interfaces import IContentPackageImporterUpdater

from nti.contenttypes.courses.interfaces import NTI_COURSE_FILE_SCHEME


class OperatorMixin(object):

    def __init__(self, *args):
        pass

    @Lazy
    def _figure_pattern(self):
        pattern = r'\.\.[ ]+%s\s?::\s?(.+)' % 'course-figure'
        pattern = re.compile(pattern, re.VERBOSE | re.UNICODE)
        return pattern


@interface.implementer(IContentOperator)
@component.adapter(IRenderableContentPackage)
class RenderablePackageContentOperator(OperatorMixin):

    def _process(self, line, filer, result):
        modified = False
        m = self._figure_pattern.match(line)
        if m is not None:
            reference = m.groups()[0]
            if is_internal_file_link(reference):
                internal = save_resource_to_filer(reference, filer)
                __traceback_info__ = reference, internal
                if internal:
                    line = re.sub(reference, internal, line)
                    modified = True
        result.append(line)
        return modified

    def _replace_all(self, content, filer, result):
        modified = False
        input_lines = statemachine.string2lines(content)
        input_lines = statemachine.StringList(input_lines, '<string>')
        for idx in range(len(input_lines)):
            modified = self._process(input_lines[idx],
                                     filer, result) or modified
        return modified

    def operate(self, content, unused_context=None, **kwargs):
        if not content:
            return content
        filer = kwargs.get('filer')
        if filer is None:
            return content
        is_bytes = isinstance(content, bytes)
        content = text_(content) if is_bytes else content
        try:
            result = []
            modified = self._replace_all(content, filer, result)
            if modified:
                content = u'\n'.join(result)
        except Exception:
            logger.exception("Cannot operate on content")
        return bytes_(content) if is_bytes else content


@component.adapter(IRenderableContentPackage)
@interface.implementer(IContentPackageImporterUpdater)
class RenderableContentPackageImporterUpdater(OperatorMixin):

    def _process(self, package, line, result, source_filer, target_filer):
        modified = False
        m = self._figure_pattern.match(line)
        if m is not None:
            reference = m.groups()[0]
            if reference.startswith(NTI_COURSE_FILE_SCHEME):
                href, unused = transfer_resource_from_filer(reference, package,
                                                            source_filer, target_filer)
                if href:
                    line = re.sub(reference, href, line)
                    modified = True
        result.append(line)
        return modified

    def process_content(self, package, source_filer, target_filer):
        result = []
        modified = False
        content = text_(package.contents or b'')
        lines = statemachine.string2lines(content)
        lines = statemachine.StringList(lines, '<string>')
        for idx in range(len(lines)):
            modified = self._process(package, lines[idx], result,
                                     source_filer, target_filer) or modified
        if modified:
            content = u'\n'.join(result)
            package.contents = bytes_(content)

    def updateFromExternalObject(self, package, unused_external=None, *unused_args, **kwargs):
        source_filer = kwargs.get('source_filer')
        target_filer = kwargs.get('target_filer')
        if source_filer is not None and target_filer is not None:
            self.process_content(package, source_filer, target_filer)
