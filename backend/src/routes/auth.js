const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const Joi = require('joi');

const db = require('../config/database');
const logger = require('../utils/logger');

const router = express.Router();

// Validation schemas
const registerSchema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().min(8).required(),
    tenantName: Joi.string().min(2).max(100).required(),
    firstName: Joi.string().min(1).max(50).optional(),
    lastName: Joi.string().min(1).max(50).optional()
});

const loginSchema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
});

// JWT helper functions
const generateToken = (payload) => {
    return jwt.sign(payload, process.env.JWT_SECRET, {
        expiresIn: process.env.JWT_EXPIRES_IN || '7d'
    });
};

const verifyToken = (token) => {
    return jwt.verify(token, process.env.JWT_SECRET);
};

// Authentication middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ 
            error: 'Access denied', 
            message: 'No token provided' 
        });
    }

    try {
        const decoded = verifyToken(token);
        req.user = decoded;
        next();
    } catch (error) {
        logger.warn('Invalid token attempt:', { 
            error: error.message,
            ip: req.ip 
        });
        
        return res.status(403).json({ 
            error: 'Access denied', 
            message: 'Invalid token' 
        });
    }
};

// Register new user and tenant
router.post('/register', async (req, res) => {
    try {
        // Validate input
        const { error, value } = registerSchema.validate(req.body);
        if (error) {
            return res.status(400).json({
                error: 'Validation error',
                message: error.details[0].message
            });
        }

        const { email, password, tenantName, firstName, lastName } = value;

        // Check if user already exists
        const existingUser = await db.query(
            'SELECT id FROM users WHERE email = $1',
            [email]
        );

        if (existingUser.rows.length > 0) {
            return res.status(409).json({
                error: 'User exists',
                message: 'A user with this email already exists'
            });
        }

        // Create tenant slug from name
        const tenantSlug = tenantName.toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');

        // Check if tenant slug already exists
        const existingTenant = await db.query(
            'SELECT id FROM tenants WHERE slug = $1',
            [tenantSlug]
        );

        if (existingTenant.rows.length > 0) {
            return res.status(409).json({
                error: 'Tenant exists',
                message: 'A tenant with this name already exists'
            });
        }

        // Hash password
        const saltRounds = 12;
        const passwordHash = await bcrypt.hash(password, saltRounds);

        // Start transaction
        const client = await db.getClient();
        try {
            await client.query('BEGIN');

            // Create tenant
            const tenantResult = await client.query(
                `INSERT INTO tenants (id, name, slug, plan, status, created_at, updated_at) 
                 VALUES ($1, $2, $3, $4, $5, NOW(), NOW()) 
                 RETURNING *`,
                [uuidv4(), tenantName, tenantSlug, 'free', 'active']
            );
            const tenant = tenantResult.rows[0];

            // Create user
            const userResult = await client.query(
                `INSERT INTO users (id, tenant_id, email, password_hash, role, first_name, last_name, created_at, updated_at) 
                 VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW()) 
                 RETURNING id, tenant_id, email, role, first_name, last_name, created_at`,
                [uuidv4(), tenant.id, email, passwordHash, 'admin', firstName, lastName]
            );
            const user = userResult.rows[0];

            await client.query('COMMIT');

            // Generate JWT token
            const token = generateToken({
                userId: user.id,
                tenantId: user.tenant_id,
                email: user.email,
                role: user.role
            });

            logger.info('New user registered:', {
                userId: user.id,
                tenantId: user.tenant_id,
                email: user.email,
                tenantName: tenant.name
            });

            res.status(201).json({
                message: 'Registration successful',
                token: token,
                user: {
                    id: user.id,
                    email: user.email,
                    role: user.role,
                    firstName: user.first_name,
                    lastName: user.last_name
                },
                tenant: {
                    id: tenant.id,
                    name: tenant.name,
                    slug: tenant.slug,
                    plan: tenant.plan
                }
            });

        } catch (dbError) {
            await client.query('ROLLBACK');
            throw dbError;
        } finally {
            client.release();
        }

    } catch (error) {
        logger.error('Registration failed:', { 
            error: error.message,
            email: req.body.email 
        });

        res.status(500).json({
            error: 'Registration failed',
            message: 'An error occurred during registration'
        });
    }
});

