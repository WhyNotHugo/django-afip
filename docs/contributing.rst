Contributing
============

Feedback
--------

The preferred channel for interaction with the developers is via GitLab_,
especially since public issues will be available for others having similar
issues.

.. _GitLab: https://gitlab.com/hobarrera/django-afip

Hacking
-------

Unit tests are run via ``tox``. Any code contributions must pass all tests. New
features must include corresponding unit tests. Any bugfixes must include tests
that fail without it, and pass with it.

Note that tests use AFIP's testing servers and a specific key that's know to
contain at least one point of sale.

CI
--

CI does not use the in-tree test key/certificate, but ones provided via
environment variables. This allows re-running older commits after their in-tree
certificate has expired, by merely updating the CI configuration.

Note that the CI variables need to have newlines replaced with the ``\n``
sequence.
