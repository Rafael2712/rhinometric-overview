# Dockerfile para License Management UI
# Multi-stage build: Node.js (build) + Nginx (serve)

# ===== STAGE 1: Build =====
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install --silent

# Copiar código fuente
COPY . .

# Build de producción
RUN npm run build

# ===== STAGE 2: Production Serve =====
FROM nginx:1.25-alpine

LABEL maintainer="Rhinometric Team"
LABEL version="2.5.0"
LABEL description="Rhinometric License Management UI"

# Copiar build artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuración nginx personalizada
RUN echo 'server { \
    listen 8092; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /health { \
        return 200 "OK"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 8092

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8092/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
