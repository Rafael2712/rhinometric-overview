# Rhinometric Collector v1.2

A lightweight telemetry agent that collects system metrics, application logs, and distributed traces from your environment and sends them to the Rhinometric Console.

## What It Does

The collector runs as a background process (typically in Docker) alongside your services. Each cycle it:

1. **Metrics** — Collects CPU, memory, disk, and network stats from the host via `psutil`
2. **Logs** — Captures the collector's own operational log output as structured entries
3. **File Logs** *(v1.2.0)* — Tails external log files (e.g. `/var/log/app.log`) and ships new lines
4. **Traces** — Generates real distributed traces measuring each collection cycle's duration

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

### With File Log Ingestion (v1.2.0)

To tail external log files, mount them into the container and set `LOG_SOURCES`:

```bash
docker run -d --name rhyno-collector \
  --env-file collector/.env \
  --network rhinometric_rhinometric_network \
  -v /var/log/myapp:/var/log/myapp:ro \
  -e LOG_SOURCES="file:/var/log/myapp/app.log,file:/var/log/myapp/error.log" \
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
| `LOG_SOURCES` | No | *(empty)* | Comma-separated file paths to tail (v1.2.0) |
| `LOG_MAX_LINES` | No | `50` | Max lines per file per cycle (v1.2.0) |
| `LOG_POLL_INTERVAL` | No | `5` | Min seconds between file reads (v1.2.0) |

### LOG_SOURCES Format

```
LOG_SOURCES=file:/var/log/app.log,file:/var/log/syslog
LOG_SOURCES=/var/log/app.log,/var/log/syslog        # "file:" prefix is optional
```

Each entry is an absolute path to a log file. The collector will:
- Start reading from the end of the file (first cycle reads existing content)
- Track a byte offset per file — only new lines are read each cycle
- Detect file rotation (inode change) and truncation (file shrunk) — resets to beginning
- Cap reads at `LOG_MAX_LINES` per file per cycle to avoid memory spikes
- Auto-detect log level from line content (ERROR, WARNING, INFO, DEBUG)
- Skip missing files silently (logged as info)

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

# File log ingestion (v1.2.0)
LOG_SOURCES=file:/var/log/myapp/app.log,file:/var/log/myapp/error.log
LOG_MAX_LINES=50
LOG_POLL_INTERVAL=5
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
    volumes:
      # Mount log files for file-based ingestion (v1.2.0)
      - /var/log/myapp:/var/log/myapp:ro
    environment:
      - LOG_SOURCES=file:/var/log/myapp/app.log
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
| **File Logs** *(v1.2.0)* | Lines from external log files (e.g. app.log) | Log Explorer |
| **Traces** | One trace per cycle with child spans per signal | Traces view |

Each signal can be independently enabled/disabled. Disabling a signal means the collector will not collect or send that data type.

File logs are merged with internal logs into a single "logs" payload. Each entry carries labels indicating its source (`source=collector` for internal, `source=file` with `file_path` for tailed files).

## Expected Behavior After Startup

### Startup Output

```
╔══════════════════════════════════════════════════════════╗
║          Rhinometric Collector v1.2.0                    ║
╠══════════════════════════════════════════════════════════╣
║  API URL      : http://rhinometric-nginx/api             ║
║  Service Key  : my-web-app                               ║
║  Token        : rtk_…f456                                ║
║  Hostname     : collector-host                           ║
║  Environment  : production                               ║
║  Interval     : 15s                                      ║
║  Signals      : metrics, logs, traces                    ║
║  Log Level    : INFO                                     ║
║  Log Sources  : 2 file(s)                                ║
║    → /var/log/myapp/app.log                              ║
║    → /var/log/myapp/error.log                            ║
╚══════════════════════════════════════════════════════════╝

