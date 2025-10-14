const db = require('../src/config/database');
const bcrypt = require('bcrypt');
const logger = require('../src/utils/logger');

async function runSeeds() {
    try {
        logger.info('Starting database seeding...');

        // Check if seeds already exist
        const existingTenants = await db.query('SELECT COUNT(*) as count FROM tenants');
        if (parseInt(existingTenants.rows[0].count) > 0) {
            logger.info('Seeds already exist, skipping...');
            return;
        }

        // Create demo tenant
        const tenantResult = await db.query(`
            INSERT INTO tenants (name, slug, plan, status, settings)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        `, [
            'Demo Company',
            'demo-company',
            'premium',
            'active',
            JSON.stringify({
                features: ['analytics', 'api_access', 'custom_domain'],
                limits: {
                    users: 50,
                    api_calls: 10000,
                    storage_gb: 100
                },
                contact: {
                    email: 'admin@demo-company.com',
                    phone: '+1-555-0123'
                }
            })
        ]);

        const tenantId = tenantResult.rows[0].id;

        // Create demo users
        const passwordHash = await bcrypt.hash('demo123', 10);

        // Admin user
        await db.query(`
            INSERT INTO users (tenant_id, email, password_hash, role, first_name, last_name, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
            tenantId,
            'admin@demo-company.com',
            passwordHash,
            'admin',
            'Demo',
            'Administrator',
            true
        ]);

        // Regular user
        await db.query(`
            INSERT INTO users (tenant_id, email, password_hash, role, first_name, last_name, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
            tenantId,
            'user@demo-company.com',
            passwordHash,
            'user',
            'Demo',
            'User',
            true
        ]);

        // Create a second tenant for testing multi-tenancy
        const tenant2Result = await db.query(`
            INSERT INTO tenants (name, slug, plan, status, settings)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        `, [
            'Test Startup',
            'test-startup',
            'free',
            'active',
            JSON.stringify({
                features: ['basic_analytics'],
                limits: {
                    users: 5,
                    api_calls: 1000,
                    storage_gb: 10
                }
            })
        ]);

        const tenant2Id = tenant2Result.rows[0].id;

        // Create user for second tenant
        await db.query(`
            INSERT INTO users (tenant_id, email, password_hash, role, first_name, last_name, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
            tenant2Id,
            'founder@test-startup.com',
            passwordHash,
            'admin',
            'Startup',
            'Founder',
            true
        ]);

        logger.info('✅ Database seeding completed successfully');
        logger.info('Demo accounts created:');
        logger.info('  - admin@demo-company.com (admin role)');
        logger.info('  - user@demo-company.com (user role)');
        logger.info('  - founder@test-startup.com (admin role)');
        logger.info('  - Password for all accounts: demo123');

    } catch (error) {
        logger.error('❌ Database seeding failed:', { error: error.message });
        throw error;
    }
}

// Run seeds if this file is executed directly
if (require.main === module) {
    runSeeds()
        .then(() => {
            logger.info('Seeding process completed');
            process.exit(0);
        })
        .catch((error) => {
            logger.error('Seeding process failed:', { error: error.message });
            process.exit(1);
        });
}

module.exports = { runSeeds };