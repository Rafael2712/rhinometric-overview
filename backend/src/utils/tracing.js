// Instrumentación simple para Tempo
const os = require('os');

class SimpleTracing {
  constructor() {
    this.serviceName = process.env.SERVICE_NAME || 'rhinometric-api';
    this.tempoUrl = process.env.TEMPO_URL || 'http://tempo:3200';
    this.traces = [];
  }

  startTrace(operation) {
    const trace = {
      traceId: this.generateTraceId(),
      spanId: this.generateSpanId(),
      operation: operation,
      timestamp: Date.now(),
      tags: {
        'service.name': this.serviceName,
        'host.name': os.hostname(),
        'process.pid': process.pid
      },
      logs: []
    };
    
    return {
      traceId: trace.traceId,
      spanId: trace.spanId,
      finish: (tags = {}) => {
        trace.duration = Date.now() - trace.timestamp;
        trace.tags = { ...trace.tags, ...tags };
        this.sendTrace(trace);
      },
      log: (message, data = {}) => {
        trace.logs.push({
          timestamp: Date.now(),
          message,
          data
        });
      }
    };
  }

  generateId(length = 16) {
    // Generar IDs hex compatibles con OpenTelemetry
    const chars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }
  
  generateTraceId() {
    return this.generateId(32); // 32 chars para trace ID
  }
  
  generateSpanId() {
    return this.generateId(16); // 16 chars para span ID
  }

  async sendTrace(trace) {
    try {
      // Convertir a formato Jaeger compatible con Tempo
      const jaegerTrace = {
        traceID: trace.traceId,
        spans: [{
          traceID: trace.traceId,
          spanID: trace.spanId,
          operationName: trace.operation,
          startTime: trace.timestamp * 1000, // microseconds
          duration: (trace.duration || 0) * 1000,
          tags: Object.entries(trace.tags).map(([key, value]) => ({
            key,
            type: 'string',
            value: String(value)
          })),
          logs: trace.logs.map(log => ({
            timestamp: log.timestamp * 1000,
            fields: [
              { key: 'event', value: log.message },
              ...Object.entries(log.data).map(([key, value]) => ({
                key,
                value: String(value)
              }))
            ]
          })),
          process: {
            serviceName: this.serviceName,
            tags: [
              { key: 'hostname', value: os.hostname() },
              { key: 'pid', value: String(process.pid) }
            ]
          }
        }]
      };

      console.log(`[TRACE] ${trace.operation} - ${trace.duration}ms`);
      
      // Enviar a Tempo vía Jaeger HTTP
      const http = require('http');
      
      const postData = JSON.stringify({
        data: [jaegerTrace]
      });

      const options = {
        hostname: 'tempo',
        port: 14268,
        path: '/api/traces',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      };

      const req = http.request(options, (res) => {
        console.log(`[TRACE] Sent to Tempo via Jaeger: ${res.statusCode}`);
      });

      req.on('error', (e) => {
        console.error(`[TRACE] Error sending to Tempo: ${e.message}`);
      });

      req.write(postData);
      req.end();
      
    } catch (error) {
      console.error('Error enviando trace:', error);
    }
  }
}

module.exports = new SimpleTracing();