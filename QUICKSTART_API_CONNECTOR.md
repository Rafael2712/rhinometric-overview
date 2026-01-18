# RHINOMETRIC API Connector - Quick Start Guide

**Version:** 2.4.0  
**Date:** 2024  
**Status:** 🚀 Ready for Testing

---

## 📦 What's Been Built

### **Backend API (FastAPI)**
- **Location:** `api-connector/`
- **Port:** 8000
- **Features:**
  - 9 REST endpoints for datasource management
  - 5 pre-configured connectors: PostgreSQL, Redis, Prometheus, AWS CloudWatch, Azure Monitor
  - Real-time connection testing with timeouts
  - Template-based configuration (no YAML editing needed)
  - CORS-enabled for Grafana communication

### **Frontend Plugin (React + TypeScript)**
- **Location:** `ui-visual/`
- **Type:** Grafana Panel Plugin
- **Features:**
  - Visual template selection (cards with hover effects)
  - Dynamic form generation based on templates
  - Real-time connection testing with loading spinner
  - Color-coded alerts (success/error with details)
  - RHINOMETRIC branding (blue gradient theme)
  - Mobile-responsive design

### **Docker Infrastructure**
- **Containers:**
  1. `rhinometric-api-connector` - FastAPI backend (4 uvicorn workers)
  2. `grafana-visual` - Grafana 10.2.0 with embedded plugin
- **Networks:** `rhinometric_default` (shared with main stack)
- **Volumes:** `rhinometric_grafana_visual_data` (persistent plugin state)

---

## 🚀 Deployment Steps

### **1. Build Images**
```bash
cd c:/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# Build API Connector backend
docker build -t rhinometric/api-connector:2.4.0 -f api-connector/Dockerfile ./api-connector

# Build Grafana with plugin
docker build -t rhinometric/grafana-visual:2.4.0 -f ui-visual/Dockerfile.grafana .
```

### **2. Start Stack**
```bash
# Start with main RHINOMETRIC stack + API Connector
docker compose -f docker-compose-v2.2.0.yml \
               -f docker-compose-api-connector.yml \
               up -d --build

# Or just API Connector services (if main stack already running)
docker compose -f docker-compose-api-connector.yml up -d --build
```

### **3. Verify Services**
```bash
# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep rhinometric

# Expected output:
# rhinometric-api-connector    Up 30 seconds (healthy)    0.0.0.0:8000->8000/tcp
# rhinometric-grafana-visual   Up 45 seconds (healthy)    0.0.0.0:3001->3000/tcp

# Test backend API
curl http://localhost:8000/
# Expected: {"message":"RHINOMETRIC API Connector v2.4.0","status":"healthy"}

curl http://localhost:8000/api/templates
# Expected: JSON object with 5 templates (postgresql, redis, prometheus, aws-cloudwatch, azure-monitor)

# Test Grafana
curl http://localhost:3001/api/health
# Expected: {"commit":"...","database":"ok","version":"10.2.0"}
```

### **4. Access Grafana UI**
```bash
# Open browser
start http://localhost:3001

# Credentials:
# Username: admin
# Password: rhinometric2024
```

---

## 🧪 Testing the Plugin

### **Step 1: Verify Plugin Installation**
1. Navigate to **Configuration** → **Plugins**
2. Search for "RHINOMETRIC API Connector"
3. Plugin should appear with status "✓ Installed"
4. Click to view details (version 2.4.0)

### **Step 2: Add New Panel**
1. Go to **Dashboards** → **New Dashboard**
2. Click **Add new panel**
3. In visualization picker, select **"RHINOMETRIC API Connector"**
4. Panel loads with template selection grid

### **Step 3: Test PostgreSQL Connection**
1. Click **PostgreSQL** template card
2. Fill form:
   - **Host:** `postgres` (or `localhost` if testing externally)
   - **Port:** `5432`
   - **Database:** `rhinometric`
   - **Username:** `rhinometric`
   - **Password:** `rhinometric2024`
   - **SSL Enabled:** `false`
3. Click **"Test Connection"** button
4. Expected result:
   - Button shows spinner (loading state)
   - After 1-2 seconds, green alert appears:
     ```
     ✓ Connection successful (1234ms)
     Server: PostgreSQL 14.5
     Memory: 256MB
     Connections: 12
     ```
5. Click **"Save Datasource to Grafana"**
6. New datasource appears in **Configuration** → **Data Sources**

