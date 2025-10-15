const responseTime = require('response-time');
const { httpRequestsTotal, httpRequestDuration } = require('../utils/metrics');

// Middleware para capturar métricas de cada request
const metricsMiddleware = responseTime((req, res, time) => {
  const route = req.route ? req.route.path : req.path;
  const method = req.method;
  const statusCode = res.statusCode;
  const tenantId = req.user ? req.user.tenant_id : 'anonymous';
  
  // Incrementar contador de requests
  httpRequestsTotal.inc({
    method,
    route,
    status_code: statusCode,
    tenant_id: tenantId
  });
  
  // Registrar tiempo de respuesta (convertir ms a segundos)
  httpRequestDuration.observe({
    method,
    route,
    status_code: statusCode
  }, time / 1000);
});

module.exports = metricsMiddleware;