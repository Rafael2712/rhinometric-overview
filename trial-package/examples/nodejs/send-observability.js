const { trace, metrics } = require('@opentelemetry/api');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const axios = require('axios');
const prom = require('prom-client');

// =============================================================================
// CONFIGURATION
// =============================================================================
const RHINOMETRIC_HOST = process.env.RHINOMETRIC_HOST || 'localhost';
const SERVICE_NAME = 'demo-nodejs-app';

const config = {
  prometheus: { port: 9090 },
  loki: { port: 3100 },
  tempo: { grpc: 4317, http: 4318 }
};

// =============================================================================
// 1. METRICS - Prometheus
// =============================================================================
const register = new prom.Registry();

const httpRequestsTotal = new prom.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'endpoint', 'status'],
  registers: [register]
});

const activeConnections = new prom.Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [register]
});

const requestDuration = new prom.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
  registers: [register]
});

async function sendMetrics() {
  console.log(`\n📊 Sending metrics to Prometheus (${RHINOMETRIC_HOST}:${config.prometheus.port})`);
  
  const methods = ['GET', 'POST', 'PUT', 'DELETE'];
  const endpoints = ['/api/users', '/api/products', '/api/orders'];
  const statuses = [200, 201, 400, 404, 500];
  
  for (let i = 0; i < 20; i++) {
    const method = methods[Math.floor(Math.random() * methods.length)];
    const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    
    httpRequestsTotal.inc({ method, endpoint, status: status.toString() });
    activeConnections.set(Math.floor(Math.random() * 100) + 50);
    requestDuration.observe(Math.random() * 2);
    
    console.log(`✅ Metric sent: ${method} ${endpoint} ${status}`);
    await new Promise(resolve => setTimeout(resolve, 300));
  }
  
  console.log('✅ All metrics recorded');
}

// =============================================================================
// 2. LOGS - Loki
// =============================================================================
async function sendLogs() {
  console.log(`\n📝 Sending logs to Loki (${RHINOMETRIC_HOST}:${config.loki.port})`);
  
  const lokiUrl = `http://${RHINOMETRIC_HOST}:${config.loki.port}/loki/api/v1/push`;
  const levels = ['info', 'warn', 'error', 'debug'];
  const messages = [
    'Request processed successfully',
    'Database connection established',
    'Cache invalidated',
    'User authentication completed',
    'Background job executed'
  ];
  
  for (let i = 0; i < 15; i++) {
    const level = levels[Math.floor(Math.random() * levels.length)];
    const message = messages[Math.floor(Math.random() * messages.length)];
    const timestampNs = (Date.now() * 1e6).toString();
    
    const logEntry = {
      streams: [{
        stream: {
          service_name: SERVICE_NAME,
          level: level,
          environment: 'trial'
        },
        values: [
          [timestampNs, `[${level.toUpperCase()}] ${message} - req_id=${i}`]
        ]
      }]
    };
    
    try {
      const response = await axios.post(lokiUrl, logEntry, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.status === 204) {
        console.log(`✅ Log sent: [${level.toUpperCase()}] ${message}`);
      } else {
        console.log(`⚠️ Unexpected status: ${response.status}`);
      }
    } catch (error) {
      console.error(`⚠️ Error sending log:`, error.message);
    }
    
    await new Promise(resolve => setTimeout(resolve, 200));
  }
}

// =============================================================================
// 3. TRACES - Tempo (OpenTelemetry)
// =============================================================================
async function sendTraces() {
  console.log(`\n🔍 Sending traces to Tempo (${RHINOMETRIC_HOST}:${config.tempo.grpc})`);
  
  // Configure OpenTelemetry
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: SERVICE_NAME,
    'environment': 'trial'
  });
  
  const provider = new NodeTracerProvider({ resource });
  const exporter = new OTLPTraceExporter({
    url: `${RHINOMETRIC_HOST}:${config.tempo.grpc}`,
  });
  
  provider.addSpanProcessor(new BatchSpanProcessor(exporter));
  provider.register();
  
  const tracer = trace.getTracer('demo-tracer');
  
  // Generate sample traces
  for (let i = 0; i < 10; i++) {
    const parentSpan = tracer.startSpan('http_request');
    parentSpan.setAttribute('http.method', 'GET');
    parentSpan.setAttribute('http.url', `/api/resource/${i}`);
    parentSpan.setAttribute('http.status_code', 200);
    
    // Simulate async operations
    await new Promise(resolve => {
      const dbSpan = tracer.startSpan('database_query', { parent: parentSpan });
      setTimeout(() => {
        dbSpan.end();
        
        const cacheSpan = tracer.startSpan('cache_check', { parent: parentSpan });
        setTimeout(() => {
          cacheSpan.end();
          parentSpan.end();
          resolve();
        }, Math.random() * 50);
      }, Math.random() * 100);
    });
    
    console.log(`✅ Trace ${i + 1}/10 sent`);
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Force flush
  await provider.forceFlush();
  console.log('✅ All traces flushed to Tempo');
}

// =============================================================================
// MAIN
// =============================================================================
async function main() {
  console.log('='.repeat(70));
  console.log('🎯 Rhinometric Trial - Node.js Observability Demo');
  console.log('='.repeat(70));
  console.log(`Service: ${SERVICE_NAME}`);
  console.log(`Target: ${RHINOMETRIC_HOST}`);
  console.log('='.repeat(70));
  
  try {
    // 1. Send Metrics
    await sendMetrics();
    
    // 2. Send Logs
    await sendLogs();
    
    // 3. Send Traces
    await sendTraces();
    
    console.log('\n' + '='.repeat(70));
    console.log('✅ ALL DATA SENT SUCCESSFULLY');
    console.log('='.repeat(70));
    console.log('\n📊 View in Grafana:');
    console.log(`   → Dashboards: http://${RHINOMETRIC_HOST}:3000/dashboards`);
    console.log(`   → Explore Logs: http://${RHINOMETRIC_HOST}:3000/explore (Loki)`);
    console.log(`   → Explore Traces: http://${RHINOMETRIC_HOST}:3000/explore (Tempo)`);
    console.log('\n🔐 Login: admin / admin_secure_2024');
    console.log('='.repeat(70));
    
    process.exit(0);
  } catch (error) {
    console.error('\n\n❌ Error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
