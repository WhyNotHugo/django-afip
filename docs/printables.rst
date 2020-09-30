Printable Receipts
------------------

**django-afip** supports generating PDF files for validated receipts.  This
functionality is backed mostly by three model classes:

* :class:`~.TaxPayerProfile`: Contains the TaxPayer's metadata (such as
  name, address, etc).
* :class:`~.ReceiptPDF`: Contains receipts' metadata which is required for the
  PDF generation. Since the information in ``TaxPayerProfile`` is bound to
  change over time, it's actually copied over to ``ReceiptPDF``.
* :class:`~.ReceiptEntry`: Represents a single entry (e.g.: an item in an
  invoice) in a printable receipt.

Creation of ``ReceiptPDF`` instances can generally be done with the
:meth:`~.ReceiptPDFManager.create_for_receipt` helper method.
``ReceiptEntry`` instances should be created manually.

The PDF files themselves are created the first time you save the model instance
(via a ``pre_save`` hook). You can generate (either before saving, or because
you need to regenerate it) by calling :meth:`.ReceiptPDF.save_pdf`.

Note that the ``TaxPayerProfile`` model is merely a helper one -- it's entirely
possible to construct ``ReceiptPDF`` manually without them.

Barcodes
~~~~~~~~

Generated PDFs include the barcode defined in AFIP 1702/04.

We use the receipt's expiration date for the barcode. After some
debate with fellow developers and accountants, we've resolved that the CAE's
expiration date should be used. Even though `resolution 1702/04`_ does not
explicitly state this (it just says "Expiration Date"), their own receipt PDFs
use this date.
Another argument in favour of this, is that not all receipts have expiration dates.

It was also later confirmed via a `response`_ from AFIP that the CAE expiration
should be used.

.. _resolution 1702/04: http://www.afip.gov.ar/afip/resol170204.html
.. _response: https://www.afip.gob.ar/genericos/cit/VerConsulta.aspx?evt=2SSMPS%2bjf%2f1c%2fsn%2bheAaSw%3d%3d

Exposing receipts
~~~~~~~~~~~~~~~~~

Views
.....

Printable receipts can be exposed via views. They all require a ``pk``
URL-param, so URL registration should look something like:

.. code-block:: python

    path(
        "receipts/pdf/<int:pk>",
        views.ReceiptPDFView.as_view(),
        name="receipt_view",
    ),

This uses **django_renderpdf** under the hook, and is a subclass of ``PDFView``. See
into its own documentation for finer details on the view's rendering/response
behaviour.

Note that you'll generally want to subclass these and add some form of permission
checking.

.. autoclass:: django_afip.views.ReceiptPDFView
    :members:

Templates
.........

The template used for the HTML and PDF receipts is found in
``templates/receipts/code_X.html``, where X is the :class:`~.ReceiptType`'s
code. If you want to override the default (you probably do), simply place a
template with the same path/name inside your own app, and make sure it's listed
*before* ``django_afip`` in ``INSTALLED_APPS``.

Note that you may also expose receipts as plain Django media files. The URL
will be relative or absolute depending on your media files configuration.

.. code-block:: python

    printable = ReceiptPDF.objects.last()
    printable.pdf_file
    # <FieldFile: receipts/790bc4f648e844bda7149ac517fdcf65.pdf>
    printable.pdf_file.url
    # '/media/receipts/790bc4f648e844bda7149ac517fdcf65.pdf'
