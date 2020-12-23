#!/bin/sh
set -e

if [ -n "$SEARX_MORTY_URL" ]; then
    sed -i 's!__SEARX_MORTY_URL__!'$SEARX_MORTY_URL'!g' /etc/nginx/conf.d/default.conf
fi

exec "$@"
