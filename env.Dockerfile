FROM python:3.8-alpine

COPY requirements.txt requirements-dev.txt /

RUN apk add build-base git libxml2-dev libxslt-dev libffi-dev openssl-dev npm \
&& pip install -r /requirements.txt \
&& pip install -r /requirements-dev.txt \
&& rm -f /requirements.txt /requirements-dev.txt
