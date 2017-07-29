Usage
=====

Getting started
---------------

First of all, you'll need to create a :class:`~.TaxPayer`
instance, and upload the related SSL key and certificate (for authorization).

Official documentation for obtaining the certificate is available
`here <http://www.afip.gov.ar/ws/WSAA/WSAA.ObtenerCertificado.pdf>`_, and for
delegation `here <http://www.afip.gov.ar/ws/WSAA/ADMINREL.DelegarWS.pdf>`_.

django-afip includes admin views for every model included, and it's the
recommended way to create :class:`~.TaxPayer` objects (at least during
development/testing).

Once you have created a :class:`~.TaxPayer`, you'll need its points of sales. This,
again, can be done via the admin by selecting "fetch points of sales'. You may
also do this programmatically via :meth:`~.TaxPayer.fetch_points_of_sales`.

Metadata populuation
~~~~~~~~~~~~~~~~~~~~

You'll also need to pre-populate certain models with AFIP-defined metadata
(:class:`~.ReceiptType`, :class:`~.DocumentType` and a few others).

Rather than include fixtures which require updating over time, we fetch this
information from AFIP's web services via an included django management command.
This command is idempotent, and running it more than once will not create any
duplicate data. To fetch all metadata, simply run::

    python manage.py afipmetadata

This metadata can also be downloaded programmatically, via
:func:`~.models.populate_all`.

You are now ready to start creating and validating receipts. While you may do
this via the admin as well, you probably want to do this programmatically or via
some custom view.
Note that the admin views provided do very little validations - it's generally
intended as a developer tool, though it's known to be used for invoicing by a
few people who understand it's limitations.

Example
~~~~~~~

This brief example shows how to achieve the above::

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
    models.populate_all()

    # Get the TaxPayer's Point of Sales:
    taxpayer.fetch_points_of_sales()

Validating receipts
-------------------

After getting started, you should be ready to emit/validate receipts.

The first step is, naturally, to create a :class:`~.Receipt` instance. Receipts
are then sent to AFIP's web services in batches, so you van actually validate
multiple ones, by operating over a ``QuerySet``; eg:
``Receipt.objects.filter(...).validate()``.

To validate the receipts, you'll need to use :meth:`.Receipt.validate` or
:meth:`.ReceiptQuerySet.validate` .  Authorization is handled transparently
(consult the API documentation if you'd prefer to do this manually).

Validation is also possible via the ``Receipt`` admin.

About the admin
---------------

As mentioned above, admin views are included for most models. If you need
to customize admin views, it is recommended that you subclass these and aviod
repeating anything.

Admin views are generally present for developers to check data (especially
during development and tests), or for low-volume power-users to generate their
invoices (but they really do need to know what they're doing). They are not
really intended for end-users, and definitely not on multi-user systems.
