API
===

Core models
-----------

These are the code models which will normally be used for  ``Receipt`` validation.

.. autoclass:: django_afip.models.PointOfSales
    :members:
.. autoclass:: django_afip.models.Receipt
    :members:
.. autoclass:: django_afip.models.ReceiptValidation
    :members:
.. autoclass:: django_afip.models.Tax
    :members:
.. autoclass:: django_afip.models.TaxPayer
    :members:
.. autoclass:: django_afip.models.Vat
    :members:

PDF-related models
------------------

These models are used only for PDF generation, or can be used for storing
additional non-validated metadata. You DO NOT need any of these classes
unless you intend to generate PDFs for receipts.

.. autoclass:: django_afip.models.ReceiptEntry
    :members:
.. autoclass:: django_afip.models.ReceiptPDF
    :members:
.. autoclass:: django_afip.models.TaxPayerProfile
    :members:

Metadata models
---------------

These models represent metadata like currency types or document types. Their
tables should be populated from AFIP's webservices, using the ``afipmetadata``
command.

.. autofunction:: django_afip.models.populate_all

.. autoclass:: django_afip.models.ConceptType
    :members:
.. autoclass:: django_afip.models.CurrencyType
    :members:
.. autoclass:: django_afip.models.DocumentType
    :members:
.. autoclass:: django_afip.models.Observation
    :members:
.. autoclass:: django_afip.models.ReceiptType
    :members:
.. autoclass:: django_afip.models.TaxType
    :members:
.. autoclass:: django_afip.models.VatType
    :members:

Managers
~~~~~~~~

Managers should be accessed via models. For example, ``ReceiptManager``
should be accessed using ``Receipt.objects``.

.. autoclass:: django_afip.models.ReceiptManager
    :members:
.. autoclass:: django_afip.models.ReceiptPDFManager
    :members:

QuerySets
---------

QuerySets are generally accessed via their models. For example,
``Receipt.objects.filter()`` will return a ``ReceiptQuerySet``.

.. autoclass:: django_afip.models.ReceiptQuerySet
    :members:
