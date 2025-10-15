const { Pool } = require('pg');
const logger = require('../utils/logger');

// Database connection configuration - Simplified for debugging
const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'rhinometric_saas',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
    // Simplified connection pool settings
    max: 5,                     // Small pool for testing
    min: 1,                     // Minimum pool size
    idleTimeoutMillis: 30000,   // Keep connections alive longer
    connectionTimeoutMillis: 2000, // Quick fail for connection attempts (2s)
    acquireTimeoutMillis: 10000,   // Reasonable wait for pool acquisition
    application_name: 'rhinometric_api',
    // PostgreSQL specific optimizations
    keepAlive: true,
    keepAliveInitialDelayMillis: 10000,
};

// Create connection pool
const pool = new Pool(dbConfig);

// Handle pool errors
pool.on('error', (err, client) => {
    logger.error('Unexpected error on idle client', { error: err.message });
});

// Enhanced database connection test with retry logic
const testConnection = async (retries = 3) => {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const client = await pool.connect();
            logger.info('Database connection established successfully', {
                attempt,
                host: dbConfig.host,
                database: dbConfig.database
            });
            
            // Test query with timeout
            const result = await client.query('SELECT NOW() as current_time, version()');
            logger.info('Database test query executed:', { 
                currentTime: result.rows[0].current_time,
                version: result.rows[0].version.split(' ')[0],
                responseTime: `${Date.now()}ms`
            });
            
            client.release();
            return { success: true, attempt };
        } catch (err) {
            logger.error(`Database connection failed (attempt ${attempt}/${retries}):`, { 
                error: err.message,
                code: err.code,
                host: dbConfig.host,
                port: dbConfig.port,
                database: dbConfig.database
            });
            
            if (attempt < retries) {
                logger.info(`Retrying in 2 seconds... (attempt ${attempt + 1}/${retries})`);
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
    }
    return { success: false, attempts: retries };
};

// Execute query helper
const query = async (text, params = []) => {
    const start = Date.now();
    try {
        const result = await pool.query(text, params);
        const duration = Date.now() - start;
        
        logger.debug('Query executed:', {
            query: text.substring(0, 100) + '...',
            duration: `${duration}ms`,
            rows: result.rowCount
        });
        
        return result;
    } catch (err) {
        logger.error('Query execution failed:', {
            error: err.message,
            query: text.substring(0, 100) + '...',
            params: params
        });
        throw err;
    }
};

// Get client from pool for transactions
const getClient = async () => {
    return await pool.connect();
};

module.exports = {
    pool,
    query,
    getClient,
    testConnection
};