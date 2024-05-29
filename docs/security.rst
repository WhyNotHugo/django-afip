Seguridad
=========

En Juio de 2020, AFIP reconfiguró sus servidores e introdujo un problema de
seguridad: las claves Diffie-Hellman que usa son demasiado pequeñas y
consideradas débiles por la mayoría de las librerías de SSL/TLS.

Esto es fácil de verificar en ``sh`` con::

    > curl -Lo /dev/null 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    curl: (35) OpenSSL/3.3.0: error:0A00018A:SSL routines::dh key too small

O en ``python`` con::

    >>> requests.get("https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL")
    SSLError: HTTPSConnectionPool(host='servicios1.afip.gov.ar', port=443): Max retries exceeded with url: /wsfev1/service.asmx?WSDL (Caused by SSLError(SSLError(1, '[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1000)')))

El problema sólo aplica a los servidores de producción, y no a los servidores de
testing.

Reporté el problema al AFIP, pero las respuestas que recibí me dieron la
impresión de que no tenían idea de que estaba hablando. No logré que mi mensaje
se re-envíe a alguien capaz de resolver el problema.

Desde entonces, ``django-afip`` incluye código para aceptar claves
Diffie-Hellman inseguras. Esta es la única solución si uno quiere comunicarse
con servidores de producción. Cuatro años después la situación sigue igual.
