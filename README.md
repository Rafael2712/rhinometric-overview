# Mi Proyecto – Observabilidad

## Resumen
Traefik → NGINX (web). PgBouncer → PostgreSQL.
Prometheus recolecta métricas (node-exporter, cAdvisor, nginx-exporter, postgres-exporter, pgbouncer-exporter, Traefik).
Logs con Promtail → Loki. Grafana visualiza (dashboards provisionados).
