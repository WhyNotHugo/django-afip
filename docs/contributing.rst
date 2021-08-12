Contribuciones
==============

Si tenés dudas o consultas, lo ideal es que abras un issue en GitHub_. Los
issues públicos son lo ideal porque si tenés una duda, es muy probable que el
siguiente programador que quiera usar la librería tenga las mismas dudas o dudas
muy similares.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

Hacking
-------

Para correr los tests usá `tox`. Tox crea un ambiente aislado con todas las
dependencies y corre los tests en un ambiente determinístico y reproducible.

Usá `tox -l` para ver los distintos ambientes, y `tox -e AMBIENTE` para correr
tests para ese ambiente.

A la hora de solucionar un bug, lo ideal es escribir un tests que lo
reproduzca, así una vez que tengas el fix es fácil determinar si está
solucionado, y también evita que volvamos a introducir el mismo bug en futuro.

Además de los tests comunes, hay tests de integración, que se pueden correr con
`tox -e live`. Estos tests usan credenciales de prueba en el servidor de
prueba, y asumen que existe al menos un punto de ventas para el contribuyente.

Bases de datos de testing
-------------------------

Los tests corren con tres bases de datos: `mysql`, `postgres` y `sqlite`.
Generalmente correr los tests con `sqlite` basta, pero para evitar problemas de
compatibilidad, CI corre con los tres.

Para corer los servidores de prueba localmente de forma efímera, podés usar
podman o docker:

.. code-block:: bash

    # Para postgres:
    podman run --env=POSTGRES_PASSWORD=postgres --publish=5432:5432 --rm postgres:13
    # Para mysql / mariadb:
    podman run --env=MYSQL_ROOT_PASSWORD=mysql --publish=3306:3306 --rm -it mariadb:10

Tené en cuenta que los servidores pueden tardar un par de segundos en
arrancar. Si estás corriendo tests a mano no es un problema, pero si estás
scripteando, conviene agregar un delay cortito (o usar healthchecks).
