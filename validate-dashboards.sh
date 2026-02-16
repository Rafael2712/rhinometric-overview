#!/bin/bash

# 🎯 VALIDACIÓN COMPLETA DE DASHBOARDS RHINOMETRIC
# Este script valida que todos los dashboards estén funcionando correctamente

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🔍 VALIDACIÓN DE DASHBOARDS - RHINOMETRIC OBSERVABILITY   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Grafana credentials
GRAFANA_URL="http://localhost:3000"
GRAFANA_AUTH="admin:admin_trial_2024"
PROM_URL="http://localhost:9090"

# Check Grafana
echo "1️⃣  Verificando Grafana..."
if curl -s -f "$GRAFANA_URL/api/health" > /dev/null; then
    echo "   ✅ Grafana está UP"
else
    echo "   ❌ Grafana está DOWN"
    exit 1
fi
echo ""

# Check Datasources
echo "2️⃣  Verificando Datasources..."
curl -s "$GRAFANA_URL/api/datasources" -u "$GRAFANA_AUTH" | python3 << 'EOF'
import sys, json
datasources = json.load(sys.stdin)
for ds in datasources:
    print(f"   ✅ {ds['name']} ({ds['type']}) - UID: {ds['uid']}")
EOF
echo ""

# Check Dashboards
echo "3️⃣  Verificando Dashboards importados..."
DASHBOARD_COUNT=$(curl -s "$GRAFANA_URL/api/search?type=dash-db" -u "$GRAFANA_AUTH" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "   ✅ Total: $DASHBOARD_COUNT dashboards"
curl -s "$GRAFANA_URL/api/search?type=dash-db" -u "$GRAFANA_AUTH" | python3 << 'EOF'
import sys, json
dashboards = json.load(sys.stdin)
for d in sorted(dashboards, key=lambda x: x['title']):
    print(f"      • {d['title']}")
EOF
echo ""

# Check Prometheus Targets
echo "4️⃣  Verificando Prometheus Targets..."
curl -s "$PROM_URL/api/v1/targets" | python3 << 'EOF'
import sys, json
data = json.load(sys.stdin)['data']['activeTargets']
up = [t for t in data if t['health'] == 'up']
down = [t for t in data if t['health'] != 'up']
print(f"   ✅ {len(up)}/{len(data)} targets UP")
for t in down:
    job = t['labels']['job']
    error = t.get('lastError', 'Unknown error')[:50]
    print(f"   ⚠️  {job}: {error}")
EOF
echo ""

# Check Traces
echo "5️⃣  Verificando Traces de Tempo..."
TRACE_COUNT=$(curl -s "$GRAFANA_URL/api/datasources/proxy/uid/cf1m5g6s0xvy8f/api/search?q=%7B%7D" -u "$GRAFANA_AUTH" | python3 -c "import sys, json; r = json.load(sys.stdin); print(len(r.get('traces', [])))")
if [ "$TRACE_COUNT" -gt 0 ]; then
    echo "   ✅ $TRACE_COUNT trazas encontradas"
else
    echo "   ⚠️  No se encontraron trazas"
fi
echo ""

# Check Metrics
echo "6️⃣  Verificando Métricas disponibles..."
curl -s "$PROM_URL/api/v1/label/__name__/values" | python3 << 'EOF'
import sys, json
metrics = json.load(sys.stdin)['data']
checks = {
    'Redis': len([m for m in metrics if 'redis_' in m]),
    'Postgres': len([m for m in metrics if 'pg_' in m]),
    'Tempo': len([m for m in metrics if 'tempo_' in m or 'tempodb_' in m]),
    'Promtail': len([m for m in metrics if 'promtail_' in m]),
    'Node Exporter': len([m for m in metrics if 'node_' in m and not 'grafana_live_node' in m]),
    'cAdvisor': len([m for m in metrics if 'container_' in m]),
    'Blackbox': len([m for m in metrics if 'probe_' in m]),
    'Alertmanager': len([m for m in metrics if 'grafana_alerting_alertmanager' in m]),
}
for service, count in sorted(checks.items()):
    status = "✅" if count > 0 else "❌"
    print(f"   {status} {service}: {count} métricas")
EOF
echo ""

# Check Logs
echo "7️⃣  Verificando Loki Logs..."
LOKI_URL="http://localhost:3100"
STREAM_COUNT=$(curl -s "$LOKI_URL/loki/api/v1/label/service_name/values" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', [])))")
echo "   ✅ $STREAM_COUNT streams de logs activos"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ VALIDACIÓN COMPLETADA                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Accede a Grafana: $GRAFANA_URL"
echo "🔑 Usuario: admin / admin_trial_2024"
echo ""
echo "🎯 Dashboards principales:"
echo "   • Overview: $GRAFANA_URL/d/ef1m1elql2h34e"
echo "   • Tempo: $GRAFANA_URL/d/cf1m3xo0up14wd"
echo "   • Loki: $GRAFANA_URL/d/af1m3xp4gl2ioe"
echo "   • Navigation: $GRAFANA_URL/d/af1m423nclq80f"
echo ""
