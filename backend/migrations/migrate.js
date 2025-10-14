const db = require('../src/config/database');
const logger = require('../src/utils/logger');

async function runMigrations() {
    try {
        logger.info('Starting database migrations...');

        // Create tenants table
        await db.query(`
            CREATE TABLE IF NOT EXISTS tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                plan VARCHAR(50) NOT NULL DEFAULT 'free',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                settings JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        `);

        // Create users table
        await db.query(`
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                last_login TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        `);

        // Create indexes
        await db.query(`
            CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
            CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
        `);

        // Create updated_at trigger function
        await db.query(`
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        `);

        // Create triggers for updated_at
        await db.query(`
            DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
            CREATE TRIGGER update_tenants_updated_at 
                BEFORE UPDATE ON tenants 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        `);

        await db.query(`
            DROP TRIGGER IF EXISTS update_users_updated_at ON users;
            CREATE TRIGGER update_users_updated_at 
                BEFORE UPDATE ON users 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        `);

        logger.info('✅ Database migrations completed successfully');

    } catch (error) {
        logger.error('❌ Database migration failed:', { error: error.message });
        throw error;
    }
}

// Run migrations if this file is executed directly
if (require.main === module) {
    runMigrations()
        .then(() => {
            logger.info('Migration process completed');
            process.exit(0);
        })
        .catch((error) => {
            logger.error('Migration process failed:', { error: error.message });
            process.exit(1);
        });
}

module.exports = { runMigrations };