# Configuring Client Services in Rhinometric

## What Are Client Services?

Rhinometric monitors two categories of services:

- **Platform Services** are the internal components that make up the monitoring stack itself (databases, collectors, dashboards, etc.). These are pre-configured and managed automatically.
- **Client Services** are the external endpoints, websites, or APIs that *you* want to monitor. These represent your own infrastructure  the systems your customers or users depend on.

By default, a fresh Rhinometric installation has **0 client services**. Platform services are detected automatically. Client services appear in the dashboard only after you configure them.

---

## How Client Services Appear in the Dashboard

Once configured, client services show up in two places:

1. **Home page**  The "Monitored Services" card displays:
   - `Client: X` (your monitored endpoints)
   - `Platform: Y` (internal services)
   - `Total: Z`

2. **Services page**  Use the **All / Platform / Client** filter tabs to view services by category. Each service displays its status (up/down) and category badge.

---

## Adding a New Client Service

Client services are added by creating a new **Prometheus scrape job** that monitors an external target through the blackbox exporter. Follow these steps:

### Step 1: Open the Prometheus Configuration

Edit the file:

```
config/prometheus-v2.2.yml
```

### Step 2: Add a New Scrape Job

At the end of the file, add a block like this:

```yaml
  - job_name: 'blackbox-web-myapp'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://www.example.com/
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: rhinometric-blackbox-exporter:9115
```

Replace the values:

| Field | What to Change |
|---|---|
| `job_name` | A unique name starting with `blackbox-web-` (e.g. `blackbox-web-myapp`) |
| `targets` | The URL(s) you want to monitor |
| `module` | Use `http_2xx` for HTTPS/HTTP checks, or another blackbox module if needed |

### Step 3: Restart Prometheus

After saving the file, restart the Prometheus container:

```bash
docker compose restart prometheus
```

### Step 4: Verify

Wait 30 seconds, then check:

- Open the **Services** page in Rhinometric
- Switch to the **Client** tab
- Your new service should appear with status "up" or "down"

---

## Adding Multiple Client Services

You can add multiple targets in the same job, or create separate jobs:

**Option A: Multiple targets in one job**

```yaml
  - job_name: 'blackbox-web-client-sites'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://www.example.com/
          - https://api.example.com/health
          - https://store.example.com/
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: rhinometric-blackbox-exporter:9115
```

**Option B: One job per service** (recommended for different check settings)

Create separate `job_name` entries for each service (e.g. `blackbox-web-api`, `blackbox-web-store`).

---

## How Classification Works

Rhinometric automatically classifies services based on the Prometheus job name:

- Jobs matching known platform names (e.g. `prometheus`, `grafana`, `redis`, `blackbox-http`) are classified as **Platform**.
- All other jobs are classified as **Client**.

You do not need to add any special labels. Any new scrape job that is not in the platform list will automatically appear as a client service.

---

## Removing a Client Service

To stop monitoring a client service:

1. Remove or comment out the corresponding `job_name` block from `config/prometheus-v2.2.yml`
2. Restart Prometheus: `docker compose restart prometheus`
3. The service will disappear from the dashboard within a few minutes

---

## Optional: Alert Rules for Client Services

To receive alerts when a client service goes down, edit:

```
config/rules/alerts/website.yml
```

This file contains commented-out templates for common alert rules (website down, high latency, SSL expiring). Uncomment and adapt them for your targets.

---

## Need Help?

If you have questions about configuring client services, contact your Rhinometric administrator or refer to the main documentation.