# Rhinometric Collector v1.1

A lightweight telemetry agent that collects system metrics, application logs, and distributed traces from your environment and sends them to the Rhinometric Console.

## What It Does

The collector runs as a background process (typically in Docker) alongside your services. Each cycle it:

1. **Metrics** — Collects CPU, memory, disk, and network stats from the host via `psutil`
2. **Logs** — Captures the collector's own operational log output as structured entries
3. **Traces** — Generates real distributed traces measuring each collection cycle's duration

All data is sent to your Rhinometric Console instance via authenticated HTTP POST, where it feeds the Log Explorer, Traces view, AI Anomaly detection, SLO tracking, and AI Insights.

## Prerequisites

- Docker (recommended) or Python 3.10+
- A Rhinometric Console instance (the API URL)
- A service configured with **Telemetry Enabled** mode in Rhinometric Console
- The service's **Service Key** and **Telemetry Token** (found in Services > Telemetry Setup)

## Quick Start (Docker)

```bash
# 1. Build the image
docker build -t rhinometric-collector ./collector

# 2. Create your .env file
cp collector/.env.example collector/.env
# Edit .env with your actual values

# 3. Run
docker run -d --name rhyno-collector \
  --env-file collector/.env \
  --restart unless-stopped \
  rhinometric-collector
```

If the Rhinometric Console runs on the same Docker host:

```bash
docker run -d --name rhyno-collector \
  --env-file collector/.env \
  --network rhinometric_rhinometric_network \
  --restart unless-stopped \
  rhinometric-collector
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `RHYNO_API_URL` | **Yes** | — | Rhinometric API base URL (e.g. `http://rhinometric-nginx/api`) |
| `RHYNO_SERVICE_KEY` | **Yes** | — | Service key from Rhinometric Console |
| `RHYNO_TELEMETRY_TOKEN` | **Yes** | — | Telemetry token from Rhinometric Console |
| `COLLECT_INTERVAL` | No | `15` | Seconds between collection cycles (min: 5) |
| `ENABLE_METRICS` | No | `true` | Collect system metrics (CPU, memory, disk, network) |
| `ENABLE_LOGS` | No | `true` | Capture and send collector log entries |
| `ENABLE_TRACES` | No | `true` | Generate distributed traces |
| `LOG_LEVEL` | No | `INFO` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `RHYNO_ENVIRONMENT` | No | `production` | Environment tag on all telemetry |

### YAML Configuration (Optional)

Place `config.yaml` next to `main.py` or set `RHYNO_CONFIG_FILE` to point to it.

**Precedence:** ENV variables > YAML values > built-in defaults

See `config.yaml.example` for the full template.

### Example .env File

```env
RHYNO_API_URL=http://rhinometric-nginx/api
RHYNO_SERVICE_KEY=my-web-app
RHYNO_TELEMETRY_TOKEN=rtk_abc123def456
COLLECT_INTERVAL=15
ENABLE_METRICS=true
ENABLE_LOGS=true
ENABLE_TRACES=true
LOG_LEVEL=INFO
RHYNO_ENVIRONMENT=production
```

## Running with Docker

### Basic

```bash
docker run --rm --env-file .env rhinometric-collector
```

### On Rhinometric Network (same host)

```bash
docker run -d --name rhyno-collector \
  --env-file .env \
  --network rhinometric_rhinometric_network \
  --restart unless-stopped \
  rhinometric-collector
```

### Docker Compose

```yaml
services:
  rhinometric-collector:
    build: ./collector
    env_file: ./collector/.env
    restart: unless-stopped
    networks:
      - rhinometric_rhinometric_network

networks:
  rhinometric_rhinometric_network:
    external: true
```

## Running with Python (Direct)

```bash
cd collector
pip install requests psutil pyyaml
export RHYNO_API_URL=http://localhost/api
export RHYNO_SERVICE_KEY=my-service
export RHYNO_TELEMETRY_TOKEN=rtk_...
python main.py
```

## Signals Explained

| Signal | What It Collects | Where It Appears in Console |
|---|---|---|
| **Metrics** | CPU %, memory %, disk %, network I/O, collector uptime | SLO, AI Insights, Anomalies |
| **Logs** | Collector's own operational log entries | Log Explorer |
| **Traces** | One trace per cycle with child spans per signal | Traces view |

Each signal can be independently enabled/disabled. Disabling a signal means the collector will not collect or send that data type.

## Expected Behavior After Startup

### Startup Output

```
╔══════════════════════════════════════════════════════════╗
║          Rhinometric Collector v1.1.0                    ║
╠══════════════════════════════════════════════════════════╣
║  API URL      : http://rhinometric-nginx/api             ║
║  Service Key  : my-web-app                               ║
║  Token        : rtk_…f456                                ║
║  Hostname     : collector-host                           ║
║  Environment  : production                               ║
║  Interval     : 15s                                      ║
║  Signals      : metrics, logs, traces                    ║
║  Log Level    : INFO                                     ║
╚══════════════════════════════════════════════════════════╝

2026-03-20T10:00:00 [INFO] rhyno.collector.main — Running preflight connectivity check…
2026-03-20T10:00:00 [INFO] rhyno.collector.main — ✓ API reachable at http://rhinometric-nginx/api
2026-03-20T10:00:00 [INFO] rhyno.collector.main — Collector running. Press Ctrl+C to stop.
```

