django-afip
===========

(:ref:`See here for English <English>`)

**django-afip** es una aplicación Django para interactuar con los web-services
del AFIP. Actualmente están implementados WSFE y WSAA.

El código está actualmente en GitHub_. Si tenés alguna pregunta o duda, ese es
el lugar donde consultar.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

Funcionalidades
---------------

* Validar comprobantes (facturas y otros tipos) con el servicio WSFE del AFIP.
* Generar PDFs de comprobantes validados (listos para enviar a clientes).

Diseño
------

``django-afip`` nació de la necesidad de automatizar facturación para un
e-commerce. Los clientes arman su pedido, pagan online, y el sistema genera
facturas automáticamente, las valida con el AFIP, y se las manda por email.

Actualmente no hay vistas ni formularios para manualmente crear o validar
facturas. El admin funciona, pero es más una herramienta de desarrollo e
inspección que algo pulido para usuario no-técnicos.

Generalmente los casos de uso son no-interactivos, donde las facturas son
generadas automáticamente en base a modelos pre-existentes (por ejemplo, con
datos de pedidos en el mismo u otro sistema), por lo cual no hay demasiada
funcionalidad relacionada a validar input manual.

Si te encontrás necesitando validar datos cargados por el usuario para
facturación, preguntate si realmente la debería estar cargando el usuario.
Muchas veces la información ya está en algún otro sistema y es ideal leer eso
en vez de agregar una carga manual.

Aún así, son bienvenidos parches que agreguen funcionalidad reusable de
formularios, vistas o serializers para DRF.

Sólo Django?
------------

Si estás considerando usar otro framework web en Python, y el hecho de que
esto esté implementado en Django te desmotiva, te insto a reconsiderar.

Integrar con servicios del AFIP es algo no-trivial, y tiene muchas
peculiaridades. Is pensás que usar algo como Flask va a ser más sencillo y
rápido, probablemente termines re-implementando la mitad de Django y esta
librería a mano. Podría evitarte ese trabajo usando algo ya-hecho.


Recomiendo ver este artículo en el tema:
`Use Django or end up building a Django <https://hackernoon.com/use-django-or-end-up-building-a-django-6cce65eb7255>`_

Requisito
---------

Actualmente **django-afip** funciona con:

* Django 3.0, 3.1 y 3.1
* Python 3.8, 3.9, 3.10 and 3.11
* Posgres, Sqlite, MySql/MariaDB

Te recomendamos usar Postgres.

Versiones más viejas de ``django-afip`` continúan funcionando con veriones
viejas de Django y Python, y lo continuarán haciendo a no ser que AFIP haga
cambios incompatibles. Sin embargo, no recibirán nueva funcionalidades ni
actualizaciones en caso de que AFIP haga cambios a sus webservices.

Tabla de contenidos
===================

.. toctree::
   :maxdepth: 2

   installation
   usage
   printables
   api
   contributing
   changelog

Índices y tablas
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _English:

English
=======

**django-afip** is a django application for interacting with AFIP's
web-services (and models all related data).

AFIP is Argentina's tax collection agency, which requires invoices and other
receipts be informed to them via a WSDL-based API.

Initially this project and its documentation was fully available in English,
since one of the applications using it had contributors from abroad.

This is no longer the case, and given that, naturally, most developers seeks to
use this library are from Argentina, documentation has been translated to make
collaboration simpler.

Feel free to open issue in English if that's you're native tongue. Paid
consultancy for integrations is also available.
