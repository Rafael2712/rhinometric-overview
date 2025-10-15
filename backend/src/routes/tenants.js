const express = require('express');
const Joi = require('joi');
const { v4: uuidv4 } = require('uuid');

const db = require('../config/database');
const logger = require('../utils/logger');
const SimpleAuth = require('../middleware/simpleAuth');

const router = express.Router();
const simpleAuth = new SimpleAuth();

// Authentication and authorization middleware
const requireAuth = simpleAuth.authenticateToken();
const requireAdmin = simpleAuth.authorize(['admin', 'tenant_manager']);
const requireUser = simpleAuth.authorize(['admin', 'tenant_manager', 'user']);

// Validation schemas
const createTenantSchema = Joi.object({
    name: Joi.string().min(2).max(100).required(),
    plan: Joi.string().valid('free', 'starter', 'professional', 'enterprise').default('free')
});

const updateTenantSchema = Joi.object({
    name: Joi.string().min(2).max(100).optional(),
    plan: Joi.string().valid('free', 'starter', 'professional', 'enterprise').optional(),
    status: Joi.string().valid('active', 'suspended', 'inactive').optional()
});

// Get all tenants (paginated) - Requires authentication
router.get('/', requireAuth, requireUser, async (req, res) => {
    try {
        // In a real app, check if user is super admin
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const offset = (page - 1) * limit;

        const result = await db.query(`
            SELECT t.*, 
                   COUNT(u.id) as user_count,
                   t.created_at,
                   t.updated_at
            FROM tenants t
            LEFT JOIN users u ON t.id = u.tenant_id
            GROUP BY t.id
            ORDER BY t.created_at DESC
            LIMIT $1 OFFSET $2
        `, [limit, offset]);

        const countResult = await db.query('SELECT COUNT(*) FROM tenants');
        const totalCount = parseInt(countResult.rows[0].count);

        res.json({
            tenants: result.rows,
            pagination: {
                page: page,
                limit: limit,
                total: totalCount,
                pages: Math.ceil(totalCount / limit)
            }
        });

    } catch (error) {
        logger.error('Get tenants failed:', { error: error.message });
        res.status(500).json({
            error: 'Failed to retrieve tenants',
            message: 'An error occurred while retrieving tenants'
        });
    }
});

// Get single tenant
router.get('/:id', requireAuth, requireUser, async (req, res) => {
    try {
        const tenantId = req.params.id;

        // Check if user has access to this tenant
        // In a real app, verify tenant access permissions

        const result = await db.query(`
            SELECT t.*, 
                   COUNT(u.id) as user_count
            FROM tenants t
            LEFT JOIN users u ON t.id = u.tenant_id
            WHERE t.id = $1
            GROUP BY t.id
        `, [tenantId]);

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'Tenant not found',
                message: 'The requested tenant does not exist'
            });
        }

        res.json({
            tenant: result.rows[0]
        });

    } catch (error) {
        logger.error('Get tenant failed:', { 
            error: error.message,
            tenantId: req.params.id 
        });
        
        res.status(500).json({
            error: 'Failed to retrieve tenant',
            message: 'An error occurred while retrieving tenant'
        });
    }
});

// Create new tenant - Requires admin/tenant_manager role
router.post('/', requireAuth, requireAdmin, async (req, res) => {
    try {
        // Validate input
        const { error, value } = createTenantSchema.validate(req.body);
        if (error) {
            return res.status(400).json({
                error: 'Validation error',
                message: error.details[0].message
            });
        }

        const { name, plan } = value;

        // Create tenant slug from name
        const slug = name.toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');

        // Check if tenant slug already exists
        const existingTenant = await db.query(
            'SELECT id FROM tenants WHERE slug = $1',
            [slug]
        );

        if (existingTenant.rows.length > 0) {
            return res.status(409).json({
                error: 'Tenant exists',
                message: 'A tenant with this name already exists'
            });
        }

        // Create tenant
        const tenantId = uuidv4();
        const result = await db.query(`
            INSERT INTO tenants (id, name, slug, plan, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            RETURNING *
        `, [tenantId, name, slug, plan, 'active']);

        const tenant = result.rows[0];

        logger.info('Tenant created:', {
            tenantId: tenant.id,
            name: tenant.name,
            createdBy: req.user.userId
        });

        res.status(201).json({
            message: 'Tenant created successfully',
            tenant: tenant
        });

    } catch (error) {
        logger.error('Create tenant failed:', { 
            error: error.message,
            name: req.body.name 
        });

        res.status(500).json({
            error: 'Failed to create tenant',
            message: 'An error occurred while creating tenant'
        });
    }
});

