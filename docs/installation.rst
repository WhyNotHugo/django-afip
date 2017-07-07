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





