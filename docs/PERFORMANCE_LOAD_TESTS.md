# Performance & Load Testing — Synthetic Host Simulation

> **Rhinometric Console v2.6.0** · Enterprise License (100 hosts)
> Last updated: 2026-02-17

---

## 1. Objective

Validate how the Rhinometric stack behaves under progressively increasing host counts (20 → 50 → 70 → 100) using the Enterprise license limit of 100 hosts. This test exercises:

- **Prometheus scrape performance** with many targets
- **License page host counter** accuracy (`get_monitored_hosts_count()`)
- **Grafana dashboard rendering** under load
- **System resource consumption** (CPU, RAM, disk I/O)
- **Console responsiveness** (Home, Logs, Traces, Dashboards, License)

### What is NOT tested

- RBAC, login, authentication, or session handling
- License validator logic (we stay within the 100-host cap)
- Alertmanager or notification delivery
- Any destructive or irreversible change

---

## 2. Test Environment

| Component | Details |
|-----------|---------|
| **VM** | `89.167.22.228` |
| **OS** | Ubuntu 24.04.3 LTS |
| **CPU** | AMD EPYC-Genoa, 8 vCPUs @ 2.0 GHz, 1 socket, 1 thread/core |
| **RAM** | 16 GB (15 Gi usable) |
| **Disk** | 301 GB (`/dev/sda1`), ~266 GB free |
| **Docker** | 28.2.2 |
| **Prometheus** | v2.53.0 (`prom/prometheus:v2.53.0`) |
| **Scrape interval** | 15s (global default; node-exporter job inherits it) |
| **file_sd refresh** | 15s |
| **Prometheus RAM limit** | 768 MiB (Docker resource constraint) |
| **Sim container RAM limit** | 512 MiB (Docker resource constraint) |

---

## 3. How Hosts Are Counted

The license system counts hosts via the function `get_monitored_hosts_count()` in `routers/license.py` (line 82):

```python
# Simplified logic
node_count = prometheus_query('count(count by (instance) (up{job="node-exporter"}))')
cadvisor_count = prometheus_query('count(count by (instance) (up{job="cadvisor"}))')
return max(node_count, cadvisor_count)
```

**Key insight**: Each unique `instance` label in the `node-exporter` Prometheus job counts as one host. Our simulation creates N unique instances by running N HTTP servers on different ports inside a single container.

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  VM (89.167.22.228) · 8 vCPU · 16 GB RAM · 301 GB disk         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Docker network: rhinometric_rhinometric_network      │       │
│  │                                                       │       │
│  │  ┌─────────────────────┐                              │       │
│  │  │ rhinometric-sim-    │  Ports 9200..9299            │       │
│  │  │ node-exporter       │  (N lightweight HTTP         │       │
│  │  │ (python:3.11-slim)  │   servers, each serving      │       │
│  │  │                     │   /metrics with unique        │       │
│  │  │ Limit: 1 CPU/512MB  │   node_uname_info nodename)  │       │
│  │  └─────────┬───────────┘                              │       │
│  │            │ scraped every 15s                        │       │
│  │            ▼                                          │       │
│  │  ┌──────────────────────┐                             │       │
│  │  │ rhinometric-prometheus│◄── file_sd_configs         │       │
│  │  │ (prom/prometheus     │    loads loadtest_targets   │       │
│  │  │  :v2.53.0)           │    .json (refresh 15s)     │       │
│  │  │ Limit: 768 MB        │                             │       │
│  │  └──────────┬───────────┘                             │       │
│  │             │ queried by                              │       │
│  │             ▼                                         │       │
│  │  ┌──────────────────────┐                             │       │
│  │  │ rhinometric-console  │                             │       │
│  │  │ -backend (FastAPI)   │──► License page shows       │       │
│  │  │                      │    host count = N + 1       │       │
│  │  └──────────────────────┘    (sim + real)             │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Files Involved

| File | Purpose |
|------|---------|
| `loadtest/sim_node_exporter.py` | Python script spawning N lightweight HTTP metric servers |
| `docker-compose.loadtest.yml` | Docker Compose for the simulation container |
| `scripts/run_host_load_test.sh` | Start/scale the simulation (generates targets, starts container, restarts Prometheus) |
| `scripts/stop_host_load_test.sh` | Stop simulation and clean up |
| `prometheus/loadtest_targets.json` | Auto-generated Prometheus `file_sd` targets (do not edit manually) |
| `config/prometheus-v2.2.yml` | Prometheus config (has `file_sd_configs` in `node-exporter` job) |
| `docker-compose-v2.5.0-SECURE.yml` | Main stack (has volume mount for `loadtest_targets.json`) |