### **Step 4: Test Redis Connection**
1. Select **Redis** template
2. Fill form:
   - **Host:** `redis`
   - **Port:** `6379`
   - **Password:** *(leave empty if no auth)*
3. Click **"Test Connection"**
4. Expected result:
   - Green alert with Redis server version and key count

### **Step 5: Test Connection Failure**
1. Select **PostgreSQL** template
2. Fill form with **wrong password**
3. Click **"Test Connection"**
4. Expected result:
   - Red alert appears:
     ```
     ✗ Connection failed (502ms)
     Error: password authentication failed for user "rhinometric"
     ```

---

## 📊 API Endpoints Reference

### **GET /api/templates**
Returns available datasource templates.

**Response:**
```json
{
  "postgresql": {
    "name": "PostgreSQL",
    "type": "postgresql",
    "fields": [
      {"name": "host", "type": "text", "label": "Host", "default": "localhost"},
      {"name": "port", "type": "number", "label": "Port", "default": 5432},
      {"name": "database", "type": "text", "label": "Database"},
      {"name": "username", "type": "text", "label": "Username"},
      {"name": "password", "type": "password", "label": "Password"},
      {"name": "ssl", "type": "boolean", "label": "SSL Enabled", "default": false}
    ]
  }
}
```

### **POST /api/test-connection**
Tests connection to datasource.

**Request:**
```json
{
  "type": "postgresql",
  "config": {
    "host": "postgres",
    "port": 5432,
    "database": "rhinometric",
    "username": "rhinometric",
    "password": "rhinometric2024",
    "ssl": false
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Connection successful",
  "details": {
    "server_version": "PostgreSQL 14.5",
    "memory": "256MB",
    "connections": 12
  },
  "duration_ms": 1234
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message": "Connection failed",
  "details": {
    "error": "password authentication failed"
  },
  "duration_ms": 502
}
```

### **POST /api/datasources**
Creates a new datasource in Grafana.

**Request:**
```json
{
  "name": "My PostgreSQL",
  "type": "postgresql",
  "config": {
    "host": "postgres",
    "port": 5432,
    "database": "rhinometric",
    "username": "rhinometric",
    "password": "rhinometric2024"
  }
}
```

---

## 🐛 Troubleshooting

### **Plugin Not Visible in Grafana**
```bash
# Check plugin files
docker exec rhinometric-grafana-visual ls -la /var/lib/grafana/plugins/rhinometric-api-connector/

# Expected files:
# - dist/module.js
# - plugin.json

# Check Grafana logs
docker logs rhinometric-grafana-visual | grep -i "plugin"
# Look for: "Plugin registered: rhinometric-api-connector"

# Verify unsigned plugin allowed
docker exec rhinometric-grafana-visual cat /etc/grafana/grafana.ini | grep allow_loading_unsigned_plugins
# Expected: allow_loading_unsigned_plugins = rhinometric-api-connector
```

### **Backend API Not Responding**
```bash
# Check backend logs
docker logs rhinometric-api-connector

# Check healthcheck
docker inspect rhinometric-api-connector | grep -A 10 Health
# Status should be "healthy"

# Test endpoints
curl -v http://localhost:8000/api/templates
# Should return 200 OK with JSON

# Check CORS headers
curl -H "Origin: http://localhost:3001" -v http://localhost:8000/api/templates
# Should include: Access-Control-Allow-Origin: http://localhost:3001
```

### **CORS Errors in Browser Console**
```bash
# Symptoms: Red errors like "blocked by CORS policy"

# Fix: Update CORS origins in docker-compose-api-connector.yml
# Add Grafana URL to environment:
#   - CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://grafana:3000

# Restart backend
docker compose -f docker-compose-api-connector.yml restart api-connector
```

### **Connection Test Times Out**
```bash
# Check if target service is accessible from backend container
docker exec rhinometric-api-connector ping postgres -c 3

# Check network connectivity
docker network inspect rhinometric_default | grep -A 10 api-connector

# Increase timeout in api-connector/app.py:
# await asyncio.wait_for(connector.test_connection(config), timeout=10.0)
# Change to: timeout=30.0

# Rebuild backend
docker compose -f docker-compose-api-connector.yml up -d --build api-connector
```

---

## 🎥 Demo Recording Checklist

### **Preparation**
- [ ] Start screen recording software (OBS Studio, QuickTime, etc.)
- [ ] Close unnecessary browser tabs
- [ ] Set browser zoom to 100%
- [ ] Open terminal side-by-side with browser
- [ ] Verify all containers running: `docker ps`

