# ==========================================
# RHINOMETRIC v2.4.0 - Plugin Builder
# ==========================================
# Multi-stage build for React plugin

# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build plugin
RUN npm run build

# Stage 2: Runtime (minimal)
FROM alpine:3.18

WORKDIR /plugin

# Copy built artifacts
COPY --from=builder /build/dist ./dist
COPY --from=builder /build/src/plugin.json ./

# Set permissions
RUN chmod -R 755 /plugin

# This is just for building - actual deployment uses Grafana container
CMD ["echo", "Plugin built successfully. Copy to Grafana plugins directory."]
