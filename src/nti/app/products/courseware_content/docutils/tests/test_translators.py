#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import contains_string

import os
import fudge
import shutil
import tempfile

from nti.contentlibrary_rendering._render import render_document

from nti.contentlibrary_rendering.docutils import publish_doctree

from nti.app.testing.application_webtest import ApplicationLayerTest


class TestTranslators(ApplicationLayerTest):

    def _ichigo_asset(self):
        return os.path.join(os.path.dirname(__file__), 
                            'data/ichigo.png')

    def _generate_from_file(self, source):
        index = document = None
        current_dir = os.getcwd()
        try:
            # change directory early
            tex_dir = tempfile.mkdtemp(prefix="render_")
            os.chdir(tex_dir)
            # make asset available
            shutil.copy(self._ichigo_asset(), tex_dir)
            # parse and run directives
            name = os.path.join(os.path.dirname(__file__), 'data/%s' % source)
            with open(name, "rb") as fp:
                source_doc = publish_doctree(fp.read())
            # render
            document = render_document(source_doc,
                                       outfile_dir=tex_dir,
                                       jobname="sample")
            index = os.path.join(tex_dir, 'index.html')
            assert_that(os.path.exists(index), is_(True))
            with open(index, "r") as fp:
                index = fp.read()
        except Exception:
            print('Exception %s, %s' % (source, tex_dir))
            raise
        else:
            shutil.rmtree(tex_dir)
        finally:
            os.chdir(current_dir)
        return (index, document)

    @fudge.patch('nti.app.products.courseware_content.docutils.directives.is_dataserver_asset')
    def test_figure(self, mock_isca):
        mock_isca.is_callable().with_args().returns(True)
        index, _ = self._generate_from_file('figure.rst')
        assert_that(index,
                    contains_string('<div class="figure" id="bankai inchigo">'))
        assert_that(index,
                    contains_string('<img alt="bankai inchigo"'))
        assert_that(index,
                    contains_string('<div class="caption"><b>Figure bankai </b>: <span>Bankai second form</span>'))