### Per-Cycle Output

```
2026-03-20T10:00:15 [INFO] rhyno.collector.sender — [metrics] ✓ sent — 200 — 45ms
2026-03-20T10:00:15 [INFO] rhyno.collector.sender — [logs] ✓ sent — 200 — 12ms
2026-03-20T10:00:15 [INFO] rhyno.collector.sender — [traces] ✓ sent — 200 — 8ms
2026-03-20T10:00:15 [INFO] rhyno.collector.main — Cycle 1 ✓ — 3/3 OK — [metrics:✓ | logs:✓(4) | traces:✓(3)] — 523ms
```

### Partial Failure

```
2026-03-20T10:00:30 [INFO] rhyno.collector.sender — [metrics] ✓ sent — 200 — 50ms
2026-03-20T10:00:30 [WARNING] rhyno.collector.sender — [logs] ✗ rejected — HTTP 403 — Signal 'logs' is not enabled
2026-03-20T10:00:30 [INFO] rhyno.collector.sender — [traces] ✓ sent — 200 — 10ms
2026-03-20T10:00:30 [INFO] rhyno.collector.main — Cycle 2 ⚠ — 2/3 OK — [metrics:✓ | logs:✗ | traces:✓(3)] — 520ms
```

The collector **does not crash** when one signal fails. Other signals continue normally.

## How to Know Data Is Reaching Rhinometric

1. **Startup log** shows `✓ API reachable` — means the backend accepted the connection
2. **Cycle logs** show `✓ sent — 200` for each signal — means data was accepted
3. In the Console, go to **Services** — your service should show **Telemetry Status: Receiving Data** (green badge)
4. **Log Explorer** — select your service, logs from the collector appear
5. **Traces** — traces from the collector appear with `collector.cycle` operation names
6. **AI Insights / SLO** — show "Telemetry + Synthetic" as the data source

If the status stays at "Configured" (blue badge), check:
- Is the collector running? (`docker logs rhyno-collector`)
- Is `RHYNO_API_URL` correct and reachable from the collector container?
- Is the network configuration correct? (use `--network rhinometric_rhinometric_network` if on the same host)

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `RHYNO_API_URL is required` | Missing or empty env var | Set `RHYNO_API_URL` in your `.env` file |
| `RHYNO_SERVICE_KEY is required` | Missing or empty env var | Copy the service key from Console > Services |
| `RHYNO_TELEMETRY_TOKEN is required` | Missing or empty env var | Copy the token from Console > Services > Telemetry Setup |
| `✗ Cannot reach API` at startup | Wrong URL or network issue | Verify URL, check firewall, use `--network` flag |
| `[metrics] ✗ connection error` | API unreachable during cycle | Check network, the collector will retry next cycle |
| `[logs] ✗ rejected — HTTP 403` | Signal not enabled for this service | Enable the signal in Console > Services > Edit |
| `HTTP 401 — Invalid telemetry token` | Token mismatch | Regenerate token in Console and update `.env` |
| `HTTP 404 — Service not found` | Wrong service key | Verify `RHYNO_SERVICE_KEY` matches the Console |
| Collector runs but Console shows "Configured" | Data not arriving | Check `docker logs`, verify network connectivity |
| `Cycle N ✗ — 0/3 OK` | All signals failing | Check API URL, token, and service key |

## Graceful Shutdown

The collector handles `SIGINT` (Ctrl+C) and `SIGTERM` (Docker stop) gracefully:

```
2026-03-20T10:05:00 [INFO] rhyno.collector.main — Received signal 2 — shutting down gracefully…
2026-03-20T10:05:00 [INFO] rhyno.collector.main — Collector stopped cleanly.
```

## Architecture

```
collector/
├── main.py             # Entry point — startup banner, main loop, signal handling
├── config.py           # Config loading: ENV > YAML > defaults, validation
├── sender.py           # HTTP client with retry/backoff, preflight check
├── metrics.py          # Real system metrics via psutil
├── logs.py             # Captures collector's own log output
├── traces.py           # Real traces with measured durations
├── utils.py            # ID generation, time helpers, logging setup, masking
├── Dockerfile          # Production Docker image
├── .env.example        # Environment variable template
├── config.yaml.example # YAML configuration template
└── README.md           # This file
```

## Version History

| Version | Changes |
|---|---|
| 1.1.0 | Customer-ready packaging: startup validation, masked tokens, preflight check, LOG_LEVEL support, per-signal results, health check, comprehensive README |
| 1.0.0 | Initial production collector with metrics, logs, traces |
