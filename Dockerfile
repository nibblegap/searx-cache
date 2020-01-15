FROM registry.gitlab.e.foundation:5000/e/cloud/my-spot/env as builder

COPY . /src/
RUN pip install --force-reinstall --prefix /install /src


FROM python:3.8-alpine
LABEL maintainer="spot <https://gitlab.e.foundation/e/cloud/my-spot/>"
LABEL description="A privacy-respecting, hackable metasearch engine."

RUN apk add ca-certificates libxslt py3-gunicorn

COPY --from=builder /install/ /usr/local/

EXPOSE 80
STOPSIGNAL SIGINT

ENV PYTHONPATH="/usr/local/lib/python3.8/site-packages"
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "searx.webapp:app"]