// Update tenant
router.put('/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
        const tenantId = req.params.id;

        // Validate input
        const { error, value } = updateTenantSchema.validate(req.body);
        if (error) {
            return res.status(400).json({
                error: 'Validation error',
                message: error.details[0].message
            });
        }

        // Check if tenant exists
        const existingTenant = await db.query(
            'SELECT * FROM tenants WHERE id = $1',
            [tenantId]
        );

        if (existingTenant.rows.length === 0) {
            return res.status(404).json({
                error: 'Tenant not found',
                message: 'The requested tenant does not exist'
            });
        }

        // Build update query dynamically
        const updateFields = [];
        const updateValues = [];
        let paramIndex = 1;

        Object.keys(value).forEach(field => {
            if (value[field] !== undefined) {
                updateFields.push(`${field} = $${paramIndex}`);
                updateValues.push(value[field]);
                paramIndex++;
            }
        });

        if (updateFields.length === 0) {
            return res.status(400).json({
                error: 'No update data',
                message: 'No valid fields to update'
            });
        }

        // Add updated_at field
        updateFields.push(`updated_at = NOW()`);

        // Add WHERE clause parameter
        updateValues.push(tenantId);

        const query = `
            UPDATE tenants 
            SET ${updateFields.join(', ')}
            WHERE id = $${paramIndex}
            RETURNING *
        `;

        const result = await db.query(query, updateValues);
        const updatedTenant = result.rows[0];

        logger.info('Tenant updated:', {
            tenantId: updatedTenant.id,
            updates: value,
            updatedBy: req.user.userId
        });

        res.json({
            message: 'Tenant updated successfully',
            tenant: updatedTenant
        });

    } catch (error) {
        logger.error('Update tenant failed:', { 
            error: error.message,
            tenantId: req.params.id 
        });

        res.status(500).json({
            error: 'Failed to update tenant',
            message: 'An error occurred while updating tenant'
        });
    }
});

// Delete tenant
router.delete('/:id', requireAuth, requireAdmin, async (req, res) => {
    try {
        const tenantId = req.params.id;

        // Check if tenant exists
        const existingTenant = await db.query(
            'SELECT * FROM tenants WHERE id = $1',
            [tenantId]
        );

        if (existingTenant.rows.length === 0) {
            return res.status(404).json({
                error: 'Tenant not found',
                message: 'The requested tenant does not exist'
            });
        }

        // Check if tenant has users (prevent accidental deletion)
        const userCount = await db.query(
            'SELECT COUNT(*) FROM users WHERE tenant_id = $1',
            [tenantId]
        );

        if (parseInt(userCount.rows[0].count) > 0) {
            return res.status(409).json({
                error: 'Cannot delete tenant',
                message: 'Tenant has associated users. Please remove users first.'
            });
        }

        // Delete tenant
        await db.query('DELETE FROM tenants WHERE id = $1', [tenantId]);

        logger.info('Tenant deleted:', {
            tenantId: tenantId,
            deletedBy: req.user.userId
        });

        res.json({
            message: 'Tenant deleted successfully'
        });

    } catch (error) {
        logger.error('Delete tenant failed:', { 
            error: error.message,
            tenantId: req.params.id 
        });

        res.status(500).json({
            error: 'Failed to delete tenant',
            message: 'An error occurred while deleting tenant'
        });
    }
});

// Get tenant statistics
router.get('/:id/stats', requireAuth, requireUser, async (req, res) => {
    try {
        const tenantId = req.params.id;

        // Get tenant statistics
        const stats = await db.query(`
            SELECT 
                (SELECT COUNT(*) FROM users WHERE tenant_id = $1) as user_count,
                (SELECT COUNT(*) FROM users WHERE tenant_id = $1 AND created_at >= NOW() - INTERVAL '30 days') as new_users_30d,
                (SELECT created_at FROM tenants WHERE id = $1) as tenant_created_at
        `, [tenantId]);

        if (stats.rows.length === 0) {
            return res.status(404).json({
                error: 'Tenant not found',
                message: 'The requested tenant does not exist'
            });
        }

        res.json({
            statistics: stats.rows[0]
        });

    } catch (error) {
        logger.error('Get tenant stats failed:', { 
            error: error.message,
            tenantId: req.params.id 
        });

        res.status(500).json({
            error: 'Failed to retrieve tenant statistics',
            message: 'An error occurred while retrieving statistics'
        });
    }
});

module.exports = router;