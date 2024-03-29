FROM nginx:1.17.6-alpine

COPY etc/nginx/conf.d/spot.conf /etc/nginx/conf.d/default.conf
COPY etc/nginx/proxy_spot_params /etc/nginx/proxy_spot_params
RUN sed -i 's!http_x_forwarded_for!remote_addr!g' /etc/nginx/nginx.conf
COPY --chown=nginx:nginx searx/static /var/www/spot/static
COPY nginx-docker-entrypoint.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
