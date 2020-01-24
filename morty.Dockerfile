FROM golang:1.13-alpine as builder

RUN apk add git && go get github.com/asciimoo/morty


FROM alpine:3.11

COPY --from=builder /go/bin/morty /usr/bin/morty

EXPOSE 80
CMD ["morty", "-listen", ":80", "-timeout", "5", "-ipv6"]
