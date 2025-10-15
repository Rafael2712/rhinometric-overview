const express = require('express');
const fetch = require('node-fetch');
const logger = require('../utils/logger');
const KeycloakAuth = require('../middleware/keycloakAuth');

const router = express.Router();
const keycloakAuth = new KeycloakAuth();

// Configuración de Keycloak
const KEYCLOAK_URL = process.env.KEYCLOAK_URL || 'http://keycloak:8080';
const REALM = process.env.KEYCLOAK_REALM || 'rhinometric';
const CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID || 'rhinometric-api';
const CLIENT_SECRET = process.env.KEYCLOAK_CLIENT_SECRET || '';

// Login con Keycloak (Direct Access Grant)
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

        // Autenticar con Keycloak usando Direct Access Grant
        const tokenUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`;
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                grant_type: 'password',
                client_id: CLIENT_ID,
                client_secret: CLIENT_SECRET,
                username: username,
                password: password,
                scope: 'openid profile email'
            })
        });

        const tokenData = await response.json();

        if (!response.ok) {
            logger.warn('Login failed', { 
                username, 
                error: tokenData.error,
                description: tokenData.error_description 
            });
            
            return res.status(401).json({
                error: 'Authentication Failed',
                message: tokenData.error_description || 'Invalid credentials'
            });
        }

        // Decodificar token para obtener información del usuario
        const userInfo = keycloakAuth.decodeTokenUnsafe(tokenData.access_token);
        const payload = userInfo?.payload;

        logger.info('Login successful', { 
            username, 
            userId: payload?.sub,
            roles: payload?.realm_access?.roles 
        });

        res.json({
            message: 'Authentication successful',
            user: {
                id: payload?.sub,
                username: payload?.preferred_username,
                email: payload?.email,
                name: payload?.name,
                roles: payload?.realm_access?.roles || [],
                clientRoles: payload?.resource_access?.[CLIENT_ID]?.roles || []
            },
            tokens: {
                access_token: tokenData.access_token,
                refresh_token: tokenData.refresh_token,
                expires_in: tokenData.expires_in,
                token_type: tokenData.token_type
            }
        });

    } catch (error) {
        logger.error('Login error:', {
            error: error.message,
            stack: error.stack
        });

        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Login service temporarily unavailable'
        });
    }
});

// Refresh token
router.post('/refresh', async (req, res) => {
    try {
        const { refresh_token } = req.body;

        if (!refresh_token) {
            return res.status(400).json({
                error: 'Validation Error',
                message: 'Refresh token is required'
            });
        }

        const tokenUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`;
        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                grant_type: 'refresh_token',
                client_id: CLIENT_ID,
                client_secret: CLIENT_SECRET,
                refresh_token: refresh_token
            })
        });

        const tokenData = await response.json();

        if (!response.ok) {
            logger.warn('Token refresh failed', { 
                error: tokenData.error,
                description: tokenData.error_description 
            });
            
            return res.status(401).json({
                error: 'Token Refresh Failed',
                message: tokenData.error_description || 'Invalid refresh token'
            });
        }

        logger.info('Token refreshed successfully');

        res.json({
            message: 'Token refreshed successfully',
            tokens: {
                access_token: tokenData.access_token,
                refresh_token: tokenData.refresh_token,
                expires_in: tokenData.expires_in,
                token_type: tokenData.token_type
            }
        });

    } catch (error) {
        logger.error('Token refresh error:', error.message);

        res.status(500).json({
            error: 'Internal Server Error',
            message: 'Token refresh service temporarily unavailable'
        });
    }
});

// Logout
router.post('/logout', keycloakAuth.authenticate(), async (req, res) => {
    try {
        const { refresh_token } = req.body;

        if (refresh_token) {
            // Logout del token en Keycloak
            const logoutUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout`;
            await fetch(logoutUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    client_id: CLIENT_ID,
                    client_secret: CLIENT_SECRET,
                    refresh_token: refresh_token
                })
            });
        }

        logger.info('User logged out', { 
            userId: req.user.id,
            username: req.user.username 
        });

        res.json({
            message: 'Logout successful'
        });

    } catch (error) {
        logger.error('Logout error:', error.message);
        
        res.json({
            message: 'Logout completed (with warnings)',
            warning: 'Could not revoke tokens in Keycloak'
        });
    }
});

// Obtener información del usuario actual
router.get('/me', keycloakAuth.authenticate(), (req, res) => {
    res.json({
        user: {
            id: req.user.id,
            username: req.user.username,
            email: req.user.email,
            name: req.user.name,
            roles: req.user.roles,
            clientRoles: req.user.clientRoles
        }
    });
});

// Verificar token (health check para autenticación)
router.get('/verify', keycloakAuth.authenticate(), (req, res) => {
    res.json({
        valid: true,
        user: req.user.username,
        roles: req.user.roles,
        expires: req.user.token.exp
    });
});

// Obtener configuración pública de Keycloak
router.get('/config', async (req, res) => {
    try {
        const keycloakHealth = await keycloakAuth.healthCheck();
        
        res.json({
            keycloak: {
                url: KEYCLOAK_URL,
                realm: REALM,
                clientId: CLIENT_ID,
                healthy: keycloakHealth.healthy,
                authUrl: `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth`,
                tokenUrl: `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`,
                userInfoUrl: `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/userinfo`,
                logoutUrl: `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout`
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