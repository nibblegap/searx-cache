spot for /e/ (https://e.foundation)
===================================

A privacy-respecting, hackable `metasearch
engine <https://en.wikipedia.org/wiki/Metasearch_engine>`__.

Spot was forked from searx: read `documentation <https://asciimoo.github.io/searx>`__ and the `wiki <https://github.com/asciimoo/searx/wiki>`__ for more information.

Spot is based on Python3.7+

Getting Started
~~~~~~~~~~~~

You can run spot with docker-compose to run the **redis** database and
the **spot** service. First of all you have to install **docker** and
**docker-compose** on your host, then follow instructions below to run spot
with one command.

- Run the docker-compose **up** command to start the project ``docker-compose up --build``
- Getting the ip of the spot service and go to http://<spot-ip>:8888

.. note::  Here the command to get the IP of the spot service
 ``docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-spot_spot_1``

You can also install **redis** and **spot** on your host, for all the details, follow this `step by step
installation <https://github.com/asciimoo/searx/wiki/Installation>`__.

Developer mode
~~~~~~~~~~~~

First run the redis database:

- ``docker-compose up -d redis``

Then on spot workdir run the following commands to start spot:

- ``docker-compose build spot``
- ``docker-compose run --rm -v $(pwd):/ws -w /ws -e PYTHONPATH=/ws spot sh``
- ``python3 -X dev searx/webapp.py``

Run tests:

- ``docker run -it --rm -v $(pwd):/ws -w /ws -v /var/run/docker.sock:/var/run/docker.sock -e PYTHONPATH=/ws registry.gitlab.e.foundation:5000/e/cloud/my-spot/env bash``
- ``pytest --pdb --pdbcls IPython.terminal.debugger:TerminalPdb tests``

Bugs
~~~~

Bugs or suggestions? Visit the `issue
tracker <https://github.com/asciimoo/searx/issues>`__.

`License <https://github.com/asciimoo/searx/blob/master/LICENSE>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

More about searx
~~~~~~~~~~~~~~~~

-  `openhub <https://www.openhub.net/p/searx/>`__
-  `twitter <https://twitter.com/Searx_engine>`__
-  IRC: #searx @ freenode
