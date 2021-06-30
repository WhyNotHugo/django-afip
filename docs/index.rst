django-afip
===========

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
facturas. El admin funciona, aunque es más una herramienta de desarrollo e
inspección que algo pulido para usuario no-técnicos.

Si te encontrás necesitando validar datos cargados por el usuario para
facturación, preguntate si realmente la debería estar cargando el usuario.
Muchas veces la información ya está en algún otro sistema y es ideal leer eso
en vez de agregar una carga manual.

Aún así, son bienvenidos PRs que agreguen funcionalidad reusable de formularios
y vistas.

Casos de uso
------------

**Ejemplo 1**

Un sitio web donde cliente contratan un servicio online. Varios usuarios
diarios hacen pagos, y reciben comprobantes por email cuando su pago es
confirmado. No hay ninguna intervención humana del lado del vendedor hasta que
un pedido esté pago.

**Ejemplo 2**

Cientos o miles de clientes comprando productos a diario. Cargan sus datos de
envío, pagan con MercadoPago, y les llega una factura por mail inmediatamente.

Pueden decidir cancelar su pedido dentro de un plazo, y se genera una nota de
crédito por el mismo monto, que también es entregada por email.

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

Mantener compatibilidad con versiones viejas de Python y Django es mucho
trabajo que a nadie le interesa hacer. Soportar versiones viejas tampoco nos
permite usar funcionalidades nuevas, y hace testing muchísimo más complejo.

Recortamos las versiones soportadas, y actualmente soportamos:

* La última versión de Django y el último LTS.
* Las últimas tres versiones de Python (eg: 3.6, 3.7 and 3.8).

Versiones más viejas probablemente funcionen, pero en caso de problemas, la
primera respuesta siempre es actualizar.

Versiones más viejas de ``django-afip`` continúan funcionando con veriones
viejas de Django y Python, y lo continuarán haciendo a no ser que AFIP haga
cambios incompatibles.

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
