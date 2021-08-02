Contributing
============

Feedback
--------

The preferred channel for interaction with the developers is via GitHub_,
especially since public issues will be available for others having similar
issues.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

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

Test database servers
---------------------

When running tests with postgres (or mysql), you need to run tests servers
locally. You can do this with podman or docker, using:

.. code-block:: bash

    podman run --env=POSTGRES_PASSWORD=postgres --publish=5432:5432 --name=dja-postgres postgres:13

Keep in mind that the container might take a second to initialise. This is
never an issue if you're running both commands manually, but if you're
scripting, you might want to use healthchecks (or a short delay).
