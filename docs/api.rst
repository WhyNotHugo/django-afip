API
===

Core models
-----------

These are the code models which will normally be used for  ``Receipt`` validation.

.. autoclass:: django_afip.models.PointOfSales
    :members:
.. autoclass:: django_afip.models.Receipt
    :members:
.. autoclass:: django_afip.models.ReceiptBatch
    :members:
.. autoclass:: django_afip.models.ReceiptValidation
    :members:
.. autoclass:: django_afip.models.Tax
    :members:
.. autoclass:: django_afip.models.TaxPayer
    :members:
.. autoclass:: django_afip.models.Validation
    :members:
.. autoclass:: django_afip.models.Vat
    :members:

Managers
~~~~~~~~

Managers should be accessed via models. For example, ``ReceiptBatchManager``
should be accessed using ``ReceiptBatch.objects``.

.. autoclass:: django_afip.models.ReceiptBatchManager
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
