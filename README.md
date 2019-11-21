# spot for /e/ (https://e.foundation)

A privacy-respecting, hackable [metasearch engine](https://en.wikipedia.org/wiki/Metasearch_engine).

Spot was forked from searx: read [documentation](https://asciimoo.github.io/searx) and the [wiki](https://github.com/asciimoo/searx/wiki) for more information.

## Changes between Spot and Searx

* cache results in Redis database
* eelo theme
* better python packaging and docker integration for production deployement
* drop of Python 2 support
* pytest as test launcher

The aim is to move that changes in the upstream project when it will be easier to rebase from this one.

## Getting Started

You can run spot with docker-compose to run the *redis* database and
the *spot* service. First of all you have to install *docker* and
*docker-compose* on your host, then follow instructions below to run spot
with one command.

###  For production

* Run the docker-compose *up* command to start the project 
```
COMPOSE_FILE="docker-compose.yml:docker-compose-dev.yml" docker-compose up --build nginx spot redis
```
* Getting the ip of the spot service and go to `http://<spot-ip>`, below the docker way to get the IP of the nginx container
```
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-spot_nginx_1
```

### For developer

You can directly run spot, with a python command. First, you should install all dependencies on your host `./manage.sh update_dev_packages` or you can use the `env` container.

```
docker run -it --rm -v $(pwd):/ws -w /ws -e PYTHONPATH=/ws registry.gitlab.e.foundation:5000/e/cloud/my-spot/env sh
python ./searx/webapp.py
```