---

## 5. Test Results

### 5.1 Baseline — 1 host (no simulation)

| Metric | Value |
|--------|-------|
| **License Host Usage** | 1 / 100 |
| **Prometheus targets (node-exporter)** | 1 UP, 0 DOWN |
| **Prometheus CPU** | ~1–2% |
| **Prometheus RAM** | ~140 MiB / 768 MiB |
| **sim-node-exporter** | Not running |
| **System load (1/5/15 min)** | < 0.5 |
| **System RAM available** | ~12 Gi |
| **Container health** | All healthy (except victoria-metrics — preexisting) |
| **Stability** | No restarts, no errors |

---

### 5.2 Test: 20 simulated hosts (total: 21)

**Date**: 2026-02-17
**Command**: `./scripts/run_host_load_test.sh 20`

| Metric | Value |
|--------|-------|
| **License Host Usage** | **21 / 100** (79 available) |
| **Prometheus targets (node-exporter)** | 21 UP, 0 DOWN |
| **Prometheus CPU** | ~2–3% |
| **Prometheus RAM** | ~174 MiB / 768 MiB (22.6%) |
| **sim-node-exporter CPU** | < 1% |
| **sim-node-exporter RAM** | ~20 MiB / 512 MiB (3.9%) |
| **System load (1/5/15 min)** | 0.29 / 0.54 / 0.56 |
| **System RAM available** | ~12 Gi |
| **Container health** | All healthy (victoria-metrics unhealthy — preexisting) |

**Dashboards reviewed**: License page.
**Observations**:
- Host count appeared correctly within ~30s of launching the test.
- No container restarts or unhealthy transitions during the test.
- After running `stop_host_load_test.sh`, host count returned to 1 within ~5 minutes (Prometheus staleness window).

**Verdict**: ✅ No impact. VM barely noticed the additional load.

---

### 5.3 Test: 50 simulated hosts (total: 51)

**Date**: 2026-02-17
**Command**: `./scripts/run_host_load_test.sh 50`

| Metric | Value |
|--------|-------|
| **License Host Usage** | **51 / 100** (49 available) |
| **Prometheus targets (node-exporter)** | 51 UP, 0 DOWN |
| **Prometheus CPU** | **2.34%** |
| **Prometheus RAM** | **185.5 MiB / 768 MiB (24.2%)** |
| **sim-node-exporter CPU** | **0.78%** |
| **sim-node-exporter RAM** | **20.2 MiB / 512 MiB (3.9%)** |
| **System load (1/5/15 min)** | 1.07 / 0.62 / 0.58 |
| **System RAM available** | ~12 Gi |
| **Container health** | All healthy (victoria-metrics unhealthy — preexisting) |

**Dashboards reviewed**:
- 01 – System Overview (CPU, RAM, Disk, System Uptime, Network Traffic)
- 04 – Docker Containers (running containers, CPU & RAM per container)
- 06 – Rhinometric Console Backend (latencies, error rate, requests)

**Observations**:
- License page updated correctly to 51/100.
- All 51 Prometheus targets reporting UP with 0 DOWN.
- CPU and RAM on the VM are well within comfortable margins.
- Network traffic increased proportionally (expected) but no anomalous spikes.
- Backend latencies remain in the low milliseconds; error rate at 0.
- No container restarts or state changes during the entire test duration.
- Console navigation (Home, Logs, Traces, Dashboards, License) remained fluid and responsive.

**Verdict**: ✅ No degradation. The VM handled 51 hosts without breaking a sweat.

---

### 5.4 Test: 70 simulated hosts (total: 71) — PENDING

**Date**: _To be executed_
**Command**: `./scripts/run_host_load_test.sh 70`

| Metric | Value |
|--------|-------|
| **License Host Usage** | ___ / 100 |
| **Prometheus targets (node-exporter)** | ___ UP, ___ DOWN |
| **Prometheus CPU** | ___% |
| **Prometheus RAM** | ___ MiB / 768 MiB (___%) |
| **sim-node-exporter CPU** | ___% |
| **sim-node-exporter RAM** | ___ MiB / 512 MiB (___%) |
| **System load (1/5/15 min)** | ___ / ___ / ___ |
| **System RAM available** | ___ Gi |
| **Container health** | ___ |

