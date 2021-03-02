Usage
=====

Glossary
--------

Keep these terms in mind while reading this documentation. Note that we're not
reinventing anything here, this is what these terms actually means, and what AFIP calls
these. It's maybe non-obvious to developers getting started.

- **TaxPayer**: A TaxPayer is one of the taxpayers on who's behalf your application
  will be invoicing.
- **Receipt**: Generally this library deals with receipts. Receipts can be invoices,
  credit notes, and other types.
- **Point of Sale**: Each point of sales has its own unique sequence of receipt
  numbers. Point of sale 9 will emit receipts ``0009-00000001``, ``0009-00000002``, and so
  forth.

Getting started
---------------

First of all, you'll need to create a :class:`~.TaxPayer` instance.
You'll then need to create keys and register with them with AFIP before continuing
(more on this below).

django-afip includes admin views for every model included, and it's the
recommended way to create `TaxPayer` objects (at least during
development/testing).

Creating a private key
~~~~~~~~~~~~~~~~~~~~~~

There are three ways to create a private key, and the result of any work fine:

1. Follow the official `instructions <http://www.afip.gov.ar/ws/WSAA/WSAA.ObtenerCertificado.pdf>`_.
2. Use the :meth:`~.TaxPayer.generate_key` method. This will generate a key for you, and
   save if for the TaxPayer.
3. Visit the Django admin, and use the "generate key" action. This just wraps around
   the above method, and prompts you to download the key.

I'd recommend you use the latter, since it's the easiest, or the second if you would
really like to avoid using the Django admin.

Registering the key with the AFIP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll then need to register the generated key with the AFIP:

1. `Register a key for authentication <https://www.afip.gob.ar/ws/WSAA/wsaa_obtener_certificado_produccion.pdf>`_.
2. `Register a key for invoicing key <https://www.afip.gob.ar/ws/WSAA/wsaa_asociar_certificado_a_wsn_produccion.pdf>`_.
3. `Create a point of sales <https://serviciosweb.afip.gob.ar/genericos/guiasPasoPaso/VerGuia.aspx?id=135>`_.

You'll obtain a certificate during this process. You should assign this to the
TaxPayer's ``certificate`` attribute (again, you can do this using the Django admin).

Fetching points of sales
~~~~~~~~~~~~~~~~~~~~~~~~

Once you have created a :class:`~.TaxPayer`, you'll need its points of sales. This,
again, can be done via the admin by selecting "fetch points of sales'. You may
also do this programatically via :meth:`~.TaxPayer.fetch_points_of_sales`.

Loading Metadata
~~~~~~~~~~~~~~~~

You'll also need to pre-populate certain models with AFIP-defined metadata
(:class:`~.ReceiptType`, :class:`~.DocumentType` and a few others).

This package includes fixtures with this metadata, which can be imported by
running::

    python manage.py afipmetadata

This command is idempotent, and running it more than once will not create any
duplicate data.

This metadata can also be imported programatically, by using the function
:func:`~.models.load_metadata`. This can be useful for your unit tests.

You are now ready to start creating and validating receipts. While you may do
this via the admin as well, you probably want to do this programmatically or via
some custom view.
Note that the admin views provided do very little validations - it's generally
intended as a developer tool, though it's known to be used for invoicing by a
few people who understand it's limitations.

Manually setting keys
~~~~~~~~~~~~~~~~~~~~~

This brief example shows how to set an existing key and certificate, and do all of the
above steps programatically:

.. code-block:: python

    from django.core.files import File
    from django_afip import models

    # Create a TaxPayer object:
    taxpayer = models.TaxPayer(
        pk=1,
        name='test taxpayer',
        cuit=20329642330,
        is_sandboxed=True,
    )

    # Add the key and certificate files to the TaxPayer:
    with open('/path/to/your.key') as key:
        taxpayer.key.save('test.key', File(key))
    with open('/path/to/your.crt') as crt:
        taxpayer.certificate.save('test.crt', File(crt))

    taxpayer.save()

    # Load all metadata:
    models.load_metadata()

    # Get the TaxPayer's Point of Sales:
    taxpayer.fetch_points_of_sales()

Validating receipts
-------------------

After getting started, you should be ready to emit/validate receipts.

The first step is, naturally, to create a :class:`~.Receipt` instance. Receipts
are then sent to AFIP's web services in batches, so you can actually validate
multiple ones, by operating over a ``QuerySet``; eg:
``Receipt.objects.filter(...).validate()``.

To validate the receipts, you'll need to use :meth:`.Receipt.validate` or
:meth:`.ReceiptQuerySet.validate` .

Authorization is handled transparently, so you really shouldn't have to deal with that
manually.

Validation is also possible via the ``Receipt`` admin.

About the admin
---------------

As mentioned above, admin views are included for most models. If you need
to customize admin views, it is recommended that you subclass these and avoid
repeating anything.

Admin views are generally present for developers to check data (especially
during development and tests), or for low-volume power-users to generate their
invoices (but they really do need to know what they're doing). They **are not**
really intended for end-users, and definitely not on multi-user systems.

Forms and views
---------------

There are no forms or views included to generate receipts. This is because all usages
so far, are for automated receipt generation (e.g.: receipts are generate
programatically based on an existing order or sale).

If you have electronic records of your orders or sales, I'd suggest you do the same. If
you need forms and views, you'll need to write them yourself.

Something that's abstract/reusable enough is welcome as a PR.
