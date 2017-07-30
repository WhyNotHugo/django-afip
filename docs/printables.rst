Printable Receipts
------------------

Version 1.2.0 introduced PDF-generation for validated receipts.  This
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

Since version 3.2.0, PDFs include the barcode defined in AFIP 1702/04.

Version 3.2.0 used the receipt's expiration date for the barcode. After some
debate with fellow developers and accountants, we've resolved that the CAE's
expiration date should be used. Even though `resolution 1702/04`_ does not
explicitly state this (it just says "Expiration Date", their own receipt PDFs
use this date.
Also, not all receipts have expiration dates.

.. _resolution 1702/04: http://www.afip.gov.ar/afip/resol170204.html

Exposing receipts
~~~~~~~~~~~~~~~~~

Generated receipt files may be exposed both as PDF or html with an existing
view, for example, using::

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
