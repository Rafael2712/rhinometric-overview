# Rhinometric Platform - Technical Architecture Report

**Version:** 2.5.1  
**Date:** January 28, 2026  
**Environment:** Production (rhinometric-core-restore)  
**Infrastructure:** Hetzner Cloud VM (89.167.15.73)

---

## Executive Summary

Rhinometric is an AI-powered observability and anomaly detection platform designed for enterprise environments. The platform provides comprehensive monitoring, alerting, and intelligent anomaly detection across distributed systems with sub-second detection latency and enterprise-grade reliability.

**Key Capabilities:**
- Real-time metrics collection and aggregation (15s scrape interval)
- AI-powered anomaly detection with machine learning models
- Distributed tracing across microservices
- Centralized log aggregation with structured parsing
- Multi-tier alerting system with severity classification
- Executive dashboards for C-level visibility

---

## 1. Platform Architecture

### 1.1 Infrastructure Components

**Deployment Model:** Containerized microservices on single VM (horizontal scaling ready)

**Core Services (19 containers):**

1. **Observability Stack:**
   - Prometheus v2.x (metrics aggregation, TSDB)
   - Grafana v10.x (visualization, dashboards)
   - Loki v2.x (log aggregation)
   - Jaeger (distributed tracing)
   - OpenTelemetry Collector (telemetry pipeline)

2. **Application Services:**
   - Console Backend (Python/FastAPI, port 8105)
   - Console Frontend (React/Vite, port 3002)
   - License Server v2 (Python/FastAPI, port 5000)
   - AI Anomaly Detection Engine (Python/scikit-learn, port 8085)

3. **Data Layer:**
   - PostgreSQL 15 (operational data)
   - Redis 7 (caching, session management)

4. **Supporting Services:**
   - Alertmanager, Promtail, Node Exporter, cAdvisor, Blackbox Exporter, PgBouncer

### 1.2 Current Scale

**Load:**
- HTTP Requests: ~1 million/day (~12 req/s average)
- Metrics: ~6000 time series active
- Logs: ~500 MB/day
- Traces: ~10K traces/day

**Resources:**
- VM: 4 vCPUs, 8 GB RAM, 160 GB SSD
- CPU: 20-30% average
- Memory: 5.5 GB used (69%)
- Disk: 25 GB used (16%)

---

## 2. Observability Implementation

### 2.1 Metrics & Alerts

**Active Alerts (13+):**

**Console Backend (3):**
- HighHttpLatencyP95 (P95 > 1s for 5min, severity: warning)
- HighHttpErrorRate (5xx > 5% for 2min, severity: critical)
- HighHttpRequestRate (> 100 req/s for 5min, severity: info)

**License Server (4):**
- LicenseServerDown (unreachable > 1min, severity: critical, business-critical tier)
- LicenseServerHighErrorRate (5xx > 5% for 2min, severity: critical)
- LicenseServerHighLatency (P95 > 1s for 5min, severity: warning)
- LicenseServerNoTraffic (no requests for 10min, severity: warning)

**AI Anomaly (6):**
- AIAnomalyServiceDown (unreachable > 2min, severity: critical)
- AIAnomalyNoAPITraffic (no requests for 15min, severity: warning)
- AIAnomalyHighActiveAnomalies (> 50 active for 10min, severity: warning)
- Plus 3 existing AI-specific alerts

**Scrape Configuration:**
- 12+ jobs active
- 15-second scrape interval
- 15-day retention policy
- ~500 unique time series per service

### 2.2 Dashboard Catalog

**1. Executive Overview (10 panels)**
- Health status: Console, License, AI (UP/DOWN indicators)
- Active anomalies counter + sparkline
- Active alerts 24h counter
- Total requests 24h (1M+)
- Global error rate % (gauge with thresholds)
- Platform uptime (hours)
- Service request rates (QPS timeseries)
- Critical alerts timeline (bar chart)

**Target:** C-level, executives  
**Refresh:** 30s  
**URL:** /d/executive-overview

**2. Console Backend Performance (9 panels)**
- QPS by endpoint, error rate gauge, total requests
- Requests in progress, status code distribution
- Latency percentiles (P50/P95/P99)
- Top 10 slowest endpoints (table)
- Request/Response size, DB connection pool

**Target:** Backend engineers, DevOps  
**Refresh:** 10s

**3. License Server Performance (6 panels)**
- Service status, request rate QPS, total requests 24h
- Error rate %, latency percentiles, requests by status code

