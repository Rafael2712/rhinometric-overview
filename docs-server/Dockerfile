FROM nginx:alpine

# Copy runbooks (ES + EN) to nginx html directory
COPY docs/runbooks /usr/share/nginx/html/runbooks

# Copy anomalies HTML viewer
COPY docs/anomalies /usr/share/nginx/html/anomalies

# Copy assets (logo)
COPY docs/assets /usr/share/nginx/html/assets

# Copy custom nginx config
COPY nginx/conf.d/docs-rhinometric.conf /etc/nginx/conf.d/default.conf

# Create logs directory
RUN mkdir -p /var/log/nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
