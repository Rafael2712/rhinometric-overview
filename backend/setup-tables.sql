-- Crear tablas básicas para generar métricas de base de datos
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_orgs_created_at ON organizations(created_at);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

-- Insertar datos de ejemplo
INSERT INTO organizations (name, slug, subscription_plan, created_at) VALUES
    ('Demo Corp', 'demo-corp', 'premium', NOW() - INTERVAL '30 days'),
    ('Test Ltd', 'test-ltd', 'basic', NOW() - INTERVAL '15 days'),
    ('Example Inc', 'example-inc', 'enterprise', NOW() - INTERVAL '5 days'),
    ('Startup Co', 'startup-co', 'basic', NOW() - INTERVAL '2 days'),
    ('Enterprise Corp', 'enterprise-corp', 'enterprise', NOW() - INTERVAL '45 days')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO users (email, name, organization_id, created_at) VALUES
    ('admin@democorp.com', 'Admin User', 1, NOW() - INTERVAL '25 days'),
    ('manager@testltd.com', 'Manager User', 2, NOW() - INTERVAL '10 days'),
    ('user@exampleinc.com', 'Regular User', 3, NOW() - INTERVAL '2 days'),
    ('founder@startupco.com', 'Founder', 4, NOW() - INTERVAL '1 day'),
    ('ceo@enterprisecorp.com', 'CEO User', 5, NOW() - INTERVAL '40 days'),
    ('dev@democorp.com', 'Developer', 1, NOW() - INTERVAL '20 days'),
    ('support@testltd.com', 'Support User', 2, NOW() - INTERVAL '8 days')
ON CONFLICT (email) DO NOTHING;