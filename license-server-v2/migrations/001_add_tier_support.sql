-- ═══════════════════════════════════════════════════════════════════════════
-- RHINOMETRIC LICENSE SERVER - SCHEMA UPDATE FOR COMMERCIAL TIERS
-- Version: 2.5.0
-- Date: December 10, 2025
-- Purpose: Add tier support (demo_cloud, trial, annual_standard)
-- ═══════════════════════════════════════════════════════════════════════════

-- Add new columns to licenses table for tier-based licensing
ALTER TABLE licenses
ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'trial',
ADD COLUMN IF NOT EXISTS max_hosts INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS license_status VARCHAR(50) DEFAULT 'not_activated';

-- Create enum for tiers (PostgreSQL compatible)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'license_tier') THEN
        CREATE TYPE license_tier AS ENUM ('demo_cloud', 'trial', 'annual_standard', 'enterprise');
    END IF;
END$$;

-- Create enum for license status
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'license_status_enum') THEN
        CREATE TYPE license_status_enum AS ENUM ('not_activated', 'active', 'expired', 'revoked', 'over_limit');
    END IF;
END$$;

-- Add constraint comments for documentation
COMMENT ON COLUMN licenses.tier IS 'License tier: demo_cloud (4h), trial (14d/5 hosts), annual_standard (1y/20 hosts)';
COMMENT ON COLUMN licenses.max_hosts IS 'Maximum number of hosts allowed for this license';
COMMENT ON COLUMN licenses.activated_at IS 'Timestamp when license was first activated/validated';
COMMENT ON COLUMN licenses.license_status IS 'Current status: not_activated, active, expired, revoked, over_limit';

-- Update existing licenses to have tier and max_hosts based on license_key pattern
UPDATE licenses 
SET tier = 'trial', max_hosts = 5, license_status = 'active'
WHERE license_key LIKE '%TRIAL%' AND tier IS NULL;

UPDATE licenses 
SET tier = 'annual_standard', max_hosts = 20, license_status = 'active'
WHERE license_key LIKE '%ANNUAL%' AND tier IS NULL;

UPDATE licenses 
SET tier = 'demo_cloud', max_hosts = 20, license_status = 'active'
WHERE license_key LIKE '%DEMO%' AND tier IS NULL;

-- Create index for efficient tier-based queries
CREATE INDEX IF NOT EXISTS idx_licenses_tier ON licenses(tier);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses(license_status);
CREATE INDEX IF NOT EXISTS idx_licenses_activated ON licenses(activated_at);

-- Create a view for license summary with computed fields
CREATE OR REPLACE VIEW v_license_summary AS
SELECT 
    l.id,
    l.customer_name,
    l.license_key,
    l.tier,
    l.max_hosts,
    l.created_at AS issued_at,
    l.activated_at,
    l.expires_at,
    l.license_status AS status,
    l.client_email AS organization_email,
    l.client_company AS organization,
    
    -- Computed fields
    CASE 
        WHEN l.expires_at IS NULL THEN NULL
        WHEN l.expires_at > NOW() THEN EXTRACT(DAY FROM l.expires_at - NOW())::INTEGER
        ELSE 0
    END AS days_remaining,
    
    CASE
        WHEN l.license_status = 'revoked' THEN 'revoked'
        WHEN l.activated_at IS NULL THEN 'not_activated'
        WHEN l.expires_at IS NOT NULL AND l.expires_at < NOW() THEN 'expired'
        WHEN l.is_active = false THEN 'inactive'
        ELSE 'active'
    END AS computed_status,
    
    -- Activation count
    (SELECT COUNT(*) FROM license_activations WHERE license_id = l.id) AS activation_count,
    
    -- Last activation
    (SELECT MAX(activated_at) FROM license_activations WHERE license_id = l.id) AS last_activation
    
FROM licenses l;

COMMENT ON VIEW v_license_summary IS 'Comprehensive view of licenses with computed status and activation info';

-- Create function to auto-expire licenses
CREATE OR REPLACE FUNCTION update_expired_licenses()
RETURNS void AS $$
BEGIN
    UPDATE licenses
    SET license_status = 'expired'
    WHERE expires_at < NOW()
      AND license_status = 'active';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_expired_licenses IS 'Updates licenses status to expired when past expiration date';

-- ═══════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA FOR TESTING (Optional - uncomment to use)
-- ═══════════════════════════════════════════════════════════════════════════

/*
-- Demo Cloud License (4 hours)
INSERT INTO licenses (
    customer_name, license_key, tier, max_hosts, 
    expires_at, license_status, client_email, client_company
) VALUES (
    'Demo User',
    'RHINO-DEMO-CLOUD-2025-ABCD1234EFGH',
    'demo_cloud',
    20,
    NOW() + INTERVAL '4 hours',
    'not_activated',
    'demo@example.com',
    'Demo Company'
) ON CONFLICT (license_key) DO NOTHING;

-- Trial License (14 days, 5 hosts)
INSERT INTO licenses (
    customer_name, license_key, tier, max_hosts,
    expires_at, license_status, client_email, client_company
) VALUES (
    'Trial Customer',
    'RHINO-TRIAL-2025-XYZ9876QWER',
    'trial',
    5,
    NOW() + INTERVAL '14 days',
    'not_activated',
    'trial@customer.com',
    'Trial Corp'
) ON CONFLICT (license_key) DO NOTHING;

-- Annual Standard License (1 year, 20 hosts)
INSERT INTO licenses (
    customer_name, license_key, tier, max_hosts,
    expires_at, license_status, client_email, client_company
) VALUES (
    'Enterprise Customer',
    'RHINO-ANNUAL-2025-MNOP5432LIJK',
    'annual_standard',
    20,
    NOW() + INTERVAL '1 year',
    'not_activated',
    'admin@enterprise.com',
    'Enterprise Inc'
) ON CONFLICT (license_key) DO NOTHING;
*/

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Check schema changes
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'licenses'
  AND column_name IN ('tier', 'max_hosts', 'activated_at', 'license_status')
ORDER BY ordinal_position;

-- Check view
SELECT * FROM v_license_summary LIMIT 5;

COMMIT;
