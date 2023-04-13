django-afip
===========

.. image:: https://github.com/WhyNotHugo/django-afip/actions/workflows/tests.yml/badge.svg
  :target: https://github.com/WhyNotHugo/django-afip/actions/workflows/tests.yml
  :alt: unit tests

.. image:: https://github.com/WhyNotHugo/django-afip/actions/workflows/live.yml/badge.svg
  :target: https://github.com/WhyNotHugo/django-afip/actions/workflows/live.yml
  :alt: integrations tests

.. image:: https://results.pre-commit.ci/badge/github/WhyNotHugo/django-afip/main.svg
  :target: https://results.pre-commit.ci/latest/github/WhyNotHugo/django-afip/main
  :alt: pre-commit.ci status

.. image:: https://readthedocs.org/projects/django-afip/badge/?version=latest
  :target: http://django-afip.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/dm/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: downloads

.. image:: https://img.shields.io/pypi/l/django-afip.svg
  :target: https://github.com/WhyNotHugo/django-afip/blob/main/LICENCE
  :alt: licence

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/WhyNotHugo/django-afip/
  :alt: code style: black

What's this?
------------

AFIP is Argentina's tax collection agency. For emitting invoices, taxpayers are
required to inform AFIP of each invoice by using a dedicated SOAP-like web
service for that.

**django-afip** is a Django application implementing the necessary bits for
Django-based applications to both store and comunícate invoicing information.

Features
--------

* Validate invoices and other receipt types with AFIP's WSFE service.
* Generate valid PDF files for those receipts to send to clients.

Documentation
-------------

The full documentation is available at https://django-afip.readthedocs.io/

Changelog
---------

The changelog is published with the rest of the documentation:
https://django-afip.readthedocs.io/en/stable/changelog.html

Donate
------

While some of the work done here is done for clients, much of it is done in my
free time. If you appreciate the work done here, please consider donating_.

.. _donating: https://github.com/sponsors/WhyNotHugo

Licence
-------

This software is distributed under the ISC licence. See LICENCE for details.

Copyright (c) 2015-2022 Hugo Osvaldo Barrera <hugo@barrera.io>