**Target:** Operations, product  
**Refresh:** 10s

**4. AI Anomaly Detection (24 panels)**
- Total/active anomalies, ML models active
- API request rate, detection rate by severity
- Top 10 metrics with anomalies, logs live tail
- Heatmap anomalies by metric, learned baselines
- Detection time P95, service status
- HTTP metrics monitoring (rate, errors, latency)
- Anomaly states, deviation %, scores

**Target:** Data scientists, ML engineers  
**Refresh:** 10s

**Total Dashboards:** 7 (4 specialized + 1 executive + 2 system)

---

## 3. AI Anomaly Detection Engine

### 3.1 Technology Stack

- Python 3.11
- scikit-learn (statistical models)
- pandas, NumPy
- FastAPI (REST API)

### 3.2 Detection Algorithms

1. **Statistical Anomaly Detection:**
   - Z-score analysis (threshold: 3σ)
   - IQR (Interquartile Range) method
   - Moving average deviation

2. **Time Series Analysis:**
   - Baseline learning (7-day rolling window)
   - Seasonal decomposition
   - Trend detection

3. **Machine Learning Models:**
   - Isolation Forest (unsupervised)
   - Local Outlier Factor (LOF)
   - DBSCAN clustering

### 3.3 Performance

- Inference latency: < 100ms (P95)
- Throughput: 1000+ data points/second
- Model update: Hourly incremental learning

**Classification:**
- Critical: > 50% deviation
- High: 30-50% deviation
- Medium: 15-30% deviation
- Low: 5-15% deviation

**Accuracy:**
- Precision: ~85%
- Recall: ~92%
- F1 Score: ~88%

---

## 4. Distributed Tracing

**Implementation:**
- OpenTelemetry SDK (Python)
- Automatic HTTP instrumentation
- W3C Trace Context standard
- 7-day trace retention

**Current Scale:**
- 2+ services instrumented
- 5-10 spans per trace average
- Query latency: < 500ms

---

## 5. Log Management

**Architecture:**
- Promtail (log shipper) + Loki (aggregation) + LogQL (queries)

**Extracted Labels (11):**
service, level, endpoint, method, status_code, request_id, user_id, duration_ms, error_type, source_file, source_line

**Performance:**
- Query latency: < 1s for 1-hour window
- Retention: 30 days
- Compression: ~10:1 ratio

---

## 6. Capacity & Scaling

### 6.1 Current Capacity

**Hardware:** Hetzner CPX31 (4 vCPUs, 8 GB RAM, 160 GB SSD)

**Utilization:**
- CPU: 20-30% average, 60% peak
- Memory: 69% (5.5 GB/8 GB)
- Disk: 16% (25 GB/160 GB)
- Network: < 100 Mbit/s

### 6.2 Maximum Capacity (Current Hardware)

- HTTP Requests: 5-10 million/day (60-120 req/s sustained)
- Metrics: 50K active time series
- Logs: 5 GB/day
- Traces: 100K traces/day
- Concurrent users: 500-1000

### 6.3 Scaling Strategy

**Phase 1: Vertical Scaling**
- Upgrade to CPX51 (16 vCPUs, 32 GB RAM)
- Capacity: 3-4x increase

**Phase 2: Service Separation**
- License Server → AWS Lightsail (dedicated)
- AI Anomaly → GPU-accelerated VM
- Observability stack centralized

**Phase 3: Full Distribution**
- Console Backend: 3 replicas, auto-scaling
- License Server: 2 replicas, active-active
- AI Anomaly: 2 replicas with model sharing
- Prometheus: Federated (3 nodes)
- Loki: Distributed mode (3 nodes)
- PostgreSQL: Primary + 2 read replicas
- Redis: 3-node cluster

**Estimated Capacity (Phase 3):**
- 100+ million req/day (1200+ req/s)
- 500K+ active time series
- 50+ GB logs/day
- 10K+ concurrent users

---

## 7. Security Architecture

**Authentication:**
- JWT (console)
- API keys (license server)
- Basic auth (Grafana, Prometheus)

**Planned:**
- OAuth2/OIDC (Google, Azure AD)
- RBAC
- SSO

**Network:**
- Firewall rules (UFW/iptables)
- SSH key-only
- TLS/SSL (planned for external endpoints)

**Data:**
- Encrypted disk volumes (LUKS)
- PostgreSQL encryption support
- TLS for database connections

---

## 8. Backup & Disaster Recovery

