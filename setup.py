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
    install_requires=open('requirements.txt').read().splitlines()[:-1] +
        ['suds-py3==1.0.0.0'],
    dependency_links=(
        'git+https://github.com/hobarrera/suds-py3.git#egg=suds-py3-1.0.0.0',
    ),
    use_scm_version={'version_scheme': 'post-release'},
    setup_requires=['setuptools_scm'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
