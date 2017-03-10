Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

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
