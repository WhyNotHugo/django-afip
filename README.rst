django-afip
===========

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data). For the moment only WSFE and WSAA
are implemented.

Instalation
-----------

First install the actual package::

    pip install django-afip

And then configure your project to use it by adding it to settings.py::

    INSTALLED_APPS = (
        ...
        'django_afip',
        ...
    )

If you want to use AFIP's testing servers, then you'll need to configure the
app to do so::

    AFIP_DEBUG = True

Getting started
---------------

First of all, you'll need to create a taxpayer, and upload the related ssl key and
certificate (for authorization). django-afip includes admin views for every
model included, and it's the recomended way to create one.

Secondly, you'll need to pre-populate certain models with AFIP-defined data.
Rather than include fixtures which require updating over time, a special view
has been included for importing them from the WS with live data. Only a
superuser can activate this population.

To access this view, add something like this to your views.py::

    urlpatterns = [
        ...
        url(r'^__afip__/', include('django_afip.urls')),
        ...
    ]

Then visit http://example.com/__afip__/populate_models. This will retrieve
Receipt Types, Document Types, and a few other data types from AFIP's WS.
Again, only a user with superuser priviledges will trigger this download.

You are now ready to start creating and validating receipts.

Licence
-------

This software is distributed under the ISC licence. See LICENCE for details.

Copyright (c) 2015 Hugo Osvaldo Barrera <hugo@barrera.io>
