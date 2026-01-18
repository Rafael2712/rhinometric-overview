# RHINOMETRIC Universal Connector Roadmap

**Vision:** "Connect to anything the client wants to monitor - 100% on-premise"

---

## 📊 Current Status (v2.4.0 - Messaging Extended)

### **✅ COMPLETED (8 connectors)**

| Category | Connectors | Status |
|----------|------------|--------|
| 🗄️ **Database** | PostgreSQL, Redis | ✅ Complete |
| 💬 **Messaging** | RabbitMQ, Kafka, MQTT | ✅ **NEW** |
| ☁️ **Cloud** | AWS CloudWatch, Azure Monitor | ✅ Complete |
| 🌐 **API** | Prometheus | ✅ Complete |

**Coverage:** ~60% of enterprise use cases

---

## 🎯 Phase F Completion Plan (Next 6 days)

### **Week 1 Remaining (2 days) - NoSQL + Time-series**

#### **Day 4-5: Add 3 NoSQL Connectors**

**1. MongoDB** (150 lines)
```python
# connectors/mongodb_connector.py
- Connection: mongodb://host:27017
- Metrics: collections, documents, storage size
- Operations: insert/query rate
- Auth: username/password or certificate
```

**2. Elasticsearch** (160 lines)
```python
# connectors/elasticsearch_connector.py
- Connection: http://host:9200
- Metrics: cluster health, indices, docs count
- Operations: index/search rate
- Auth: API key or basic auth
```

**3. InfluxDB** (140 lines)
```python
# connectors/influxdb_connector.py
- Connection: http://host:8086
- Metrics: buckets, measurements, series cardinality
- Operations: write/query rate
- Auth: token or username/password
```

**Total:** 450 lines backend + 60 lines frontend + 9 tests = **519 lines**  
**Time:** 2 days (including testing)

---

### **Week 2 Priority (after NoSQL) - HTTP Generic + Scripts**

#### **HTTP Generic Connector** (180 lines)
```python
# connectors/http_generic_connector.py
Features:
- Accept any HTTP/HTTPS endpoint
- Custom headers (Authorization, API keys, etc.)
- Auto-detect response format (JSON/XML/CSV/Plain text)
- Extract metrics from response body
- Support GET/POST methods
- Configurable timeout and retries

Example use cases:
✓ REST API monitoring
✓ Webhook testing
✓ Custom internal APIs
✓ Health check endpoints
```

**UI Fields:**
```yaml
- url: text (e.g., "https://api.example.com/health")
- method: select (GET, POST)
- headers: json ({"Authorization": "Bearer token"})
- timeout: number (default: 10)
- expected_status: number (default: 200)
- extract_metrics: json ({"response_time": "$.duration", "count": "$.total"})
```

---

#### **Custom Script Connector** (150 lines)
```python
# connectors/script_connector.py
Features:
- Execute local bash/python/powershell scripts
- Parse stdout for metrics
- Timeout and error handling
- Sandboxed execution (limited permissions)
- Environment variables support

Security:
✓ Script must exist in predefined directory
✓ No arbitrary code execution
✓ Read-only filesystem access
✓ Resource limits (CPU, memory, time)

Example use cases:
✓ Custom application monitoring
✓ Legacy system integration
✓ Proprietary protocol support
✓ Complex data aggregation
```

**UI Fields:**
```yaml
- script_path: select (dropdown of allowed scripts)
- arguments: text (space-separated)
- timeout: number (default: 30)
- parse_format: select (json, csv, key-value)
- metric_mapping: json ({"cpu_usage": "line[0]", "memory": "line[1]"})
```

---

## 🏭 Optional: Industrial/IoT (Week 3 if time permits)

### **Modbus Connector** (200 lines)
```python
# connectors/modbus_connector.py
Protocol: Modbus TCP/RTU
Use cases: PLCs, industrial sensors, SCADA systems
Metrics: register values, coil status, connection health
Libraries: pymodbus
```

### **OPC-UA Connector** (220 lines)
```python
# connectors/opcua_connector.py
Protocol: OPC Unified Architecture
Use cases: Industrial automation, manufacturing
Metrics: node values, subscriptions, server status
Libraries: asyncua
```

**Note:** Industrial connectors are lower priority (fewer clients need them immediately).

---

## 📈 Final Universal Connector Architecture

