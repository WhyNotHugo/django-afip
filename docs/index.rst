django-afip
===========

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

django-afip's official location is at its GitLab_ repository.

.. _GitLab: https://gitlab.com/hobarrera/django-afip

Features
--------

* Validate invoices and other receipt types with AFIP's WSFE service.
* Generate valid PDF files for those receipts to send to clients.

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
   api
   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
