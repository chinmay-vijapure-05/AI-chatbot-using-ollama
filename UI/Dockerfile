FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Copy frontend files
COPY . .

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Install wget for HEALTHCHECK and ensure files are owned by the existing nginx user
RUN apk add --no-cache wget && chown -R nginx:nginx /usr/share/nginx/html
USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]