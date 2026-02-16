FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache curl wget

COPY package*.json ./

RUN npm install --production && \
    npm cache clean --force

COPY . .

RUN mkdir -p /app/cache /app/config && \
    chmod 755 /app/cache /app/config

ENV NODE_ENV=production
ENV PORT=8090
ENV LOG_LEVEL=info

EXPOSE 8090

HEALTHCHECK --interval=20s --timeout=5s --retries=3 --start-period=20s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8090/health || exit 1

CMD ["node", "server.js"]
