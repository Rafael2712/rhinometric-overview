# RHINOMETRIC v2.4.0 - Grafana App Plugins Integration

## 🎯 Overview

This release includes **two native Grafana App Plugins** with full Rhinometric branding:

1. **Dashboard Builder** - Visual dashboard creation tool
2. **API Connector** - Visual API/datasource configuration interface

Both plugins are **integrated inside Grafana** for a unified user experience.

---

## 📦 Plugin Structure

```
grafana-plugins/
├── rhinometric-dashboard-builder/
│   ├── plugin.json           # Plugin manifest
│   ├── package.json          # Dependencies
│   ├── tsconfig.json         # TypeScript config
│   └── src/
│       ├── module.tsx        # Plugin entry point
│       └── components/
│           └── DashboardBuilderPage.tsx  # Main UI
│
└── rhinometric-api-connector/
    ├── plugin.json
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── module.tsx
        └── components/
            └── APIConnectorPage.tsx      # Main UI
```

---

## 🎨 Branding Assets

```
grafana-branding/
├── img/
│   ├── rhinometric_logo.svg     # Main logo
│   └── rhinometric_icon.svg     # Favicon
└── apply-branding.sh            # Branding application script
```

The branding script replaces:
- Grafana logo with Rhinometric logo
- Page titles and metadata
- Favicon
- Custom CSS for colors and styling

---

## 🚀 Installation

### Step 1: Build Plugins

```bash
# Make build script executable
chmod +x build-plugins.sh

# Build both plugins
./build-plugins.sh
```

This will:
1. Install npm dependencies for both plugins
2. Build with `grafana-toolkit`
3. Generate `dist/` folders with compiled plugins

### Step 2: Restart Grafana

```bash
# Restart Grafana to load plugins
docker compose -f docker-compose-v2.2.0.yml restart grafana

# Wait 30 seconds for Grafana to initialize
sleep 30
```

### Step 3: Verify Installation

```bash
# Check Grafana logs for plugin loading
docker logs rhinometric-grafana | grep -i "rhinometric"
```

You should see:
```
Registering plugin: rhinometric-dashboard-builder
Registering plugin: rhinometric-api-connector
```

---

## 🎯 Accessing the Plugins

### From Grafana UI:

1. **Login to Grafana**: http://localhost:80
   - Username: `admin`
   - Password: `admin_secure_2024` (from `.env`)

2. **Navigate to Apps**:
   - Click hamburger menu (☰) in top-left
   - Go to **"Apps"** section
   - You'll see:
     - 🔨 **Rhinometric Dashboard Builder**
     - 🔌 **Rhinometric API Connector**

3. **Open Plugins**:
   - Click on either plugin
   - The plugin page will load with full Rhinometric branding

---

## 🔨 Dashboard Builder Features

### Visual Dashboard Creation
- **Drag & Drop Panels**: Add panels by clicking panel types
- **Grid Layout**: Drag panels to reposition, resize with handles
- **Panel Types**:
  - Time Series
  - Stat
  - Table
  - Gauge
  - Bar Chart
  - Pie Chart

### Workflow:
1. Enter dashboard name
2. Click panel type to add (e.g., "Time Series")
3. Drag and resize panels on canvas
4. Click **"Save Dashboard"** to persist

### Backend Integration:
- Saves to backend service at `http://localhost:8001/api/dashboards/save`
- Converts grid positions to Grafana `gridPos` format

---

## 🔌 API Connector Features

### Supported Connectors:
1. **AWS CloudWatch** - AWS services
2. **Azure Monitor** - Azure resources
3. **Apache Kafka** - Message streaming
4. **MQTT** - IoT protocols
5. **RabbitMQ** - Message queues
6. **PostgreSQL** - Databases
7. **MongoDB** - NoSQL databases
8. **REST API** - Generic HTTP endpoints

### Workflow:
1. Select connector type (e.g., "PostgreSQL")
2. Fill configuration form:
   - Connection name
   - Host, port, credentials
   - Type-specific settings
3. Click **"Test Connection"** to verify
4. Click **"Save Connection"** to persist

### Form Examples:

**PostgreSQL:**
- Host: `rhinometric-postgres`
- Port: `5432`
- Database: `rhinometric_licenses`
- Username: `rhinometric`
- Password: (from environment)

**REST API:**
- URL: `https://api.example.com`
- Auth Type: Bearer Token / API Key / Basic
- Custom Headers: JSON object

### Backend Integration:
- Tests connections at `http://localhost:8000/api/test-connection`
- Saves at `http://localhost:8000/api/connections`
- Lists active connections at `http://localhost:8000/api/connections`

---

## 🎨 Branding Implementation

### Visual Changes:

