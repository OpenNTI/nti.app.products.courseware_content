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
from hamcrest import has_item
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder
does_not = is_not

import os
import shutil

from zope import component

from nti.dataserver.users import User

from nti.app.contentlibrary import VIEW_CONTENTS
from nti.app.contentlibrary import VIEW_PUBLISH_CONTENTS

from nti.app.contentlibrary_rendering import VIEW_QUERY_JOB

from nti.app.contentlibrary.utils import PAGE_INFO_MT

from nti.app.products.courseware_content import VIEW_COURSE_LIBRARY

from nti.app.products.courseware.tests import PersistentInstructedCourseApplicationTestLayer

from nti.app.publishing import VIEW_PUBLISH
from nti.app.publishing import VIEW_UNPUBLISH

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contentlibrary import CONTENT_UNIT_MIME_TYPE
from nti.contentlibrary import CONTENT_PACKAGE_MIME_TYPE
from nti.contentlibrary import RENDERABLE_CONTENT_UNIT_MIME_TYPE
from nti.contentlibrary import RENDERABLE_CONTENT_PACKAGE_MIME_TYPE

from nti.contentlibrary.interfaces import IContentPackageLibrary
from nti.contentlibrary.interfaces import IDelimitedHierarchyContentPackageEnumeration

from nti.contentlibrary_rendering.interfaces import SUCCESS

from nti.contentlibrary_rendering.interfaces import IContentPackageRenderMetadata

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseEnrollmentManager

from nti.contenttypes.courses.utils import get_content_unit_courses

from nti.dataserver.tests import mock_dataserver

from nti.externalization.externalization import StandardExternalFields

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.traversal import find_interface

CLASS = StandardExternalFields.CLASS
LINKS = StandardExternalFields.LINKS
MIMETYPE = StandardExternalFields.MIMETYPE


