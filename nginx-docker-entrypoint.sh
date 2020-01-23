#!/bin/sh
set -e

if [ -n "$SPOT_MORTY_URL" ]; then
    sed -i 's!__SPOT_MORTY_URL__!'$SPOT_MORTY_URL'!g' /etc/nginx/conf.d/default.conf
fi

exec "$@"
