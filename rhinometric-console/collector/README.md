# Rhinometric Collector v1

Production-ready telemetry agent for Rhinometric Console.

## Architecture

```
collector/
├── main.py           # Entry point — main loop, signal handling
├── config.py         # Dual config: env vars + optional YAML
├── sender.py         # HTTP client with retry/backoff
├── metrics.py        # Real system metrics via psutil
├── logs.py           # Captures collector's own log output
├── traces.py         # Real traces with measured durations
└── utils.py          # ID generation, time helpers, logging setup
```

### Data Flow

```
┌──────────┐  collect   ┌──────────┐  POST /api/telemetry/*  ┌─────────────────┐
│  psutil  │ ──────────▶│  sender  │ ────────────────────────▶│  Rhinometric    │
│  logs    │            │  (retry) │                          │  Backend        │
│  traces  │            └──────────┘                          └─────────────────┘
└──────────┘
```

Each cycle:
1. **Metrics** — CPU %, memory %, disk %, process uptime (via psutil)
2. **Logs** — Collector's own buffered log records (real events)
3. **Traces** — Parent span for the cycle + child spans per signal send

## Configuration

### Environment Variables (recommended for Docker)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RHYNO_API_URL` | Yes | — | Rhinometric API base URL |
| `RHYNO_SERVICE_KEY` | Yes | — | Service key from Rhinometric |
| `RHYNO_TELEMETRY_TOKEN` | Yes | — | Telemetry token |
| `COLLECT_INTERVAL` | No | `15` | Seconds between cycles |
| `ENABLE_METRICS` | No | `true` | Collect system metrics |
| `ENABLE_LOGS` | No | `true` | Capture agent logs |
| `ENABLE_TRACES` | No | `true` | Generate traces |
| `RHYNO_ENVIRONMENT` | No | `production` | Environment tag |

### YAML (optional)

Place `config.yaml` next to `main.py` or set `RHYNO_CONFIG_FILE`.
Environment variables always override YAML values.

## Running

### Docker (recommended)

```bash
# Build
docker build -t rhinometric-collector .

# Run with env file
docker run --rm --env-file .env rhinometric-collector

# Run on Rhinometric network (for internal URLs)
docker run --rm \
  --env-file .env \
  --network rhinometric_rhinometric_network \
  rhinometric-collector
```

### Python (direct)

```bash
pip install requests psutil pyyaml
export RHYNO_API_URL=http://localhost/api
export RHYNO_SERVICE_KEY=my-key
export RHYNO_TELEMETRY_TOKEN=rtk_...
python main.py
```

## Signals

The collector shuts down cleanly on SIGINT (Ctrl+C) or SIGTERM.
