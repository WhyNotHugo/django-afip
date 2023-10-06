Contribuciones
==============

Si tenés dudas o consultas, lo ideal es que abras un issue en GitHub_. Los
issues públicos son lo ideal porque si tenés una duda, es muy probable que el
siguiente programador que quiera usar la librería tenga las mismas dudas o dudas
muy similares.

.. _GitHub: https://github.com/WhyNotHugo/django-afip

Testing
-------

We use `tox` for tests. `tox` sets up a dedicated virtual environment and runs
tests inside of it. This keeps environments isolated and somewhat deterministic
and reproducible.

To list all possible test environments, use `tox -l`. To run tests in an
environment, use `tox -e ENVIRONMENT`. A quick way to run all unit tests is to
use `tox -e py-sqlite`.

If you find a bug, try and write a test that reproduces it. This will make
finding a solution easier but also avoid regression on that same issue.

There are also live tests. These are executed automatically on CI and test
using AFIP's testing servers. These tests are somewhat flaky because
authentication cannot be done too often. Skipping tests for authentication
seems like a great way to break authentication-related code without noticing.

Live tests are run only when using `tox -e live`.

Bases de datos de testing
-------------------------

Los tests corren con tres bases de datos: `mysql`, `postgres` y `sqlite`.
Generalmente correr los tests con `sqlite` basta, pero para evitar problemas de
compatibilidad, CI corre con los tres.

Para corer los servidores de prueba localmente de forma efímera, podés usar
docker:

.. code-block:: bash

    # Para postgres:
    docker run --env=POSTGRES_PASSWORD=postgres --publish=5432:5432 --rm postgres:13
    # Para mysql / mariadb:
    docker run --env=MYSQL_ROOT_PASSWORD=mysql --publish=3306:3306 --rm -it mariadb:10

Tené en cuenta que los servidores pueden tardar un par de segundos en
arrancar. Si estás corriendo tests a mano no es un problema, pero si estás
scripteando, conviene agregar un delay cortito (o usar healthchecks).
