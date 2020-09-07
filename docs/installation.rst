Installation
============

Actual package installation is quite simple and can be done via pip.
Dependencies should be handled by pip fine [#]_:

.. code-block:: python

    pip install django-afip

You'll then need to configure your project to use this app by adding it to your
``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_afip',
        ...
    )

Make sure to run all migrations after you've added the app:

.. code-block:: python

    python manage.py migrate afip

.. [#] Receipt PDF generation uses weasyprint, which has some additional
       dependencies.  Consult `their documentation
       <http://weasyprint.readthedocs.io/en/stable/install.html>`_ for clear
       and up-to-date details.

Configuration
-------------

It is also possible (yet optional) to define optional storages for files used
by the app.  If undefined, the default file storage is used.

The value of these settings should be a string with the path to the instance of
a storage to use (eg: ``'myapp.storages.my_private_storage'``). Both S3 and
the default storages have been tested, but any django-compatible storage should
work just fine. See the django documentation for more details on storages.

.. code-block:: python

    AFIP_KEY_STORAGE  # Keys for authenticating with AFIP (TaxPayer.key)
    AFIP_CERT_STORAGE  # Certs for auth'ing with AFIP (TaxPayer.certificate)
    AFIP_PDF_STORAGE  # PDFs generated for receipts (ReceiptPDF.pdf_file)
    AFIP_LOGO_STORAGE  # Logos used in invoices (TaxPayerExtras.logo)


Versioning
----------

It is recommended that you pin versions, at least to major releases, since
major releases are not guaranteed to be totally compatibility (clear upgrade
notes ARE provided though):

.. code-block:: txt

    django-afip>=4.0,< 5.0

We strictly follow `Semantic Versioning`_. We only support version of Django
that are currently supported upstream.

Django-afip is compatible with all `currently supported django versions`_.

.. _Semantic Versioning: http://semver.org/
.. _currently supported django versions: https://www.djangoproject.com/download/#supported-versions

Upgrading
---------

Backwards compatibility may break at major release, however, we always provide
migrations to upgrade existing installations (I actually always use those
on multiple production instances without any data loss).

.. warning::

    If you're on a pre-v4.0.0 release, you should upgrade to v4.0.0 and then
    further, since migrations will be squashed and purged in  latter releases.

    If you're working on new/non-production projects, it's safe to ignore this
    warning (though you'll have to drop your current DB).
