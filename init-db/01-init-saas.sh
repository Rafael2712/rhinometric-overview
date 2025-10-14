#!/bin/bash
set -e

# Create database for SaaS platform
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create schemas for multi-tenancy
    CREATE SCHEMA IF NOT EXISTS tenant_client1;
    CREATE SCHEMA IF NOT EXISTS tenant_client2;
    CREATE SCHEMA IF NOT EXISTS system_config;
    
    -- Create tenant management tables
    CREATE TABLE IF NOT EXISTS system_config.tenants (
        id SERIAL PRIMARY KEY,
        tenant_name VARCHAR(100) UNIQUE NOT NULL,
        schema_name VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT true,
        license_key VARCHAR(255),
        subscription_type VARCHAR(50) DEFAULT 'trial'
    );
    
    -- Insert demo tenants
    INSERT INTO system_config.tenants (tenant_name, schema_name, license_key, subscription_type) 
    VALUES 
        ('client1', 'tenant_client1', 'demo_license_client1', 'trial'),
        ('client2', 'tenant_client2', 'demo_license_client2', 'trial')
    ON CONFLICT (tenant_name) DO NOTHING;
    
    -- Create user management table
    CREATE TABLE IF NOT EXISTS system_config.tenant_users (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER REFERENCES system_config.tenants(id),
        username VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255),
        role VARCHAR(50) DEFAULT 'viewer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT true,
        UNIQUE(tenant_id, username)
    );
    
    -- Grant permissions
    GRANT ALL ON SCHEMA system_config TO $POSTGRES_USER;
    GRANT ALL ON ALL TABLES IN SCHEMA system_config TO $POSTGRES_USER;
    GRANT ALL ON SCHEMA tenant_client1 TO $POSTGRES_USER;
    GRANT ALL ON SCHEMA tenant_client2 TO $POSTGRES_USER;
EOSQL

echo "Multi-tenant database structure created successfully"