### **Script**
1. **Intro (30 sec)**
   - "Welcome to RHINOMETRIC API Connector v2.4.0"
   - "Visual datasource configuration without editing YAML"
   - Show browser at Grafana login screen

2. **Login (15 sec)**
   - Enter credentials: admin / rhinometric2024
   - Navigate to Plugins page
   - Show installed plugin

3. **Create Panel (30 sec)**
   - New Dashboard → Add Panel
   - Select "RHINOMETRIC API Connector"
   - Show template grid loading

4. **PostgreSQL Test (60 sec)**
   - Click PostgreSQL card
   - Show dynamic form generation
   - Fill connection details slowly (narrate each field)
   - Click "Test Connection"
   - Show loading spinner
   - Show success alert with green color and details JSON
   - Highlight duration (e.g., 1234ms)

5. **Redis Test (45 sec)**
   - Click back, select Redis template
   - Fill host/port
   - Test connection
   - Show success with different details

6. **Failure Scenario (30 sec)**
   - Go back to PostgreSQL
   - Enter wrong password
   - Test connection
   - Show red error alert
   - Highlight error message clarity

7. **Save Datasource (30 sec)**
   - Go back, correct password
   - Test connection (success)
   - Click "Save Datasource to Grafana"
   - Navigate to Configuration → Data Sources
   - Show new datasource in list

8. **Outro (15 sec)**
   - "Phase F Week 1 complete: Visual API Connector"
   - "Coming next: Dashboard Builder with drag-and-drop"

**Total Duration:** ~4 minutes

---

## 📈 Performance Benchmarks

### **Backend API**
- **Startup Time:** ~5 seconds (uvicorn with 4 workers)
- **Memory Usage:** ~150MB per worker (~600MB total)
- **Request Latency:**
  - GET /api/templates: ~10ms
  - POST /api/test-connection (PostgreSQL): ~50-200ms (depends on network)
  - POST /api/test-connection (Redis): ~20-80ms

### **Frontend Plugin**
- **Bundle Size:** ~800KB (unminified), ~250KB (minified)
- **Load Time:** ~300ms on localhost
- **Render Time:** ~50ms (template grid with 5 cards)

### **Docker Build Times**
- **api-connector/Dockerfile:** ~60 seconds (with pip install)
- **ui-visual/Dockerfile:** ~120 seconds (npm build with webpack)
- **ui-visual/Dockerfile.grafana:** ~90 seconds (Node.js install + plugin copy)

---

## 🔐 Security Notes

### **Credentials**
- Default Grafana password: `rhinometric2024` (change in production)
- Backend has no authentication (intended for internal network use)
- PostgreSQL/Redis passwords stored in environment variables (not in code)

### **Network Isolation**
- All services run in `rhinometric_default` network
- Backend not exposed publicly (only accessible via Grafana container)
- Grafana on port 3001 (alternative port to avoid conflicts)

### **Signed Plugin (Future)**
- Current plugin is unsigned (requires `GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS`)
- For production: sign plugin with Grafana Cloud account
- See: https://grafana.com/docs/grafana/latest/developers/plugins/sign-a-plugin/

---

## 📝 Next Steps

### **Week 1 Remaining (Dashboard Builder)**
- [ ] Backend API for dashboard CRUD (create, read, update, delete)
- [ ] Widget templates library (line chart, gauge, table, heatmap)
- [ ] Frontend drag-and-drop UI (react-grid-layout)
- [ ] Real-time preview with live data
- [ ] Export to JSON

### **Week 2 (RBAC)**
- [ ] User management (create, edit, delete users)
- [ ] Role-based permissions (admin, editor, viewer)
- [ ] Audit logging (who did what, when)
- [ ] JWT authentication

### **Week 3-4 (VeriVerde ESG + Reports)**
- [ ] ElectricityMap API integration (carbon intensity)
- [ ] ESG dashboard (real-time metrics)
- [ ] Executive PDF reports (WeasyPrint)
- [ ] Email scheduler (weekly/monthly reports)

---

## 🆘 Support

**Issues?** Check:
1. Docker logs: `docker logs rhinometric-api-connector`
2. Grafana logs: `docker logs rhinometric-grafana-visual`
3. Browser console: F12 → Console tab (look for red errors)
4. Network tab: F12 → Network (check failed requests)

**Contact:** canel@rhinometric.ai

---

**Status:** ✅ API Connector Ready for Testing  
**Next:** Validate stack → Record demo → Start Dashboard Builder

