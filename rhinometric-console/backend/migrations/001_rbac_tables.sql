-- ============================================================================
-- RHINOMETRIC v2.5.0 - RBAC DATABASE MIGRATION
-- Migration: 001_rbac_tables.sql
-- Date: 2026-01-16
-- Description: Create tables for Role-Based Access Control
-- ============================================================================

-- ============================================================================
-- 1. CREATE ROLES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    level INTEGER NOT NULL,  -- Jerarquía: 1=OWNER, 2=ADMIN, 3=OPERATOR, 4=VIEWER
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index para búsquedas rápidas por nombre
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_level ON roles(level);

COMMENT ON TABLE roles IS 'Roles disponibles en la plataforma (OWNER, ADMIN, OPERATOR, VIEWER)';
COMMENT ON COLUMN roles.level IS 'Nivel jerárquico: menor número = más permisos';

-- ============================================================================
-- 2. CREATE USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    must_change_password BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- Quién creó este usuario
    
    -- Campos adicionales
    avatar_url TEXT,
    phone VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en'
);

-- Indices para búsquedas rápidas
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS 'Usuarios de la plataforma con autenticación bcrypt';
COMMENT ON COLUMN users.password_hash IS 'Hash bcrypt de la contraseña (nunca texto plano)';
COMMENT ON COLUMN users.must_change_password IS 'Forzar cambio de contraseña en próximo login';

-- ============================================================================
-- 3. CREATE USER_ROLES TABLE (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- Quién asignó el rol
    
    -- Constraint: Un usuario no puede tener el mismo rol duplicado
    UNIQUE(user_id, role_id)
);

-- Indices para joins rápidos
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

COMMENT ON TABLE user_roles IS 'Asignación de roles a usuarios (relación N:N)';

-- ============================================================================
-- 4. CREATE PERMISSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    resource VARCHAR(100) NOT NULL,  -- Ej: 'dashboards', 'alerts', 'users'
    action VARCHAR(50) NOT NULL,     -- Ej: 'create', 'read', 'update', 'delete'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint: Combinación única de resource + action
    UNIQUE(resource, action)
);

-- Index para búsquedas rápidas
CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);

COMMENT ON TABLE permissions IS 'Permisos granulares sobre recursos';
COMMENT ON COLUMN permissions.resource IS 'Recurso protegido (dashboards, alerts, users, etc.)';
COMMENT ON COLUMN permissions.action IS 'Acción permitida (create, read, update, delete)';

-- ============================================================================
-- 5. CREATE ROLE_PERMISSIONS TABLE (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint: Un rol no puede tener el mismo permiso duplicado
    UNIQUE(role_id, permission_id)
);

-- Indices para joins rápidos
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

COMMENT ON TABLE role_permissions IS 'Permisos asignados a cada rol';

-- ============================================================================
-- 6. POBLAR ROLES INICIALES
-- ============================================================================
INSERT INTO roles (name, description, level) VALUES
    ('OWNER', 'Propietario de cuenta - Control total incluyendo facturación y transferencia de ownership', 1),
    ('ADMIN', 'Administrador - Gestión completa de configuración, usuarios (excepto OWNER) y recursos', 2),
    ('OPERATOR', 'Operador - Crear/editar dashboards personales, configurar alertas limitadas, visualizar todo', 3),
    ('VIEWER', 'Observador - Solo lectura de dashboards, métricas, logs y traces', 4)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 7. POBLAR PERMISOS INICIALES
-- ============================================================================

-- Permisos sobre DASHBOARDS
INSERT INTO permissions (resource, action, description) VALUES
    ('dashboards', 'create', 'Crear nuevos dashboards'),
    ('dashboards', 'read', 'Ver dashboards existentes'),
    ('dashboards', 'update', 'Editar dashboards existentes'),
    ('dashboards', 'delete', 'Eliminar dashboards'),
    ('dashboards', 'share', 'Compartir dashboards con otros usuarios')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre ALERTS
