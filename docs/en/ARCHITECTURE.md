#  Rhinometric - Technical Architecture

**Version:** 2.5.1 | **Date:** December 2025

## High-Level Architecture

\\\

                    USER (Browser/API Client)                     

                             
                
                  Rhinometric Console    
                  (React + FastAPI)      
                  Port: 3002             
                
                             
        
                                                
    
  Prometheus            Loki              Jaeger     
  (Metrics)            (Logs)            (Traces)    
  Port: 9090         Port: 3100        Port: 16686   
    
                                                

            AI Anomaly Engine (Python ML)                  
            Alertmanager (Alert Routing)                   

\\\

## Component Details

### **Console (Frontend + Backend)**
- **Frontend:** React 18 + TypeScript + TailwindCSS
- **Backend:** FastAPI (Python 3.11) + uvicorn
- **Database:** PostgreSQL 15 (user auth, settings)
- **Cache:** Redis 7 (session management)
- **Ports:** 3002 (HTTP), 3001 (API internal)

### **Prometheus** (Time-Series Database)
- **Storage:** Local disk (retention: 15 days)
- **Scrape Targets:** 13 default (self, node-exporter, postgres-exporter, etc.)
- **Query Performance:** <100ms for 24h range queries
- **HA Mode:** Not configured (single instance)

### **Loki** (Log Aggregation)
- **Storage:** Filesystem (retention: 7 days)
- **Ingestion:** Promtail (Docker logs + /var/log)
- **Index:** Label-based (no full-text indexing)
- **Query Performance:** <500ms for 1h log queries

### **Jaeger** (Distributed Tracing)
- **Storage:** In-memory (production: use Cassandra/Elasticsearch)
- **Protocol:** OTLP (OpenTelemetry)
- **Sampling:** 100% (production: use probabilistic sampling)

### **AI Anomaly Engine**
- **Models:** Isolation Forest (anomaly detection), LSTM (time-series prediction)
- **Training:** 7-day baseline, retrained daily
- **Detection:** Every 5 minutes
- **Metrics Monitored:** 50+ system metrics (CPU, RAM, network, disk)

## Data Flows

### **Metrics Flow**
1. Exporters (node-exporter, cAdvisor) expose metrics on /metrics
2. Prometheus scrapes every 15 seconds
3. Console queries Prometheus /api/v1/query every 30 seconds
4. AI Engine fetches historical data every 5 minutes

### **Logs Flow**
1. Docker containers write to stdout/stderr
2. Promtail tails Docker logs
3. Promtail ships to Loki /loki/api/v1/push
4. Console queries Loki /loki/api/v1/query_range

### **Traces Flow**
1. Instrumented apps send OTLP traces to Jaeger :4317
2. Jaeger stores in memory (or Cassandra)
3. Console embeds Jaeger UI via iframe

## Ports Reference

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Console Frontend | 3002 | 3002 | HTTP |
| Console Backend | 3001 | - | HTTP (internal) |
| Prometheus | 9090 | 9090 | HTTP |
| Grafana | 3000 | 3000 | HTTP |
| Loki | 3100 | 3100 | HTTP |
| Jaeger UI | 16686 | 16686 | HTTP |
| Jaeger OTLP | 4317 | 4317 | gRPC |
| Alertmanager | 9093 | 9093 | HTTP |
| PostgreSQL | 5432 | - | TCP (internal) |
| Redis | 6379 | - | TCP (internal) |
| Node Exporter | 9100 | - | HTTP (internal) |
| cAdvisor | 8080 | - | HTTP (internal) |

## Hardware Requirements

### **Small Deployment (10-50 hosts)**
- **CPU:** 4 vCPU
- **RAM:** 8 GB
- **Disk:** 50 GB SSD
- **Network:** 100 Mbps

### **Medium Deployment (50-200 hosts)**
- **CPU:** 8 vCPU
- **RAM:** 16 GB
- **Disk:** 200 GB SSD
- **Network:** 1 Gbps

### **Large Deployment (200+ hosts)**
- **CPU:** 16+ vCPU
- **RAM:** 32+ GB
- **Disk:** 500 GB+ SSD (NVMe preferred)
- **Network:** 1 Gbps+
- **HA:** Multi-node Prometheus federation

## Security

### **Authentication**
- Console: Username/password (bcrypt hashed)
- Grafana: Separate admin credentials
- Prometheus/Loki/Jaeger: No auth (protected by firewall)

### **Network**
- Internal Docker network (\hinometric-net\)
- External ports exposed only for Console, Prometheus, Grafana

### **Data Privacy**
- All data stored locally (no external transmission)
- Logs/metrics never leave infrastructure
- Optional: Encrypt volumes at rest

## Scalability Considerations

### **Current Limits (v2.5.1)**
- Max hosts: ~200 (single Prometheus instance)
- Max log ingestion: 10 GB/day
- Max trace volume: 1,000 spans/second

### **Future Scaling (Roadmap)**
- Prometheus federation (multiple instances)
- Loki with S3/GCS backend
- Jaeger with Cassandra/Elasticsearch
- Horizontal scaling with Kubernetes

---

For detailed installation instructions, see [INSTALLATION.md](./INSTALLATION.md).

** 2025 Rhinometric**
