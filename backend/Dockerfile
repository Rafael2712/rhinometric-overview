# Multi-stage build for production optimization
FROM node:10.24.0-alpine AS base

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create app directory
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S rhinometric -u 1001

# Copy package files
COPY package*.json ./

# Development stage
FROM base AS development
ENV NODE_ENV=development
RUN npm ci --include=dev
COPY . .
RUN chown -R rhinometric:nodejs /app
USER rhinometric
EXPOSE 3001
CMD ["dumb-init", "npm", "run", "dev"]

# Production dependencies stage
FROM base AS deps
ENV NODE_ENV=production
RUN npm ci --only=production && npm cache clean --force

# Production stage
FROM base AS production
ENV NODE_ENV=production

# Copy production dependencies
COPY --from=deps --chown=rhinometric:nodejs /app/node_modules ./node_modules

# Copy source code
COPY --chown=rhinometric:nodejs . .

# Create logs directory
RUN mkdir -p logs && chown -R rhinometric:nodejs logs

# Switch to non-root user
USER rhinometric

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:' + (process.env.PORT || 3001) + '/api/v1/health', (res) => process.exit(res.statusCode === 200 ? 0 : 1))"

# Expose port
EXPOSE 3001

# Start application
CMD ["dumb-init", "node", "server.js"]