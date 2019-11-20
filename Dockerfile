FROM registry.gitlab.e.foundation:5000/e/cloud/my-spot/env as builder

COPY . /src/
RUN pip install --force-reinstall --prefix /install /src


FROM python:3.7-alpine
LABEL maintainer="searx <https://github.com/asciimoo/searx>"
LABEL description="A privacy-respecting, hackable metasearch engine."

RUN apk add \
 ca-certificates \
 libxslt \
 py3-gunicorn \
&& pip install coverage

COPY --from=builder /install/ /usr/local/

EXPOSE 80
STOPSIGNAL SIGINT

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "--pythonpath", "/usr/local/lib/python3.7/site-packages", "searx.webapp:app"]
