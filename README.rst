django-afip
===========

.. image:: https://gitlab.com/WhyNotHugo/django-afip/badges/master/build.svg
  :target: https://gitlab.com/WhyNotHugo/django-afip/commits/master
  :alt: build status

.. image:: https://readthedocs.org/projects/django-afip/badge/?version=latest
  :target: http://django-afip.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/django-afip.svg
  :alt: licence

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

Features
--------

* Validate invoices and other receipt types with AFIP's WSFE service.
* Generate valid PDF files for those receipts to send to clients.

Documentation
-------------

For detailed configuration, have a look at the latest docs at readthedocs_.

.. _readthedocs: https://django-afip.readthedocs.io/

Licence
-------

This software is distributed under the ISC licence. See LICENCE for details.

Copyright (c) 2015-2017 Hugo Osvaldo Barrera <hugo@barrera.io>
