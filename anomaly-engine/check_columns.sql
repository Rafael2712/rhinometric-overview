-- Check external_services columns
SELECT column_name, data_type FROM information_schema.columns WHERE table_name='external_services' ORDER BY ordinal_position;

-- Check external_service_checks columns
SELECT column_name, data_type FROM information_schema.columns WHERE table_name='external_service_checks' ORDER BY ordinal_position;

-- Check incidents columns
SELECT column_name, data_type FROM information_schema.columns WHERE table_name='incidents' ORDER BY ordinal_position;