#### Grafana UI:
- **Title Bar**: "RHINOMETRIC" in teal gradient (#00d4aa → #00ffcc)
- **Logo**: Custom Rhinometric icon
- **Favicon**: "R" letter in teal gradient
- **Footer**: "Powered by Rhinometric - Trial Version (180 days)"

#### Plugin Pages:
- **Header**: "RHINOMETRIC" logo + plugin name
- **Primary Color**: #00d4aa (Rhinometric teal)
- **Buttons**: Grafana UI components styled with theme
- **Cards**: Hover effects with teal border/shadow

### CSS Customization:

Applied via `apply-branding.sh`:
```css
.sidemenu__logo {
  background: linear-gradient(90deg, #00d4aa 0%, #00ffcc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}
```

---

## 🔧 Configuration

### Docker Compose Changes:

```yaml
grafana:
  environment:
    # Plugin paths
    GF_PATHS_PLUGINS: "/var/lib/grafana/plugins"
    GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS: "rhinometric-dashboard-builder,rhinometric-api-connector"
    
    # Branding
    GF_SERVER_NAME: "Rhinometric Observability Platform"
    GF_BRANDING_TITLE: "Rhinometric"
    GF_BRANDING_FOOTER: "Powered by Rhinometric - Trial Version (180 days)"
    
  volumes:
    # Plugin mounts
    - ./grafana-plugins/rhinometric-dashboard-builder:/var/lib/grafana/plugins/rhinometric-dashboard-builder:ro
    - ./grafana-plugins/rhinometric-api-connector:/var/lib/grafana/plugins/rhinometric-api-connector:ro
    
    # Branding assets
    - ./grafana-branding:/branding:ro
    - ./grafana-branding/apply-branding.sh:/docker-entrypoint-initdb.d/apply-branding.sh:ro
```

---

## 🐛 Troubleshooting

### Plugins Not Appearing in Menu

**Check plugin loading:**
```bash
docker logs rhinometric-grafana | grep plugin
```

**Verify volume mounts:**
```bash
docker exec rhinometric-grafana ls -la /var/lib/grafana/plugins/
```

**Check permissions:**
```bash
sudo chown -R 472:472 ./grafana-plugins/
```

### Build Errors

**Install dependencies manually:**
```bash
cd grafana-plugins/rhinometric-dashboard-builder
npm install --legacy-peer-deps
npm run build
```

**Check Node.js version:**
```bash
node --version  # Should be v16+ or v18+
```

### Branding Not Visible

**Verify branding script execution:**
```bash
docker exec rhinometric-grafana cat /usr/share/grafana/public/build/custom.css
```

**Check logo files:**
```bash
docker exec rhinometric-grafana ls -la /usr/share/grafana/public/img/
```

### Backend Connection Errors

**Verify backend services:**
```bash
curl http://localhost:8001/api/health
curl http://localhost:8000/api/health
```

**Check Docker network:**
```bash
docker exec rhinometric-grafana ping -c 3 rhinometric-dashboard-builder
docker exec rhinometric-grafana ping -c 3 rhinometric-api-connector
```

---

## 📊 Plugin Development

### Adding New Panel Types (Dashboard Builder)

Edit `DashboardBuilderPage.tsx`:
```typescript
const panelTypes = [
  { label: 'Time Series', value: 'timeseries', icon: 'graph-bar' },
  // Add new type:
  { label: 'Heatmap', value: 'heatmap', icon: 'fire' },
];
```

### Adding New Connectors (API Connector)

Edit `APIConnectorPage.tsx`:
```typescript
const connectors: Connector[] = [
  { id: 'aws', name: 'AWS CloudWatch', icon: 'cloud', description: '...' },
  // Add new connector:
  { id: 'influxdb', name: 'InfluxDB', icon: 'database', description: 'Time series DB' },
];
```

Then add form rendering in `renderForm()` switch statement.

---

## 🔄 Updating Plugins

### Rebuild After Changes:

```bash
# Rebuild specific plugin
cd grafana-plugins/rhinometric-dashboard-builder
npm run build

# Or rebuild all
./build-plugins.sh
```

### Hot Reload (Development):

```bash
# Watch mode for development
cd grafana-plugins/rhinometric-dashboard-builder
npm run watch
```

Changes will be automatically compiled. Refresh Grafana page to see updates.

---

## 📚 Technology Stack

### Plugins:
- **React 18** - UI framework
- **TypeScript** - Type safety
- **@grafana/ui** - Grafana UI components
- **@grafana/data** - Data structures
- **@grafana/runtime** - Runtime APIs
- **react-grid-layout** - Drag & drop grid (Dashboard Builder)
- **emotion** - CSS-in-JS styling

### Build Tools:
- **@grafana/toolkit** - Official Grafana plugin SDK
- **webpack** (via toolkit) - Module bundler
- **babel** (via toolkit) - JavaScript transpiler

---

## 🎓 Next Steps

### For Users:
1. Build plugins with `./build-plugins.sh`
2. Restart Grafana
3. Access plugins from Grafana menu → Apps
4. Create dashboards and configure connectors visually

### For Developers:
1. Review plugin source code in `grafana-plugins/`
2. Customize forms, add features
3. Rebuild with `npm run build`
4. Test in development mode with `npm run watch`

---

## 📞 Support

For issues or questions:
- Email: rafael.canelon@rhinometric.com
- Documentation: See `POSTMORTEM_INCIDENT_REPORT.md`
- Logs: `docker logs rhinometric-grafana`

---

**✅ RHINOMETRIC v2.4.0 - Complete Integration**

Visual UIs now available inside Grafana for a unified observability experience.
