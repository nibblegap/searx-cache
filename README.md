# spot for [/e/](https://e.foundation)

![logo](searx/static/themes/eelo/img/favicon.png)

A privacy-respecting, hackable [metasearch engine](https://en.wikipedia.org/wiki/Metasearch_engine).

Spot was forked from searx: read [documentation](https://asciimoo.github.io/searx) and the [wiki](https://github.com/asciimoo/searx/wiki) for more information.

## Changes between Spot and Searx

* eelo theme
* docker packaging thinking to be production ready
* better locale support

## Architecture

5 services are used for production:

* [traefik](https://docs.traefik.io/) as edge router to publish services.
* [filtron](https://github.com/asciimoo/filtron) as reverse HTTP proxy to filter requests by different rules.
* [morty](https://github.com/asciimoo/morty) as proxy to serve thumbnails.
* [nginx](https://www.nginx.com/) as http server to serve static files.
* Spot the meta search engine.
* [tor](https://www.torproject.org) as open network that helps you defend against traffic analysis.


```mermaid
graph TD
  A(traefik) --> |https://spot.ecloud.global| B(filtron)
  A(traefik) --> |https://proxy.spot.ecloud.global| C(morty)
  C --> |image link| C
  B --> D(nginx)
  D --> |static file| D
  D --> |API| E(spot)
  E --> H(tor1)
  E --> I(tor2)
  E --> J(torN)
```

## Getting Started

You can run spot with docker-compose. First of all you have to install
docker and docker-compose on your host, then follow instructions
below to run spot for production or local environment.

### Like production

* Run the docker-compose up command to start the project 
```
COMPOSE_FILE=docker-compose.yml:docker-compose-build.yml docker-compose up --build morty
SPOT_MORTY_URL=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-spot_morty_1)
COMPOSE_FILE=docker-compose.yml:docker-compose-build.yml docker-compose up --build spot nginx filtron tor
```

* Getting the ip of the filtron service and go to `http://<ip>`, below the docker way to get the IP of the filtron container
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

Then, open your browser and navigate to the container IP.
