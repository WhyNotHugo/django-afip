#!/usr/bin/env python3
from __future__ import annotations

from setuptools import find_packages
from setuptools import setup

with open("README.rst") as f:
    readme = f.read()

setup(
    name="django-afip",
    description="AFIP integration for django",
    author="Hugo Osvaldo Barrera",
    author_email="hugo@barrera.io",
    url="https://github.com/WhyNotHugo/django-afip",
    project_urls={
        "Documentation": "https://django-afip.readthedocs.io/",
        "Issue Tracker": "https://github.com/WhyNotHugo/django-afip/issues",
        "Donate": "https://liberapay.com/WhyNotHugo/",
        "Changelog": "https://django-afip.readthedocs.io/en/latest/changelog.html",
    },
    license="ISC",
    packages=find_packages(exclude=["testapp"]),
    include_package_data=True,
    long_description=readme,
    long_description_content_type="text/x-rst",
    install_requires=[
        "cryptography>=3.2,<40",
        "django>=3.2,<4.3",
        "django_renderpdf>=3.0.0,<5.0.0",
        "lxml>=3.4.4",
        "pyopenssl>=16.2.0",
        'backports.zoneinfo;python_version<"3.9"',
        "setuptools-git>=1.1",
        "wheel>=0.24.0",
        "zeep>=1.1.0,<5.0.0",
        "qrcode[pil]>=6.1,<8.0",
        "pyyaml>=5.3.1,<7.0.0",
    ],
    extras_require={
        "docs": ["Sphinx", "sphinx-autobuild", "sphinx_rtd_theme"],
        "postgres": ["psycopg2"],
        "mysql": ["mysqlclient"],
        "factories": ["factory-boy"],
    },
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
