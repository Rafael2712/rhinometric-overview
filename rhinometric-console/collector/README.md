# Rhinometric Minimal Telemetry Collector

A lightweight Docker-based collector that sends synthetic **metrics**, **logs**, and **traces** to the Rhinometric telemetry ingestion API every 10 seconds.

> **Purpose:** This is a testing/validation tool — not a production agent.

## Required Environment Variables

| Variable           | Description                                      | Default                       |
|--------------------|--------------------------------------------------|-------------------------------|
| `SERVICE_KEY`      | The `telemetry_service_key` of your service      | *(required)*                  |
| `TELEMETRY_TOKEN`  | The `rtk_*` token generated on service creation  | *(required)*                  |
| `BASE_URL`         | Rhinometric API base URL                         | `http://localhost:80/api`     |
| `INTERVAL`         | Seconds between collection cycles                | `10`                          |

## Quick Start

### 1. Build the image

```bash
cd collector
docker build -t rhinometric-collector .
```

### 2. Run the collector

```bash
docker run --rm \
  -e SERVICE_KEY="your-service-key" \
  -e TELEMETRY_TOKEN="rtk_your-token-here" \
  -e BASE_URL="http://your-host/api" \
  -e INTERVAL=10 \
  --name rhinometric-collector \
  rhinometric-collector
```

### 3. Run on the same Docker network

If running alongside the Rhinometric stack:

```bash
docker run --rm \
  --network rhinometric_default \
  -e SERVICE_KEY="your-service-key" \
  -e TELEMETRY_TOKEN="rtk_your-token-here" \
  -e BASE_URL="http://rhinometric-nginx:80/api" \
  -e INTERVAL=10 \
  --name rhinometric-collector \
  rhinometric-collector
```

## What It Sends

Each cycle sends:

- **5 metrics** — heartbeat, HTTP request count, latency, CPU, memory
- **3 log entries** — randomized info/warn/error messages
- **2 trace spans** — parent HTTP span + child DB span

## Expected Behavior

After starting the collector:

1. Service `telemetry_status` transitions: `configured` → `connected` → `receiving_data`
2. `telemetry_attached` becomes `true`
3. `last_telemetry_at` updates every cycle
4. Telemetry Setup panel in the UI shows live status

## Stopping

```bash
docker stop rhinometric-collector
```
