#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name='django-afip',
    description='AFIP integration for django',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://github.com/WhyNotHugo/django-afip',
    license='ISC',
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=[
        'django>=2.0.0',
        'django_renderpdf>=0.1.0',
        'lxml>=3.4.4',
        'pyopenssl>=16.2.0',
        'python-barcode>=0.8.0',
        'pytz>=2015.4',
        'setuptools-git>=1.1',
        'setuptools-scm>=1.7.0',
        'wheel>=0.24.0',
        'zeep>=1.1.0',
    ],
    extras_require={
        'docs': ['Sphinx', 'sphinx-autobuild'],
        'postgres': ['psycopg2'],
        'mysql': ['mysqlclient'],
        'factories': ['factory-boy'],
    },
    use_scm_version={
        'version_scheme': 'post-release',
        'write_to': 'django_afip/version.py',
    },
    setup_requires=['setuptools_scm'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
