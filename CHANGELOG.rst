Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

4.0.0
-----
* The ``ReceiptPDF.save_pdf_to`` method has been removed.
* The ``active_since`` field has been moved from ``TaxPayerProfile`` to
  ``TaxPayer``.
* Invoices in the admin will show a small asterisk if their value in the
  original currency doesn't match their value in ARS.
* The ``ReceiptPDF`` class now has a new ``client_vat_condition`` field. Newly
  created instances must define this non-nullable field.
* ``ReceiptPDF`` instances will now auto-generate the PDF file when they are
  saved if the receipt has been validated. Note that they are only generated
  ONCE, and regeneration must be done manually.

3.3.0
-----
* The ``ReceiptPDF.save_pdf_to`` method has been deprecated and will be removed
  in 4.0.0.
* VAT conditions in models are now limited to know types -- this should very
  much help create UIs and forms. If you come across a missing VAT condition,
  please open an issue for it.
* Improved the documentation surrounding PDF generation.

3.2.1
-----
* Use CAE expirations for receipt barcodes, not receipt expiration. This is the
  behaviour follows by AFIP's own generators, even though the spec doesn't
  explicitly state this.

3.2.0
-----
* New runtime dependency: pyBarcode>=0.8b1.
* The receipt class now has a ``is_validated`` property to check if a single
  instance has been validated.
* All internal errors now raise ``DjangoAfipException`` or a subclass of it.
* Add barcodes to receipt PDFs (AFIP 1702/04).
* TaxPayer certs are now blankable, which should improve admin usability, as
  well as make forms for new TaxPayers friendlier. You might need to check your
  forms if users are expected to always provide a certificate.
* Certificate expiration dates are now stored (via a pre-save hook) and exposed
  by the ``TaxPayer`` model. This should also make it impossible to upload
  garbage instead of a proper certificate file.

3.1.0
-----
* Receipt entries are now shown in the Receipts admin.
* Fix receipt entries being mis-rendered (missing quantity) in PDFs.
* Allow generating PDFs for receipts via the admin.
* Use PES (ARS) as a default currency for Receipts (only if metadata is
  present), and '1' as a currency quote.
* Customized admins are now included for a few more models.

3.0.0
-----
* The entire ``ReceiptBatch`` model has been dropped, along with
  ``Validation``. Receipts are now validated via Receipt querysets, eg:
  ``Receipt.objects.filter(...).validate()``. The existing
  ``ReceiptValidation`` objects remain unchanged.
* Validation of Receipts can now be done in a single action via the ``Receipt``
  admin.
* ``Receipt`` instances have a new ``validate()`` method to validate that
  single receipt.
* The ``receiptnumber`` tag is now deprecated. Use ``Receipt.formatted_number``
  instead.

2.7.0
-----

* Drop support for Django 1.9, support Django 1.11.
* The default ordering of ``Receipt`` instances has now changed, both via
  querysets and in the admin.
* The total amount for receipts is not shown in ARS.
* CI now run tests with all supported Python and Django versions.
* This version has experimental Django 2.0 support.
* Include a new ReceiptPDF admin.
* All exceptions now inherit from ``DjangoAfipException``.

2.6.1
-----

* Language settings of downstream apps should no longer generate bogus
  migrations for ``django-afip``.

2.6.0
-----

* It is now possible to generate keys and CSRs for taxpayers, both
  programmatically, and via the admin.
* The ``AuthTicket.authorize`` method no longer takes a ``save`` argument.
  Authorized tickets are now always immediately saved.
* Add a missing migration.

2.5.1
-----

* Fix an error validating receipts with not VAT or Tax.

2.5.0
-----

* We now rely on ``zeep``, rather ``suds``, update your dependencies
  accordingly.

2.4.0
-----

* Raise ``CertificateExpired``, ``UntrustedCertificate`` or
  ``AuthenticationError`` when attempting an authentication fail.
* The field ``ReceiptEntry.amount`` has been renamed to ``quantity``.
* Add a links to documentation on where to obtain the AFIP WS certificates.
* Introduce this changelog.
