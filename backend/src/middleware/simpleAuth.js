const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const logger = require('../utils/logger');

class SimpleAuth {
    constructor() {
        this.jwtSecret = process.env.JWT_SECRET || 'ultra_secure_jwt_secret_2024_rhinometric_production';
        this.jwtExpiration = process.env.JWT_EXPIRATION || '24h';
        
        // Mock users database (en producción esto estaría en PostgreSQL)
        this.users = [
            {
                id: '1',
                username: 'admin',
                email: 'admin@rhinometric.com',
                password: bcrypt.hashSync('admin123', 10),
                roles: ['admin'],
                name: 'System Administrator'
            },
            {
                id: '2',
                username: 'manager',
                email: 'manager@rhinometric.com',
                password: bcrypt.hashSync('manager123', 10),
                roles: ['tenant_manager'],
                name: 'Tenant Manager'
            },
            {
                id: '3',
                username: 'user',
                email: 'user@rhinometric.com',
                password: bcrypt.hashSync('user123', 10),
                roles: ['user'],
                name: 'Standard User'
            }
        ];
        
        logger.info('Simple Auth initialized', {
            jwtExpiration: this.jwtExpiration,
            usersCount: this.users.length
        });
    }

    // Autenticar usuario con username/password
    async authenticate(username, password) {
        try {
            const user = this.users.find(u => u.username === username || u.email === username);
            
            if (!user) {
                logger.warn('Authentication failed - user not found', { username });
                return { success: false, message: 'User not found' };
            }

            const isValidPassword = await bcrypt.compare(password, user.password);
            
            if (!isValidPassword) {
                logger.warn('Authentication failed - invalid password', { username });
                return { success: false, message: 'Invalid password' };
            }

            // Generar JWT token
            const token = jwt.sign(
                {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    roles: user.roles,
                    name: user.name
                },
                this.jwtSecret,
                { 
                    expiresIn: this.jwtExpiration,
                    issuer: 'rhinometric-api',
                    audience: 'rhinometric-app'
                }
            );

            logger.info('Authentication successful', { 
                userId: user.id,
                username: user.username,
                roles: user.roles 
            });

            return {
                success: true,
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    name: user.name,
                    roles: user.roles
                },
                token
            };

        } catch (error) {
            logger.error('Authentication error:', error.message);
            return { success: false, message: 'Authentication service error' };
        }
    }

    // Middleware de autenticación JWT
    authenticateToken = () => {
        return (req, res, next) => {
            try {
                const authHeader = req.headers.authorization;
                
                if (!authHeader || !authHeader.startsWith('Bearer ')) {
                    return res.status(401).json({
                        error: 'Authentication required',
                        message: 'No valid authorization token provided'
                    });
                }

                const token = authHeader.substring(7);

                // Verificar JWT token
                const decoded = jwt.verify(token, this.jwtSecret, {
                    issuer: 'rhinometric-api',
                    audience: 'rhinometric-app'
                });

                // Agregar información del usuario a la request
                req.user = {
                    id: decoded.id,
                    username: decoded.username,
                    email: decoded.email,
                    name: decoded.name,
                    roles: decoded.roles || [],
                    token: decoded
                };

                logger.debug('User authenticated successfully', {
                    userId: req.user.id,
                    username: req.user.username,
                    roles: req.user.roles
                });

                next();

            } catch (error) {
                logger.error('JWT Authentication failed:', {
                    error: error.message,
                    path: req.path
                });

                let message = 'Invalid or expired token';
                if (error.name === 'TokenExpiredError') {
                    message = 'Token has expired';
                } else if (error.name === 'JsonWebTokenError') {
                    message = 'Invalid token format';
                }

                return res.status(401).json({
                    error: 'Authentication failed',
                    message: message
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
            const userRoles = req.user.roles || [];
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
        return (req, res, next) => {
            const authHeader = req.headers.authorization;
            
            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                req.user = null;
                return next();
            }

            // Hay token, intentar autenticar
            return this.authenticateToken()(req, res, next);
        };
    };

    // Verificar health (siempre true para JWT simple)
    async healthCheck() {
        return { 
            healthy: true, 
            type: 'jwt-simple',
            users: this.users.length 
        };
    }

    // Obtener información de todos los usuarios (sin passwords)
    getUsers() {
        return this.users.map(user => ({
            id: user.id,
            username: user.username,
            email: user.email,
            name: user.name,
            roles: user.roles
        }));
    }
}

module.exports = SimpleAuth;