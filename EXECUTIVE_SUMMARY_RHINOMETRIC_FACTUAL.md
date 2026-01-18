# RHINOMETRIC v2.5.0 "Rhino Radar"  
## Executive Summary for Leads and Partners

**Date:** December 17, 2025  
**Version:** 2.5.0  
**Status:** Production Operational

---

## What is Rhinometric?

Rhinometric is an **on-premise observability platform** that enables monitoring of complete IT infrastructures while keeping all data within the client's facilities. Unlike cloud solutions such as Datadog or New Relic, Rhinometric allows maintaining all data within the client's infrastructure, facilitating **data sovereignty** and regulatory compliance (e.g., GDPR).

---

## Problems It Solves

### 1. Lack of Operational Visibility
- Real-time metrics from servers, containers, and applications
- 15+ pre-loaded dashboards for immediate analysis
- Centralized logs from all services
- Distributed traces with Jaeger

### 2. Cloud Provider Dependency
- Positions itself as an on-premise alternative to major SaaS observability solutions (Datadog, New Relic, Splunk), for organizations that cannot or do not want to send their data externally
- Licensing model based on number of hosts, without variable charges per data volume ingested
- Complete control of information (GDPR, ENS, sensitive data)

### 3. Deployment Complexity
- 3 distribution formats:
  - **Demo OVA:** Virtual machine ready in 5 minutes (4-hour trial)
  - **Trial Installer:** Automated Linux script (14 days, up to 5 hosts)
  - **Annual License:** Complete production (1 year, configurable hosts)

### 4. Lack of Proactive Detection
- Anomaly detection engine based on AI models (Prophet + IsolationForest), already available in the platform with improvements planned in the roadmap
- Alert foundation with Prometheus (Alertmanager integration in roadmap)
- License monitoring with advance expiration notice

---

## Technology Stack (Verified)

Based on `docker-compose-v2.5.0.yml`:

### Storage
- **PostgreSQL 15.10:** License and configuration database
- **Redis 7.2:** Session cache and rate limiting

### Observability
- **Prometheus 2.53.0:** Metrics (30-day retention)
- **Loki 3.0.0:** Centralized logs
- **Jaeger (all-in-one):** Distributed traces
- **Grafana 10.4.0:** Visualization and dashboards

### Telemetry Collection
- **OpenTelemetry Collector 0.91.0:** Standard trace/metric ingestion
- **cAdvisor:** Docker container metrics
- **Node Exporter:** Operating system metrics

### Application
- **License Server v2:** FastAPI (migrated from Flask, 10x performance improvement)
- **Console v3:** Vue.js + FastAPI web interface
- **AI Anomaly Engine:** Predictive detection with Python

---

## Target Audience

### Ideal Sectors
- **Public Sector:** Government agencies requiring on-premise data (ENS)
- **Healthcare:** Hospitals with sensitive medical data (LOPD)
- **Banking:** Strict regulatory compliance
- **SMEs:** Companies seeking an economical alternative to SaaS
- **MSPs:** Managed service providers reselling monitoring

### Client Profile
- 10-200 monitored hosts
- Hybrid infrastructure (on-premise + cloud)
- Regulatory compliance requirements
- Preference for complete data control

---

## Distribution Models

According to `RELEASE_NOTES.md` v2.5.0:

### 1. Demo Cloud (4 hours)
- **Format:** OVA file (virtual machine)
- **Compatibility:** VirtualBox, VMware
- **Content:** Complete pre-configured stack
- **Use:** Quick tests, commercial demos
- **Limitations:** 4 hours of use, then expires

### 2. Trial Installer (14 days)
- **Format:** Linux installation script
- **Platforms:** Ubuntu, Debian, CentOS, RHEL
- **Hosts:** Up to 5 hosts
- **Content:** Complete installation with Docker Compose
- **Limitations:** 14 days, then expires

### 3. Annual License (1 year)
- **Format:** Installer + .lic file
- **Hosts:** Configurable (no technical limit)
- **Duration:** 1 year renewable
- **Support:** Email included
- **Updates:** Included during validity

---

