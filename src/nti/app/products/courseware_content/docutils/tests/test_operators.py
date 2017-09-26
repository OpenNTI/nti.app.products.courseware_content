#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import contains_string

import os
import fudge
import unittest

from nti.app.products.courseware_content.docutils.operators import RenderablePackageContentOperator
from nti.app.products.courseware_content.docutils.operators import RenderableContentPackageImporterUpdater

from nti.base._compat import text_
from nti.base._compat import bytes_

from nti.contentlibrary.zodb import RenderableContentPackage

from nti.contenttypes.courses.interfaces import NTI_COURSE_FILE_SCHEME


class TestOperators(unittest.TestCase):

    def _content(self, source):
        name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
        with open(name, "rb") as fp:
            return fp.read()

    def operate(self, content):
        operator = RenderablePackageContentOperator()
        content = operator.operate(content, filer=object())
        return content

    @fudge.patch('nti.app.products.courseware_content.docutils.operators.is_internal_file_link',
                 'nti.app.products.courseware_content.docutils.operators.save_resource_to_filer',
                 'nti.app.products.courseware_content.docutils.operators.transfer_resource_from_filer')
    def test_export_import(self, mock_iil, mock_srf, mock_trx):
        # export
        internal = NTI_COURSE_FILE_SCHEME + 'assets/ichigo.png'
        mock_iil.is_callable().with_args().returns(True)
        mock_srf.is_callable().with_args().returns(internal)
        content = text_(self._content('figure.rst'))
        content = self.operate(content)
        assert_that(content, contains_string(internal))

        # import
        href = '/dataserver2/ichigo.png'
        mock_trx.is_callable().with_args().returns((href, True))
        package = RenderableContentPackage()
        package.contents = bytes_(content)
        updater = RenderableContentPackageImporterUpdater()
        updater.updateFromExternalObject(package, source_filer=object(),
                                         target_filer=object())
        content = text_(package.contents)
        assert_that(content, contains_string(href))
