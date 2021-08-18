Instalación
===========

Podés instalar este paquete usando pip:

.. code-block:: python

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

.. code-block:: python

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

El valor de estos ajustes debería ser un ``str`` con el path a una instancia
del storage a usar. (eg: ``'myapp.storages.my_private_storage'``). Tanto S3
como el storage predeterminado han sido testeados ampliamente, aunque cualquier
storage compatible con django debería funcionar sin dramas.

.. code-block:: python

    AFIP_KEY_STORAGE  # Clave para autenticación con el AFIP. (TaxPayer.key)
    AFIP_CERT_STORAGE  # Certificados para autenticación con el AFIP (TaxPayer.certificate)
    AFIP_PDF_STORAGE  # PDFs generados para comprobantes (ReceiptPDF.pdf_file)
    AFIP_LOGO_STORAGE  # Logos usados para comprobantes (TaxPayer.logo)

Si estás exponiendo tu Storage predeterminado a la web (que suele ser el caso
en muchas aplicaciones), es recomendable, como mínimo, redefinir
``AFIP_KEY_STORAGE`` para evitar exponer tu claves a la web.

Versionado
----------

Recomendamos pinnear versiones de dependencias. Las versiones mayores (e.g.:
de 8.X a 9.X) pueden requerir actualizar código. Esto no implica re-escribir
todo, pero suelen haber consideraciones que tenés que tener en cuenta.

El CHANGELOG siempre incluye detalles de cambios en la API y que ajustes puede
que necesites hacer.

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
