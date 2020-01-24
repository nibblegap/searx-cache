FROM golang:1.13-alpine as builder

RUN apk add git && go get github.com/asciimoo/filtron


FROM alpine:3.11

COPY --from=builder /go/bin/filtron /usr/bin/filtron
COPY etc/filtron/rules.json /etc/filtron/rules.json

EXPOSE 80
CMD ["filtron", "-listen", ":80", "-rules", "/etc/filtron/rules.json", "-target", "nginx"]
