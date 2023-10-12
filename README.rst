django-afip
===========

.. image:: https://img.shields.io/pypi/v/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/dm/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: downloads

.. image:: https://img.shields.io/pypi/l/django-afip.svg
  :target: https://github.com/WhyNotHugo/django-afip/blob/main/LICENCE
  :alt: licence

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

It is also possible to build the documentation from source using:

.. code-block:: sh

    tox -e docs

Changelog
---------

The changelog is included with the rest of the documentation:
https://django-afip.readthedocs.io/en/stable/changelog.html

Donate
------

While some of the work done here is done for clients, much of it is done in my
free time. If you appreciate the work done here, please consider donating_.

.. _donating: https://whynothugo.nl/sponsor/

Licence
-------

This software is distributed under the ISC licence. See LICENCE for details.

Copyright (c) 2015-2022 Hugo Osvaldo Barrera <hugo@barrera.io>
