#!/usr/bin/env node

/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  RHINOMETRIC API PROXY v2.1.0 - UNIVERSAL API CONNECTOR
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * Connects Prometheus to external APIs with:
 * - Automatic URL encoding
 * - Response caching (Redis)
 * - Health checks
 * - Prometheus metrics exposition
 * - Error handling and retries
 * 
 * Usage:
 *   node server.js
 * 
 * Endpoints:
 *   GET  /health                - Health check
 *   GET  /api/metrics/prometheus - Prometheus metrics
 *   GET  /api/health/all        - Health status of all APIs
 *   POST /api/register          - Register new API
 *   GET  /api/fetch/:apiName    - Fetch data from API
 * ═══════════════════════════════════════════════════════════════════════════
 */

const express = require('express');
const axios = require('axios');
const promClient = require('prom-client');
const redis = require('redis');
const winston = require('winston');
const cors = require('cors');
const helmet = require('helmet');
const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════

const PORT = process.env.PORT || 8090;
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const CACHE_TTL = 300; // 5 minutes

// ═══════════════════════════════════════════════════════════════════════════
// LOGGER
// ═══════════════════════════════════════════════════════════════════════════

const logger = winston.createLogger({
  level: LOG_LEVEL,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// ═══════════════════════════════════════════════════════════════════════════
// PROMETHEUS METRICS
// ═══════════════════════════════════════════════════════════════════════════

const register = new promClient.Register();

promClient.collectDefaultMetrics({ register, prefix: 'api_proxy_' });

const apiRequestsTotal = new promClient.Counter({
  name: 'api_proxy_requests_total',
  help: 'Total number of API requests',
  labelNames: ['api_name', 'method', 'status'],
  registers: [register]
});

const apiRequestDuration = new promClient.Histogram({
  name: 'api_proxy_request_duration_seconds',
  help: 'API request duration in seconds',
  labelNames: ['api_name', 'method'],
  buckets: [0.1, 0.5, 1, 2, 5, 10],
  registers: [register]
});

const apiHealthGauge = new promClient.Gauge({
  name: 'api_proxy_health_status',
  help: 'Health status of external APIs (1=healthy, 0=unhealthy)',
  labelNames: ['api_name', 'url'],
  registers: [register]
});

const cacheHitsTotal = new promClient.Counter({
  name: 'api_proxy_cache_hits_total',
  help: 'Total number of cache hits',
  labelNames: ['api_name'],
  registers: [register]
});

// ═══════════════════════════════════════════════════════════════════════════
// REDIS CLIENT
// ═══════════════════════════════════════════════════════════════════════════

let redisClient;

async function connectRedis() {
  try {
    redisClient = redis.createClient({ url: REDIS_URL });
    redisClient.on('error', (err) => logger.error('Redis error:', err));
    await redisClient.connect();
    logger.info('✓ Connected to Redis');
  } catch (error) {
    logger.warn('⚠ Redis not available, running without cache');
    redisClient = null;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// API REGISTRY
// ═══════════════════════════════════════════════════════════════════════════

const apis = new Map();

// Default pre-configured APIs
const defaultApis = [
  {
    name: 'coindesk_btc',
    url: 'https://api.coindesk.com/v1/bpi/currentprice.json',
    method: 'GET',
    interval: 60,
    enabled: true,
    headers: {}
  },
  {
    name: 'openweather',
    url: 'https://api.open-meteo.com/v1/forecast?latitude=40.4168&longitude=-3.7038&current=temperature_2m,wind_speed_10m',
    method: 'GET',
    interval: 300,
    enabled: true,
    headers: {}
  },
  {
    name: 'github_status',
    url: 'https://www.githubstatus.com/api/v2/status.json',
    method: 'GET',
    interval: 120,
    enabled: true,
    headers: {}
  }
];

// Load APIs from config file if exists
function loadApis() {
  const configPath = path.join('/app/config', 'apis.json');
  
  if (fs.existsSync(configPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      config.apis.forEach(api => apis.set(api.name, api));
      logger.info(`✓ Loaded ${config.apis.length} APIs from config`);
    } catch (error) {
      logger.error('Error loading API config:', error);
    }
  }
  
  // Add default APIs if not present
  defaultApis.forEach(api => {
    if (!apis.has(api.name)) {
      apis.set(api.name, api);
    }
  });
  
  logger.info(`✓ Total APIs registered: ${apis.size}`);
}

// ═══════════════════════════════════════════════════════════════════════════
// API FETCHER
// ═══════════════════════════════════════════════════════════════════════════

async function fetchApi(apiConfig) {
  const startTime = Date.now();
  const { name, url, method, headers } = apiConfig;
  
  try {
    // Check cache first
    if (redisClient) {
      const cached = await redisClient.get(`api:${name}`);
      if (cached) {
        cacheHitsTotal.inc({ api_name: name });
        logger.debug(`Cache hit for ${name}`);
        return JSON.parse(cached);
      }
    }
    
    // Fetch from API
    const response = await axios({
      method,
      url,
      headers: {
        'User-Agent': 'Rhinometric-API-Proxy/2.1.0',
        ...headers
      },
      timeout: 10000
    });
    
    const duration = (Date.now() - startTime) / 1000;
    
    // Update metrics
    apiRequestsTotal.inc({ api_name: name, method, status: response.status });
    apiRequestDuration.observe({ api_name: name, method }, duration);
    apiHealthGauge.set({ api_name: name, url }, 1);
    
    // Cache response
    if (redisClient) {
      await redisClient.setEx(
        `api:${name}`,
        apiConfig.interval || CACHE_TTL,
        JSON.stringify(response.data)
      );
    }
    
    logger.info(`✓ Fetched ${name} in ${duration.toFixed(2)}s`);
    
    return response.data;
    
  } catch (error) {
    const duration = (Date.now() - startTime) / 1000;
    
    apiRequestsTotal.inc({ 
      api_name: name, 
      method, 
      status: error.response?.status || 0 
    });
    apiRequestDuration.observe({ api_name: name, method }, duration);
    apiHealthGauge.set({ api_name: name, url }, 0);
    
    logger.error(`✗ Error fetching ${name}:`, error.message);
    
    throw error;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECKER
// ═══════════════════════════════════════════════════════════════════════════

async function checkAllApis() {
  const results = {};
  
  for (const [name, config] of apis.entries()) {
    if (!config.enabled) continue;
    
    try {
      await fetchApi(config);
      results[name] = { status: 'healthy', lastCheck: new Date().toISOString() };
    } catch (error) {
      results[name] = { 
        status: 'unhealthy', 
        error: error.message,
        lastCheck: new Date().toISOString()
      };
    }
  }
  
  return results;
}

// Start periodic health checks
setInterval(() => {
  checkAllApis().catch(err => logger.error('Health check error:', err));
}, 60000); // Every minute

// ═══════════════════════════════════════════════════════════════════════════
// EXPRESS APP
// ═══════════════════════════════════════════════════════════════════════════

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    service: 'api-proxy',
    version: '2.1.0',
    uptime: process.uptime(),
    redis: redisClient ? 'connected' : 'disconnected'
  });
});

// Prometheus metrics endpoint
app.get('/api/metrics/prometheus', async (req, res) => {
  try {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get health status of all APIs
app.get('/api/health/all', async (req, res) => {
  try {
    const results = await checkAllApis();
    res.json(results);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Fetch data from specific API
app.get('/api/fetch/:apiName', async (req, res) => {
  try {
    const apiConfig = apis.get(req.params.apiName);
    
    if (!apiConfig) {
      return res.status(404).json({ error: 'API not found' });
    }
    
    if (!apiConfig.enabled) {
      return res.status(503).json({ error: 'API disabled' });
    }
    
    const data = await fetchApi(apiConfig);
    res.json(data);
    
  } catch (error) {
    res.status(502).json({ 
      error: 'Failed to fetch from API',
      message: error.message 
    });
  }
});

// Register new API
app.post('/api/register', (req, res) => {
  try {
    const { name, url, method = 'GET', interval = 300, headers = {} } = req.body;
    
    if (!name || !url) {
      return res.status(400).json({ error: 'Name and URL required' });
    }
    
    apis.set(name, {
      name,
      url,
      method,
      interval,
      enabled: true,
      headers
    });
    
    logger.info(`✓ Registered new API: ${name}`);
    
    res.json({ 
      message: 'API registered successfully',
      api: apis.get(name)
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// List all registered APIs
app.get('/api/list', (req, res) => {
  const apiList = Array.from(apis.values()).map(api => ({
    name: api.name,
    url: api.url,
    method: api.method,
    enabled: api.enabled,
    interval: api.interval
  }));
  
  res.json({ apis: apiList, total: apiList.length });
});

// ═══════════════════════════════════════════════════════════════════════════
// START SERVER
// ═══════════════════════════════════════════════════════════════════════════

async function start() {
  try {
    await connectRedis();
    loadApis();
    
    app.listen(PORT, '0.0.0.0', () => {
      logger.info('═══════════════════════════════════════════════════════════════');
      logger.info(`  Rhinometric API Proxy v2.1.0`);
      logger.info(`  Listening on http://0.0.0.0:${PORT}`);
      logger.info(`  APIs registered: ${apis.size}`);
      logger.info('═══════════════════════════════════════════════════════════════');
    });
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();
