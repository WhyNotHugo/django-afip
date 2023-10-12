Uso
=====

Glosario
--------

Tené en cuenta estos términos mientras leas la documentación. Nótese que no
estamos reinventando nada acá, estos son los términos que usa el AFIP, aunque
pueden ser no-obvios para desarrolladores.

- **Contribuyente** / :class:`.TaxPayer`: La persona o entidad de parte de la
  cual vas a estar generando comprobantes.
- **Comprobante** / :class:`.Receipt`: Estos pueden ser facturas, notas de
  créditos, etc.
- **Punto de ventas** / :class:`.PointOfSales`:  Cada punto de ventas sigue una
  secuencia de numeración propia. El punto de ventas 9 emite comprobantes con
  números ``0009-00000001``, ``0009-00000002``, etc.

Cómo empezar
---------------

Antes que nada, deberías crear una instancia de la clase :class:`~.TaxPayer`.
Vas a necesitar generar claves y registrarlas con el AFIp antes de poder
continuar (más detalles más abajo).

``django-afip`` incluye un vistas del admin para cada modelo incluido, y es la
forma recomendad de crear un ``TaxPayer``, al menos durante desarrollo y
deploys iniciales.

Crear una clave privada
~~~~~~~~~~~~~~~~~~~~~~~

Hay tres formas de crear una clave privada, las cuales dan resultados equivalentes:

1. Seguí las: `instrucciones oficiales <http://www.afip.gov.ar/ws/WSAA/WSAA.ObtenerCertificado.pdf>`_.
2. Usá el método :meth:`~.TaxPayer.generate_key`. Esto genera la clave y la
   guarda en el sistema.
3. Usando el admin, usá la acción "generate key". Esto es simplemente un
   wrapper a la función (2) que te ofrece guardar el archivo que necesitás
   mandar al AFIP.

La recomendación es usar la última de estas opciones, dado que es la más fácil,
o, en caso de no estar usando el admin, la segunda opción.

Registración de clave con el AFIP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vas a necesitar registrar tu clave con el AFIP:

1. `Registrá la clave para autenticación <https://www.afip.gob.ar/ws/WSAA/wsaa_obtener_certificado_produccion.pdf>`_.
2. `Registrá la clave para facturación <https://www.afip.gob.ar/ws/WSAA/wsaa_asociar_certificado_a_wsn_produccion.pdf>`_.
3. `Creá un punto de ventas <https://serviciosweb.afip.gob.ar/genericos/guiasPasoPaso/VerGuia.aspx?id=135>`_.

Vas a obtener un certificado durante este proceso. Deberías asignar este
certificado al atributo ``certificate`` de tu ``TaxPayer`` (de nuevo, podés
hacer esto mediante el admin).

Obtención de puntos de ventas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Una vez que hayas creado un :class:`~.TaxPayer`, vas a necesitar sus puntos de
venta. Esto podés hacerlo mediante el admin (útil durando expirimentación /
desarrollo) usando "fetch points of sales", o usando
:meth:`~.TaxPayer.fetch_points_of_sales`.

Resúmen
~~~~~~~

Este ejemplo muestra como setear una clave y certificado existentes, y demás
pasos de forma programatica:

.. code-block:: python

    from django.core.files import File
    from django_afip import models

    # Create a TaxPayer object:
    taxpayer = models.TaxPayer(
        pk=1,
        name='test taxpayer',
        cuit=20329642330,
        is_sandboxed=True,
    )

    # Add the key and certificate files to the TaxPayer:
    with open('/path/to/your.key') as key:
        taxpayer.key.save('test.key', File(key))
    with open('/path/to/your.crt') as crt:
        taxpayer.certificate.save('test.crt', File(crt))

    taxpayer.save()

    # Load all metadata:
    models.load_metadata()

    # Get the TaxPayer's Point of Sales:
    taxpayer.fetch_points_of_sales()


.. TODO: estaría bueno acá un paso de revisar que todo anda y conecta okay
.. TODO: además de troubleshooting de los problemas típicos.

Validación de comprobantes
--------------------------

Tras completar los pasos anteriores ya deberías estar listo para emitir
comprobantes.

El primer paso es crear un comprobante, creando una instancia de
:class:`~.Receipt`.

Para validar el comprobante, usá el método :meth:`.Receipt.validate`.
Recomendamos no especificar un ticket explíticatmente y dejar que la librería
se encargue de la autenticación

Acerca del admin
----------------

La mayoría de los modelos incluyen vistas del admin. Si necesitás cambios, te
recomendamos usar subclases y evitar re-escribirlas.

Las vistas del admin incluídas actualmente están más orientadas a
desarrolladores (para desarrollo, testeo manual, y inspeccionar producción), o
para usuarios técnicos de bajo volúmen. **No** están diseñadas para el usuario
final o usuarios no-técnicos.

Type annotations
----------------

Most of this library's public interface includes type annotations. Applications
using this library may use ``mypy`` and ``django-stubs`` to perform
type-checking and find potential issues earlier in the development cycle.
