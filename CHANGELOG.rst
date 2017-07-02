Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

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