**VM Snapshots:**
- Daily automated + manual on major changes
- Retention: 7 daily, 4 weekly, 3 monthly
- Size: ~26 GB per snapshot
- Restore time: 10-15 minutes

**Current Snapshots:**
1. RHINOMETRIC-STABLE-PASO2B (25.13 GB)
2. RHINOMETRIC-CORE-PASO4-OBSERVABILITY-COMPLETE (26 GB)
3. Latest: In progress

**Database:**
- Continuous: PostgreSQL WAL archiving
- Full backups: Daily at 02:00 UTC
- Retention: 30 days

**RTO:** 30 minutes  
**RPO:** 1 hour (snapshots), 5 minutes (WAL)

---

## 9. Service Level Objectives

**Console Backend:**
- Availability: 99.5% (target: 99.9%)
- Latency P95: < 500ms (target: < 300ms)
- Error rate: < 1% (target: < 0.5%)

**License Server:**
- Availability: 99.9% (business-critical)
- Latency P95: < 200ms
- Error rate: < 0.1%

**AI Anomaly:**
- Availability: 99%
- Inference latency P95: < 100ms
- False positive rate: < 20%

**Last 7 Days Performance:**
- Availability: 99.7%
- Total requests: 7 million
- Average response: 85ms
- Error rate: 0.05%

---

## 10. Development & Operations

### 10.1 Change Management Rules

1. Never modify Python code in production without testing
2. Always backup configuration files before changes
3. Validate syntax before restarting services
4. Restart only affected service, not entire stack
5. Git commit after every verified change
6. Document all changes in commit messages

### 10.2 Incident Response

**Severity Levels:**
- P0 (Critical): Platform down, < 15 min response
- P1 (High): Major feature broken, < 1 hour
- P2 (Medium): Degraded performance, < 4 hours
- P3 (Low): Minor issues, < 24 hours

---

## 11. Roadmap

**v1.1 - Intelligence Layer (Q1 2026)**
- Mark anomaly as false positive
- Feedback loop for AI improvement
- Model performance metrics dashboard

**v1.2 - Alert Management (Q2 2026)**
- Alertmanager integration
- Silence/Acknowledge alerts
- Alert states UI
- On-call scheduling

**v1.3 - Advanced Alerting (Q2 2026)**
- Create alert from anomaly (with validation)
- Alert rule templates
- Preview before deployment

**v1.4 - Reporting (Q3 2026)**
- PDF report generation
- Scheduled delivery
- Custom report builder

**v2.0 - Enterprise Features (Q4 2026)**
- Multi-tenancy
- RBAC with fine-grained permissions
- SSO/SAML
- High availability
- Geo-replication

---

## 12. Cost Analysis

**Current (Monthly):**
- Hetzner VM CPX31: €15
- Snapshots (3x26GB): €1.56
- AWS Lightsail: $5
- SMTP relay: €10
- **Total:** ~€34/month (~€408/year)

**10x Scale Projection:**
- 3x CPX51: €300
- Managed PostgreSQL: €150
- Load balancer: €50
- Monitoring (Grafana Cloud): €100
- **Total:** ~€600/month (~€7,200/year)

**100x Scale Projection:**
- Kubernetes cluster (10 nodes): €2,000
- Managed services: €1,000
- CDN + WAF: €500
- Support: €500
- **Total:** ~€4,000/month (~€48,000/year)

---

## 13. Technical Specifications Summary

**Platform:** Rhinometric v2.5.1  
**Containers:** 19 active  
**Languages:** Python 3.11, JavaScript (React)  
**Databases:** PostgreSQL 15, Redis 7  
**Observability:** Prometheus, Grafana, Loki, Jaeger, OpenTelemetry  
**Alerts:** 13+ active rules  
**Dashboards:** 7 (4 service-specific, 1 executive, 2 system)  
**Current Load:** 1M req/day, 6K time series, 500MB logs/day  
**Max Capacity (current):** 10M req/day, 50K time series, 5GB logs/day  
**Uptime:** 99.7% (last 7 days)  
**Response Time:** 85ms average  
**Error Rate:** 0.05%  

---

## 14. Contact & Support

**Technical Contact:**  
Email: rafael.canelon@rhinometric.com

**Documentation:**  
- Git: /opt/rhinometric/
- Dashboards: http://89.167.15.73:3000
- Metrics: http://89.167.15.73:9090
- Traces: http://89.167.15.73:16686

---

**Document Version:** 1.0  
**Classification:** Technical / Internal  
**Last Updated:** January 28, 2026  
**Next Review:** February 28, 2026
