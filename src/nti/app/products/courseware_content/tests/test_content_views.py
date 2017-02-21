#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import contains
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder
does_not = is_not

import os

from nti.dataserver.users import User

from nti.app.contentlibrary import VIEW_CONTENTS
from nti.app.contentlibrary import VIEW_PUBLISH_CONTENTS

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY

from nti.app.products.courseware.tests import PersistentInstructedCourseApplicationTestLayer

from nti.app.publishing import VIEW_PUBLISH
from nti.app.publishing import VIEW_UNPUBLISH

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contentlibrary_rendering.interfaces import SUCCESS

from nti.dataserver.tests import mock_dataserver


class TestContentViews(ApplicationLayerTest):

    layer = PersistentInstructedCourseApplicationTestLayer

    default_origin = b'http://janux.ou.edu'

    entry_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2015_CS_1323'
    package_ntiid = 'tag:nextthought.com,2011-10:OU-HTML-CS1323_F_2015_Intro_to_Computer_Programming.introduction_to_computer_programming'

    def _get_rst_data(self, filename='sample.rst'):
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'r') as f:
            result = f.read()
        return result

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_post_content(self):
        publish_contents = self._get_rst_data('basic.rst')
        entry_href = '/dataserver2/Objects/%s' % self.entry_ntiid
        res = self.testapp.get(entry_href).json_body
        course_ntiid = res['CourseNTIID']
        course_href = '/dataserver2/Objects/%s' % course_ntiid
        res = self.testapp.get(course_href).json_body
        library_href = self.require_link_href_with_rel(res, VIEW_COURSE_LIBRARY)

        def _get_package_ntiids( course_res=None ):
            if course_res is None:
                course_res = self.testapp.get( course_href ).json_body
            packages = course_res['ContentPackageBundle']['ContentPackages']
            return [x['NTIID'] for x in packages]
        # Base case has only has one package
        content_package_ntiids = _get_package_ntiids( res )
        assert_that( content_package_ntiids, has_length(1) )
        assert_that( content_package_ntiids, contains(self.package_ntiid) )

        new_title = 'new_title'
        data = {'title': new_title,
                'Class': 'RenderableContentPackage',
                'MimeType': u'application/vnd.nextthought.renderablecontentpackage'}
        res = self.testapp.post_json( library_href, data )
        res = res.json_body
        new_package_ntiid = res['NTIID']
        assert_that( res['isRendered'], is_(False))
        assert_that( res.get('LatestRenderJob'), none())
        publish_href = self.require_link_href_with_rel(res, VIEW_PUBLISH)
        contents_href = self.require_link_href_with_rel(res, VIEW_CONTENTS)
        self.forbid_link_with_rel(res, VIEW_PUBLISH_CONTENTS)
        self.forbid_link_with_rel(res, VIEW_UNPUBLISH)

        self.testapp.put(contents_href,
                         upload_files=[
                            ('contents', 'contents.rst', bytes(publish_contents))])

        new_package_ntiids = _get_package_ntiids()
        assert_that( new_package_ntiids, has_length(2))
        assert_that( new_package_ntiids, contains_inanyorder(self.package_ntiid,
                                                             new_package_ntiid))

        published_package = self.testapp.post( publish_href )
        published_package = published_package.json_body
        assert_that( published_package['isRendered'], is_(True))
        job = published_package.get( 'LatestRenderJob' )
        assert_that( job, not_none())
        assert_that( job['State'], is_(SUCCESS))
        new_package_ntiids = _get_package_ntiids()
        assert_that( new_package_ntiids, has_length(2))
        assert_that( new_package_ntiids, contains_inanyorder(self.package_ntiid,
                                                             new_package_ntiid))

        get_contents = self.testapp.get( contents_href )
        get_contents = get_contents.json_body
        assert_that( get_contents['data'], is_(publish_contents))

        # Now update contents (unpublished).
        new_contents = "%s\nmore text" % publish_contents
        res = self.testapp.put(contents_href,
                               upload_files=[
                                    ('contents', 'contents.rst', bytes(new_contents))])
        res = res.json_body

        # Now we have publish_contents href
        publish_contents_href = self.require_link_href_with_rel(res,
                                                                VIEW_PUBLISH_CONTENTS)

        publish_contents_res = self.testapp.get( publish_contents_href )
        publish_contents_res = publish_contents_res.json_body
        assert_that( publish_contents_res['data'], is_(publish_contents))
        get_contents = self.testapp.get( contents_href )
        get_contents = get_contents.json_body
        assert_that( get_contents['data'], is_(new_contents))
        valid_version = publish_contents_res['version']

        # Now publish and the publish_contents rel is no longer necessary
        published_package = self.testapp.post( publish_href )
        self.forbid_link_with_rel(published_package.json_body, VIEW_PUBLISH_CONTENTS)
        # Validate versioning
        conflict_contents = "%s\nconflict" % publish_contents
        self.testapp.put('%s?version=%s' % (contents_href, 'invalid_version'),
                         upload_files=[
                            ('contents', 'contents.rst', bytes(conflict_contents))],
                         status=409)
        self.testapp.put('%s?version=%s' % (contents_href, valid_version),
                         upload_files=[
                            ('contents', 'contents.rst', bytes(conflict_contents))])

        # TODO: Validate in-server state:
        # -packages for course, index
        # -enrolled access
        # -publishing
        # -job, post-publish status
        # -test contents
