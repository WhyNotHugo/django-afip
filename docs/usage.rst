Uso
=====

Glosario
--------

Tené en cuenta estos términos mientras leas la documentación. Nótese que no
estamos reinventando nada acá, estos son los términos que usa el AFIP, aunque
pueden ser no-obvios para desarrolladores.

- **Contribuyente** / ``TaxPayer``: La persona o entidad de parte de la cual vas
  a estar generando comprobantes.
- **Comprobante** / ``Receipt``: Estos pueden ser facturas, notas de créditos,
  etc.
- **Punto de ventas** / ``PointOfSale``:  Cada punto de ventas sigue una
  sequencia de numeración propia. El punto de ventas 9 emite comprobantes con
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

Once you have created a :class:`~.TaxPayer`, you'll need its points of sales. This,
again, can be done via the admin by selecting "fetch points of sales'. You may
also do this programatically via :meth:`~.TaxPayer.fetch_points_of_sales`.

Loading Metadata
~~~~~~~~~~~~~~~~

You'll also need to pre-populate certain models with AFIP-defined metadata
(:class:`~.ReceiptType`, :class:`~.DocumentType` and a few others).

This package includes fixtures with this metadata, which can be imported by
running::

    python manage.py afipmetadata

This command is idempotent, and running it more than once will not create any
duplicate data.

This metadata can also be imported programatically, by using the function
:func:`~.models.load_metadata`. This can be useful for your unit tests.

.. hint::

    Since it's safe to run ``load_metadata`` as many times as you wish, it may
    be feasible to run this right after you run your migrations in your deploy
    script. This will make sure you always have all metadata loaded in all
    environments.

You are now ready to start creating and validating receipts. While you may do
this via the admin as well, you probably want to do this programmatically or via
some custom view.
Note that the admin views provided do very little validations - it's generally
intended as a developer tool, though it's known to be used for invoicing by a
few people who understand it's limitations.

Manually setting keys
~~~~~~~~~~~~~~~~~~~~~

This brief example shows how to set an existing key and certificate, and do all of the
above steps programatically:

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

Validating receipts
-------------------

After getting started, you should be ready to emit/validate receipts.

The first step is, naturally, to create a :class:`~.Receipt` instance. Receipts
are then sent to AFIP's web services in batches, so you can actually validate
multiple ones, by operating over a ``QuerySet``; eg:
``Receipt.objects.filter(...).validate()``.

To validate the receipts, you'll need to use :meth:`.Receipt.validate` or
:meth:`.ReceiptQuerySet.validate` .

Authorization is handled transparently, so you really shouldn't have to deal with that
manually.

Validation is also possible via the ``Receipt`` admin.

About the admin
---------------

As mentioned above, admin views are included for most models. If you need
to customize admin views, it is recommended that you subclass these and avoid
repeating anything.

Admin views are generally present for developers to check data (especially
during development and tests), or for low-volume power-users to generate their
invoices (but they really do need to know what they're doing). They **are not**
really intended for end-users, and definitely not on multi-user systems.

Forms and views
---------------

There are no forms or views included to generate receipts. This is because all usages
so far, are for automated receipt generation (e.g.: receipts are generate
programatically based on an existing order or sale).

If you have electronic records of your orders or sales, I'd suggest you do the same. If
you need forms and views, you'll need to write them yourself.

Something that's abstract/reusable enough is welcome as a PR.
