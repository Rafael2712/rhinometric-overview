# 📊 DEMO SERVICES - Rhinometric v2.5.0

## Overview

This Rhinometric installation includes **23 demo collector services** to demonstrate monitoring capabilities. These services are **examples only** and should be disabled in production client deployments.

---

## 🎯 Purpose

Demo services showcase Rhinometric's ability to monitor:
- ✅ **REST APIs** (public and authenticated)
- ✅ **Webhook events** (GitHub, generic webhooks)
- ✅ **Database metrics** (PostgreSQL sessions, queries, locks)
- ✅ **Container health** (Docker containers, resource usage)

---

## 📋 Demo Services List

### **REST API Collectors** (External Public APIs)

These collectors demonstrate REST API monitoring by calling public APIs:

| Service | API Source | Purpose | Metrics Collected |
|---------|-----------|---------|-------------------|
| `rest-collector-coingecko-crypto` | CoinGecko | Cryptocurrency market data | Bitcoin/Ethereum prices, volume |
| `rest-collector-catfacts` | Cat Facts API | Random cat facts | API response time, success rate |
| `rest-collector-dog-images` | Dog Images API | Random dog images | API latency, payload size |
| `rest-collector-random-activity` | Bored API | Activity suggestions | Request duration, availability |
| `rest-collector-jsonplaceholder-posts` | JSONPlaceholder | Sample post data | CRUD operation metrics |
| `rest-collector-jsonplaceholder-users` | JSONPlaceholder | Sample user data | Query performance |
| `rest-collector-public-rest-api-for-testing` | Public Test APIs | Generic REST testing | HTTP status codes |

### **Webhook Collectors**

| Service | Webhook Type | Purpose |
|---------|-------------|---------|
| `webhook-collector-github-production` | GitHub Events | Demonstrates webhook event collection (push, PR, issues) |

### **Database Collectors** (PostgreSQL Monitoring)

These demonstrate database observability using a test PostgreSQL instance:

| Service | Metrics | Purpose |
|---------|---------|---------|
| `database-collector-rhinometric-postgres-sessions` | Active sessions | Connection pool monitoring |
| `database-collector-rhinometric-postgres-queries` | Query performance | Slow query detection |
| `database-collector-rhinometric-postgres-locks` | Lock contention | Deadlock analysis |
| `database-collector-rhinometric-postgres-transactions` | Transaction stats | Commit/rollback rates |
| `database-collector-rhinometric-postgres-size` | Database size | Growth tracking |
| `database-collector-rhinometric-postgres-tables` | Table statistics | Index usage, bloat |
| `database-collector-rhinometric-postgres-replica-lag` | Replication lag | HA monitoring |

---

## 🏷️ Identification

All demo services are labeled with:
```yaml
labels:
  rhinometric_scope: "demo"
```

This allows filtering in:
- **Prometheus queries**: `up{rhinometric_scope="demo"}`
- **Grafana dashboards**: Template variables
- **Backend KPIs**: Separate demo count from production services

---

## 🚀 For Production Deployments

### **Option A: Disable Demo Services**

Comment out or remove demo services from `docker-compose-v2.5.0.yml`:

```yaml
# Comment these sections:
# services:
#   rest-collector-coingecko-crypto:
#   rest-collector-catfacts:
#   rest-collector-dog-images:
#   ...
```

### **Option B: Replace with Client Services**

Replace demo collectors with client-specific collectors:

```yaml
services:
  rest-collector-client-api:
    build: ./rest-collector-client-api
    container_name: rhinometric-rest-collector-client-api
    environment:
      API_URL: https://api.client-production.com
      API_TOKEN: ${CLIENT_API_TOKEN}
    labels:
      rhinometric_scope: "production"  # Change from "demo"
```

### **Option C: Keep for Testing**

If keeping demo services for reference:
1. Ensure `rhinometric_scope="demo"` label is present
2. Document in client onboarding that these are examples
3. Show "Demo Environment" badge in UI (implemented in Home page)

---

## 📊 Metrics Impact

Demo services generate approximately:
- **~50,000 metrics** in Prometheus (timeseries)
- **~10 MB/day** of log data in Loki
- **~5 traces/minute** in Jaeger

For production, disable demos to reduce:
- ✅ Prometheus storage (reduces TSDB size by ~30%)
- ✅ Loki storage (reduces log volume)
- ✅ Network traffic (no external API calls)

---

## 🔍 Verification

Check if demo services are running:

```bash
# List demo services
docker ps --filter "label=rhinometric_scope=demo"

# Count demo services in Prometheus
curl -s "http://localhost:9090/api/v1/query?query=count(up{rhinometric_scope=\"demo\"})" | jq '.data.result[0].value[1]'
```

Expected output: `"23"` if all demos are running.

---

## 📝 Notes for Clients

**What you see in this demo**:
- 23 example services monitoring public APIs and databases
- Real metrics collection (not mock data)
- Demonstration of Rhinometric's collector capabilities

**What you should do**:
- Replace demo collectors with your own infrastructure
- Use the same patterns (REST, Webhook, Database collectors)
- Maintain the `rhinometric_scope` label for proper categorization

---

**Last Updated**: December 2, 2025  
**Rhinometric Version**: 2.5.0
