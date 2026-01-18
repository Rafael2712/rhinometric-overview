# RhinoMetric AI Anomaly Detection

Enterprise-grade machine learning-based anomaly detection service for observability metrics.

## Version: 2.2.0

## Features

- **Multiple ML Algorithms**: Isolation Forest, LOF, One-Class SVM, Statistical methods
- **Configurable Metrics**: YAML-based configuration for all metrics
- **Auto-Retraining**: Models automatically retrain with new data
- **RESTful API**: Complete FastAPI-based REST API
- **Prometheus Integration**: Query metrics and export service metrics
- **Alertmanager Integration**: Send alerts for detected anomalies
- **Model Persistence**: Save and load trained models
- **Background Detection**: Automated periodic anomaly checks
- **Production-Ready**: Health checks, logging, error handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   RhinoMetric AI Anomaly                     │
│                    Detection Service                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌─────────────────┐                 │
│  │   FastAPI    │◄────►│   Detector      │                 │
│  │   REST API   │      │    Engine       │                 │
│  └──────────────┘      └────────┬────────┘                 │
│                                  │                           │
│                                  ▼                           │
│                        ┌─────────────────┐                  │
│                        │ Model Ensemble  │                  │
│                        ├─────────────────┤                  │
│                        │ - IsolationFor. │                  │
│                        │ - LOF           │                  │
│                        │ - One-Class SVM │                  │
│                        │ - Statistical   │                  │
│                        └─────────────────┘                  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    External Integrations                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Prometheus │    │ Alertmanager │    │   Grafana    │   │
│  │  (Metrics) │    │   (Alerts)   │    │(Visualize)   │   │
│  └────────────┘    └──────────────┘    └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Configuration

Edit `config.yaml` to configure metrics, models, and integrations.

### 2. Run with Docker

```bash
docker build -t rhinometric-ai-anomaly:2.2.0 .
docker run -p 8085:8085 \
  -e PROMETHEUS_URL=http://prometheus:9090 \
  -e ALERTMANAGER_URL=http://alertmanager:9093 \
  -v $(pwd)/models:/app/models \
  rhinometric-ai-anomaly:2.2.0
```

### 3. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python -m app.main
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /status` - Service status and statistics

### Anomalies
- `GET /anomalies` - Get recent anomalies
- `GET /anomalies/summary` - Anomaly summary by metric

### Detection
- `POST /detect` - Trigger detection for all metrics
- `POST /detect/{metric_name}` - Detect anomalies for specific metric

### Configuration
- `GET /metrics/config` - Get metrics configuration
- `GET /metrics/config/{metric_name}` - Get specific metric config
- `POST /config/reload` - Reload configuration

### Models
- `GET /models` - Get model information
- `POST /models/save` - Save trained models

### Monitoring
- `GET /metrics` - Prometheus metrics export

## Configuration

### Metric Configuration Example

```yaml
metrics:
  - name: "cpu_usage"
    display_name: "CPU Usage"
    query: '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
    enabled: true
    priority: "high"
    models:
      - isolation_forest
      - lof
      - statistical
    thresholds:
      warning: 70
      critical: 90
    sensitivity: "medium"
```

### Model Configuration

```yaml
models:
  isolation_forest:
    enabled: true
    contamination: 0.1
    n_estimators: 100
  lof:
    enabled: true
    n_neighbors: 20
  statistical:
    enabled: true
    zscore_threshold: 3.0
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_URL` | Prometheus server URL | `http://prometheus:9090` |
| `ALERTMANAGER_URL` | Alertmanager URL | `http://alertmanager:9093` |
| `CHECK_INTERVAL_SECONDS` | Detection interval | `300` |
| `LOOKBACK_HOURS` | Hours of data to analyze | `24` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CONFIG_PATH` | Config file path | `/app/config.yaml` |

## Metrics Exported

The service exports the following Prometheus metrics:

- `rhinometric_anomaly_api_requests_total` - API request count
- `rhinometric_anomaly_detections_total` - Total anomalies detected
- `rhinometric_anomaly_detection_duration_seconds` - Detection duration
- `rhinometric_anomaly_active_count` - Active anomalies count
- `rhinometric_anomaly_models_trained` - Trained models status

## Development

### Running Tests

```bash
# Unit tests
pytest tests/test_models.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

## Integration with RhinoMetric

This service is part of the RhinoMetric v2.2.0 observability platform:

1. **Queries Prometheus** for metrics data
2. **Detects anomalies** using ML models
3. **Sends alerts** to Alertmanager
4. **Exports metrics** for Grafana dashboards

## Troubleshooting

### No data for metrics

Check Prometheus connection:
```bash
curl http://localhost:8085/status
```

Verify Prometheus is scraping targets:
```bash
curl http://prometheus:9090/api/v1/targets
```

### Models not training

Check data availability:
```bash
curl "http://localhost:8085/detect/cpu_usage"
```

Ensure metrics return sufficient data points (minimum 20 by default).

### High memory usage

Reduce model complexity in `config.yaml`:
- Decrease `n_estimators` for Isolation Forest
- Reduce `lookback_hours`
- Disable unused models

## License

Proprietary - RhinoMetric Enterprise Edition

## Support

For issues or questions, contact the RhinoMetric team.