INSERT INTO permissions (resource, action, description) VALUES
    ('alerts', 'create', 'Crear nuevas reglas de alerta'),
    ('alerts', 'read', 'Ver alertas activas y reglas'),
    ('alerts', 'update', 'Modificar reglas de alerta'),
    ('alerts', 'delete', 'Eliminar reglas de alerta'),
    ('alerts', 'silence', 'Silenciar alertas temporalmente'),
    ('alerts', 'acknowledge', 'Reconocer alertas')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre USERS
INSERT INTO permissions (resource, action, description) VALUES
    ('users', 'create', 'Crear nuevos usuarios'),
    ('users', 'read', 'Ver lista de usuarios y detalles'),
    ('users', 'update', 'Modificar usuarios existentes'),
    ('users', 'delete', 'Eliminar usuarios'),
    ('users', 'assign_roles', 'Asignar o remover roles de usuarios')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre INTEGRATIONS
INSERT INTO permissions (resource, action, description) VALUES
    ('integrations', 'create', 'Crear nuevas integraciones (Slack, PagerDuty, etc.)'),
    ('integrations', 'read', 'Ver integraciones configuradas'),
    ('integrations', 'update', 'Modificar integraciones existentes'),
    ('integrations', 'delete', 'Eliminar integraciones')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre DATASOURCES
INSERT INTO permissions (resource, action, description) VALUES
    ('datasources', 'create', 'Crear nuevas fuentes de datos'),
    ('datasources', 'read', 'Ver fuentes de datos configuradas'),
    ('datasources', 'update', 'Modificar fuentes de datos'),
    ('datasources', 'delete', 'Eliminar fuentes de datos')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre SETTINGS
INSERT INTO permissions (resource, action, description) VALUES
    ('settings', 'read', 'Ver configuración de la plataforma'),
    ('settings', 'update', 'Modificar configuración de la plataforma')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre BILLING (solo OWNER)
INSERT INTO permissions (resource, action, description) VALUES
    ('billing', 'read', 'Ver información de facturación'),
    ('billing', 'update', 'Modificar métodos de pago y planes')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre REPORTS
INSERT INTO permissions (resource, action, description) VALUES
    ('reports', 'create', 'Generar reportes ejecutivos/técnicos'),
    ('reports', 'read', 'Ver reportes generados'),
    ('reports', 'schedule', 'Programar reportes automáticos')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre METRICS/LOGS/TRACES (lectura de datos)
INSERT INTO permissions (resource, action, description) VALUES
    ('metrics', 'read', 'Consultar métricas en Prometheus'),
    ('logs', 'read', 'Consultar logs en Loki'),
    ('traces', 'read', 'Consultar traces en Jaeger')
ON CONFLICT (resource, action) DO NOTHING;

-- Permisos sobre API KEYS
INSERT INTO permissions (resource, action, description) VALUES
    ('api_keys', 'create', 'Crear API keys para acceso programático'),
    ('api_keys', 'read', 'Ver API keys existentes'),
    ('api_keys', 'delete', 'Revocar API keys')
ON CONFLICT (resource, action) DO NOTHING;

-- ============================================================================
-- 8. ASIGNAR PERMISOS A ROLES
-- ============================================================================

-- OWNER: TODOS los permisos (control total)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'OWNER'),
    id
FROM permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ADMIN: Todos excepto billing
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'ADMIN'),
    id
FROM permissions
WHERE resource != 'billing'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- OPERATOR: Dashboards personales, alertas limitadas, lectura completa
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'OPERATOR'),
    id
FROM permissions
WHERE 
    -- Puede crear/editar dashboards personales
    (resource = 'dashboards' AND action IN ('create', 'read', 'update')) OR
    -- Puede ver y silenciar alertas
    (resource = 'alerts' AND action IN ('read', 'silence', 'acknowledge')) OR
    -- Puede leer métricas/logs/traces
    (resource IN ('metrics', 'logs', 'traces') AND action = 'read') OR
    -- Puede ver integraciones y datasources (pero no modificar)
    (resource IN ('integrations', 'datasources') AND action = 'read') OR
    -- Puede generar reportes manuales
    (resource = 'reports' AND action IN ('create', 'read'))
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- VIEWER: Solo lectura
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE name = 'VIEWER'),
    id