2026-03-23T10:00:00 [INFO] rhyno.collector.main — Running preflight connectivity check…
2026-03-23T10:00:00 [INFO] rhyno.collector.main — ✓ API reachable at http://rhinometric-nginx/api
2026-03-23T10:00:00 [INFO] rhyno.collector.main — Collector running. Press Ctrl+C to stop.
```

### Per-Cycle Output

```
2026-03-23T10:00:15 [INFO] rhyno.collector.sender — [metrics] ✓ sent — 200 — 45ms
2026-03-23T10:00:15 [INFO] rhyno.collector.sender — [logs] ✓ sent — 200 — 12ms
2026-03-23T10:00:15 [INFO] rhyno.collector.sender — [traces] ✓ sent — 200 — 8ms
2026-03-23T10:00:15 [INFO] rhyno.collector.main — Cycle 1 ✓ — 3/3 OK — [metrics:✓ | logs:✓(12) | traces:✓(3)] — 523ms
```

### Partial Failure

```
2026-03-23T10:00:30 [INFO] rhyno.collector.sender — [metrics] ✓ sent — 200 — 50ms
2026-03-23T10:00:30 [WARNING] rhyno.collector.sender — [logs] ✗ rejected — HTTP 403 — Signal 'logs' is not enabled
2026-03-23T10:00:30 [INFO] rhyno.collector.sender — [traces] ✓ sent — 200 — 10ms
2026-03-23T10:00:30 [INFO] rhyno.collector.main — Cycle 2 ⚠ — 2/3 OK — [metrics:✓ | logs:✗ | traces:✓(3)] — 520ms
```

The collector **does not crash** when one signal fails. Other signals continue normally.

## How File Log Tailing Works (v1.2.0)

The `FileTailer` class implements offset-based file tailing:

1. **First read**: Opens the file, reads from offset 0 (beginning), stores byte position
2. **Subsequent reads**: Seeks to stored offset, reads only new lines appended since last read
3. **Rotation detection**: Compares file inode — if it changes (logrotate), resets to beginning
4. **Truncation detection**: If file size < stored offset (file was truncated/cleared), resets to beginning
5. **Rate limiting**: Reads at most `LOG_MAX_LINES` lines per file per cycle
6. **Level detection**: Scans each line for keywords (ERROR, WARNING, DEBUG, etc.)
7. **Missing files**: Silently skipped with an info-level log message

### Labels on File Logs

Each file log entry sent to the backend carries these labels:

```json
{
  "service_key": "your-service-key",
  "source": "file",
  "file_path": "/var/log/myapp/app.log",
  "environment": "production"
}
```

Internal collector logs use `"source": "collector"` instead.

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
| `file:/path → file not found` | File doesn't exist or not mounted | Check path, mount volume with `-v` in Docker |
| `file:/path → stat error` | Permission denied | Ensure container can read the file (`:ro` mount) |
| Collector runs but Console shows "Configured" | Data not arriving | Check `docker logs`, verify network connectivity |
| `Cycle N ✗ — 0/3 OK` | All signals failing | Check API URL, token, and service key |

## Graceful Shutdown

The collector handles `SIGINT` (Ctrl+C) and `SIGTERM` (Docker stop) gracefully:

```
2026-03-23T10:05:00 [INFO] rhyno.collector.main — Received signal 2 — shutting down gracefully…
2026-03-23T10:05:00 [INFO] rhyno.collector.main — Collector stopped cleanly.
```

## Architecture

```
collector/
├── main.py             # Entry point — startup banner, main loop, signal handling
├── config.py           # Config loading: ENV > YAML > defaults, validation
├── sender.py           # HTTP client with retry/backoff, preflight check
├── metrics.py          # Real system metrics via psutil
├── logs.py             # Internal log buffer + file tailing (v1.2.0)
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
| 1.2.0 | File-based log ingestion: `LOG_SOURCES` to tail external log files with offset tracking, rotation/truncation detection, level auto-detection, and rate limiting (`LOG_MAX_LINES`). Fully backward compatible — omitting `LOG_SOURCES` preserves v1.1.0 behavior. |
| 1.1.0 | Customer-ready packaging: startup validation, masked tokens, preflight check, LOG_LEVEL support, per-signal results, health check, comprehensive README |
| 1.0.0 | Initial production collector with metrics, logs, traces |
