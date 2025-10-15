const express = require('express');
const logger = require('../utils/logger');
const SimpleAuth = require('../middleware/simpleAuth');
const { authAttempts } = require('../utils/metrics');

const router = express.Router();
const simpleAuth = new SimpleAuth();

// Login endpoint
router.post('/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({
                error: 'Validation Error',
                message: 'Username and password are required'
            });
        }

        logger.info('Login attempt', { username });

        const result = await simpleAuth.authenticate(username, password);

        if (!result.success) {
            // Registrar intento de autenticación fallido
            authAttempts.inc({ result: 'failure', method: 'password' });
            
            return res.status(401).json({
                error: 'Authentication Failed',
                message: result.message
            });
        }

        // Registrar intento de autenticación exitoso
        authAttempts.inc({ result: 'success', method: 'password' });

        res.json({
            message: 'Authentication successful',
            user: result.user,
            token: result.token,
            expires_in: '24h'
        });

    } catch (error) {
        logger.error('Login error:', error.message);

        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Authentication service temporarily unavailable'
        });
    }
});

// Obtener información del usuario actual
router.get('/me', simpleAuth.authenticateToken(), (req, res) => {
    res.json({
        user: {
            id: req.user.id,
            username: req.user.username,
            email: req.user.email,
            name: req.user.name,
            roles: req.user.roles
        }
    });
});

// Verificar token (health check para autenticación)
router.get('/verify', simpleAuth.authenticateToken(), (req, res) => {
    res.json({
        valid: true,
        user: req.user.username,
        roles: req.user.roles,
        expires: req.user.token.exp
    });
});

// Logout (simple - JWT es stateless)
router.post('/logout', simpleAuth.authenticateToken(), (req, res) => {
    logger.info('User logged out', { 
        userId: req.user.id,
        username: req.user.username 
    });

    res.json({
        message: 'Logout successful',
        note: 'JWT tokens remain valid until expiration'
    });
});

// Obtener usuarios disponibles (solo para admin)
router.get('/users', 
    simpleAuth.authenticateToken(), 
    simpleAuth.authorize(['admin']), 
    (req, res) => {
        const users = simpleAuth.getUsers();
        res.json({
            users: users,
            count: users.length
        });
    }
);

// Obtener configuración de autenticación
router.get('/config', async (req, res) => {
    try {
        const healthCheck = await simpleAuth.healthCheck();
        
        res.json({
            auth: {
                type: 'jwt-simple',
                healthy: healthCheck.healthy,
                loginEndpoint: '/api/v1/auth/login',
                verifyEndpoint: '/api/v1/auth/verify',
                userInfoEndpoint: '/api/v1/auth/me'
            },
            demo: {
                users: [
                    { username: 'admin', password: 'admin123', roles: ['admin'] },
                    { username: 'manager', password: 'manager123', roles: ['tenant_manager'] },
                    { username: 'user', password: 'user123', roles: ['user'] }
                ]
            }
        });

    } catch (error) {
        logger.error('Config endpoint error:', error.message);
        
        res.status(500).json({
            error: 'Configuration unavailable',
            message: error.message
        });
    }
});

module.exports = router;