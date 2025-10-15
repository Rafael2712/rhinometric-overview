const express = require('express');
const logger = require('../utils/logger');
const SimpleAuth = require('../middleware/simpleAuth');

const router = express.Router();
const simpleAuth = new SimpleAuth();

// Ultra-fast health check endpoint
router.get('/', async (req, res) => {
    try {
        const startTime = Date.now();
        
        // Fast network connectivity check using built-in net module
        const net = require('net');
        
        const checkDbPort = () => {
            return new Promise((resolve) => {
                const socket = new net.Socket();
                const timeout = 1000; // 1 second timeout
                
                socket.setTimeout(timeout);
                
                socket.on('connect', () => {
                    socket.destroy();
                    resolve({ success: true, duration: Date.now() - startTime });
                });
                
                socket.on('timeout', () => {
                    socket.destroy();
                    resolve({ success: false, duration: Date.now() - startTime, error: 'timeout' });
                });
                
                socket.on('error', (err) => {
                    socket.destroy();
                    resolve({ success: false, duration: Date.now() - startTime, error: err.message });
                });
                
                const dbHost = process.env.DB_HOST || 'localhost';
                socket.connect(5432, dbHost); // PostgreSQL hostname and port
            });
        };
        
        // Check database port connectivity
        const dbResult = await checkDbPort();
        const dbHealthy = dbResult.success;
        const dbResponseTime = dbResult.duration;
        
        // Check Authentication system
        const authResult = await simpleAuth.healthCheck();
        const authHealthy = authResult.healthy;
        
        // System information
        const systemInfo = {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            version: process.version,
            platform: process.platform
        };
        
        // Overall health status
        const isHealthy = dbHealthy && authHealthy;
        const status = isHealthy ? 'healthy' : 'unhealthy';
        const statusCode = isHealthy ? 200 : 503;
        
        const healthCheck = {
            status: status,
            timestamp: new Date().toISOString(),
            uptime: `${Math.floor(process.uptime())}s`,
            checks: {
                database: {
                    status: dbHealthy ? 'healthy' : 'unhealthy',
                    responseTime: `${dbResponseTime}ms`,
                    method: 'port_check'
                },
                authentication: {
                    status: authHealthy ? 'healthy' : 'unhealthy',
                    type: authResult.type,
                    users: authResult.users
                },
                memory: {
                    status: systemInfo.memory.rss < 1000000000 ? 'healthy' : 'warning',
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
            status,
            dbHealthy,
            dbResponseTime: `${dbResponseTime}ms`,
            authHealthy
        });
        
        res.status(statusCode).json(healthCheck);
        
    } catch (error) {
        logger.error('Health check failed:', {
            error: error.message,
            stack: error.stack
        });
        
        res.status(500).json({
            status: 'error',
            timestamp: new Date().toISOString(),
            error: 'Health check failed',
            message: error.message
        });
    }
});

// Simple alive check
router.get('/alive', (req, res) => {
    res.json({
        status: 'alive',
        timestamp: new Date().toISOString(),
        uptime: `${Math.floor(process.uptime())}s`
    });
});

// Ready check - more thorough but still fast
router.get('/ready', async (req, res) => {
    try {
        // Check if all required environment variables are present
        const requiredEnvVars = ['DB_HOST', 'DB_NAME', 'DB_USER'];
        const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
        
        if (missingVars.length > 0) {
            return res.status(503).json({
                status: 'not_ready',
                timestamp: new Date().toISOString(),
                error: 'Missing environment variables',
                missing: missingVars
            });
        }
        
        res.json({
            status: 'ready',
            timestamp: new Date().toISOString(),
            uptime: `${Math.floor(process.uptime())}s`,
            environment: {
                node_version: process.version,
                db_configured: !!process.env.DB_HOST
            }
        });
        
    } catch (error) {
        res.status(500).json({
            status: 'error',
            timestamp: new Date().toISOString(),
            error: error.message
        });
    }
});

module.exports = router;