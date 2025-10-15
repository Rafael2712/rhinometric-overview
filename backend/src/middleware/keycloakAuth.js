const jwksClient = require('jwks-rsa');
const jwt = require('jsonwebtoken');
const logger = require('../utils/logger');

class KeycloakAuth {
    constructor() {
        this.keycloakUrl = process.env.KEYCLOAK_URL || 'http://keycloak:8080';
        this.realm = process.env.KEYCLOAK_REALM || 'rhinometric';
        this.clientId = process.env.KEYCLOAK_CLIENT_ID || 'rhinometric-api';
        
        // JWKS client para validar tokens JWT
        this.client = jwksClient({
            jwksUri: `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/certs`,
            requestHeaders: {}, 
            timeout: 30000, 
        });
        
        logger.info('Keycloak Auth initialized', {
            keycloakUrl: this.keycloakUrl,
            realm: this.realm,
            clientId: this.clientId
        });
    }

    // Obtener clave pública para validar JWT
    getKey = (header, callback) => {
        this.client.getSigningKey(header.kid, (err, key) => {
            if (err) {
                logger.error('Error getting signing key:', err);
                return callback(err);
            }
            const signingKey = key.publicKey || key.rsaPublicKey;
            callback(null, signingKey);
        });
    };

    // Middleware de autenticación
    authenticate = (options = {}) => {
        return async (req, res, next) => {
            try {
                // Extraer token del header Authorization
                const authHeader = req.headers.authorization;
                if (!authHeader || !authHeader.startsWith('Bearer ')) {
                    return res.status(401).json({
                        error: 'Authentication required',
                        message: 'No valid authorization token provided'
                    });
                }

                const token = authHeader.substring(7); // Remove 'Bearer '

                // Verificar y decodificar el token JWT
                const decoded = await new Promise((resolve, reject) => {
                    jwt.verify(token, this.getKey, {
                        audience: this.clientId,
                        issuer: `${this.keycloakUrl}/realms/${this.realm}`,
                        algorithms: ['RS256']
                    }, (err, decoded) => {
                        if (err) {
                            logger.error('JWT verification failed:', {
                                error: err.message,
                                token: token.substring(0, 20) + '...'
                            });
                            reject(err);
                        } else {
                            resolve(decoded);
                        }
                    });
                });

                // Agregar información del usuario a la request
                req.user = {
                    id: decoded.sub,
                    username: decoded.preferred_username,
                    email: decoded.email,
                    name: decoded.name,
                    roles: decoded.realm_access?.roles || [],
                    clientRoles: decoded.resource_access?.[this.clientId]?.roles || [],
                    token: decoded
                };

                logger.debug('User authenticated successfully', {
                    userId: req.user.id,
                    username: req.user.username,
                    roles: req.user.roles
                });

                next();

            } catch (error) {
                logger.error('Authentication failed:', {
                    error: error.message,
                    path: req.path
                });

                return res.status(401).json({
                    error: 'Authentication failed',
                    message: 'Invalid or expired token'
                });
            }
        };
    };

    // Middleware de autorización basada en roles
    authorize = (requiredRoles = []) => {
        return (req, res, next) => {
            if (!req.user) {
                return res.status(401).json({
                    error: 'Authentication required',
                    message: 'User not authenticated'
                });
            }

            // Si no se requieren roles específicos, permitir acceso
            if (!requiredRoles.length) {
                return next();
            }

            // Verificar si el usuario tiene alguno de los roles requeridos
            const userRoles = [...req.user.roles, ...req.user.clientRoles];
            const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));

            if (!hasRequiredRole) {
                logger.warn('Authorization failed - insufficient permissions', {
                    userId: req.user.id,
                    username: req.user.username,
                    userRoles: userRoles,
                    requiredRoles: requiredRoles,
                    path: req.path
                });

                return res.status(403).json({
                    error: 'Authorization failed',
                    message: 'Insufficient permissions',
                    required: requiredRoles,
                    current: userRoles
                });
            }

            logger.debug('User authorized successfully', {
                userId: req.user.id,
                roles: userRoles,
                requiredRoles: requiredRoles
            });

            next();
        };
    };

    // Middleware opcional - no falla si no hay token
    optionalAuth = () => {
        return async (req, res, next) => {
            const authHeader = req.headers.authorization;
            
            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                // No hay token, continuar sin autenticación
                req.user = null;
                return next();
            }

            // Hay token, intentar autenticar
            return this.authenticate()(req, res, next);
        };
    };

    // Obtener información del token sin verificarlo (para debugging)
    decodeTokenUnsafe = (token) => {
        try {
            return jwt.decode(token, { complete: true });
        } catch (error) {
            logger.error('Error decoding token:', error);
            return null;
        }
    };

    // Verificar si Keycloak está disponible
    async healthCheck() {
        try {
            const fetch = require('node-fetch');
            const response = await fetch(`${this.keycloakUrl}/realms/${this.realm}/.well-known/openid_configuration`);
            
            if (response.ok) {
                logger.debug('Keycloak health check passed');
                return { healthy: true, url: this.keycloakUrl };
            } else {
                throw new Error(`Keycloak returned ${response.status}`);
            }
        } catch (error) {
            logger.error('Keycloak health check failed:', error.message);
            return { healthy: false, error: error.message };
        }
    }
}

module.exports = KeycloakAuth;