# 🎨 RhinoMetric Dashboard Studio

**Visual Dashboard Builder for Non-Technical Users**

Create professional Grafana dashboards in 5 steps without writing PromQL queries.

---

## ✨ Features

- 🎯 **No-Code Dashboard Creation**: 5-step wizard for easy dashboard building
- 📊 **6 Pre-Built Templates**: System Overview, App Performance, Database, Network, Containers, AI Anomaly
- 🔐 **JWT Authentication**: Secure API access with token-based auth
- 🎨 **Modern UI**: Built with React 18 + Tailwind CSS + shadcn/ui
- ⚡ **Fast & Responsive**: Vite bundler, optimized production builds
- 🐳 **Docker Ready**: Multi-stage builds with Nginx

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (for development)
- Docker & Docker Compose
- Dashboard Builder API running on port 8001
- Grafana running on port 3000

### Development Mode

```bash
cd dashboard-studio
npm install
npm run dev
```

Visit: **http://localhost:3001**

### Production Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# Or build manually
docker build -t rhinometric-dashboard-studio:latest .
docker run -d -p 3001:3001 --name dashboard-studio \
  --network mi-proyecto_rhinometric_network_v22 \
  rhinometric-dashboard-studio:latest
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```env
VITE_API_BASE=http://localhost:8001
VITE_GRAFANA_URL=http://localhost:3000
```

### JWT Token Generation

Generate a JWT token for authentication:

```bash
docker exec rhinometric-dashboard-builder python -c \
  "import jwt; from datetime import datetime, timedelta, timezone; \
   print(jwt.encode({'user_id': 'admin', 'username': 'admin', 'role': 'admin', \
   'iat': datetime.now(timezone.utc), 'exp': datetime.now(timezone.utc) + timedelta(days=365)}, \
   'your_jwt_secret_for_license_system_change_this', algorithm='HS256'))"
```

Copy the token and paste it in the Dashboard Studio UI when prompted.

---

## 📖 Usage Guide

### 5-Step Dashboard Creation

1. **Choose Template**: Select from 6 pre-built templates
2. **Select Datasource**: Choose Prometheus datasource (auto-detected)
3. **Configure Panels**: Automatic configuration based on template
4. **Layout**: Auto-optimized grid layout
5. **Preview & Create**: Review settings and create dashboard

### Quick Create

- Click "Create Now" on any template card for instant dashboard creation
- Dashboard opens automatically in Grafana

### Dashboard History

- View recently created dashboards in the History page
- Search by title or UID
- Quick access to open dashboards in Grafana

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Dashboard Studio (React SPA) :3001     │
│  - Template Selection UI                │
│  - 5-Step Wizard                        │
│  - JWT Auth                             │
└──────────────────┬──────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────┐
│  Dashboard Builder (FastAPI) :8001      │
│  - Template Engine                      │
│  - Grafana API Client                   │
│  - Panel Builder                        │
└──┬───────────────────┬──────────────────┘
   │ Grafana API       │ PostgreSQL
┌──▼────────┐    ┌─────▼─────┐
│  Grafana  │    │ PostgreSQL│
│   :3000   │    │   :5432   │
└───────────┘    └───────────┘
```

---

## 📦 Project Structure

```
dashboard-studio/
├── src/
│   ├── components/
│   │   ├── ui.jsx                 # Reusable UI components
│   │   ├── Header.jsx             # Navigation header
│   │   └── wizard/                # Wizard step components
│   │       ├── StepTemplate.jsx
│   │       ├── StepDatasource.jsx
│   │       ├── StepPanels.jsx
│   │       ├── StepLayout.jsx
│   │       └── StepPreview.jsx
│   ├── lib/
│   │   ├── api.js                 # API client (axios)
│   │   ├── store.js               # State management (zustand)
│   │   └── utils.js               # Utilities & constants
│   ├── pages/
│   │   ├── HomePage.jsx           # Template gallery
│   │   ├── NewDashboardPage.jsx   # 5-step wizard
│   │   └── DashboardsPage.jsx     # History page
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── public/
├── Dockerfile                     # Multi-stage Docker build
├── nginx.conf                     # Nginx configuration
├── docker-compose.yml             # Compose orchestration
├── package.json                   # Dependencies
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS config
└── README.md
```

---

## 🧪 Testing

### Smoke Test (End-to-End)

Run the automated smoke test script:

```bash
./smoke-test.sh
```

This will:
1. Check API connectivity (:8001)
2. Verify Grafana datasource
3. Create test dashboard
4. Validate dashboard creation
5. Open dashboard in browser

### Manual Testing Checklist

- [ ] JWT token authentication works
- [ ] All 6 templates load correctly
- [ ] Quick create generates dashboard
- [ ] Custom wizard completes 5 steps
- [ ] Dashboard opens in Grafana with data
- [ ] History page shows created dashboards
- [ ] Search filters dashboards correctly

---

## 🎯 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check & API info |
| `/api/v1/templates` | GET | List available templates |
| `/api/v1/datasources` | GET | Get Grafana datasources |
| `/api/v1/dashboards` | POST | Create dashboard |
| `/api/v1/dashboards` | GET | List dashboards |

---

## 🐛 Troubleshooting

### "Cannot connect to Dashboard Builder API"

- Ensure Dashboard Builder is running: `docker ps | grep dashboard-builder`
- Check API health: `curl http://localhost:8001/health`
- Verify network: Containers must be on same network

### "No Prometheus Datasource Found"

- Check Grafana datasources: http://localhost:3000/datasources
- Verify Prometheus UID is `prometheus`
- Restart Dashboard Builder if datasource added after startup

### "401 Unauthorized"

- JWT token expired or invalid
- Regenerate token using command above
- Ensure JWT_SECRET matches between services

### Dashboard created but empty

- Check datasource UID matches (`prometheus` not `prometheus-uid`)
- Verify Prometheus has data: http://localhost:9090/graph
- Check dashboard in Grafana for panel errors

---

## 🚀 Performance

- **Build time**: ~30s (multi-stage Docker)
- **Bundle size**: ~200KB gzipped
- **First load**: < 1s
- **Dashboard creation**: < 500ms
- **Lighthouse score**: 95+ (Performance, Accessibility, Best Practices)

---

## 📝 License

Part of RhinoMetric v2.2.0 - Dashboard Builder Suite

---

## 🤝 Support

- Documentation: `/docs`
- API Reference: http://localhost:8001/docs
- Grafana: http://localhost:3000

---

**Built with ❤️ by the RhinoMetric Team**