FROM permissions
WHERE 
    action = 'read' AND
    resource IN ('dashboards', 'alerts', 'metrics', 'logs', 'traces', 'integrations', 'datasources', 'reports')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ============================================================================
-- 9. MIGRAR USUARIO ADMIN ACTUAL A DB
-- ============================================================================

-- Crear usuario OWNER inicial (migración del usuario hardcodeado "admin")
-- Password: "admin" (DEBE ser cambiado en primer login)
-- Hash bcrypt de "admin": $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2VHl4kqLwe
INSERT INTO users (
    username, 
    email, 
    password_hash, 
    full_name, 
    is_active, 
    must_change_password
) VALUES (
    'admin',
    'admin@rhinometric.local',  -- DEBE ser actualizado en primer login
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2VHl4kqLwe',
    'Default Administrator',
    TRUE,
    TRUE  -- Forzar cambio de contraseña
)
ON CONFLICT (username) DO NOTHING
RETURNING id;

-- Asignar rol OWNER al usuario admin
INSERT INTO user_roles (user_id, role_id)
SELECT 
    (SELECT id FROM users WHERE username = 'admin'),
    (SELECT id FROM roles WHERE name = 'OWNER')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- ============================================================================
-- 10. TRIGGERS PARA UPDATED_AT
-- ============================================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger en users
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger en roles
DROP TRIGGER IF EXISTS update_roles_updated_at ON roles;
CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 11. VISTAS ÚTILES
-- ============================================================================

-- Vista: Usuarios con sus roles
CREATE OR REPLACE VIEW user_roles_view AS
SELECT 
    u.id AS user_id,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    r.name AS role_name,
    r.level AS role_level,
    ur.assigned_at,
    creator.username AS created_by_username
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
LEFT JOIN users creator ON u.created_by = creator.id;

-- Vista: Permisos efectivos de usuarios
CREATE OR REPLACE VIEW user_permissions_view AS
SELECT DISTINCT
    u.id AS user_id,
    u.username,
    r.name AS role_name,
    p.resource,
    p.action,
    p.description
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = TRUE
ORDER BY u.username, r.name, p.resource, p.action;

-- ============================================================================
-- 12. FUNCIONES DE UTILIDAD
-- ============================================================================

-- Función: Verificar si usuario tiene permiso
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id INTEGER,
    p_resource VARCHAR,
    p_action VARCHAR
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE 
            u.id = p_user_id AND
            u.is_active = TRUE AND
            p.resource = p_resource AND
            p.action = p_action
    );
END;
$$ LANGUAGE plpgsql;

-- Función: Obtener roles de usuario
CREATE OR REPLACE FUNCTION get_user_roles(p_user_id INTEGER)
RETURNS TABLE(role_name VARCHAR, role_level INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT r.name, r.level
    FROM users u
    JOIN user_roles ur ON u.id = ur.user_id
    JOIN roles r ON ur.role_id = r.id
    WHERE u.id = p_user_id AND u.is_active = TRUE
    ORDER BY r.level;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 13. GRANTS (Permisos PostgreSQL)
-- ============================================================================

-- Asegurar que usuario 'rhinometric' tiene permisos
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rhinometric;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rhinometric;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rhinometric;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================

-- Verificar que todo se creó correctamente
SELECT 'Migration 001_rbac_tables.sql completed successfully' AS status;

-- Mostrar resumen
SELECT 'Roles creados:' AS info, COUNT(*) AS count FROM roles
UNION ALL
SELECT 'Permisos creados:', COUNT(*) FROM permissions
UNION ALL
SELECT 'Usuarios creados:', COUNT(*) FROM users
UNION ALL
SELECT 'Asignaciones rol-permiso:', COUNT(*) FROM role_permissions;
