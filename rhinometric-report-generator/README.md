# RhinoMetric Report Generator v2.2.0

## 🎯 Enterprise PDF/HTML Report Generation Service

Professional report generation system with PDF/HTML export, email delivery, and automated scheduling.

## Features

- **📄 PDF Reports**: Professional PDF generation with ReportLab
- **🌐 HTML Reports**: Responsive HTML reports with modern design
- **📧 Email Delivery**: SMTP-based email with attachments
- **📊 Data Aggregation**: Pulls data from Prometheus, AI Anomaly API, Grafana
- **⏰ Scheduled Reports**: Cron-based automated report generation
- **📈 Multiple Report Types**: Executive, Technical, Anomaly Analysis
- **🔒 Secure**: Environment variable configuration, no hardcoded credentials
- **📡 RESTful API**: Complete API for report management
- **📊 Prometheus Metrics**: Built-in monitoring and observability

## Architecture

```
rhinometric-report-generator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── data_aggregator.py   # Data collection from sources
│   ├── pdf_generator.py     # PDF report generation
│   └── email_service.py     # Email delivery service
├── templates/
│   └── email_report.html    # Email template
├── config.yaml              # Service configuration
├── Dockerfile               # Container image
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Quick Start

### Using Docker Compose

```yaml
services:
  rhinometric-report-generator:
    build: ./rhinometric-report-generator
    container_name: rhinometric-report-generator
    ports:
      - "8086:8086"
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
      - GRAFANA_URL=http://grafana:3000
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - SMTP_FROM=rhinometric@example.com
    volumes:
      - ./reports:/app/reports
      - ./rhinometric-report-generator/config.yaml:/app/config.yaml
    networks:
      - rhinometric
    depends_on:
      - prometheus
      - grafana
      - rhinometric-ai-anomaly
```

### Standalone

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROMETHEUS_URL=http://localhost:9090
export GRAFANA_URL=http://localhost:3000
export SMTP_HOST=smtp.gmail.com
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password

# Run service
python -m app.main
```

## Configuration

Edit `config.yaml` to configure reports:

```yaml
reports:
  - name: executive_daily
    display_name: "Executive Daily Report"
    enabled: true
    type: executive
    format:
      - pdf
      - html
    recipients:
      - admin@example.com
    schedule:
      enabled: true
      cron: "0 8 * * *"  # Daily at 8 AM
    lookback_hours: 24
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8086` | Server port |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus URL |
| `GRAFANA_URL` | `http://grafana:3000` | Grafana URL |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password |
| `SMTP_FROM` | `rhinometric@example.com` | From email address |

## API Endpoints

### Generate Report

```bash
POST /api/v1/reports/generate
Content-Type: application/json

{
  "report_type": "executive",
  "period_hours": 24,
  "formats": ["pdf", "html"],
  "recipients": ["admin@example.com"],
  "include_charts": true,
  "include_anomalies": true,
  "include_metrics": true
}
```

**Response:**

```json
{
  "report_id": "executive_20240101_080000",
  "report_type": "executive",
  "status": "completed",
  "generated_at": "2024-01-01T08:00:00",
  "formats": ["pdf", "html"],
  "files": {
    "pdf": "/app/reports/executive_20240101_080000.pdf",
    "html": "/app/reports/executive_20240101_080000.html"
  },
  "email_sent": true,
  "recipients": ["admin@example.com"]
}
```

### List Reports

```bash
GET /api/v1/reports/list?limit=50&report_type=executive
```

### Download Report

```bash
GET /api/v1/reports/download/{filename}
```

### Delete Report

```bash
DELETE /api/v1/reports/{filename}
```

### Health Check

```bash
GET /health
```

### Prometheus Metrics

```bash
GET /metrics
```

## Report Types

### Executive Report
- High-level system overview
- Health score and status
- Key metrics summary
- Anomaly and alert counts
- Executive insights

### Technical Report
- Detailed system metrics
- Application performance
- Resource utilization
- Network traffic analysis
- Database metrics

### Anomaly Analysis Report
- AI-detected anomalies
- Confidence scores
- Severity breakdown
- Time series analysis
- Model performance

## Email Configuration

### Gmail Setup

1. Enable 2-Factor Authentication
2. Generate App Password
3. Use credentials:

```bash
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
```

### SendGrid Setup

```bash
export SMTP_HOST=smtp.sendgrid.net
export SMTP_PORT=587
export SMTP_USERNAME=apikey
export SMTP_PASSWORD=your-sendgrid-api-key
```

## Monitoring

Prometheus metrics exposed at `/metrics`:

- `rhinometric_reports_generated_total` - Total reports generated
- `rhinometric_reports_sent_total` - Total reports sent via email
- `rhinometric_report_generation_seconds` - Report generation duration
- `rhinometric_active_reports` - Currently generating reports

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-asyncio

# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload --port 8086

# Format code
black app/

# Lint
flake8 app/
```

## Troubleshooting

### PDF Generation Issues

If WeasyPrint fails, install system dependencies:

```bash
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0
```

### Email Delivery Issues

1. Check SMTP credentials
2. Verify firewall allows port 587
3. Test SMTP connection:

```python
python -c "import aiosmtplib; print('OK')"
```

### Data Aggregation Issues

1. Verify Prometheus is accessible
2. Check AI Anomaly API health
3. Review logs: `docker logs rhinometric-report-generator`

## License

© 2024 RhinoMetric. Enterprise Edition.

## Support

- Documentation: `/docs` endpoint (FastAPI Swagger UI)
- Health: `GET /health`
- Metrics: `GET /metrics`
