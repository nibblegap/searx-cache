# spot for [/e/](https://e.foundation)

![logo](searx/static/themes/eelo/img/favicon.png)

A privacy-respecting, hackable [metasearch engine](https://en.wikipedia.org/wiki/Metasearch_engine).

Spot was forked from searx: read [documentation](https://asciimoo.github.io/searx) and the [wiki](https://github.com/asciimoo/searx/wiki) for more information.

## Changes between Spot and Searx

* eelo theme
* docker packaging thinking to be production ready
* better locale support

## Getting Started

You can run spot with docker-compose. First of all you have to install
docker and docker-compose on your host, then follow instructions
below to run spot for production or local environment.

### Like production

3 containers are used for production, traefik as edge router,
filtron to drop malicious requests, nginx to server static files and spot as backend.

* Run the docker-compose up command to start the project 
```
COMPOSE_FILE=docker-compose.yml:docker-compose-build.yml docker-compose up --build spot nginx filtron
```

* Getting the ip of the nginx service and go to `http://<nginx-ip>`, below the docker way to get the IP of the filtron container
```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-spot_filtron_1
```

### For developer

You can directly run spot, with a python command inside a docker container which
contains all dependencies.

```
docker run -it --rm -v $(pwd):/ws -w /ws registry.gitlab.e.foundation:5000/e/cloud/my-spot/env sh
SEARX_DEBUG=1 python -X dev searx/webapp.py
```

Then go open your browser and navigate to the container IP.
