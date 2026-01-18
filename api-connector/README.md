# RHINOMETRIC v2.4.0 - API Connector

Visual datasource connector for RHINOMETRIC observability platform.

## Features

- ✅ **Visual Connection Testing**: Test connections in real-time
- ✅ **Pre-configured Templates**: AWS, Azure, PostgreSQL, Redis, Prometheus
- ✅ **RESTful API**: FastAPI backend with async support
- ✅ **Grafana Integration**: Compatible with Grafana datasources

## Supported Datasources

### Databases
- **PostgreSQL**: Full support with SSL
- **Redis**: Cache, queue, pub/sub

### Cloud Providers
- **AWS CloudWatch**: Metrics and logs
- **Azure Monitor**: Metrics and logs

### Monitoring
- **Prometheus**: Metrics server
- **Loki**: Log aggregation (coming soon)
- **Tempo**: Distributed tracing (coming soon)

## Installation

```bash
cd api-connector
pip install -r requirements.txt
```

## Usage

### Start API Server

```bash
python app.py
```

Server runs on `http://localhost:8000`

### API Endpoints

**Get available templates**:
```bash
curl http://localhost:8000/api/templates
```

**Test PostgreSQL connection**:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "postgres",
    "password": "secret",
    "ssl": false
  }'
```

**Test Redis connection**:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "redis",
    "host": "localhost",
    "port": 6379,
    "database": 0,
    "password": ""
  }'
```

**Test AWS CloudWatch**:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "aws-cloudwatch",
    "region": "us-east-1",
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY"
  }'
```

## Development

### Project Structure

```
api-connector/
├── app.py                 # Main FastAPI application
├── connectors/            # Datasource connectors
│   ├── __init__.py
│   ├── postgresql.py      # PostgreSQL connector
│   ├── redis_connector.py # Redis connector
│   ├── prometheus_connector.py
│   ├── aws.py             # AWS CloudWatch
│   └── azure.py           # Azure Monitor
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Adding New Connectors

1. Create new connector in `connectors/` directory
2. Implement `test_connection()` method
3. Add to `connectors/__init__.py`
4. Update templates in `app.py`
5. Add integration tests

## Testing

```bash
pytest tests/
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t rhinometric-api-connector .
docker run -p 8000:8000 rhinometric-api-connector
```

## Integration with Grafana

The API can be consumed by a Grafana plugin to provide visual datasource configuration.

## License

Proprietary - RHINOMETRIC v2.4.0
