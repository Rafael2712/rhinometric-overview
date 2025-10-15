const promClient = require('prom-client');

// Registro global de métricas
const register = new promClient.Registry();

// Métricas por defecto del sistema (CPU, memoria, etc.)
promClient.collectDefaultMetrics({ register });

// 1. CONTADOR: Requests totales por endpoint y método
const httpRequestsTotal = new promClient.Counter({
  name: 'rhinometric_http_requests_total',
  help: 'Total de requests HTTP por endpoint y método',
  labelNames: ['method', 'route', 'status_code', 'tenant_id']
});

// 2. HISTOGRAMA: Tiempo de respuesta por endpoint  
const httpRequestDuration = new promClient.Histogram({
  name: 'rhinometric_http_request_duration_seconds',
  help: 'Duración de requests HTTP en segundos',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
});

// 3. GAUGE: Usuarios activos por tenant
const activeUsers = new promClient.Gauge({
  name: 'rhinometric_active_users',
  help: 'Usuarios activos por tenant',
  labelNames: ['tenant_id']
});

// 4. CONTADOR: Intentos de autenticación
const authAttempts = new promClient.Counter({
  name: 'rhinometric_auth_attempts_total',
  help: 'Total de intentos de autenticación',
  labelNames: ['result', 'method'] // result: success/failure, method: jwt/password
});

// 5. HISTOGRAMA: Performance de queries de base de datos
const dbQueryDuration = new promClient.Histogram({
  name: 'rhinometric_db_query_duration_seconds',
  help: 'Duración de queries de base de datos',
  labelNames: ['operation', 'table'],
  buckets: [0.001, 0.01, 0.1, 0.5, 1, 2]
});

// 6. GAUGE: Conexiones activas de base de datos
const dbConnections = new promClient.Gauge({
  name: 'rhinometric_db_connections_active',
  help: 'Conexiones activas a la base de datos'
});

// 7. GAUGE: Información del sistema
const systemInfo = new promClient.Gauge({
  name: 'rhinometric_system_info',
  help: 'Información del sistema y versión',
  labelNames: ['version', 'node_version', 'environment']
});

// Registrar todas las métricas
register.registerMetric(httpRequestsTotal);
register.registerMetric(httpRequestDuration);
register.registerMetric(activeUsers);
register.registerMetric(authAttempts);
register.registerMetric(dbQueryDuration);
register.registerMetric(dbConnections);
register.registerMetric(systemInfo);

// Inicializar métricas del sistema
systemInfo.set({
  version: '1.0.0',
  node_version: process.version,
  environment: process.env.NODE_ENV || 'development'
}, 1);

module.exports = {
  register,
  httpRequestsTotal,
  httpRequestDuration,
  activeUsers,
  authAttempts,
  dbQueryDuration,
  dbConnections,
  systemInfo
};