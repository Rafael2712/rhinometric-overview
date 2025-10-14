const { Pool } = require('pg');
const logger = require('../utils/logger');

// Database connection configuration
const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'rhinometric_saas',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
    // Connection pool settings
    max: 20,                    // Maximum number of clients
    idleTimeoutMillis: 30000,   // Close idle clients after 30 seconds
    connectionTimeoutMillis: 2000, // Return error after 2 seconds if connection could not be established
};

// Create connection pool
const pool = new Pool(dbConfig);

// Handle pool errors
pool.on('error', (err, client) => {
    logger.error('Unexpected error on idle client', { error: err.message });
});

// Database connection test
const testConnection = async () => {
    try {
        const client = await pool.connect();
        logger.info('Database connection established successfully');
        
        // Test query
        const result = await client.query('SELECT NOW() as current_time');
        logger.info('Database test query executed:', { 
            currentTime: result.rows[0].current_time 
        });
        
        client.release();
        return true;
    } catch (err) {
        logger.error('Database connection failed:', { 
            error: err.message,
            host: dbConfig.host,
            port: dbConfig.port,
            database: dbConfig.database
        });
        return false;
    }
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