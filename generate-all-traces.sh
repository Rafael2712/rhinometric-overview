#!/bin/bash
# Script maestro para generar trazas variadas de 8 microservicios

echo "🚀 Generando trazas con 8 microservicios diferentes..."
echo ""

# frontend-web - Alto tráfico (150 trazas)
echo "📦 Generando 150 trazas para frontend-web..."
docker run -d --rm --name tracegen-frontend --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=15 --duration=10s \
  --service="frontend-web" --otlp-attributes="http.method=\"GET\"" \
  --otlp-attributes="http.route=\"/home\"" --otlp-attributes="environment=\"production\""

# api-gateway - Tráfico medio (120 trazas)
echo "📦 Generando 120 trazas para api-gateway..."
docker run -d --rm --name tracegen-gateway --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=12 --duration=10s \
  --service="api-gateway" --otlp-attributes="http.method=\"POST\"" \
  --otlp-attributes="http.route=\"/api/v1/request\""

# auth-service - Tráfico bajo (80 trazas)
echo "📦 Generando 80 trazas para auth-service..."
docker run -d --rm --name tracegen-auth --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=8 --duration=10s \
  --service="auth-service" --otlp-attributes="http.method=\"POST\"" \
  --otlp-attributes="http.route=\"/auth/login\"" --otlp-attributes="auth.type=\"jwt\""

# payment-service - CRÍTICO con errores (50 trazas con errores)
echo "📦 Generando 50 trazas con ERRORES para payment-service..."
docker run -d --rm --name tracegen-payment --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=5 --duration=10s \
  --service="payment-service" --status-code=Error \
  --otlp-attributes="http.method=\"POST\"" --otlp-attributes="http.route=\"/payment/process\"" \
  --otlp-attributes="payment.gateway=\"stripe\"" --otlp-attributes="error.type=\"timeout\""

# inventory-service - Alto tráfico (140 trazas)
echo "📦 Generando 140 trazas para inventory-service..."
docker run -d --rm --name tracegen-inventory --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=14 --duration=10s \
  --service="inventory-service" --otlp-attributes="http.method=\"GET\"" \
  --otlp-attributes="http.route=\"/products/search\"" --otlp-attributes="cache.hit=\"false\""

# database-proxy - Muy alto tráfico (180 trazas)
echo "📦 Generando 180 trazas para database-proxy..."
docker run -d --rm --name tracegen-db --network mi-proyecto_rhinometric_network \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-endpoint=tempo:4317 --otlp-insecure --rate=18 --duration=10s \
  --service="database-proxy" --otlp-attributes="db.system=\"postgresql\"" \
  --otlp-attributes="db.operation=\"SELECT\"" --otlp-attributes="db.name=\"rhinometric\""

echo ""
echo "⏳ Esperando 12 segundos a que terminen todos los generadores..."
sleep 12

echo ""
echo "✅ ¡Generación completada!"
echo ""
echo "📊 Resumen:"
echo "   - frontend-web: 150 trazas"
echo "   - api-gateway: 120 trazas"
echo "   - auth-service: 80 trazas"
echo "   - payment-service: 50 trazas (CON ERRORES ⚠️)"
echo "   - user-service: 49 trazas (ya generadas)"
echo "   - notification-service: 51 trazas (ya generadas)"
echo "   - inventory-service: 140 trazas"
echo "   - database-proxy: 180 trazas"
echo ""
echo "🔢 TOTAL: ~820 trazas de 8 servicios únicos"
echo ""
echo "🔍 Ahora verifica en Grafana Explore → Tempo:"
echo "   URL: http://localhost:3000/explore"
echo "   Queries sugeridas:"
echo "     - {} (todas las trazas)"
echo "     - {service.name=\"payment-service\"} (ver errores)"
echo "     - {service.name=\"frontend-web\"}"
echo "     - {status=error} (todas las trazas con error)"
echo ""
