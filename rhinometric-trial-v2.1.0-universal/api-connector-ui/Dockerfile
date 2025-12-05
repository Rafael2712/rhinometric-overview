FROM node:20-alpine

WORKDIR /app

# Copy UI files
COPY index.html .
COPY app.js .
COPY server.js .

# Make server executable
RUN chmod +x server.js

# Expose port
EXPOSE 8091

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8091/ || exit 1

# Start server
CMD ["node", "server.js"]
