# GAPS – rhinometric.com Website Integration

> Items that could NOT be implemented without touching RBAC/auth or require manual UI work.

## Completed ✅

| # | Item | Status | Details |
|---|------|--------|---------|
| 1 | Prometheus target | ✅ | `blackbox-web-rhinometric` job in `prometheus-v2.2.yml` |
| 2 | Service count = 13 | ✅ | PromQL filter excludes infra, includes website |
| 3 | Blackbox probe | ✅ | `probe_success{job="blackbox-web-rhinometric"}` = 1 |
| 4 | AI Anomaly signals (4) | ✅ | availability, response_time, ssl_expiry, dns_time |
| 5 | Prometheus alerts (5) | ✅ | Down, HighLatency, SSLExpiring, SSLCritical, ProbeFailure |
| 6 | Grafana dashboard | ✅ | uid=dfd0diwlk9340c, 12 panels, v4 |
| 7 | TODO-RBAC comments (3) | ✅ | kpis.py lines 30, 302, 393 |
| 8 | RBAC/Auth untouched | ✅ | Zero changes to auth.py |
| 9 | Database unchanged | ✅ | No migrations, purely PromQL-based |

## Gaps / Deferred 🔲

| # | Item | Reason | Suggested Action |
|---|------|--------|------------------|
| 1 | Console UI dashboard card click-through | Frontend (React) would need a route mapping for `blackbox-web-rhinometric` → Grafana dashboard | Add mapping in frontend dashboard config when ready |
| 2 | AlertManager routing | Website alerts fire to default receiver; may need dedicated Slack/email channel | Add `route.match` in `alertmanager.yml` for `service=rhinometric-website` |
| 3 | AI Anomaly model training | New signals need ~24h of baseline data before anomaly detection is effective | Monitor after 24h |
| 4 | Multi-tenant RBAC scoping | Service visibility per tenant not implemented (marked with TODO-RBAC) | Implement when multi-tenancy ships |

## Files Modified

```
config/prometheus-v2.2.yml           # Added rule_files glob + blackbox-web-rhinometric job
config/rules/alerts/website.yml      # NEW – 5 website alert rules
rhinometric-ai-anomaly/config.yaml   # Added 4 website monitoring signals
rhinometric-console/backend/routers/kpis.py  # Filter fix + is_platform classification + TODO-RBAC
```

## Backups

```
config/prometheus-v2.2.yml.backup-before-integration
rhinometric-ai-anomaly/config.yaml.backup-before-website
rhinometric-console/backend/routers/kpis.py.backup
```
