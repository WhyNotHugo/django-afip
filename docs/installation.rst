Instalación
===========

Podés instalar este paquete usando pip:

.. code-block:: sh

    pip install django-afip

La generación de PDFs usa ``weasyprint``, que tiene algunas dependencias
adicionales. Consultá :doc:`su documentación <weasyprint:first_steps>` para
instrucciones detalladas al día.

Recomendamos usar algo como Poetry_ para manejar dependencias y asegurarte de
que las versiónes de tus dependencies no cambien de repente sin tu
intervención.

.. _Poetry: https://python-poetry.org/

Settings
--------

Vas a necesitar agregar la aplicación al ``settings.py`` de tu proyecto:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_afip',
        ...
    )

Asegurate de correr todas las migraciones después de agregar la app:

.. code-block:: sh

    python manage.py migrate afip

Vas a necesitar correr las migraciones en cada ambiente / base de datos que
uses.

Cada versión nueva de django-afip puede incluir nuevas migraciones, y
recomendamos seguir la práctica estándar de correr las migraciones en cada
deploy.

Metadatos
---------

Vas a necesitar algunos metadatos adicionales para poder hacer integraciones.
Esto son "Tipos de comprobante" (:class:`~.ReceiptType`), "Tipos de documento"
(:class:`~.DocumentType`), y :ref:`unos cuantos más <metadata-models>`.

Estos metadatos están disponibles via la API de AFIP, pero esta librería
incluye esos mismos datos como fixtures que podés importar fácilmente::

    python manage.py afipmetadata

Este comando es idempotente, y correrlo más de una vez no crea datos
duplicados.

Los metadatos también pueden ser importados programáticamente, usando
:func:`~.models.load_metadata`. Esto es útil para tests unitarios que dependan
de su existencia.

.. hint::

    Es necesario importar estos datos en cada instancia / base de datos, al igual
    que migraciones. La recomendación es correr el comando de arriba en el mismo
    script que dispare las migraciones. Esto asegura que todos tus ambientes
    siempre tengan metadatos al día.

Almacenamiento
--------------

También es posible (y opcional) definir varios :doc:`Storage
<django:ref/files/storage>` para los archivos de la app. Si no están definidos,
se usará el Storage predeterminado.

Podés configurar storages personalizados usando el setting :setting:`STORAGES`
de Django con los siguientes alias:

.. code-block:: python

    STORAGES = {
        # …default storages…
        "afip_keys": {  # Clave para autenticación con el AFIP. (TaxPayer.key)
            "BACKEND": "myapp.storages.PrivateStorage",
        },
        "afip_certs": {  # Certificados para autenticación con el AFIP (TaxPayer.certificate)
            "BACKEND": "myapp.storages.PrivateStorage",
        },
        "afip_pdfs": {  # PDFs generados para comprobantes (ReceiptPDF.pdf_file)
            "BACKEND": "myapp.storages.ClientStorage",
        },
        "afip_logos": {  # Logos usados para comprobantes (TaxPayer.logo)
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
    }

Si estás exponiendo tu Storage predeterminado a la web (que suele ser el caso
en muchas aplicaciones), es importante, como mínimo, redefinir ``afip_keys``
para evitar exponer tu claves a la web.

.. deprecated:: 14.0

    Los siguientes settings están deprecados y serán removidos en una versión
    futura. Usá :setting:`STORAGES` de Django en su lugar:

    - ``AFIP_KEY_STORAGE`` → ``STORAGES["afip_keys"]``
    - ``AFIP_CERT_STORAGE`` → ``STORAGES["afip_certs"]``
    - ``AFIP_PDF_STORAGE`` → ``STORAGES["afip_pdfs"]``
    - ``AFIP_LOGO_STORAGE`` → ``STORAGES["afip_logos"]``

Versionado
----------

Recomendamos pinnear versiones de dependencias. Las versiones mayores (e.g.:
de 8.X a 9.X) pueden requerir actualizar código. Esto no implica re-escribir
todo, pero suelen haber consideraciones que tenés que tener en cuenta.

El  :doc:`changelog <changelog>` siempre incluye detalles de cambios en la API
y ajustes que sean necesario.

Si estás usando ``requirements.txt``, usá algo como::

    django-afip>=8.0,< 9.0

Seguimos estrictamente `Semantic Versioning`_.

.. _Semantic Versioning: http://semver.org/

Actualizaciones
---------------

Compatibilidad para atrás puede romper en versiones mayores, aunque siempre
incluimos migraciones para actualizar instalaciones existentes. Usamos estas
mismas migraciones para actualizar instancias productivas año tras año.

.. warning::

    Si estás usando una versión previa a 4.0.0, deberías actualizar a 4.0.0,
    ejecutar las migraciones, y luego continuar. La migraciones fueros
    squasheadas en esa versión y no está garantizado que actualizar salteándola
    funcione.

.. _database-support:

Database support
----------------

Postgres is recommended. MySQL is supported, but CI runs are limited. If you
use a combination missing from the CI run matrix, feel free to reach out.
sqlite should work, and is only supported with the latest Python and latest
Django. sqlite should only by used for prototypes, demos, or example projects,
as it has not been tested for production-grade reliability.

.. _transactions:

Transactions
............

Generally, avoid calling network-related methods within a transaction. The
implementation has assumptions that they **are not** called during a request
cycle. Assumptions are made about this, and `django-afip` handles transactions
internally to keep data consistent at all times.
