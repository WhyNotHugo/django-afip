django-afip
===========

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

The code is hosted at GitHub_. If you have questions or found a bug, that's
also the place to reach out.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

Features
--------

* Validate invoices and other receipt types with AFIP's WSFE service.
* Generate valid PDF files for those receipts to send to clients.

Design
------

``django-afip`` came out of the need to automate invoicing for an e-commerce.
Users place orders, pay via mercadopago, and the system generates invoices
automatically, validates them with AFIP, and then emails them to clients.

Because of this, there's no many views and forms to validate manual creation of
invoices. The admin works, but is more of a tests tool that polished for
non-tech users.

If you're wondering how to validate user input when creating invoices, ask
yourself if the information they're inputting isn't already in the system and
if they can't read if from there.

That said, if you do work on generic forms and views that validate receipts,
PRs are welcome.

Use cases
---------

**Example 1**

A self-service website allows users to services online. A few users a day make
payments, and receive an invoice by email when their payment is confirmed. No
manual intervention in required.

**Example 2**

Between hundred up to a few thousand users buy products on a website each day.
They pay using MercadoPago, and their invoice is delivered by email
immediately.

If they decide to cancel their order in time, a credit note is generated for
the same amount, and emailed to them. This "cancels out" the invoice.

Only django?
------------

If you're thinking about using some other web framework for your site, and this
put you off, I'd urge you to reconsider.

Integrating with AFIP is quite non-trivial, with many quirks. If you think
something like Flask is simpler and faster, you'll probably end up
reimplementing half of Django and this library yourself.

See `Use Django or end up building a Django <https://hackernoon.com/use-django-or-end-up-building-a-django-6cce65eb7255>`_

English or Spanish?
-------------------

Having had to work with mixed teams with developers abroad, it became natural
to use English for code and documentation (especially code, where Python is
basically English).

However, questions and support in Spanish are fine, since a great deal of the
developers using the library speak Spanish (for obvious reasons).

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
