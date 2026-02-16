# RHINOMETRIC VeriVerde Exporter

## Overview

VeriVerde is a lightweight sustainability and energy monitoring exporter for the RHINOMETRIC observability platform. It exposes environmental and energy-related metrics in Prometheus format, enabling organizations to monitor their carbon footprint, energy efficiency, and compliance with green policies.

## Key Features

- **Energy Consumption Monitoring**: Track power usage in real-time
- **Temperature Monitoring**: Monitor server room or rack temperatures
- **Carbon Footprint Calculation**: Automatic CO₂ emissions estimation
- **Renewable Energy Tracking**: Monitor percentage of renewable energy usage
- **Efficiency Scoring**: Operational efficiency metrics (0-100 scale)
- **Sensor Integration**: Connect to real hardware sensors or use simulation mode
- **Prometheus Native**: Standard Prometheus exposition format
- **Zero Dependencies**: Pure Python stdlib implementation

## Metrics Exposed

| Metric | Type | Description |
|--------|------|-------------|
| `rhinometric_energy_kwh` | gauge | Current energy consumption in kilowatt-hours |
| `rhinometric_room_temperature_c` | gauge | Room or rack temperature in Celsius |
| `rhinometric_renewable_percent` | gauge | Percentage of renewable energy being used |
| `rhinometric_co2_emissions_kg` | gauge | Estimated CO₂ emissions in kilograms |
| `rhinometric_efficiency_score` | gauge | Operational efficiency score (0-100) |
| `rhinometric_veriverde_info` | gauge | Exporter version and mode information |

## Configuration

Configure via environment variables:

```bash
# HTTP server port (default: 9200)
VERIVERDE_PORT=9200

# Optional: URL to energy sensor API (JSON format expected)
VERIVERDE_ENERGY_SENSOR_URL=http://sensor.local/api/energy

# Optional: URL to temperature sensor API (JSON format expected)
VERIVERDE_TEMP_SENSOR_URL=http://sensor.local/api/temperature

# Static renewable energy percentage (default: 0)
VERIVERDE_RENEWABLE_PERCENT=35.0

# CO₂ emissions factor in kg per kWh (default: 0.233 - EU average)
CO2_FACTOR_KG_PER_KWH=0.233

# Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
LOG_LEVEL=INFO
```

## Sensor API Format

If connecting to real sensors, your API should return JSON in this format:

**Energy Sensor** (`VERIVERDE_ENERGY_SENSOR_URL`):
```json
{
  "energy_kwh": 3.45
}
```

**Temperature Sensor** (`VERIVERDE_TEMP_SENSOR_URL`):
```json
{
  "temperature_c": 22.5
}
```

## Docker Usage

### Standalone

```bash
docker build -t rhinometric-veriverde:latest .

docker run -d \
  --name veriverde-exporter \
  -p 9200:9200 \
  -e VERIVERDE_RENEWABLE_PERCENT=40 \
  -e CO2_FACTOR_KG_PER_KWH=0.200 \
  rhinometric-veriverde:latest
```

### With Docker Compose

Already integrated in `docker-compose-v2.2.0.yml`:

```yaml
services:
  rhinometric-veriverde:
    build: ./rhinometric-veriverde
    container_name: rhinometric-veriverde
    environment:
      VERIVERDE_RENEWABLE_PERCENT: 35
      CO2_FACTOR_KG_PER_KWH: 0.233
    ports:
      - "9200:9200"
    networks:
      - rhinometric_network_v22
```

## Endpoints

- **`/metrics`**: Prometheus metrics exposition
- **`/health`**: Health check endpoint (JSON)

## Example Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'veriverde'
    static_configs:
      - targets: ['rhinometric-veriverde:9200']
    scrape_interval: 30s
```

## Integration with Grafana

The **VeriVerde Insights** dashboard is automatically provisioned in Grafana, showing:

- Real-time energy consumption trends
- Temperature monitoring with alerts
- CO₂ emissions tracking
- Renewable energy percentage
- Operational efficiency score
- Historical data and comparisons

## Simulation Mode

When no sensor URLs are configured, VeriVerde runs in **simulation mode**:

- **Energy**: Fluctuates based on time of day (higher during business hours)
- **Temperature**: Random values between 18-28°C
- **Renewable %**: Static value from environment variable

This allows you to:
- Test dashboards before hardware installation
- Demo the platform to clients
- Develop and validate integrations

## Use Cases

### 1. Public Sector Compliance
Monitor and report energy consumption for ESG compliance and sustainability goals.

### 2. Green Data Centers
Track PUE (Power Usage Effectiveness) and temperature efficiency in server rooms.

### 3. Renewable Energy Monitoring
Measure the impact of solar/wind installations on overall energy mix.

### 4. Cost Optimization
Identify peak consumption periods and optimize workload scheduling.

### 5. Carbon Footprint Reporting
Automatic CO₂ calculations for environmental reporting requirements.

## CO₂ Emission Factors

Default factor: **0.233 kg CO₂/kWh** (EU average 2024)

Common factors by region:
- **Spain**: 0.200 kg/kWh
- **Germany**: 0.350 kg/kWh
- **France**: 0.055 kg/kWh (high nuclear)
- **Poland**: 0.650 kg/kWh (coal-heavy)
- **Norway**: 0.020 kg/kWh (hydropower)

Configure via `CO2_FACTOR_KG_PER_KWH` environment variable.

## Efficiency Score Calculation

Score = 100 - Energy Penalty - Temperature Penalty

- **Energy Penalty**: Higher consumption = higher penalty (max 50 points)
- **Temperature Penalty**: Deviation from optimal range (20-24°C) = penalty (max 50 points)

Optimal conditions: Low energy + temperature in 20-24°C range = score ~100

## Security Considerations

- No authentication required (internal network only)
- Read-only metrics exposition
- No sensitive data exposed
- Non-root container execution
- No write operations to disk

## Troubleshooting

**Metrics not updating:**
```bash
# Check exporter logs
docker logs rhinometric-veriverde

# Verify endpoint
curl http://localhost:9200/health
curl http://localhost:9200/metrics
```

**Sensor connection failed:**
- Check sensor URL is reachable from container
- Verify JSON format matches expected schema
- Exporter will fall back to simulation mode on errors

**High CO₂ emissions:**
- Verify `CO2_FACTOR_KG_PER_KWH` is correct for your region
- Check `VERIVERDE_RENEWABLE_PERCENT` is properly configured
- Review actual energy consumption patterns

## License

Proprietary - Part of RHINOMETRIC Enterprise Platform
© 2025 Rafael Canel - rafael.canelon@rhinometric.com

## Support

For issues or questions:
- GitHub: https://github.com/Rafael2712/rhinometric-overview/issues
- Email: rafael.canelon@rhinometric.com
