const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { register, Counter, Histogram } = require('prom-client');

const app = express();
const PORT = process.env.PORT || 8001;
const GRAFANA_URL = process.env.GRAFANA_URL || 'http://localhost:3000';
const GRAFANA_USER = process.env.GRAFANA_USER || 'admin';
const GRAFANA_PASSWORD = process.env.GRAFANA_PASSWORD || 'admin';

// Metrics
const requestCounter = new Counter({
  name: 'dashboard_builder_requests_total',
  help: 'Total requests to Dashboard Builder API',
  labelNames: ['method', 'route', 'status']
});

const requestDuration = new Histogram({
  name: 'dashboard_builder_request_duration_seconds',
  help: 'Request duration',
  labelNames: ['method', 'route']
});

app.use(cors());
app.use(express.json());

// Metrics middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    requestCounter.inc({ method: req.method, route: req.path, status: res.statusCode });
    requestDuration.observe({ method: req.method, route: req.path }, duration);
  });
  next();
});

// Grafana API client
const grafana = axios.create({
  baseURL: GRAFANA_URL,
  auth: { username: GRAFANA_USER, password: GRAFANA_PASSWORD },
  headers: { 'Content-Type': 'application/json' }
});

// Dashboard templates
const templates = {
  'ai-anomaly': {
    title: 'AI Anomaly Detection',
    tags: ['ai', 'anomaly', 'rhinometric'],
    panels: [
      {
        id: 1, gridPos: { h: 4, w: 6, x: 0, y: 0 }, type: 'stat',
        title: 'Anomalías Detectadas (24h)',
        targets: [{ expr: 'increase(rhinometric_anomaly_detections_total[24h])', datasource: { uid: 'prometheus' } }]
      }
    ]
  },
  'system-overview': {
    title: 'System Overview',
    tags: ['system', 'infrastructure'],
    panels: [
      {
        id: 1, gridPos: { h: 6, w: 12, x: 0, y: 0 }, type: 'graph',
        title: 'CPU Usage',
        targets: [{ expr: '100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', datasource: { uid: 'prometheus' } }]
      }
    ]
  },
  'app-performance': {
    title: 'App Performance',
    tags: ['app', 'performance'],
    panels: [
      {
        id: 1, gridPos: { h: 4, w: 6, x: 0, y: 0 }, type: 'stat',
        title: 'Requests/sec',
        targets: [{ expr: 'sum(rate(http_requests_total[5m]))', datasource: { uid: 'prometheus' } }]
      }
    ]
  }
};

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'dashboard-builder' });
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.get('/templates', (req, res) => {
  const list = Object.keys(templates).map(key => ({
    id: key,
    title: templates[key].title,
    tags: templates[key].tags
  }));
  res.json({ templates: list });
});

app.post('/create', async (req, res) => {
  try {
    const { template, title, folder } = req.body;
    
    if (!template || !templates[template]) {
      return res.status(400).json({ error: 'Invalid template' });
    }

    const dashboard = {
      dashboard: {
        ...templates[template],
        title: title || templates[template].title,
        uid: null,
        refresh: '30s',
        schemaVersion: 30,
        version: 1
      },
      folderUid: folder || '',
      overwrite: false
    };

    const response = await grafana.post('/api/dashboards/db', dashboard);
    
    res.json({
      success: true,
      url: `${GRAFANA_URL}${response.data.url}`,
      uid: response.data.uid
    });
  } catch (error) {
    console.error('Error creating dashboard:', error.response?.data || error.message);
    res.status(500).json({
      error: 'Failed to create dashboard',
      details: error.response?.data?.message || error.message
    });
  }
});

app.listen(PORT, () => {
  console.log(`Dashboard Builder API running on :${PORT}`);
  console.log(`Grafana: ${GRAFANA_URL}`);
});
