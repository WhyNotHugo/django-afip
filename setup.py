#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='django-afip',
    version='0.8.0',
    description='AFIP integration for django',
    author='Hugo Osvaldo Barrera',
    author_email='hbarrera@z47.io',
    url='https://gitlab.com/hobarrera/django-afip',
    license='ISC',
    packages=find_packages(),
    # long_description=open('README.rst').read(),
    install_requires=open('requirements.txt').read().splitlines()[:-1] +
        ['suds-py3==1.0.0.0'],
    dependency_links=(
        'git+https://github.com/hobarrera/suds-py3.git#egg=suds-py3-1.0.0.0',
    ),
    use_scm_version={'version_scheme': 'post-release'},
    setup_requires=['setuptools_scm'],
)
