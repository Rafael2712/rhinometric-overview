# Performance & Load Testing — Synthetic Host Simulation

> **Rhinometric Console v2.6.0** · Enterprise License (100 hosts)
> Last updated: 2025-06-18

---

## 1. Objective

Validate how the Rhinometric stack behaves under progressively increasing host counts (20 → 50 → 70 → 100) using the Enterprise license limit of 100 hosts. This test exercises:

- **Prometheus scrape performance** with many targets
- **License page host counter** accuracy (`get_monitored_hosts_count()`)
- **Grafana dashboard rendering** under load
- **System resource consumption** (CPU, RAM, disk I/O)

### What is NOT tested

- RBAC, login, authentication, or session handling
- License validator logic (we stay within the 100-host cap)
- Alertmanager or notification delivery
- Any destructive or irreversible change

---

## 2. How Hosts Are Counted

The license system counts hosts via the function `get_monitored_hosts_count()` in `routers/license.py` (line 82):

```python
# Simplified logic
node_count = prometheus_query('count(count by (instance) (up{job="node-exporter"}))')
cadvisor_count = prometheus_query('count(count by (instance) (up{job="cadvisor"}))')
return max(node_count, cadvisor_count)
```

**Key insight**: Each unique `instance` label in the `node-exporter` Prometheus job counts as one host. Our simulation creates N unique instances by running N HTTP servers on different ports inside a single container.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  VM (89.167.22.228)                                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Docker network: rhinometric_rhinometric_network      │       │
│  │                                                       │       │
│  │  ┌─────────────────────┐                              │       │
│  │  │ rhinometric-sim-    │  Ports 9200..9299            │       │
│  │  │ node-exporter       │  (N lightweight HTTP         │       │
│  │  │ (python:3.11-slim)  │   servers, each serving      │       │
│  │  │                     │   /metrics with unique        │       │
│  │  │                     │   node_uname_info nodename)   │       │
│  │  └─────────┬───────────┘                              │       │
│  │            │ scraped by                               │       │
│  │            ▼                                          │       │
│  │  ┌──────────────────────┐                             │       │
│  │  │ rhinometric-prometheus│◄── file_sd_configs         │       │
│  │  │ (prom/prometheus     │    loads loadtest_targets   │       │
│  │  │  :v2.53.0)           │    .json (refresh 15s)     │       │
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

## 4. Running the Load Test

### Prerequisites

- SSH access to the VM
- All Rhinometric containers running and healthy
- Working directory: `/opt/rhinometric`

### Start simulation

```bash
cd /opt/rhinometric

# Start with 20 simulated hosts (total count = 21 including real host)
./scripts/run_host_load_test.sh 20

# Scale up to 50
./scripts/run_host_load_test.sh 50

# Scale up to 70
./scripts/run_host_load_test.sh 70

# Scale up to 100 (Enterprise license limit)
./scripts/run_host_load_test.sh 100
```

The script will:
1. Generate `prometheus/loadtest_targets.json` with N target entries
2. Start (or recreate) the `rhinometric-sim-node-exporter` container
3. Restart Prometheus and wait for it to be healthy

### Verify host count

After ~30 seconds, verify from inside the Prometheus container:

```bash
docker exec rhinometric-prometheus wget -q -O- \
  'http://localhost:9090/api/v1/query?query=count(count%20by%20(instance)%20(up%7Bjob%3D%22node-exporter%22%7D))' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['result'][0]['value'][1])"
```

Expected output: `N + 1` (N simulated + 1 real node-exporter).

You can also check the **License** page in the Rhinometric Console UI — the "Monitored Hosts" card should show the updated count.

### Stop simulation

```bash
./scripts/stop_host_load_test.sh
```

This stops the container, clears the targets file, and restarts Prometheus. Host count returns to 1 (the real host) within ~1 minute.

---

## 5. Resource Monitoring

While the test is running, monitor system resources:

```bash
# Container resource usage
docker stats rhinometric-sim-node-exporter rhinometric-prometheus

# System memory
free -h

# CPU load
uptime

# Disk I/O
iostat -x 5

# Check all containers are healthy
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Expected Resource Usage

| Hosts | sim container CPU | sim container RAM | Prometheus RAM delta |
|-------|-------------------|-------------------|---------------------|
| 20    | < 5%              | ~50 MB            | +50 MB              |
| 50    | < 10%             | ~80 MB            | +120 MB             |
| 70    | < 15%             | ~100 MB           | +170 MB             |
| 100   | < 20%             | ~130 MB           | +250 MB             |

*Values are approximate. The sim container is resource-limited to 1 CPU / 512 MB.*

---

## 6. Simulated Metrics

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

## 7. Troubleshooting

### Hosts not appearing in Prometheus

1. Check the sim container is running: `docker ps | grep sim-node-exporter`
2. Check targets file exists: `cat prometheus/loadtest_targets.json | python3 -m json.tool | head`
3. Check Prometheus targets: access Prometheus UI → Status → Targets → `node-exporter` pool
4. Check Prometheus config has `file_sd_configs`:
   ```bash
   grep -A3 file_sd_configs config/prometheus-v2.2.yml
   ```

### Prometheus lifecycle API returns 403

This is expected — the `--web.enable-lifecycle` flag is not set. The scripts use `docker restart` instead.

### Host count is wrong

- Expected: N + 1 (N simulated + 1 real)
- If count is 1: Prometheus hasn't picked up the new targets yet. Wait 30s or restart Prometheus.
- If count is N: The real node-exporter might be down. Check `docker ps | grep node-exporter`.

### High resource usage

- Scale down: `./scripts/run_host_load_test.sh 20`
- Stop completely: `./scripts/stop_host_load_test.sh`
- Check container resource limits: `docker inspect rhinometric-sim-node-exporter | grep -A10 Resources`

---

## 8. Safety Notes

- **Additive only**: No existing files are deleted; only new files are created
- **Reversible**: Running `stop_host_load_test.sh` restores the stack to its original state
- **No RBAC/Auth impact**: The simulation only adds Prometheus scrape targets
- **No license changes**: We operate within the 100-host Enterprise limit
- **Resource limited**: The sim container is capped at 1 CPU / 512 MB RAM
- **Network isolated**: The sim container only joins the existing Docker network; no new ports are exposed to the host
