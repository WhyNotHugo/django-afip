Impresiones
-----------

Originalmente **django-afip** no soportaba generación de PDFs o comprobantes a
imprimir, dado que esto lo hacían sistemas externos.

Eventualmente esto cambió, y la generación de PDFs se integró a esta librería,
pero la integración no está al 100%, por lo cual la mayoría del código para
generar los PDF es opcional.

Actualmente soportamos generar PDFs para comprobantes y esto está respaldado
principalmente por tres clases. Sólo necesitás usar estas clases si estás
generando los PDF con esta librería, y podés ignorarlas si estás generándolos
de otra forma:

* :class:`~.ReceiptPDF`: Contiene metadatos individuales de cada comprobante.
  Los datos de ``PointOfSales`` también se copian acá, dado que en caso de que
  cambie, por ejemplo, el domicilio del contribuyente, no debería cambiar el
  domicilio en comprobantes pasados.
* :class:`~.ReceiptEntry`: Representa una línea del detalle de un comprobante.

Primero deberías generar los ``ReceiptEntry`` para tu comprobante y después
generar el ``ReceiptPDF``. Esto último lo podés hacer usando el helper
:meth:`~.ReceiptPDFManager.create_for_receipt`.

Los archivos PDF en sí son generados la primera vez que guardes una instancia
de ``ReceiptPDF`` (mediante un hook ``pre_save``). Podés regenerar el PDF
usando :meth:`.ReceiptPDF.save_pdf`.

Códigos QR
~~~~~~~~~~

Los PDF incluyen el código QR que es requerido desde Marzo 2021.

Actualmente cualquier QR redirige a la documentación del AFIP (includo lo de
sus ejemplos y otra implementaciones). Esto parece ser porque AFIP nunca
terminó de implementar su parte, y está fuera de nuestro control.

Exponiendo comprobantes
~~~~~~~~~~~~~~~~~~~~~~~

Vistas
......

Los comprobantes pueden exponerse mediante una vista. Requirre el `pk` del
comprobante, así que la registración de la URL debería ser algo como:

.. code-block:: python

    path(
        "receipts/pdf/<int:pk>",
        views.ReceiptPDFView.as_view(),
        name="receipt_view",
    ),

Esto usa **django_renderpdf**, y es una subclase de ``PDFView``.

Recomendamos generalmente usar una subclase de ``ReceiptPDFView``, que tenga
alguna forma de autenticación y autorizacion.

.. autoclass:: django_afip.views.ReceiptPDFView
    :members:

Templates
.........

Los templates para las vistas son buscados en
``templates/receipts/code_X.html``, dónde X es el código del tipo de
comprobante (:class:`~.ReceiptType`). Si querés overridear el predetermindo,
simplemente incluí en tu projecto un template con el mismo nombre/path, y
asegurate de que te projecte esté listado *antes* que ``django_afip`` en
``INSTALLED_APPS``.

También podés exponer los archivos generados

Note that you may also expose receipts as plain Django media files. The URL
will be relative or absolute depending on your media files configuration.

.. code-block:: pycon

    >>> printable = ReceiptPDF.objects.last()
    >>> printable.pdf_file
    <FieldFile: receipts/790bc4f648e844bda7149ac517fdcf65.pdf>
    >>> printable.pdf_file.url
    '/media/receipts/790bc4f648e844bda7149ac517fdcf65.pdf'

Los templates provistos siguen las indicaciones de la `RG1415`_, que regula que
campos deben contener y dónde debe estar ubicado cada dato.

.. _RG1415: http://biblioteca.afip.gob.ar/dcp/REAG01001415_2003_01_07