```
┌─────────────────────────────────────────────────────┐
│          RHINOMETRIC Universal Connector            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🗄️ DATABASES (5 connectors)                       │
│  ├─ PostgreSQL        ✅                            │
│  ├─ Redis             ✅                            │
│  ├─ MongoDB           🔜 Day 4                      │
│  ├─ Elasticsearch     🔜 Day 4                      │
│  └─ InfluxDB          🔜 Day 5                      │
│                                                     │
│  💬 MESSAGING (3 connectors)                       │
│  ├─ RabbitMQ          ✅                            │
│  ├─ Kafka             ✅                            │
│  └─ MQTT              ✅                            │
│                                                     │
│  ☁️ CLOUD (2 connectors)                            │
│  ├─ AWS CloudWatch    ✅                            │
│  └─ Azure Monitor     ✅                            │
│                                                     │
│  🌐 APIs (2 connectors)                            │
│  ├─ Prometheus        ✅                            │
│  └─ HTTP Generic      🔜 Week 2                    │
│                                                     │
│  🧩 CUSTOM (1 connector)                            │
│  └─ Script Executor   🔜 Week 2                    │
│                                                     │
│  ⚙️ INDUSTRIAL (2 connectors) - Optional           │
│  ├─ Modbus TCP/RTU    ⏸️ Week 3 (if needed)        │
│  └─ OPC-UA            ⏸️ Week 3 (if needed)        │
│                                                     │
├─────────────────────────────────────────────────────┤
│  TOTAL: 15+ connectors covering 95% of use cases   │
└─────────────────────────────────────────────────────┘
```

---

## 🎬 Demo Scenarios (Post-Implementation)

### **Scenario 1: Microservices Stack**
```
Client: E-commerce platform with microservices
Connect:
✓ PostgreSQL (orders database)
✓ Redis (session cache)
✓ RabbitMQ (message queue)
✓ Elasticsearch (product search)
✓ HTTP Generic (custom payment API)
```

### **Scenario 2: Financial Services**
```
Client: Trading platform
Connect:
✓ InfluxDB (tick data)
✓ Kafka (market events)
✓ MongoDB (user profiles)
✓ HTTP Generic (exchange APIs)
✓ Custom Script (legacy COBOL system)
```

### **Scenario 3: Manufacturing**
```
Client: Factory automation
Connect:
✓ Modbus (PLCs)
✓ OPC-UA (SCADA)
✓ InfluxDB (sensor data)
✓ MQTT (IoT devices)
✓ PostgreSQL (production logs)
```

---

## ⏱️ Timeline Summary

| Week | Days | Focus | Deliverables |
|------|------|-------|--------------|
| **1** | 1-3 | Messaging Extended | ✅ RabbitMQ, Kafka, MQTT |
| **1** | 4-5 | NoSQL + Time-series | 🔜 MongoDB, Elasticsearch, InfluxDB |
| **2** | 1-2 | HTTP + Scripts | 🔜 Generic HTTP, Script executor |
| **2** | 3-5 | Dashboard Builder | Backend + Frontend |
| **3** | 1-3 | RBAC | User management + Audit |
| **3** | 4-5 | VeriVerde ESG | APIs + Dashboard |
| **4** | 1-5 | Reports + Testing | PDF generation + E2E tests |

---

## 🚀 Go/No-Go Decision Points

### **Option A: Complete Universal Connector First (Recommended)**
```
✅ Pros:
- Product differentiation ("connect to anything")
- Strong demo for sales
- Extensible architecture
- Future-proof

❌ Cons:
- Delays Dashboard Builder by 2 days
- More testing required
```

### **Option B: Prioritize Dashboard Builder**
```
✅ Pros:
- Complete end-to-end workflow faster
- Visual appeal for demos
- Business value visible

❌ Cons:
- Limited connectors (only 8)
- May need to add connectors later
- Potential rework
```

---

## 💡 Recommendation

**Proceed with Option A:**
1. Complete NoSQL connectors (2 days)
2. Add HTTP Generic + Scripts (2 days during Week 2)
3. Then focus on Dashboard Builder

**Rationale:**
- Messaging Extended proved architecture is solid
- Adding connectors is fast (~150 lines each)
- "Universal" is strong marketing message
- Clients expect comprehensive monitoring

---

## 📝 Next Immediate Action

**Command:**
```bash
# 1. Review current implementation
cat MESSAGING_EXTENDED_REPORT.md

# 2. Test messaging connectors
./tests/run-messaging-tests.sh

# 3. Decide on NoSQL implementation
# If YES → proceed with MongoDB connector
# If NO → move to Dashboard Builder

# 4. Update Dockerfile to include new dependencies
vim api-connector/Dockerfile
```

---

**Status:** ✅ Messaging Extended Complete - Ready for NoSQL  
**Decision Required:** Add NoSQL now OR proceed to Dashboard Builder?