class TestContentViews(ApplicationLayerTest):

    layer = PersistentInstructedCourseApplicationTestLayer

    default_origin = b'http://janux.ou.edu'

    entry_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2015_CS_1323'
    package_ntiid = 'tag:nextthought.com,2011-10:OU-HTML-CS1323_F_2015_Intro_to_Computer_Programming.introduction_to_computer_programming'

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def tearDown(self):
        """
        Clean up our site library; this will be distinct
        from the syncable site - platform.ou.edu.
        """
        with mock_dataserver.mock_db_trans(site_name='janux.ou.edu'):
            library = component.getUtility(IContentPackageLibrary)
            folder = find_interface(library, IHostPolicyFolder, strict=False)
            assert_that( folder.__name__, is_('janux.ou.edu'))
            enumeration = IDelimitedHierarchyContentPackageEnumeration(library)
            shutil.rmtree(enumeration.root.absolute_path, ignore_errors=True)

    def _get_rst_data(self, filename='sample.rst'):
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'r') as f:
            result = f.read()
        return result

    def create_user(self, username):
        with mock_dataserver.mock_db_trans(self.ds):
            # The janux policy enforces first/last names.
            self._create_user(username)

    def _create_and_enroll(self, username, section=False):
        """
        Create user and enroll.
        """
        self.create_user(username)
        with mock_dataserver.mock_db_trans(self.ds, site_name='janux.ou.edu'):
            new_user = User.get_user(username)
            course = find_object_with_ntiid(self.entry_ntiid)
            course = ICourseInstance(course)
            if section:
                course = tuple(course.SubInstances.values())[0]
            manager = ICourseEnrollmentManager(course)
            manager.enroll(new_user)

    def _test_page_info(self, package_ntiid, environ, status=200):
        accept_type = str('application/json')
        res = self.testapp.get( '/dataserver2/Objects/%s' % package_ntiid,
                           headers={str("Accept"): accept_type},
                           extra_environ=environ,
                           status=status )
        res = res.json_body
        if status == 200:
            assert_that( res['ContentPackageNTIID'], is_(package_ntiid))
            assert_that( res[CLASS], is_('PageInfo'))
            assert_that( res[MIMETYPE], is_(PAGE_INFO_MT))
            assert_that( res[LINKS], has_item( has_entry('rel', 'content')))
        return res

    def _test_get_package(self, package_ntiid, environ, status=200):
        for mimetype in (CONTENT_UNIT_MIME_TYPE,
                         CONTENT_PACKAGE_MIME_TYPE,
                         RENDERABLE_CONTENT_UNIT_MIME_TYPE,
                         RENDERABLE_CONTENT_PACKAGE_MIME_TYPE):
            accept_type = str(mimetype)
            res = self.testapp.get( '/dataserver2/Objects/%s' % package_ntiid,
                                    headers={str("Accept"): accept_type},
                                    extra_environ=environ,
                                    status=status)
        return res

    def _check_package_state(self, package_ntiid, job_count=0):
        """
        Validate the course is found with just the package. Validate
        the library has the package details and that the job status
        is correct.
        """
        with mock_dataserver.mock_db_trans(site_name='janux.ou.edu'):
            library = component.getUtility(IContentPackageLibrary)
            package = library.contentUnitsByNTIID.get( package_ntiid )
            assert_that( package, not_none() )
            assert_that( package.ntiid, is_(package_ntiid))
            courses = get_content_unit_courses(package)
            assert_that( courses, has_length(1))
            entry_ntiid = ICourseCatalogEntry(courses[0]).ntiid
            assert_that( entry_ntiid, is_(self.entry_ntiid))
            meta = IContentPackageRenderMetadata(package, None)
            assert_that(meta, not_none())
            assert_that(tuple(meta.values()), has_length(job_count))

    def _get_package_path(self, package_ntiid):
        with mock_dataserver.mock_db_trans(site_name='janux.ou.edu'):
            package = find_object_with_ntiid(package_ntiid)
            return package.root.absolute_path

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_post_content(self):
        """
        Test creating a new package in a course.
        """
        admin_environ = self._make_extra_environ(username="sjohnson@nextthought.com")
        instructor_environ = self._make_extra_environ(username="cs1323_instructor")
        self._create_and_enroll('student1')
        self._create_and_enroll('student3_section', section=True)
        student1_environ = self._make_extra_environ(username='student1')
        student3_section_environ = self._make_extra_environ(username='student1')
        publish_contents = self._get_rst_data('basic.rst')
        entry_href = '/dataserver2/Objects/%s' % self.entry_ntiid
        res = self.testapp.get(entry_href).json_body
        course_ntiid = res['CourseNTIID']
        course_href = '/dataserver2/Objects/%s' % course_ntiid
        res = self.testapp.get(course_href).json_body
        library_href = self.require_link_href_with_rel(res, VIEW_COURSE_LIBRARY)

        def _get_package_ntiids( course_res=None, environ=admin_environ ):
            if course_res is None:
                course_res = self.testapp.get( course_href, extra_environ=environ )
                course_res = course_res.json_body
            packages = course_res['ContentPackageBundle']['ContentPackages']
            return [x['NTIID'] for x in packages]
        # Base case has only has one package
        for environ in (student1_environ, admin_environ, instructor_environ, student3_section_environ):
            content_package_ntiids = _get_package_ntiids( environ=environ )
            assert_that( content_package_ntiids, has_length(1) )
            assert_that( content_package_ntiids, contains(self.package_ntiid) )

        # Create a new package in our course, without contents.
        new_title = 'new_title'
        data = {'title': new_title,
                'Class': 'RenderableContentPackage',
                'MimeType': u'application/vnd.nextthought.renderablecontentpackage'}
        res = self.testapp.post_json( library_href, data )
        res = res.json_body
        new_package_ntiid = res['NTIID']
        package_href = res['href']
        assert_that( res['isRendered'], is_(False))
        assert_that( res.get('LatestRenderJob'), none())
        publish_href = self.require_link_href_with_rel(res, VIEW_PUBLISH)
        contents_href = self.require_link_href_with_rel(res, VIEW_CONTENTS)
        self.forbid_link_with_rel(res, VIEW_PUBLISH_CONTENTS)
        self.forbid_link_with_rel(res, VIEW_UNPUBLISH)
        self._check_package_state(new_package_ntiid)

        # Now set the contents
        self.testapp.put(contents_href,
                         upload_files=[
                            ('contents', 'contents.rst', bytes(publish_contents))])

        content_package_ntiids = _get_package_ntiids()
        assert_that( content_package_ntiids, has_length(2))
        assert_that( content_package_ntiids, contains_inanyorder(self.package_ntiid,
                                                                 new_package_ntiid))
        # Student only sees one package
        for environ in (student1_environ, instructor_environ):
            content_package_ntiids = _get_package_ntiids(environ=environ)
            assert_that( content_package_ntiids, has_length(1))
            assert_that( content_package_ntiids, contains(self.package_ntiid))
        self._check_package_state(new_package_ntiid)
        # Check page info (404s until rendered, or 403 if unublished).
        self._test_page_info(new_package_ntiid, admin_environ, status=404)
        self._test_page_info(new_package_ntiid, student1_environ, status=403)
        self._test_page_info(new_package_ntiid, instructor_environ, status=403)
        self._test_page_info(new_package_ntiid, student3_section_environ, status=403)
        self._test_get_package(new_package_ntiid, admin_environ)
        self._test_get_package(new_package_ntiid, student1_environ, status=403)
        self._test_get_package(new_package_ntiid, instructor_environ, status=403)
        self._test_get_package(new_package_ntiid, student3_section_environ, status=403)

        # Publish the package, which also renders in this case
        published_package = self.testapp.post( publish_href )
        published_package = published_package.json_body
        self.require_link_href_with_rel(published_package, VIEW_QUERY_JOB)
        assert_that( published_package['isRendered'], is_(True))
        job = published_package.get( 'LatestRenderJob' )
        # NTIID changes post-render
        published_package_ntiid = published_package['NTIID']
        assert_that( job, not_none())
        assert_that( job['State'], is_(SUCCESS))
        assert_that( published_package_ntiid, is_not(new_package_ntiid))
        self.require_link_href_with_rel(job, VIEW_QUERY_JOB)
        unpublish_href = self.require_link_href_with_rel(published_package, VIEW_UNPUBLISH)
        original_package_path = self._get_package_path(new_package_ntiid)

        # Student now sees both packages, as well as newly enrolled student
        self._create_and_enroll('student2')
        student2_environ = self._make_extra_environ(username='student2')
        for environ in (student1_environ, student2_environ, admin_environ,
                        instructor_environ, student3_section_environ):
            content_package_ntiids = _get_package_ntiids( environ=environ )
            assert_that( content_package_ntiids, has_length(2))
            assert_that( content_package_ntiids, contains_inanyorder(self.package_ntiid,
                                                                     published_package_ntiid))
        self._test_page_info(published_package_ntiid, admin_environ)
        self._test_page_info(published_package_ntiid, student1_environ)
        self._test_page_info(published_package_ntiid, student2_environ)
        self._test_page_info(published_package_ntiid, instructor_environ)
        self._test_page_info(published_package_ntiid, student3_section_environ)
        self._test_get_package(new_package_ntiid, admin_environ)
        self._test_get_package(new_package_ntiid, student1_environ)
        self._test_get_package(new_package_ntiid, instructor_environ)
        self._test_get_package(new_package_ntiid, student3_section_environ)
        self._check_package_state(published_package_ntiid, job_count=1)

        # Validate contents
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

        # Validate our published contents
        publish_contents_res = self.testapp.get( publish_contents_href )
        publish_contents_res = publish_contents_res.json_body
        assert_that( publish_contents_res['data'], is_(publish_contents))
        get_contents = self.testapp.get( contents_href )
        get_contents = get_contents.json_body
        assert_that( get_contents['data'], is_(new_contents))
        valid_version = publish_contents_res['version']

        # Now re-publish and the publish_contents rel is no longer necessary
        published_package = self.testapp.post( publish_href )
        self.forbid_link_with_rel(published_package.json_body, VIEW_PUBLISH_CONTENTS)
        self._check_package_state(published_package_ntiid, job_count=2)
        new_package_path = self._get_package_path(new_package_ntiid)
        # Path changes every render
        assert_that(new_package_path, is_not(original_package_path))

        # Validate versioning
        conflict_contents = "%s\nconflict" % publish_contents
        self.testapp.put('%s?version=%s' % (contents_href, 'invalid_version'),
                         upload_files=[
                            ('contents', 'contents.rst', bytes(conflict_contents))],
                         status=409)
        self.testapp.put('%s?version=%s' % (contents_href, valid_version),
                        upload_files=[
                            ('contents', 'contents.rst', bytes(conflict_contents))])

        # Test validation 422 (on publish/render)
        invalid_contents = b"""Chapter 1 Title
                                   ========
                            """
        self.testapp.put('%s' % contents_href,
                         upload_files=[
                            ('contents', 'contents.rst', bytes(invalid_contents))],)
        self.testapp.post( publish_href, status=422 )
        res = self.testapp.put('%s' % contents_href,
                               upload_files=[
                                    ('contents', 'contents.rst', bytes(conflict_contents))])
        res = res.json_body
        valid_version = res['version']

        # Unpublish our contents and access goes away
        res = self.testapp.post( unpublish_href, status=409 )
        res = res.json_body
        unpublish_href = self.require_link_href_with_rel(res, 'confirm')
        self.testapp.post( unpublish_href )

        content_package_ntiids = _get_package_ntiids()
        assert_that( content_package_ntiids, has_length(2))
        assert_that( content_package_ntiids, contains_inanyorder(self.package_ntiid,
                                                                 published_package_ntiid))

        for environ in (student1_environ, instructor_environ,
                        student2_environ, student3_section_environ):
            content_package_ntiids = _get_package_ntiids(environ=environ)
            assert_that( content_package_ntiids, has_length(1))
            assert_that( content_package_ntiids, contains(self.package_ntiid))
        self._check_package_state(published_package_ntiid, job_count=2)

        # Admin still has access since content is rendered
        self._test_page_info(published_package_ntiid, admin_environ)
        self._test_page_info(published_package_ntiid, student1_environ, status=403)
        self._test_page_info(published_package_ntiid, student2_environ, status=403)
        self._test_page_info(published_package_ntiid, instructor_environ, status=403)
        self._test_page_info(published_package_ntiid, student3_section_environ, status=403)
        self._test_get_package(new_package_ntiid, admin_environ)
        self._test_get_package(new_package_ntiid, student1_environ, status=403)
        self._test_get_package(new_package_ntiid, student2_environ, status=403)
        self._test_get_package(new_package_ntiid, instructor_environ, status=403)
        self._test_get_package(new_package_ntiid, student3_section_environ, status=403)

        # Test deleting the package (after republishing).
        self.testapp.post( publish_href )
        res = self.testapp.delete(package_href, status=409)
        res = res.json_body
        new_package_path = self._get_package_path(new_package_ntiid)
        # Path changes every render
        assert_that(new_package_path, is_not(original_package_path))

        force_delete_href = self.require_link_href_with_rel(res, 'confirm')
        self.testapp.delete(force_delete_href)

        # Gone from package
        for environ in (student1_environ, instructor_environ,
                        student2_environ, student3_section_environ):
            content_package_ntiids = _get_package_ntiids(environ=environ)
            assert_that( content_package_ntiids, has_length(1))
            assert_that( content_package_ntiids, contains(self.package_ntiid))

        with mock_dataserver.mock_db_trans(site_name='janux.ou.edu'):
            library = component.getUtility(IContentPackageLibrary)
            package = library.contentUnitsByNTIID.get( published_package_ntiid )
            assert_that( package, none() )
            package = library.contentUnitsByNTIID.get( new_package_ntiid )
            assert_that( package, none() )
            course = find_object_with_ntiid(self.entry_ntiid)
            course = ICourseInstance(course)
            bundle = course.ContentPackageBundle
            assert_that(bundle.ContentPackages, has_length(1))
            assert_that(bundle._ContentPackages_wrefs, has_length(1))

        # Filesystem is empty
        assert_that(os.path.exists(original_package_path), is_(False))
        assert_that(os.path.exists(new_package_path), is_(False))


        # TODOe:
        # -Failed job
