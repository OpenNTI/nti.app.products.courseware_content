import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
	],
	"z3c.autoinclude.plugin": [
		'target = nti.app.products',
	],
}

setup(
	name='nti.app.products.courseware_content',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="Umbrella product to support integrated courseware and content",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='pyramid course content',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Framework :: Pyramid',
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti', 'nti.app', 'nti.app.products'],
	install_requires=[
		'setuptools'
	],
	entry_points=entry_points
)
