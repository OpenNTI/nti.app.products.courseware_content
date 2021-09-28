import codecs
from setuptools import setup, find_packages


entry_points = {
    'console_scripts': [
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.app.products',
    ],
}

TESTS_REQUIRE = [
    'nti.app.products.courseware[test]',
    'nti.app.testing',
    'nti.testing',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.app.products.courseware_content',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="Umbrella product to support integrated courseware and content",
    long_description=(_read('README.rst') + '\n\n' + _read("CHANGES.rst")),
    license='Apache',
    keywords='pyramid course content',
    classifiers=[
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.app.products.courseware_content",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti', 'nti.app', 'nti.app.products'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'docutils',
        'nti.app.contentlibrary_rendering',
        'nti.app.contentlibrary',
        'nti.app.products.courseware',
        'nti.app.publishing',
        'nti.base',
        'nti.common',
        'nti.contentlibrary',
        'nti.contentlibrary_rendering',
        'nti.contenttypes.courses',
        'nti.coremetadata',
        'nti.externalization',
        'nti.links',
        'nti.namedfile',
        'nti.ntiids',
        'nti.publishing',
        'nti.site',
        'pyramid',
        'six',
        'zope.cachedescriptors',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.security',
        'zope.traversing',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)
