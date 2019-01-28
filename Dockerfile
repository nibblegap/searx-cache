FROM python:3.7-alpine
LABEL maintainer="searx <https://github.com/asciimoo/searx>"
LABEL description="A privacy-respecting, hackable metasearch engine."

EXPOSE 8888
WORKDIR /usr/local/searx
CMD ["python", "searx/webapp.py"]

COPY requirements.txt ./requirements.txt

RUN apk -U add \
    build-base \
    libxml2 \
    libxml2-dev \
    libxslt \
    libxslt-dev \
    libffi-dev \
    openssl \
    openssl-dev \
    ca-certificates \
 && pip install -r requirements.txt \
 && pip install coverage \
 && apk del \
    build-base \
    libffi-dev \
    openssl-dev \
    libxslt-dev \
    libxml2-dev \
    openssl-dev \
    ca-certificates \
 && rm -f /var/cache/apk/*

COPY searx /usr/local/searx/searx

RUN sed -i "s/127.0.0.1/0.0.0.0/g" searx/settings.yml

STOPSIGNAL SIGINT
