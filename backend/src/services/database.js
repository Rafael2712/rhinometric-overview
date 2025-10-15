const { Pool } = require('pg');
const logger = require('../utils/logger');
const { dbQueryDuration } = require('../utils/metrics');

class DatabaseService {
    constructor() {
        this.pool = new Pool({
            host: process.env.DB_HOST || 'localhost',
            port: process.env.DB_PORT || 5432,
            database: process.env.DB_NAME || 'rhinometric_dev',
            user: process.env.DB_USER || 'postgres',
            password: process.env.DB_PASSWORD || 'rhinometric2024',
            max: 20,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 10000,
        });

        this.pool.on('error', (err) => {
            logger.error('Database pool error:', err);
        });
    }

    async executeQuery(query, params = []) {
        const startTime = Date.now();
        let client;
        
        try {
            client = await this.pool.connect();
            const result = await client.query(query, params);
            
            // Registrar métrica de duración
            const duration = (Date.now() - startTime) / 1000;
            dbQueryDuration.observe(duration);

            return {
                success: true,
                data: result.rows,
                rowCount: result.rowCount,
                duration: duration
            };

        } catch (error) {
            const duration = (Date.now() - startTime) / 1000;
            dbQueryDuration.observe(duration);

            return {
                success: false,
                error: error.message,
                duration: duration
            };
        } finally {
            if (client) client.release();
        }
    }

    // Consultas específicas para generar métricas
    async getUsers() {
        return await this.executeQuery(
            'SELECT id, email, name, created_at FROM users ORDER BY created_at DESC LIMIT 50'
        );
    }

    async getOrganizations() {
        return await this.executeQuery(
            'SELECT id, name, slug, created_at FROM organizations ORDER BY created_at DESC LIMIT 50'
        );
    }

    async getUserStats() {
        return await this.executeQuery(`
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as new_today,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week
            FROM users
        `);
    }

    async getOrgStats() {
        return await this.executeQuery(`
            SELECT 
                COUNT(*) as total_orgs,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as new_today,
                AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
            FROM organizations
        `);
    }

    async getHealthCheck() {
        return await this.executeQuery('SELECT NOW() as server_time, version() as pg_version');
    }

    async createDemoData() {
        // Crear algunas organizaciones de prueba si no existen
        const orgQuery = `
            INSERT INTO organizations (name, slug, subscription_plan, created_at) 
            VALUES 
                ('Demo Corp', 'demo-corp', 'premium', NOW() - INTERVAL '30 days'),
                ('Test Ltd', 'test-ltd', 'basic', NOW() - INTERVAL '15 days'),
                ('Example Inc', 'example-inc', 'enterprise', NOW() - INTERVAL '5 days')
            ON CONFLICT (slug) DO NOTHING
        `;

        const userQuery = `
            INSERT INTO users (email, name, created_at) 
            VALUES 
                ('admin@democorp.com', 'Admin User', NOW() - INTERVAL '25 days'),
                ('manager@testltd.com', 'Manager User', NOW() - INTERVAL '10 days'),
                ('user@exampleinc.com', 'Regular User', NOW() - INTERVAL '2 days')
            ON CONFLICT (email) DO NOTHING
        `;

        const orgResult = await this.executeQuery(orgQuery);
        const userResult = await this.executeQuery(userQuery);

        return {
            organizations: orgResult,
            users: userResult
        };
    }

    async close() {
        await this.pool.end();
    }
}

// Singleton instance
const dbService = new DatabaseService();

module.exports = dbService;