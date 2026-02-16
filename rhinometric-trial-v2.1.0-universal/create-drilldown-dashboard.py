#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

dashboard = {
    "uid": "rhinometric-drilldown-demo",
    "title": "[DRILLDOWN] Metrics - Logs - Traces",
    "tags": ["rhinometric", "drilldown", "demo"],
    "timezone": "browser",
    "editable": True,
    "graphTooltip": 1,
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "gridPos": {"h": 6, "w": 24, "x": 0, "y": 0},
            "id": 1,
            "title": "[GUIDE] Como usar el Drilldown",
            "type": "text",
            "options": {
                "mode": "markdown",
                "content": """# Drilldown: Navegacion entre Metricas, Logs y Traces

Rhinometric v2.1.0 incluye **drilldown completo** entre las 3 pilares de observabilidad:

---

## 1. Metrics -> Traces (Prometheus Exemplars)

**Donde?** En cualquier grafico de Prometheus que muestre metricas con exemplars.

**Como funciona?**
- Haz hover sobre un punto en el grafico
- Si ves un **circulo azul** junto al valor, haz click
- Te llevara directamente a la trace en Tempo

**Ejemplo:** Ve al dashboard "Prometheus Monitoring" -> panel "Query Rate" -> busca circulos azules

---

## 2. Logs -> Traces (Loki Derived Fields)

**Donde?** En el dashboard "Loki Logs Explorer" o en Explore -> Loki.

**Como funciona?**
- Los logs que contengan `trace_id=XXXXX` mostraran un boton **"Tempo"**
- Haz click en el boton para ver la trace completa
- Funciona con cualquier formato: `trace_id=abc123` o `"trace_id": "abc123"`

**Ejemplo:** 
1. Ve a **Explore** (icono de brujula en el menu izquierdo)
2. Selecciona datasource **Loki**
3. Query: `{container="rhinometric-api-proxy"} |= "trace_id"`
4. Busca el boton **"Tempo"** junto a cada log

---

## 3. Traces -> Logs (Tempo TracesToLogs)

**Donde?** En el dashboard "Distributed Tracing" o en Explore -> Tempo.

**Como funciona?**
- Abre cualquier trace en Tempo
- Haz click en un **span** (rectangulo en el timeline)
- En el panel lateral, veras un boton **"Logs for this span"**
- Te llevara a Loki con los logs filtrados por ese servicio y tiempo

**Ejemplo:**
1. Ve a **Explore** -> **Tempo**
2. Selecciona la ultima trace disponible
3. Click en cualquier span
4. Busca el boton **"Logs for this span"** en la barra superior del panel de detalles

---

## 4. Traces -> Metrics (Tempo TracesToMetrics)

**Donde?** En Explore -> Tempo.

**Como funciona?**
- Abre cualquier trace
- Haz click en la pestana **"Metrics"** (junto a "Logs")
- Veras automaticamente las metricas de Prometheus relacionadas con ese servicio

---

## Tips

- **Para probar el drilldown completo**, necesitas:
  1. Metricas con exemplars (Prometheus)
  2. Logs con `trace_id` (Loki)
  3. Traces activas (Tempo)

- **El trace generator** ya esta enviando traces. Para ver logs con trace_id, ejecuta:
  ```bash
  docker logs rhinometric-api-proxy | grep trace_id
  ```

- **Los datasources ya estan configurados**, solo navega y explora!

---

## Rutas de Drilldown Disponibles

| Desde | Hacia | Metodo | Estado |
|-------|-------|--------|--------|
| **Prometheus** | Tempo | Exemplars (circulos azules) | Configurado |
| **Loki** | Tempo | Boton "Tempo" en logs | Configurado |
| **Tempo** | Loki | Boton "Logs for this span" | Configurado |
| **Tempo** | Prometheus | Pestana "Metrics" | Configurado |
"""
            }
        },
        {
            "gridPos": {"h": 10, "w": 12, "x": 0, "y": 6},
            "id": 2,
            "title": "[DEMO] Metricas con Exemplars",
            "type": "timeseries",
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "targets": [{
                "datasource": {"type": "prometheus", "uid": "prometheus"},
                "expr": "rate(prometheus_http_requests_total[5m])",
                "refId": "A",
                "legendFormat": "{{handler}}"
            }],
            "options": {
                "tooltip": {"mode": "multi"},
                "legend": {"displayMode": "list", "placement": "bottom"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {"drawStyle": "line", "fillOpacity": 10},
                    "color": {"mode": "palette-classic"}
                }
            }
        },
        {
            "gridPos": {"h": 10, "w": 12, "x": 12, "y": 6},
            "id": 3,
            "title": "[DEMO] Logs con TraceID",
            "type": "logs",
            "datasource": {"type": "loki", "uid": "loki"},
            "targets": [{
                "datasource": {"type": "loki", "uid": "loki"},
                "expr": '{container=~"rhinometric-.+"} |= "trace"',
                "refId": "A"
            }],
            "options": {
                "showTime": True,
                "showLabels": False,
                "showCommonLabels": False,
                "wrapLogMessage": True,
                "sortOrder": "Descending"
            }
        },
        {
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
            "id": 4,
            "title": "[QUICK ACCESS] Herramientas",
            "type": "text",
            "options": {
                "mode": "markdown",
                "content": """## Enlaces Directos

| Herramienta | URL | Descripcion |
|-------------|-----|-------------|
| **Explore** | http://localhost:3000/explore | Interfaz para consultas ad-hoc |
| **Prometheus** | http://localhost:9090 | Query directo a metricas |
| **Loki** | http://localhost:3100 | API de logs |
| **Tempo** | http://localhost:3200 | API de traces |
| **API Connector** | http://localhost:8091 | Nueva UI para conectar APIs |

---

### Comandos de Prueba

```bash
# Ver logs con trace_id
docker logs rhinometric-api-proxy | grep -i trace

# Ver traces en Tempo
curl http://localhost:3200/api/search?limit=10

# Ver metricas del API Proxy
curl http://localhost:8090/api/metrics/prometheus
```
"""
            }
        }
    ]
}

# Save dashboard
with open('config/grafana/dashboards/drilldown-demo.json', 'w', encoding='utf-8') as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)

print("[OK] Drilldown demo dashboard created: config/grafana/dashboards/drilldown-demo.json")