**Dashboards reviewed**: ___
**Observations**: ___
**Verdict**: ___

---

### 5.5 Test: 100 simulated hosts (total: 101) — PENDING

**Date**: _To be executed_
**Command**: `./scripts/run_host_load_test.sh 100`

| Metric | Value |
|--------|-------|
| **License Host Usage** | ___ / 100 |
| **Prometheus targets (node-exporter)** | ___ UP, ___ DOWN |
| **Prometheus CPU** | ___% |
| **Prometheus RAM** | ___ MiB / 768 MiB (___%) |
| **sim-node-exporter CPU** | ___% |
| **sim-node-exporter RAM** | ___ MiB / 512 MiB (___%) |
| **System load (1/5/15 min)** | ___ / ___ / ___ |
| **System RAM available** | ___ Gi |
| **Container health** | ___ |

**Dashboards reviewed**: ___
**Observations**: ___
**Verdict**: ___

---

### 5.6 Summary Table

| Level | hosts_used | Prom CPU | Prom RAM | sim CPU | sim RAM | System Load | UI Feel | Notes |
|-------|-----------|----------|----------|---------|---------|-------------|---------|-------|
| Baseline (1) | 1 | ~1% | ~140 MiB | — | — | < 0.5 | Fast | Normal operation |
| 20 sim (21) | 21 | ~2–3% | ~174 MiB | < 1% | ~20 MiB | 0.29 | Fast | No impact |
| 50 sim (51) | 51 | 2.34% | 185 MiB | 0.78% | 20 MiB | 1.07 | Fast | No degradation |
| 70 sim (71) | ___ | ___ | ___ | ___ | ___ | ___ | ___ | Pending |
| 100 sim (101) | ___ | ___ | ___ | ___ | ___ | ___ | ___ | Pending |

---

## 6. Preliminary Capacity Conclusion

Based on tests conducted on 2026-02-17 with 20 and 50 simulated hosts:

**In the current VM configuration (8 vCPU AMD EPYC @ 2 GHz, 16 GB RAM, 301 GB SSD), Rhinometric Console v2.6.0 supports at least 50 monitored hosts with no perceptible degradation in console responsiveness, dashboard rendering, or backend latency.**

Key findings:
- Prometheus uses only **24% of its 768 MiB RAM limit** with 51 targets, leaving significant headroom.
- The simulation container is extremely lightweight at **< 1% CPU and 20 MiB RAM** even with 50 simulated hosts.
- System load average remains below 1.1, well within the 8-core capacity.
- **12 GB of system RAM remains available**, indicating no memory pressure.
- All services remain healthy throughout the tests with zero container restarts.

**Next steps**: Tests with 70 and 100 hosts are planned to confirm behavior at the Enterprise license limit. Based on the observed trend (near-linear and modest resource growth), we expect the system to handle 100 hosts comfortably.

> **Note**: These are synthetic hosts generating realistic but lightweight Prometheus metrics. Real-world hosts with full application stacks may produce more metric series and higher scrape payloads. This test validates the platform's monitoring infrastructure capacity, not individual host workload profiles.

---

## 7. Test Limitations

| Limitation | Impact |
|------------|--------|
| **Synthetic hosts, not real workloads** | Simulated hosts serve a fixed set of ~25 metric families. Real hosts with full application stacks may expose hundreds of metrics, increasing Prometheus ingestion load. |
| **Single container for all simulated hosts** | All N simulated node-exporters run in one container sharing a single CPU/512 MB. A real deployment has N separate machines each running their own node-exporter. |
| **Fixed scrape interval (15s)** | Lower intervals (e.g., 5s) would increase Prometheus load proportionally. These tests only validated the default 15s interval. |
| **No cadvisor simulation** | Only `node-exporter` instances are simulated. The host counter uses `max(node_count, cadvisor_count)`, so cadvisor count is not exercised at higher values. |
| **No alerting load** | Alertmanager rules that fire based on host metrics were not stressed because simulated metrics stay within normal ranges. |
| **Same VM for everything** | In production, Prometheus and the monitored hosts would be on separate machines. Network latency and bandwidth are not factors in this test. |
| **Prometheus RAM is capped at 768 MiB** | This Docker limit may need adjustment for 100+ hosts in production. |

---

## 8. Simulated Metrics

