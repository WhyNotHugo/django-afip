Instalación
===========

La instalación del paquete en sí es simplemente usando pip. [#]_:

.. code-block:: python

    pip install django-afip

Vas a necesitar agregar la aplicación al ``settings.py`` de tu proyecto:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_afip',
        ...
    )

Asegurante de correr todas las migraciones después de agregar la app:

.. code-block:: python

    python manage.py migrate afip

.. [#] La generación de PDFs usa ``weasyprint``, que tiene algunas dependencias
       adicionales. Consultá `su documentación
       <http://weasyprint.readthedocs.io/en/stable/install.html>`_ para
       instrucciones detalladas al día.

Configuración
-------------

También es posible (y opcional) definir varios `Storage
https://docs.djangoproject.com/en/3.2/ref/files/storage/`_ para los archivos
de la app. Si no están definidos, se usará el Storage predeterminado.

El valor de estos ajustes debería ser un ``str`` con el path a una instancia
del storage a usar. (eg: ``'myapp.storages.my_private_storage'``). Tanto S3
como el storage predeterminado han sido testeados ampliamente, aunque cualquier
storage compatible con django debería funcionar perfecto.

.. code-block:: python

    AFIP_KEY_STORAGE  # Clave para autenticación con el AFIP. (TaxPayer.key)
    AFIP_CERT_STORAGE  # Certificados para autenticación con el AFIP (TaxPayer.certificate)
    AFIP_PDF_STORAGE  # PDFs generados para comprobantes (ReceiptPDF.pdf_file)
    AFIP_LOGO_STORAGE  # Logos usados para comprobantes (TaxPayer.logo)


Versionado
----------

Se recomienda pinnear versiones de dependencias. Dado que las versiones major
pueden requerir actualizaciones de código (siempre se proveen instrucciones de
que cambió y que cambios son necesarios).

.. code-block:: txt

    django-afip>=4.0,< 5.0

Seguimos estrictamente `Semantic Versioning`_.

.. _Semantic Versioning: http://semver.org/

Actualizado
-----------

Compatibilidad para atrás puede romper en versiones mayores, aunque siempre
incluimos migraciones para actualizar instalaciones existentes. Usamos estas
mismas migraciones para actualizar instancias productivas año tras año.

.. warning::

    Si estás usando una versión previa a 4.0.0, deberías actualizar a 4.0.0,
    ejecutar las migraciones, y luego continuar. La migraciones fueros
    squasheadas en esa versión y no está garantizado que actualizar salteándola
    funcione.
