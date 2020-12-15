FROM python:3.9-slim

COPY requirements.txt requirements-dev.txt /

RUN apt-get update -y && apt-get install -y build-essential git libxml2-dev libz-dev libxslt1-dev libffi-dev libssl-dev npm
RUN apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common \
&& curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
&& add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
&& apt-get update \
&& apt-get install -y docker-ce docker-ce-cli containerd.io
RUN pip install -r /requirements.txt \
&& pip install -r /requirements-dev.txt \
&& pip install virtualenv docker-compose \
&& rm -f /requirements.txt /requirements-dev.txt
