-- ============================================================================
-- Rhinometric Trial - PostgreSQL Database Schema Example
-- ============================================================================
-- This database is for YOUR APPLICATION DATA, not for Rhinometric internals
-- Rhinometric uses local storage (filesystem) for metrics, logs, and traces
-- ============================================================================

-- Database: rhinometric_trial
-- User: postgres
-- Password: trial_rhinometric_2024 (default, change in .env)

\c rhinometric_trial;

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Sample data
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('john_doe', 'john@example.com', '$2b$12$...', 'John Doe', 'admin'),
('jane_smith', 'jane@example.com', '$2b$12$...', 'Jane Smith', 'user'),
('bob_wilson', 'bob@example.com', '$2b$12$...', 'Bob Wilson', 'moderator')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- 2. SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- 3. EVENTS/AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address INET,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user_id ON audit_events(user_id);
CREATE INDEX idx_audit_event_type ON audit_events(event_type);
CREATE INDEX idx_audit_created_at ON audit_events(created_at DESC);
CREATE INDEX idx_audit_details ON audit_events USING GIN(details);

-- Sample events
INSERT INTO audit_events (user_id, event_type, event_action, details, severity) VALUES
(1, 'AUTH', 'LOGIN_SUCCESS', '{"method": "password"}', 'info'),
(2, 'API', 'GET_USERS', '{"endpoint": "/api/users"}', 'info'),
(1, 'AUTH', 'PASSWORD_CHANGE', '{}', 'warning')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 4. APPLICATION METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15,4) NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON app_metrics(metric_name);
CREATE INDEX idx_metrics_timestamp ON app_metrics(timestamp DESC);
CREATE INDEX idx_metrics_labels ON app_metrics USING GIN(labels);

-- ============================================================================
-- 5. OBSERVABILITY INTEGRATION EXAMPLE
-- ============================================================================
-- This view aggregates data that can be queried by your app to expose metrics
CREATE OR REPLACE VIEW metrics_summary AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_events,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE severity = 'error') as error_count,
    COUNT(*) FILTER (WHERE severity = 'warning') as warning_count
FROM audit_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- ============================================================================
-- 6. FUNCTIONS FOR OBSERVABILITY
-- ============================================================================

-- Function to log application events
CREATE OR REPLACE FUNCTION log_event(
    p_user_id INTEGER,
    p_event_type VARCHAR,
    p_event_action VARCHAR,
    p_details JSONB DEFAULT '{}'::JSONB
) RETURNS INTEGER AS $$
DECLARE
    event_id INTEGER;
BEGIN
    INSERT INTO audit_events (user_id, event_type, event_action, details)
    VALUES (p_user_id, p_event_type, p_event_action, p_details)
    RETURNING id INTO event_id;
    
    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions 
    WHERE expires_at < NOW() 
    OR (created_at < NOW() - INTERVAL '30 days')
    RETURNING COUNT(*) INTO deleted_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. EXAMPLE QUERIES FOR INTEGRATION
-- ============================================================================

-- Query 1: Active users in last hour
COMMENT ON VIEW metrics_summary IS 
'Example query: SELECT * FROM metrics_summary LIMIT 24;';

-- Query 2: User activity heatmap
CREATE OR REPLACE VIEW user_activity_heatmap AS
SELECT 
    user_id,
    users.username,
    DATE_TRUNC('day', audit_events.created_at) as day,
    COUNT(*) as event_count
FROM audit_events
JOIN users ON users.id = audit_events.user_id
WHERE audit_events.created_at > NOW() - INTERVAL '7 days'
GROUP BY user_id, users.username, DATE_TRUNC('day', audit_events.created_at)
ORDER BY day DESC, event_count DESC;

-- Query 3: Error rate per hour
CREATE OR REPLACE VIEW error_rate_hourly AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_events,
    COUNT(*) FILTER (WHERE severity IN ('error', 'critical')) as error_events,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE severity IN ('error', 'critical')) / NULLIF(COUNT(*), 0), 
        2
    ) as error_percentage
FROM audit_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- ============================================================================
-- 8. PERMISSIONS (Optional - for production)
-- ============================================================================

-- Create read-only user for monitoring
-- CREATE USER rhinometric_readonly WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE rhinometric_trial TO rhinometric_readonly;
-- GRANT USAGE ON SCHEMA public TO rhinometric_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO rhinometric_readonly;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO rhinometric_readonly;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================

/*
HOW TO USE THIS DATABASE:

1. CONNECT FROM YOUR APP:
   
   Python:
   import psycopg2
   conn = psycopg2.connect(
       host="localhost",
       database="rhinometric_trial",
       user="postgres",
       password="trial_rhinometric_2024"
   )

   Node.js:
   const { Pool } = require('pg');
   const pool = new Pool({
       host: 'localhost',
       database: 'rhinometric_trial',
       user: 'postgres',
       password: 'trial_rhinometric_2024'
   });

2. LOG EVENTS:
   SELECT log_event(1, 'AUTH', 'LOGIN_SUCCESS', '{"ip": "192.168.1.1"}'::JSONB);

3. QUERY METRICS:
   SELECT * FROM metrics_summary;
   SELECT * FROM error_rate_hourly;

4. EXPORT TO PROMETHEUS:
   Use postgres_exporter (already running on port 9187)
   Custom metrics: Add them to postgres_exporter queries

5. INTEGRATE WITH RHINOMETRIC:
   - Your app writes to PostgreSQL
   - postgres-exporter scrapes DB metrics → Prometheus
   - View in Grafana dashboards

IMPORTANT:
- Rhinometric does NOT use this DB for metrics/logs/traces
- This DB is for YOUR application data
- postgres-exporter monitors DB health and exposes it as Prometheus metrics
*/

-- ============================================================================
-- VERIFY INSTALLATION
-- ============================================================================
SELECT 'Database schema created successfully!' as status;
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';
SELECT COUNT(*) as view_count FROM information_schema.views WHERE table_schema = 'public';
