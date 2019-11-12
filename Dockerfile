FROM python:3.7-alpine as builder

RUN apk add \
 git \
 build-base \
 libxml2-dev \
 libxslt-dev

COPY . /src/
RUN pip3 install --prefix /install /src


FROM python:3.7-alpine
LABEL maintainer="searx <https://github.com/asciimoo/searx>"
LABEL description="A privacy-respecting, hackable metasearch engine."

RUN apk add \
 ca-certificates \
 libxslt \
 build-base \
&& pip install coverage

COPY --from=builder /install/ /usr/local/

EXPOSE 8888
STOPSIGNAL SIGINT
CMD ["searx-run"]