## Technical Capabilities (Documented)

### Data Collection
- System metrics (CPU, RAM, disk, network)
- Application metrics (HTTP, response time, errors)
- Docker container logs
- Distributed transaction traces

### Available Dashboards
According to configuration files:
- System overview
- Docker Containers
- Prometheus Metrics
- Loki Logs Explorer
- Jaeger Traces
- (15+ dashboards total - exact number in Grafana files)

### Integrations
- Docker (native)
- Kubernetes (documented as roadmap)
- REST APIs (via OpenTelemetry)
- Prometheus exporters (Node, cAdvisor, Blackbox, PostgreSQL)

---

## Hardware Requirements

Based on `docker-compose-v2.5.0.yml` configuration:

### Minimum (Trial - 5 hosts)
- **CPU:** 2 vCPUs
- **RAM:** 4 GB
- **Disk:** 20 GB SSD

### Recommended (30 hosts)
- **CPU:** 4 vCPUs
- **RAM:** 8 GB
- **Disk:** 50 GB SSD

### Production (100+ hosts)
- **CPU:** 8 vCPUs
- **RAM:** 16 GB
- **Disk:** 100 GB SSD (collected data grows over time)

*Note: Approximate numbers based on memory limit configuration in docker-compose.*

---

## Competitive Advantages

### 1. Complete On-Premise
- No data sent to third parties
- Facilitates GDPR compliance by preventing data from leaving to third-party cloud providers, provided the client configures their environment according to applicable regulations
- Ideal for regulated sectors

### 2. Open-Source Stack
- Based on Prometheus, Grafana, Loki (CNCF projects)
- No vendor lock-in
- Active community

### 3. Simplified Deployment
- Automated installation in 10 minutes
- Docker Compose (no Kubernetes required)
- Pre-loaded dashboards (ready to use)

### 4. Anomaly Detection
- Local AI engine (not cloud)
- Prophet + IsolationForest algorithms
- Predictions without data leaving

### 5. Flexible Licensing System
- Free demo (4h) for testing
- 14-day trial without commitment
- Annual license with simple renewal

---

## Known Limitations

### Current Capacity
- Currently the platform is used in real test environments and internal deployments
- Designed to grow with the client from small scenarios (10-30 hosts) to larger infrastructures, adjusting hardware sizing according to needs

### Pending Features
According to `PENDIENTES_DESARROLLO_RHINOMETRIC.md`:

**High Priority (next 3 months):**
- Integrated billing system (Stripe)
- Self-service client portal
- Automatic expiration notifications
- Documented public API

**Medium Priority (6 months):**
- Multi-region (EU datacenter)
- Mobile app (iOS/Android)
- Native Kubernetes monitoring

**Low Priority (12+ months):**
- White-label for partners
- Enterprise SSO (SAML, OAuth)
- Complete multi-tenancy

---

## Real Use Cases

*Note: No documented client use cases are available in the repository. This section will be completed when verifiable references exist.*

---

## Support and Documentation

### Support Channels
- Email: rafael.canelon@rhinometric.com (verified in SMTP configuration)
- Technical documentation: Markdown files in `/docs/v2.5.0/`

### Available Documentation
According to file structure:
- Installation guide (EN/ES)
- User manual (EN/ES)
- Deployment guide
- Download endpoints
- Email testing
- Publishing guide

---

## Contact Information

**Company:** Rhinometric  
**Commercial Email:** rafael.canelon@rhinometric.com  
**SMTP Server:** smtp.zoho.eu:465 (verified in configuration)  
**License Server:** licensing.rhinometric.com:5000 (according to deployment documentation)

---

## Next Steps

### For Interested Leads
1. Request demo OVA (4-hour trial)
2. Install on local VirtualBox/VMware
3. Explore pre-loaded dashboards
4. If viable, request 14-day trial

### For Potential Partners
1. Initial contact by email
2. Technical meeting (architecture, capabilities)
3. 30-day proof of concept (POC)
4. Evaluation of distribution/resale model

---

**Document generated from verifiable repository files.**  
**Last update:** December 17, 2025  
**Document version:** 1.0
