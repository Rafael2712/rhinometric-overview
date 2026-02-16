# Dockerfile para Rhinometric Console Frontend
# Multi-stage build: Node.js (build) + Nginx (serve)

# ===== STAGE 1: Build =====
FROM node:20-alpine AS builder

# Metadata
LABEL stage=builder

WORKDIR /app

# Copiar package files primero (cache optimization)
COPY package*.json ./

# Instalar dependencias
RUN npm install --silent --legacy-peer-deps

# Copiar código fuente
COPY . .

# Build de producción
RUN npm run build

# ===== STAGE 2: Production Serve =====
FROM nginx:1.25-alpine

# Metadata
LABEL maintainer="Rhinometric Team"
LABEL version="2.5.0"
LABEL description="Rhinometric Console Frontend - UI Service"

# Copiar build artifacts desde stage anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 3002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3002/ || exit 1

# Nginx se inicia automáticamente
CMD ["nginx", "-g", "daemon off;"]
