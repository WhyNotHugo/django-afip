django-afip
===========

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

.. image:: https://ci.gitlab.com/projects/7545/status.png?ref=master
  :target: https://ci.gitlab.com/projects/7545?ref=master
  :alt: build status

.. image:: https://img.shields.io/pypi/v/django-afip.svg
  :target: https://pypi.python.org/pypi/django-afip
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/django-afip.svg
  :alt: licence

Instalation
-----------

First install the actual package::

    pip install django-afip

And then configure your project to use it by adding it to settings.py::

    INSTALLED_APPS = (
        ...
        'django_afip',
        ...
    )

Getting started
---------------

First of all, you'll need to create a TaxPayer instance, and upload the related
ssl key and certificate (for authorization).
django-afip includes admin views for every model included, and it's the
recommended way to create one.

Once you have created a TaxPayer, you'll need its points of sales. This, again,
can be done via the admin by selecting "fetch points of sales'. You may also
do this programmatically via `TaxPayer.fetch_points_of_sales`.

Finally, you'll need to pre-populate certain models with AFIP-defined metadata.

Rather than include fixtures which require updating over time, a special view
has been included for importing them from the WS with live data. Only a
superuser can activate this population. This view is idempotent, and running it
more than once will not create any duplicate data.

To access this view, add something like this to your views.py::

    urlpatterns = [
        ...
        url(r'^__afip__/', include('django_afip.urls')),
        ...
    ]

Then visit http://example.com/__afip__/populate_models. This will retrieve
Receipt Types, Document Types, and a few other data types from AFIP's WS.
Again, only a user with superuser privileges may trigger this download.

This metadata can also be downloaded programmatically, via
``models.populate_all()``.

You are now ready to start creating and validating receipts. While you may do
this via the admin as well, you probably want to do this programmatically or via
some custom view.

PDF Receipts
------------

Version 1.2.0 introduces PDF-generation for validated receipts. These PDFs are
backed by the ``ReceiptPDF`` model.

There are two ways of creating these objects; you can do this manually, or via
these steps:

 * Creating a ``TaxPayerProfile`` object for your ``TaxPayer``, with the right
   default values.
 * Create the PDFs via ``ReceiptPDF.objects.create_for_receipt()``.
 * Add the proper ``ReceiptEntry`` objects to the ``Receipt``. Each
   ``ReceiptEntry`` represents a line in the resulting PDF file.

The PDF file itself can then be generated via::

    # Save the file as a model field into your MEDIA_ROOT directory:
    receipt_pdf.save_pdf()
    # Save to some custom file-like-object:
    receipt_pdf.save_pdf_to(file_object)

The former is usually recommended since it allows simpler interaction via
standard django patterns.

Exposing receipts
~~~~~~~~~~~~~~~~~

Generated PDF files may be exposed both as pdf or html with an existing view,
for example, using::

    url(
        r'^invoices/pdf/(?P<pk>\d+)?$',
        views.ReceiptPDFView.as_view(),
        name='receipt_view',
    ),
    url(
        r'^invoices/html/(?P<pk>\d+)?$',
        views.ReceiptHTMLView.as_view(),
        name='receipt_view',
    ),

You'll generally want to subclass this view, and add some authorization checks
to it. If you want some other, more complex generation (like sending via
email), these views should serve as a reference to the PDF API.

The template used for the HTML and PDF receipts is found in
``templates/django_afip/invoice.html``. If you want to override the default (you
probably do), simply place a template with the same path/name inside your own
app, and make sure it's listed *before* ``django_afip`` in ``INSTALLED_APPS``.

Contributing
------------

Unit tests are run via ``tox``. Any code contributions must pass all tests. New
features must include corresponding unit tests. Any bugfixes must include tests
that fail without it, and pass with it.

Note that tests use AFIP's testing servers and a specific key that's know to
contain at least one point of sale.

Caveats
-------

While the app can have production and sandbox users co-exist, metadata models
(tax types, receipt types, etc) will be shared between both. In theory, these
should never diverge upstream. If they do, we are not prepared to handle it
(though it is expected that an update will be available when this change is
announced upstream).

Licence
-------

This software is distributed under the ISC licence. See LICENCE for details.

Copyright (c) 2015 Hugo Osvaldo Barrera <hugo@barrera.io>
