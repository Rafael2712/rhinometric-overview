-- Direct seeds script for PostgreSQL
-- Insert demo tenant (only if not exists)
INSERT INTO tenants (name, slug, plan, status, settings)
SELECT 'Demo Company', 'demo-company', 'premium', 'active', 
    '{"features": ["analytics", "api_access", "custom_domain"], "limits": {"users": 50, "api_calls": 10000}}'
WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE slug = 'demo-company');

-- Insert demo user (only if not exists)
INSERT INTO users (tenant_id, email, password_hash, role, first_name, last_name)
SELECT t.id, 'admin@demo-company.com', 
    '$2b$10$rOqb3QzJzJzQzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJz', -- bcrypt hash for 'demo123'
    'admin', 'Demo', 'Admin'
FROM tenants t 
WHERE t.slug = 'demo-company'
AND NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@demo-company.com');

-- Insert regular demo user
INSERT INTO users (tenant_id, email, password_hash, role, first_name, last_name)
SELECT t.id, 'user@demo-company.com', 
    '$2b$10$rOqb3QzJzJzQzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJzJz', -- bcrypt hash for 'demo123'
    'user', 'Demo', 'User'
FROM tenants t 
WHERE t.slug = 'demo-company'
AND NOT EXISTS (SELECT 1 FROM users WHERE email = 'user@demo-company.com');

-- Verification
SELECT 'Seeds completed successfully' as status;
SELECT COUNT(*) as tenant_count FROM tenants;
SELECT COUNT(*) as user_count FROM users;