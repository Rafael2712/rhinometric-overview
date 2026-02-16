const express = require('express');
const db = require('../config/database');
const logger = require('../utils/logger');

const router = express.Router();

// Health check endpoint
router.get('/', async (req, res) => {
    try {
        const startTime = Date.now();
        
        // Check database connectivity
        const dbHealthy = await db.testConnection();
        const dbResponseTime = Date.now() - startTime;
        
        // System information
        const systemInfo = {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            cpu: process.cpuUsage(),
            version: process.version,
            platform: process.platform
        };
        
        // Overall health status
        const isHealthy = dbHealthy;
        const status = isHealthy ? 'healthy' : 'unhealthy';
        const statusCode = isHealthy ? 200 : 503;
        
        const healthCheck = {
            status: status,
            timestamp: new Date().toISOString(),
            uptime: `${Math.floor(process.uptime())}s`,
            checks: {
                database: {
                    status: dbHealthy ? 'healthy' : 'unhealthy',
                    responseTime: `${dbResponseTime}ms`
                },
                memory: {
                    status: systemInfo.memory.rss < 1000000000 ? 'healthy' : 'warning', // 1GB threshold
                    usage: `${Math.round(systemInfo.memory.rss / 1024 / 1024)}MB`
                }
            },
            system: {
                node_version: systemInfo.version,
                platform: systemInfo.platform,
                uptime: systemInfo.uptime
            }
        };
        
        // Log health check
        logger.info('Health check performed', {
            status: status,
            dbHealthy: dbHealthy,
            dbResponseTime: `${dbResponseTime}ms`
        });
        
        res.status(statusCode).json(healthCheck);
        
    } catch (error) {
        logger.error('Health check failed:', { error: error.message });
        
        res.status(503).json({
            status: 'error',
            timestamp: new Date().toISOString(),
            error: 'Health check failed',
            message: error.message
        });
    }
});

// Detailed health check
router.get('/detailed', async (req, res) => {
    try {
        const startTime = Date.now();
        
        // Database detailed check
        let dbDetails = { status: 'unknown' };
        try {
            const dbStart = Date.now();
            await db.query('SELECT 1');
            const dbEnd = Date.now();
            
            dbDetails = {
                status: 'healthy',
                responseTime: `${dbEnd - dbStart}ms`,
                connections: 'active' // Could get from pool stats
            };
        } catch (dbError) {
            dbDetails = {
                status: 'unhealthy',
                error: dbError.message
            };
        }
        
        // Memory details
        const memUsage = process.memoryUsage();
        const memDetails = {
            rss: `${Math.round(memUsage.rss / 1024 / 1024)}MB`,
            heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`,
            heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
            external: `${Math.round(memUsage.external / 1024 / 1024)}MB`
        };
        
        // CPU details
        const cpuUsage = process.cpuUsage();
        const cpuDetails = {
            user: cpuUsage.user,
            system: cpuUsage.system
        };
        
        const detailedHealth = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            responseTime: `${Date.now() - startTime}ms`,
            components: {
                database: dbDetails,
                memory: memDetails,
                cpu: cpuDetails
            },
            environment: {
                node_env: process.env.NODE_ENV || 'development',
                api_version: process.env.API_VERSION || 'v1',
                port: process.env.PORT || 3001
            }
        };
        
        res.json(detailedHealth);
        
    } catch (error) {
        logger.error('Detailed health check failed:', { error: error.message });
        
        res.status(503).json({
            status: 'error',
            timestamp: new Date().toISOString(),
            error: 'Detailed health check failed',
            message: error.message
        });
    }
});

module.exports = router;