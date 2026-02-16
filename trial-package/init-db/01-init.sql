-- Inicialización de base de datos PostgreSQL para Rhinometric Trial

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear tabla de licencias (si no se usa SQLite)
CREATE TABLE IF NOT EXISTS licenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_name VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    license_type VARCHAR(50) NOT NULL,
    hardware_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_check TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_licenses_client_id ON licenses(client_id);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses(status);
CREATE INDEX IF NOT EXISTS idx_licenses_expires_at ON licenses(expires_at);

-- Insertar licencia demo (opcional)
INSERT INTO licenses (client_name, client_id, license_type, hardware_id, expires_at, status)
VALUES (
    'Trial Demo',
    'demo-client-' || uuid_generate_v4()::text,
    'trial',
    'demo-hardware-id',
    CURRENT_TIMESTAMP + INTERVAL '180 days',
    'active'
) ON CONFLICT DO NOTHING;

-- Comentario
COMMENT ON TABLE licenses IS 'Tabla de licencias de clientes - Rhinometric Trial';
