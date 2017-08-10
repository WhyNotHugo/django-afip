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

It is recommended that you pin versions, at least to major releases, since
major releases are not guaranteed to be totally compatibility (clear upgrade
notes ARE provided though):

.. code-block:: txt

    django-afip 3.0 >= , < 4.0

.. [#] Receipt PDF generation uses weasyprint, which has some additional
       dependencies.  Consult `their documentation
       <http://weasyprint.readthedocs.io/en/stable/install.html>`_ for clear
       and up-to-date details.

Versioning
----------

We strictly follow `Semantic Versioning`_

.. _Semantic Versioning: http://semver.org/

Upgrading
---------

Backwards compatibility may break at major release, however, we always provide
migrations to upgrade existing installations (we actually always use those
ourselves on our production instances without any data loss).

Squashed Migrations
~~~~~~~~~~~~~~~~~~~

Version 4.0.0 provides squashed migrations. If you're running a *very old*
version of the app, you should upgrade to 3.3.0 and then to 4.0.0 from there.

If you run more recent versions, you should upgrade to v4.0.0 and then further,
since squashed migrations will be dropped in latter releases.

If you're working on new/non-production projects, it's safe to ignore these
warnings.
