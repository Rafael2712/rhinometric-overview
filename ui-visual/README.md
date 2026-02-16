# RHINOMETRIC v2.4.0 - Visual UI Components

Frontend components for RHINOMETRIC observability platform.

## Components

### 1. API Connector Plugin (Grafana)
Visual datasource configuration without YAML editing.

### 2. Dashboard Builder (Coming Soon)
Drag-and-drop dashboard creation.

## Development

### Prerequisites
- Node.js 18+
- npm or yarn
- Grafana 9.0+

### Installation

```bash
cd ui-visual
npm install
```

### Build

```bash
# Production build
npm run build

# Development mode (watch)
npm run dev
```

### Testing

```bash
npm test
```

## Installation in Grafana

1. Build the plugin:
   ```bash
   npm run build
   ```

2. Copy to Grafana plugins directory:
   ```bash
   cp -r ui-visual/ /var/lib/grafana/plugins/rhinometric-api-connector
   ```

3. Restart Grafana:
   ```bash
   systemctl restart grafana-server
   ```

4. Enable plugin in Grafana UI:
   - Go to Configuration → Plugins
   - Search for "RHINOMETRIC"
   - Click "Enable"

## Usage

1. Add new panel to dashboard
2. Select "RHINOMETRIC API Connector" visualization
3. Configure API URL (default: http://localhost:8000)
4. Select datasource type (PostgreSQL, Redis, Prometheus, etc.)
5. Fill connection details
6. Test connection
7. Save datasource

## Architecture

```
ui-visual/
├── src/
│   ├── components/           # React components
│   │   ├── APIConnectorPanel.tsx
│   │   └── APIConnectorPanel.css
│   ├── services/            # API services
│   │   └── api.ts
│   ├── types.ts             # TypeScript types
│   ├── module.tsx           # Plugin entry point
│   └── plugin.json          # Plugin metadata
├── dist/                    # Build output
├── package.json
├── tsconfig.json
└── webpack.config.js
```

## Features

### API Connector
- ✅ Visual template selection
- ✅ Form-based configuration
- ✅ Real-time connection testing
- ✅ Test result visualization
- ✅ Save to Grafana datasources
- ✅ Supports: PostgreSQL, Redis, Prometheus, AWS, Azure

### Dashboard Builder (Roadmap)
- ⏳ Drag-and-drop panel placement
- ⏳ Widget library
- ⏳ Real-time preview
- ⏳ Export to JSON

## Customization

### Theming
Edit `APIConnectorPanel.css` to customize colors and styles.

### Adding New Datasource Types
1. Add template to backend (`api-connector/app.py`)
2. Create connector in `api-connector/connectors/`
3. Frontend will auto-detect new templates

## Troubleshooting

**Plugin not appearing in Grafana:**
- Check Grafana logs: `tail -f /var/log/grafana/grafana.log`
- Verify plugin directory permissions
- Ensure `plugin.json` is valid

**Connection test fails:**
- Verify API backend is running (`http://localhost:8000`)
- Check CORS settings in backend
- Verify network connectivity

**Build errors:**
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## License

Proprietary - RHINOMETRIC v2.4.0
