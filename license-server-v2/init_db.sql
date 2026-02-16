-- ═══════════════════════════════════════════════════════════════════════════
-- RHINOMETRIC LICENSE SERVER - DATABASE SCHEMA v2.1.0
-- ═══════════════════════════════════════════════════════════════════════════

-- Main licenses table (already exists but ensure structure)
CREATE TABLE IF NOT EXISTS licenses (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    license_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Client metadata (for CRM)
    client_email VARCHAR(255),
    client_company VARCHAR(255),
    client_phone VARCHAR(50),
    client_country VARCHAR(100),
    client_city VARCHAR(100),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    servers_count INTEGER,
    services_count INTEGER,
    infrastructure_type VARCHAR(100),
    notes TEXT,
    
    -- Audit fields
    last_check TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- License activations audit table (NEW)
CREATE TABLE IF NOT EXISTS license_activations (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,
    license_key VARCHAR(255) NOT NULL,
    
    -- Activation details
    activated_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT,
    hardware_id VARCHAR(255),
    hostname VARCHAR(255),
    
    -- Download tracking
    download_allowed BOOLEAN DEFAULT true,
    download_url TEXT,
    download_completed BOOLEAN DEFAULT false,
    
    -- Status
    validation_status VARCHAR(50) DEFAULT 'success',  -- success, expired, invalid, revoked
    error_message TEXT,
    
    -- Metadata
    client_info JSONB,  -- Additional client information
    
    CONSTRAINT fk_license
        FOREIGN KEY(license_id) 
        REFERENCES licenses(id)
        ON DELETE CASCADE
);

-- Failed validation attempts (security)
CREATE TABLE IF NOT EXISTS license_validation_failures (
    id SERIAL PRIMARY KEY,
    license_key VARCHAR(255),
    attempted_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    reason VARCHAR(255),
    hardware_id VARCHAR(255),
    
    -- Security metrics
    is_suspicious BOOLEAN DEFAULT false,
    blocked BOOLEAN DEFAULT false
);

-- External APIs table (already exists)
CREATE TABLE IF NOT EXISTS external_apis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    endpoint TEXT NOT NULL,
    auth_type VARCHAR(50) DEFAULT 'none',
    auth_token TEXT,
    scrape_interval INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES FOR PERFORMANCE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_active ON licenses(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_licenses_email ON licenses(client_email);

CREATE INDEX IF NOT EXISTS idx_activations_license_id ON license_activations(license_id);
CREATE INDEX IF NOT EXISTS idx_activations_key ON license_activations(license_key);
CREATE INDEX IF NOT EXISTS idx_activations_date ON license_activations(activated_at DESC);
CREATE INDEX IF NOT EXISTS idx_activations_ip ON license_activations(ip_address);

CREATE INDEX IF NOT EXISTS idx_failures_key ON license_validation_failures(license_key);
CREATE INDEX IF NOT EXISTS idx_failures_ip ON license_validation_failures(ip_address);
CREATE INDEX IF NOT EXISTS idx_failures_date ON license_validation_failures(attempted_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS FOR ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════

-- Active licenses with activation count
CREATE OR REPLACE VIEW v_licenses_summary AS
SELECT 
    l.id,
    l.customer_name,
    l.license_key,
    l.client_email,
    l.client_company,
    l.created_at,
    l.expires_at,
    l.is_active,
    CASE 
        WHEN l.expires_at < NOW() THEN 'expired'
        WHEN l.expires_at < NOW() + INTERVAL '7 days' THEN 'expiring'
        WHEN NOT l.is_active THEN 'revoked'
        ELSE 'active'
    END as status,
    EXTRACT(DAY FROM (l.expires_at - NOW())) as days_remaining,
    COUNT(DISTINCT la.id) as activation_count,
    COUNT(DISTINCT la.ip_address) as unique_ips,
    COUNT(DISTINCT la.hardware_id) as unique_hardware,
    MAX(la.activated_at) as last_activation
FROM licenses l
LEFT JOIN license_activations la ON l.id = la.license_id
GROUP BY l.id, l.customer_name, l.license_key, l.client_email, l.client_company, 
         l.created_at, l.expires_at, l.is_active;

-- Security: Suspicious activation patterns
CREATE OR REPLACE VIEW v_suspicious_activations AS
SELECT 
    license_key,
    COUNT(DISTINCT ip_address) as distinct_ips,
    COUNT(DISTINCT hardware_id) as distinct_hardware,
    COUNT(*) as total_activations,
    MAX(activated_at) as last_activation,
    CASE 
        WHEN COUNT(DISTINCT ip_address) > 5 THEN 'Multiple IPs'
        WHEN COUNT(DISTINCT hardware_id) > 3 THEN 'Multiple Hardware'
        WHEN COUNT(*) > 10 THEN 'Excessive Activations'
        ELSE 'Normal'
    END as alert_reason
FROM license_activations
WHERE activated_at > NOW() - INTERVAL '7 days'
GROUP BY license_key
HAVING COUNT(DISTINCT ip_address) > 5 
    OR COUNT(DISTINCT hardware_id) > 3 
    OR COUNT(*) > 10;

-- ═══════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA FOR TESTING (OPTIONAL)
-- ═══════════════════════════════════════════════════════════════════════════

-- Uncomment for development/testing
/*
INSERT INTO licenses (customer_name, license_key, expires_at, client_email, client_company, is_active)
VALUES 
    ('Demo Client Trial', 'RHINO-TRIAL-2025-DEMO001', NOW() + INTERVAL '30 days', 'demo@example.com', 'Demo Corp', true),
    ('Enterprise Client', 'RHINO-ANNUAL-2025-ENT001', NOW() + INTERVAL '365 days', 'enterprise@example.com', 'Big Corp', true),
    ('Permanent Client', 'RHINO-PERM-2024-PERM001', NOW() + INTERVAL '100 years', 'permanent@example.com', 'Gov Agency', true)
ON CONFLICT (license_key) DO NOTHING;
*/

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS (adjust username as needed)
-- ═══════════════════════════════════════════════════════════════════════════

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rhinometric;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rhinometric;
