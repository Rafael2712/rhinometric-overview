const db = require('../src/config/database');
const logger = require('../src/utils/logger');

async function rollbackMigrations() {
    try {
        logger.info('Starting database rollback...');

        // Drop triggers first
        await db.query(`
            DROP TRIGGER IF EXISTS update_users_updated_at ON users;
            DROP TRIGGER IF EXISTS update_tenants_updated_at ON tenants;
        `);

        // Drop trigger function
        await db.query(`
            DROP FUNCTION IF EXISTS update_updated_at_column();
        `);

        // Drop tables (users first due to foreign key constraint)
        await db.query(`
            DROP TABLE IF EXISTS users;
        `);

        await db.query(`
            DROP TABLE IF EXISTS tenants;
        `);

        logger.info('✅ Database rollback completed successfully');

    } catch (error) {
        logger.error('❌ Database rollback failed:', { error: error.message });
        throw error;
    }
}

// Run rollback if this file is executed directly
if (require.main === module) {
    rollbackMigrations()
        .then(() => {
            logger.info('Rollback process completed');
            process.exit(0);
        })
        .catch((error) => {
            logger.error('Rollback process failed:', { error: error.message });
            process.exit(1);
        });
}

module.exports = { rollbackMigrations };