// Login user
router.post('/login', async (req, res) => {
    try {
        // Validate input
        const { error, value } = loginSchema.validate(req.body);
        if (error) {
            return res.status(400).json({
                error: 'Validation error',
                message: error.details[0].message
            });
        }

        const { email, password } = value;

        // Find user with tenant information
        const userResult = await db.query(`
            SELECT u.*, t.name as tenant_name, t.slug as tenant_slug, t.plan as tenant_plan, t.status as tenant_status
            FROM users u 
            JOIN tenants t ON u.tenant_id = t.id 
            WHERE u.email = $1
        `, [email]);

        if (userResult.rows.length === 0) {
            return res.status(401).json({
                error: 'Authentication failed',
                message: 'Invalid email or password'
            });
        }

        const user = userResult.rows[0];

        // Check if tenant is active
        if (user.tenant_status !== 'active') {
            return res.status(403).json({
                error: 'Account suspended',
                message: 'Your account has been suspended. Please contact support.'
            });
        }

        // Verify password
        const isPasswordValid = await bcrypt.compare(password, user.password_hash);
        if (!isPasswordValid) {
            return res.status(401).json({
                error: 'Authentication failed',
                message: 'Invalid email or password'
            });
        }

        // Generate JWT token
        const token = generateToken({
            userId: user.id,
            tenantId: user.tenant_id,
            email: user.email,
            role: user.role
        });

        logger.info('User logged in:', {
            userId: user.id,
            tenantId: user.tenant_id,
            email: user.email,
            ip: req.ip
        });

        res.json({
            message: 'Login successful',
            token: token,
            user: {
                id: user.id,
                email: user.email,
                role: user.role,
                firstName: user.first_name,
                lastName: user.last_name
            },
            tenant: {
                id: user.tenant_id,
                name: user.tenant_name,
                slug: user.tenant_slug,
                plan: user.tenant_plan
            }
        });

    } catch (error) {
        logger.error('Login failed:', { 
            error: error.message,
            email: req.body.email,
            ip: req.ip 
        });

        res.status(500).json({
            error: 'Login failed',
            message: 'An error occurred during login'
        });
    }
});

// Get current user (protected route)
router.get('/me', authenticateToken, async (req, res) => {
    try {
        const userResult = await db.query(`
            SELECT u.*, t.name as tenant_name, t.slug as tenant_slug, t.plan as tenant_plan
            FROM users u 
            JOIN tenants t ON u.tenant_id = t.id 
            WHERE u.id = $1
        `, [req.user.userId]);

        if (userResult.rows.length === 0) {
            return res.status(404).json({
                error: 'User not found',
                message: 'User account not found'
            });
        }

        const user = userResult.rows[0];

        res.json({
            user: {
                id: user.id,
                email: user.email,
                role: user.role,
                firstName: user.first_name,
                lastName: user.last_name,
                createdAt: user.created_at
            },
            tenant: {
                id: user.tenant_id,
                name: user.tenant_name,
                slug: user.tenant_slug,
                plan: user.tenant_plan
            }
        });

    } catch (error) {
        logger.error('Get user failed:', { 
            error: error.message,
            userId: req.user.userId 
        });

        res.status(500).json({
            error: 'Failed to get user',
            message: 'An error occurred while retrieving user information'
        });
    }
});

// Logout user (could be used to invalidate token on server-side)
router.post('/logout', authenticateToken, (req, res) => {
    logger.info('User logged out:', {
        userId: req.user.userId,
        tenantId: req.user.tenantId,
        ip: req.ip
    });

    res.json({
        message: 'Logout successful'
    });
});

module.exports = router;