Each simulated host exposes realistic Prometheus metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `up` | gauge | Always 1 |
| `node_cpu_seconds_total` | counter | Per-CPU, per-mode (user, system, idle, iowait, irq, softirq) |
| `node_memory_MemTotal_bytes` | gauge | 8–64 GB (randomized per host) |
| `node_memory_MemAvailable_bytes` | gauge | 30–80% of total (varies over time) |
| `node_filesystem_size_bytes` | gauge | 100–2000 GB |
| `node_filesystem_avail_bytes` | gauge | 20–80% of total |
| `node_network_receive_bytes_total` | counter | Incrementing with random rate |
| `node_network_transmit_bytes_total` | counter | Incrementing with random rate |
| `node_load1`, `node_load5`, `node_load15` | gauge | Random load values |
| `node_uname_info` | gauge | Unique `nodename` per host (sim-host-NNN) |
| `node_boot_time_seconds` | gauge | Fixed timestamp per host |

---

## 9. Cheat-Sheet de Comandos

### Lanzar N hosts simulados

```bash
cd /opt/rhinometric
./scripts/run_host_load_test.sh 20    # o 50, 70, 100
```

### Detener la simulación

```bash
./scripts/stop_host_load_test.sh
```

> **Nota**: Después de detener, Prometheus mantiene las series en memoria por ~5 minutos (staleness window). El conteo en License bajará pasado ese tiempo, o tras reiniciar Prometheus.

### Verificar número de hosts en Prometheus

```bash
docker exec rhinometric-prometheus wget -q -O- \
  'http://localhost:9090/api/v1/query?query=count(count%20by%20(instance)%20(up%7Bjob%3D%22node-exporter%22%7D))' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['result'][0]['value'][1])"
```

### Ver estado de todos los targets

```bash
docker exec rhinometric-prometheus wget -q -O- \
  'http://localhost:9090/api/v1/targets?scrapePool=node-exporter' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
t = d['data']['activeTargets']
up = sum(1 for x in t if x['health']=='up')
print(f'Total: {len(t)}, Up: {up}, Down: {len(t)-up}')
"
```

### Monitorizar recursos en tiempo real

```bash
# Recursos de los contenedores clave (snapshot)
docker stats --no-stream rhinometric-sim-node-exporter rhinometric-prometheus

# Recursos en tiempo real (Ctrl+C para salir)
docker stats rhinometric-sim-node-exporter rhinometric-prometheus

# Memoria del sistema
free -h

# Carga del sistema
uptime

# I/O de disco (cada 5 segundos)
iostat -x 5

# Estado de todos los contenedores
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Recolectar snapshot completo de métricas

```bash
python3 /tmp/collect_50_metrics.py
```

> Ajustar el script según el escalón de carga si es necesario.

---

## 10. Troubleshooting

### Hosts no aparecen en Prometheus

1. Verificar que el contenedor sim está corriendo: `docker ps | grep sim-node-exporter`
2. Verificar que el fichero de targets existe: `cat prometheus/loadtest_targets.json | python3 -m json.tool | head`
3. Verificar targets en Prometheus: UI → Status → Targets → pool `node-exporter`
4. Verificar config de Prometheus:
   ```bash
   grep -A3 file_sd_configs config/prometheus-v2.2.yml
   ```

### Prometheus lifecycle API devuelve 403

Esto es esperado — el flag `--web.enable-lifecycle` no está activado. Los scripts usan `docker restart` en su lugar.

### El conteo de hosts es incorrecto

- Esperado: N + 1 (N simulados + 1 real)
- Si muestra 1: Prometheus no ha recogido los nuevos targets. Esperar 30s o reiniciar Prometheus.
- Si muestra N (sin el +1): El node-exporter real podría estar caído. Verificar con `docker ps | grep node-exporter`.

### Uso alto de recursos

- Bajar escala: `./scripts/run_host_load_test.sh 20`
- Parar del todo: `./scripts/stop_host_load_test.sh`
- Ver límites del contenedor: `docker inspect rhinometric-sim-node-exporter | grep -A10 Resources`

---

## 11. Safety Notes

- **Additive only**: No existing files are deleted; only new files are created.
- **Reversible**: Running `stop_host_load_test.sh` restores the stack to its original state.
- **No RBAC/Auth impact**: The simulation only adds Prometheus scrape targets.
- **No license changes**: We operate within the 100-host Enterprise limit.
- **Resource limited**: The sim container is capped at 1 CPU / 512 MB RAM.
- **Network isolated**: The sim container only joins the existing Docker network; no new ports are exposed to the host.
