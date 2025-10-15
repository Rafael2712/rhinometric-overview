const { Pool } = require('pg');
const logger = require('../utils/logger');

// Database configuration usando IP directa
const dbConfig = {
    host: '172.26.0.2', // IP directa del contenedor PostgreSQL
    port: 5432,
    database: process.env.DB_NAME || 'rhinometric_saas',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'rhinometric123',
};

logger.info('Database config:', { 
    host: dbConfig.host, 
    port: dbConfig.port, 
    database: dbConfig.database 
});

// Simple pool configuration for faster connections
const pool = new Pool({
    ...dbConfig,
    max: 3,
    min: 1, // Keep minimum 1 connection alive
    connectionTimeoutMillis: 2000,
    idleTimeoutMillis: 60000,
});

// Pool error handling
pool.on('error', (err) => {
    logger.error('Database pool error:', { error: err.message });
});

// Connection ready event
pool.on('connect', (client) => {
    logger.debug('New database client connected');
});

// Ultra-fast connection test using existing pool connection
const testConnection = async () => {
    const startTime = Date.now();
    
    try {
        // Simply get a client from pool and test
        const client = await pool.connect();
        await client.query('SELECT 1');
        client.release();
        
        const responseTime = Date.now() - startTime;
        logger.info('Database connection test successful', { 
            responseTime: `${responseTime}ms` 
        });
        
        return { success: true, responseTime };
        
    } catch (err) {
        const responseTime = Date.now() - startTime;
        logger.error('Database connection test failed:', { 
            error: err.message,
            responseTime: `${responseTime}ms` 
        });
        
        return { success: false, responseTime };
    }
};

module.exports = {
    pool,
    testConnection,
    query: (text, params) => pool.query(text, params),
    getClient: () => pool.connect()
};