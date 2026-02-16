-- ═══════════════════════════════════════════════════════════════════════════
--  RHINOMETRIC DATABASE INITIALIZATION - v2.1.0 ENTERPRISE
-- ═══════════════════════════════════════════════════════════════════════════
--
--  Creates database schema and sample data for Rhinometric Trial
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Create licenses table
CREATE TABLE IF NOT EXISTS licenses (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    license_key VARCHAR(512) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    max_users INTEGER DEFAULT 50,
    features JSONB DEFAULT '{"monitoring": true, "alerting": true, "traces": true, "logs": true}'::jsonb
);

-- Create index on license_key for fast lookups
CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_active ON licenses(is_active, expires_at);

-- Create external_apis table
CREATE TABLE IF NOT EXISTS external_apis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    endpoint VARCHAR(512) NOT NULL,
    auth_type VARCHAR(50) DEFAULT 'none',
    auth_token VARCHAR(512),
    scrape_interval INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_success TIMESTAMP,
    last_error TEXT,
    total_requests INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0
);

-- Create index for active APIs
CREATE INDEX IF NOT EXISTS idx_apis_active ON external_apis(is_active);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    user_email VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
--  SAMPLE DATA
-- ═══════════════════════════════════════════════════════════════════════════

-- Insert sample licenses
INSERT INTO licenses (customer_name, license_key, expires_at, max_users) VALUES
    ('Demo Customer', 'TRIAL-DEMO-2024-ABC123XYZ', NOW() + INTERVAL '180 days', 50),
    ('Enterprise Trial', 'ENT-TRIAL-2024-XYZ789ABC', NOW() + INTERVAL '30 days', 100),
    ('Development', 'DEV-LOCAL-2024-DEV000001', NOW() + INTERVAL '365 days', 10)
ON CONFLICT (license_key) DO NOTHING;

-- Insert pre-configured external APIs
INSERT INTO external_apis (name, endpoint, auth_type, scrape_interval) VALUES
    ('coindesk_btc', 'https://api.coindesk.com/v1/bpi/currentprice.json', 'none', 60),
    ('github_status', 'https://www.githubstatus.com/api/v2/status.json', 'none', 120),
    ('openweather', 'https://api.open-meteo.com/v1/forecast?latitude=40.4168&longitude=-3.7038&current=temperature_2m', 'none', 300),
    ('jsonplaceholder', 'https://jsonplaceholder.typicode.com/posts/1', 'none', 300)
ON CONFLICT (name) DO NOTHING;

-- Insert audit log sample
INSERT INTO audit_logs (action, entity_type, entity_id, user_email, details) VALUES
    ('database_initialized', 'system', NULL, 'system@rhinometric.local', '{"version": "2.1.0", "timestamp": "' || NOW() || '"}');

-- ═══════════════════════════════════════════════════════════════════════════
--  UTILITY FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- Function to check if license is valid
CREATE OR REPLACE FUNCTION is_license_valid(p_license_key VARCHAR) 
RETURNS BOOLEAN AS $$
DECLARE
    v_expires_at TIMESTAMP;
    v_is_active BOOLEAN;
BEGIN
    SELECT expires_at, is_active 
    INTO v_expires_at, v_is_active
    FROM licenses 
    WHERE license_key = p_license_key;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    RETURN v_is_active AND v_expires_at > NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to get active licenses count
CREATE OR REPLACE FUNCTION get_active_licenses_count() 
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM licenses WHERE is_active = true AND expires_at > NOW());
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
--  VIEWS FOR MONITORING
-- ═══════════════════════════════════════════════════════════════════════════

-- View for license status
CREATE OR REPLACE VIEW v_license_status AS
SELECT 
    id,
    customer_name,
    license_key,
    created_at,
    expires_at,
    is_active,
    CASE 
        WHEN expires_at < NOW() THEN 'expired'
        WHEN expires_at < NOW() + INTERVAL '7 days' THEN 'expiring_soon'
        ELSE 'active'
    END AS status,
    EXTRACT(DAY FROM expires_at - NOW()) AS days_remaining
FROM licenses
WHERE is_active = true;

-- View for API health
CREATE OR REPLACE VIEW v_api_health AS
SELECT 
    id,
    name,
    endpoint,
    is_active,
    last_success,
    last_error,
    total_requests,
    total_failures,
    CASE 
        WHEN total_requests > 0 THEN ROUND((total_failures::NUMERIC / total_requests) * 100, 2)
        ELSE 0
    END AS failure_rate_percent
FROM external_apis;

-- ═══════════════════════════════════════════════════════════════════════════
--  GRANT PERMISSIONS
-- ═══════════════════════════════════════════════════════════════════════════

-- Grant permissions to rhinometric user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rhinometric;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rhinometric;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rhinometric;

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE '✓ Rhinometric database initialized successfully';
    RAISE NOTICE '✓ Licenses: %', (SELECT COUNT(*) FROM licenses);
    RAISE NOTICE '✓ External APIs: %', (SELECT COUNT(*) FROM external_apis);
END $$;
