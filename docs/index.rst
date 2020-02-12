django-afip
===========

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

django-afip's official location is at its GitHub_ repository.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

Features
--------

* Validate invoices and other receipt types with AFIP's WSFE service.
* Generate valid PDF files for those receipts to send to clients.

Requirements
------------

It's been quite some pain dealing with older django and python versions.
Supporting older versions doesn't allow us to use new features, and makes
testing a lot more complex (including CI).

We've therefore decided to trim the officially supported versions to:

* The latest Django release, and the last LTS release.
* The three latest Python releases (eg: 3.6, 3.7 and 3.8).

Older versions of both may work, however, in case of any issues, only these
version are supported.

Note that older django-afip versions will continue to work fine on older
django+python versions.

Caveats
-------

While the app can have production and sandbox users co-exist, metadata models
(tax types, receipt types, etc) will be shared between both. In theory, these
should never diverge upstream. If they do, we are not prepared to handle it
(though it is expected that an update will be available when this change is
announced upstream).

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   installation
   usage
   printables
   api
   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
