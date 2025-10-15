const { Pool, Client } = require('pg');
const logger = require('../utils/logger');

// Database configuration
const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'rhinometric_saas',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
};

// Create a connection pool
const pool = new Pool({
    ...dbConfig,
    max: 5,                     // 5 connections max
    connectionTimeoutMillis: 3000,  // 3 second timeout
    idleTimeoutMillis: 30000,   // 30 second idle timeout
    statement_timeout: 2000,    // 2 second statement timeout
});

// Handle pool errors
pool.on('error', (err, client) => {
    logger.error('Database pool error', { error: err.message });
});

// Cache for connection health
let connectionHealthCache = {
    isHealthy: false,
    lastCheck: 0,
    cacheDuration: 10000 // Cache for 10 seconds
};

// Simple and fast connection test using the pool
const testConnection = async (retries = 1) => {
    const now = Date.now();
    
    // Return cached result if still valid
    if (connectionHealthCache.lastCheck && 
        (now - connectionHealthCache.lastCheck) < connectionHealthCache.cacheDuration) {
        logger.debug('Using cached connection health status', { 
            isHealthy: connectionHealthCache.isHealthy,
            cacheAge: now - connectionHealthCache.lastCheck
        });
        return { 
            success: connectionHealthCache.isHealthy, 
            cached: true,
            attempt: 1
        };
    }

    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            logger.info(`Testing database connection (attempt ${attempt}/${retries})`);
            
            // Use pool to get a connection quickly
            const start = Date.now();
            const client = await pool.connect();
            
            // Ultra quick test query
            await client.query('SELECT 1');
            client.release(); // Return to pool
            
            const duration = Date.now() - start;
            
            logger.info('Database connection test successful', { 
                duration: `${duration}ms`,
                attempt
            });
            
            // Update cache
            connectionHealthCache = {
                isHealthy: true,
                lastCheck: now,
                cacheDuration: 10000
            };
            
            return { success: true, attempt, duration };
            
        } catch (err) {
            logger.error(`Database connection failed (attempt ${attempt}/${retries}):`, { 
                error: err.message,
                code: err.code
            });
            
            if (attempt < retries) {
                logger.info(`Retrying in 500ms... (attempt ${attempt + 1}/${retries})`);
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
    }
    
    // Update cache with failure
    connectionHealthCache = {
        isHealthy: false,
        lastCheck: now,
        cacheDuration: 2000 // Cache failures for shorter time
    };
    
    return { success: false, attempts: retries };
};

// Execute query helper using pool
const query = async (text, params = []) => {
    const start = Date.now();
    try {
        const result = await pool.query(text, params);
        const duration = Date.now() - start;
        
        logger.debug('Query executed successfully:', {
            query: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
            duration: `${duration}ms`,
            rows: result.rowCount
        });
        
        return result;
    } catch (err) {
        logger.error('Query execution failed:', {
            error: err.message,
            query: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
            params: params
        });
        throw err;
    }
};

// Get client from pool for transactions
const getClient = async () => {
    try {
        return await pool.connect();
    } catch (err) {
        logger.error('Failed to get client from pool:', { error: err.message });
        throw err;
    }
};

// Graceful shutdown
const closePool = async () => {
    try {
        await pool.end();
        logger.info('Database pool closed successfully');
    } catch (err) {
        logger.error('Error closing database pool:', { error: err.message });
    }
};

// Initialize database connection on startup
const initializeDatabase = async () => {
    logger.info('Initializing database connection...');
    const result = await testConnection(3);
    
    if (result.success) {
        logger.info('✅ Database initialization successful');
        return true;
    } else {
        logger.error('❌ Database initialization failed');
        return false;
    }
};

module.exports = {
    pool,
    query,
    getClient,
    testConnection,
    closePool,
    initializeDatabase
};