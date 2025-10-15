const express = require('express');
const logger = require('../utils/logger');
const dbService = require('../services/database');
const SimpleAuth = require('../middleware/simpleAuth');

const router = express.Router();
const simpleAuth = new SimpleAuth();

// GET /api/v1/organizations - Obtener organizaciones (genera métrica DB)
router.get('/', simpleAuth.authenticateToken(), async (req, res) => {
    try {
        logger.info('Fetching organizations list', { userId: req.user.id });

        const result = await dbService.getOrganizations();

        if (!result.success) {
            return res.status(500).json({
                error: 'Database Error',
                message: 'Could not retrieve organizations'
            });
        }

        res.json({
            organizations: result.data,
            count: result.rowCount,
            query_duration: result.duration
        });

    } catch (error) {
        logger.error('Organizations endpoint error:', error.message);
        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Organizations service unavailable'
        });
    }
});

// GET /api/v1/organizations/stats - Estadísticas de organizaciones
router.get('/stats', simpleAuth.authenticateToken(), async (req, res) => {
    try {
        logger.info('Fetching organization statistics', { userId: req.user.id });

        const result = await dbService.getOrgStats();

        if (!result.success) {
            return res.status(500).json({
                error: 'Database Error',
                message: 'Could not retrieve organization statistics'
            });
        }

        const stats = result.data[0] || {};
        
        res.json({
            statistics: {
                total: parseInt(stats.total_orgs) || 0,
                new_today: parseInt(stats.new_today) || 0,
                average_age_days: Math.round((parseFloat(stats.avg_age_seconds) || 0) / 86400)
            },
            query_duration: result.duration,
            generated_at: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Organization stats endpoint error:', error.message);
        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Statistics service unavailable'
        });
    }
});

module.exports = router;