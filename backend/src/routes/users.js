const express = require('express');
const logger = require('../utils/logger');
const dbService = require('../services/database');
const SimpleAuth = require('../middleware/simpleAuth');

const router = express.Router();
const simpleAuth = new SimpleAuth();

// GET /api/v1/users - Obtener usuarios (genera métrica DB)
router.get('/', simpleAuth.authenticateToken(), async (req, res) => {
    try {
        logger.info('Fetching users list', { userId: req.user.id });

        const result = await dbService.getUsers();

        if (!result.success) {
            return res.status(500).json({
                error: 'Database Error',
                message: 'Could not retrieve users'
            });
        }

        res.json({
            users: result.data,
            count: result.rowCount,
            query_duration: result.duration
        });

    } catch (error) {
        logger.error('Users endpoint error:', error.message);
        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Users service unavailable'
        });
    }
});

// GET /api/v1/users/stats - Estadísticas de usuarios
router.get('/stats', simpleAuth.authenticateToken(), async (req, res) => {
    try {
        logger.info('Fetching user statistics', { userId: req.user.id });

        const result = await dbService.getUserStats();

        if (!result.success) {
            return res.status(500).json({
                error: 'Database Error',
                message: 'Could not retrieve user statistics'
            });
        }

        const stats = result.data[0] || {};
        
        res.json({
            statistics: {
                total: parseInt(stats.total_users) || 0,
                new_today: parseInt(stats.new_today) || 0,
                new_this_week: parseInt(stats.new_this_week) || 0
            },
            query_duration: result.duration,
            generated_at: new Date().toISOString()
        });

    } catch (error) {
        logger.error('User stats endpoint error:', error.message);
        res.status(500).json({
            error: 'Internal Server Error', 
            message: 'Statistics service unavailable'
        });
    }
});

// POST /api/v1/users/demo-data - Crear datos de demo
router.post('/demo-data', 
    simpleAuth.authenticateToken(), 
    simpleAuth.authorize(['admin']), 
    async (req, res) => {
        try {
            logger.info('Creating demo data', { userId: req.user.id });

            const result = await dbService.createDemoData();

            res.json({
                message: 'Demo data created successfully',
                results: result,
                created_at: new Date().toISOString()
            });

        } catch (error) {
            logger.error('Demo data creation error:', error.message);
            res.status(500).json({
                error: 'Internal Server Error',
                message: 'Could not create demo data'
            });
        }
    }
);

module.exports = router;