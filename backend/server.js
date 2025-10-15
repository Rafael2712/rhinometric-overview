require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const logger = require('./src/utils/logger');
const metricsMiddleware = require('./src/middleware/metricsMiddleware');
const metricsRoutes = require('./src/routes/metrics');
const authRoutes = require('./src/routes/auth');
const tenantRoutes = require('./src/routes/tenants');
const healthRoutes = require('./src/routes/health-fast');
const demoRoutes = require('./src/routes/demo');

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());

// CORS configuration
const corsOptions = {
    origin: (process.env.ALLOWED_ORIGINS && process.env.ALLOWED_ORIGINS.split(',')) || ['http://localhost:3000'],
    credentials: true,
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

// Rate limiting
const limiter = rateLimit({
    windowMs: (process.env.RATE_LIMIT_WINDOW || 15) * 60 * 1000, // 15 minutes default
    max: process.env.RATE_LIMIT_MAX || 100,
    message: 'Too many requests from this IP, please try again later.',
    standardHeaders: true,
    legacyHeaders: false,
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Metrics middleware (DEBE IR ANTES del logging para capturar todos los requests)
app.use(metricsMiddleware);

// Request logging middleware
app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date().toISOString()
    });
    next();
});

// Metrics endpoint (sin prefijo API para compatibilidad con Prometheus)
app.use('/metrics', metricsRoutes);

// API routes
const API_PREFIX = `/api/${process.env.API_VERSION || 'v1'}`;

app.use(`${API_PREFIX}/auth`, authRoutes);
app.use(`${API_PREFIX}/tenants`, tenantRoutes);
app.use(`${API_PREFIX}/health`, healthRoutes);
app.use(`${API_PREFIX}/demo`, demoRoutes);

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'RhinoMetric SaaS API',
        version: process.env.API_VERSION || 'v1',
        environment: process.env.NODE_ENV || 'development',
        timestamp: new Date().toISOString()
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Not Found',
        message: 'The requested endpoint does not exist',
        path: req.originalUrl
    });
});

// Global error handler
app.use((err, req, res, next) => {
    logger.error('Unhandled error:', {
        error: err.message,
        stack: err.stack,
        path: req.path,
        method: req.method,
        ip: req.ip
    });

    const statusCode = err.statusCode || 500;
    const message = process.env.NODE_ENV === 'production' 
        ? 'Internal Server Error' 
        : err.message;

    res.status(statusCode).json({
        error: 'Server Error',
        message: message,
        ...(process.env.NODE_ENV !== 'production' && { stack: err.stack })
    });
});

// Graceful shutdown
process.on('SIGTERM', () => {
    logger.info('SIGTERM received, shutting down gracefully');
    process.exit(0);
});

process.on('SIGINT', () => {
    logger.info('SIGINT received, shutting down gracefully');
    process.exit(0);
});

// Start server
app.listen(PORT, () => {
    logger.info(`🚀 RhinoMetric SaaS API running on port ${PORT}`, {
        environment: process.env.NODE_ENV || 'development',
        version: process.env.API_VERSION || 'v1',
        cors: corsOptions.origin
    });
});

module.exports = app;