#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_not
from hamcrest import contains
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder
does_not = is_not

import os

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY

from nti.app.products.courseware.tests import PersistentInstructedCourseApplicationTestLayer

from nti.app.publishing import VIEW_PUBLISH
from nti.app.publishing import VIEW_UNPUBLISH

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS


class TestContentViews(ApplicationLayerTest):

    layer = PersistentInstructedCourseApplicationTestLayer

    default_origin = b'http://janux.ou.edu'

    entry_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2015_CS_1323'
    package_ntiid = 'tag:nextthought.com,2011-10:OU-HTML-CS1323_F_2015_Intro_to_Computer_Programming.introduction_to_computer_programming'

    def _get_sample(self):
        path = os.path.join(os.path.dirname(__file__), 'sample.rst')
        with open(path, 'r') as f:
            result = f.read()
        return result

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_post_content(self):
        new_content = self._get_sample()
        entry_href = '/dataserver2/Objects/%s' % self.entry_ntiid
        res = self.testapp.get(entry_href).json_body
        course_ntiid = res['CourseNTIID']
        course_href = '/dataserver2/Objects/%s' % course_ntiid
        res = self.testapp.get(course_href).json_body
        library_href = self.require_link_href_with_rel(res,
                                                       VIEW_COURSE_LIBRARY)

        def _get_package_ntiids(course_res=None):
            if course_res is None:
                course_res = self.testapp.get(course_href).json_body
            packages = course_res['ContentPackageBundle']['ContentPackages']
            return [x['NTIID'] for x in packages]
        content_package_ntiids = _get_package_ntiids(res)
        assert_that(content_package_ntiids, has_length(1))
        assert_that(content_package_ntiids, contains(self.package_ntiid))

        new_title = 'new_title'
        data = {'title': new_title,
                'Class': 'RenderableContentPackage',
                'MimeType': u'application/vnd.nextthought.renderablecontentpackage',
                'content': new_content}
        res = self.testapp.post_json(library_href, data)
        res = res.json_body
        new_package_ntiid = res['NTIID']
        publish_href = self.require_link_href_with_rel(res, VIEW_PUBLISH)
        self.forbid_link_with_rel(res, VIEW_UNPUBLISH)
        new_package_ntiids = _get_package_ntiids()
        assert_that(new_package_ntiids, has_length(2))
        assert_that(new_package_ntiids,
                    contains_inanyorder(self.package_ntiid,
                                        new_package_ntiid))

        self.testapp.post(publish_href)
        new_package_ntiids = _get_package_ntiids()
        assert_that(new_package_ntiids, has_length(2))
        assert_that(new_package_ntiids,
                    contains_inanyorder(self.package_ntiid,
                                        new_package_ntiid))

        # TODO: Validate in-server state:
        # -packages for course, index
        # -enrolled access
        # -publishing
        # -job, post-publish status
