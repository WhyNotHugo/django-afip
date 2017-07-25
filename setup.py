#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name='django-afip',
    description='AFIP integration for django',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://gitlab.com/hobarrera/django-afip',
    license='ISC',
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=open('requirements.txt').read().splitlines() + [
        'Django>=1.8.4'
    ],
    extras_require={
        'docs': ['Sphinx', 'sphinx-autobuild']
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
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
