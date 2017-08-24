#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import contains_string

import os
import fudge
import unittest

from nti.app.products.courseware_content.docutils.operators import RenderablePackageContentOperator

from nti.base._compat import text_

from nti.contenttypes.courses.interfaces import NTI_COURSE_FILE_SCHEME


class TestOperators(unittest.TestCase):

    salt = '100'

    def _content(self, source):
        name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
        with open(name, "rb") as fp:
            return fp.read()

    @fudge.patch('nti.app.products.courseware_content.docutils.operators.is_internal_file_link',
                 'nti.app.products.courseware_content.docutils.operators.save_resource_to_filer')
    def test_figure(self, mock_iil, mock_srf):
        internal = NTI_COURSE_FILE_SCHEME + 'assets/ichigo.png'
        mock_iil.is_callable().with_args().returns(True)
        mock_srf.is_callable().with_args().returns(internal)
        content = text_(self._content('figure.rst'))
        operator = RenderablePackageContentOperator()
        content = operator.operate(content, filer=object())
        assert_that(content, contains_string(internal))
