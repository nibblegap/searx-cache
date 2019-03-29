FROM python:3.7-alpine as builder

RUN apk add \
 git \
 build-base \
 libxml2-dev \
 libxslt-dev

# Only to use the docker cache and optimize the build time
WORKDIR /src
COPY requirements.txt /src/requirements.txt
RUN pip3 install --prefix /install -r requirements.txt

COPY . /src/
RUN PYTHONPATH=/install/lib/python3.7/site-packages/ python3 setup.py install --prefix /install


FROM python:3.7-alpine
LABEL maintainer="searx <https://github.com/asciimoo/searx>"
LABEL description="A privacy-respecting, hackable metasearch engine."

RUN apk add \
 ca-certificates \
 libxslt \
&& pip install coverage

COPY --from=builder /install/ /usr/local/

EXPOSE 8888
STOPSIGNAL SIGINT
CMD ["searx-run"]
