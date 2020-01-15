FROM nginx:1.17.6-alpine

COPY etc/nginx/conf.d/spot.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx:nginx searx/static /var/www/spot/static
