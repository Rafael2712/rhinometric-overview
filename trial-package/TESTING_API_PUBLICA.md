# 🔌 TESTING RHINOMETRIC CON API PÚBLICA

## Objetivo
Conectar Rhinometric Trial a una API pública real para demostrar capacidades de observabilidad sin comprometer nuestro código.

---

## 🎯 API RECOMENDADA: JSON Placeholder

**URL:** https://jsonplaceholder.typicode.com  
**Razón:** API REST pública, gratuita, con documentación completa, sin autenticación.

**Endpoints disponibles:**
- `/posts` - 100 posts
- `/comments` - 500 comments
- `/albums` - 100 albums
- `/photos` - 5000 photos
- `/todos` - 200 todos
- `/users` - 10 users

---

## 📝 PASO 1: CREAR APLICACIÓN DEMO

Vamos a crear una app Python simple que:
1. Hace requests a la API
2. Genera logs
3. Envía métricas a Prometheus
4. Envía traces a Tempo

### Código de la App Demo

Crea este archivo: `trial-package/examples/python/api-demo.py`

```python
#!/usr/bin/env python3
"""
Demo App para testing Rhinometric con API pública
Conecta a JSONPlaceholder y genera observabilidad completa
"""

import requests
import time
import random
import logging
from datetime import datetime
from prometheus_client import start_http_server, Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api-demo')

# Configurar Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint'])
ACTIVE_USERS = Gauge('api_active_users', 'Number of active users')
ERROR_COUNT = Counter('api_errors_total', 'Total API errors', ['endpoint', 'error_type'])

# Configurar OpenTelemetry tracing
resource = Resource(attributes={
    "service.name": "api-demo-app",
    "service.version": "1.0.0",
    "deployment.environment": "trial"
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True
)
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# API Base URL
API_BASE = "https://jsonplaceholder.typicode.com"

def fetch_posts():
    """Obtiene posts de la API"""
    endpoint = "/posts"
    
    with tracer.start_as_current_span("fetch_posts") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", f"{API_BASE}{endpoint}")
        
        start_time = time.time()
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(method='GET', endpoint=endpoint, status=response.status_code).inc()
            REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
            
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("response.size", len(response.content))
            
            if response.status_code == 200:
                posts = response.json()
                logger.info(f"✅ Fetched {len(posts)} posts in {duration:.3f}s")
                return posts
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                ERROR_COUNT.labels(endpoint=endpoint, error_type='http_error').inc()
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout fetching posts")
            ERROR_COUNT.labels(endpoint=endpoint, error_type='timeout').inc()
            span.set_attribute("error", True)
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching posts: {e}")
            ERROR_COUNT.labels(endpoint=endpoint, error_type='exception').inc()
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            return []

def fetch_user(user_id):
    """Obtiene un usuario específico"""
    endpoint = f"/users/{user_id}"
    
    with tracer.start_as_current_span("fetch_user") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", f"{API_BASE}{endpoint}")
        span.set_attribute("user.id", user_id)
        
        start_time = time.time()
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(method='GET', endpoint='/users', status=response.status_code).inc()
            REQUEST_DURATION.labels(endpoint='/users').observe(duration)
            
            if response.status_code == 200:
                user = response.json()
                logger.info(f"✅ Fetched user: {user['name']} ({duration:.3f}s)")
                return user
            else:
                logger.warning(f"⚠️ User not found: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching user {user_id}: {e}")
            ERROR_COUNT.labels(endpoint='/users', error_type='exception').inc()
            return None

def fetch_comments(post_id):
    """Obtiene comentarios de un post"""
    endpoint = f"/posts/{post_id}/comments"
    
    with tracer.start_as_current_span("fetch_comments") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", f"{API_BASE}{endpoint}")
        span.set_attribute("post.id", post_id)
        
        start_time = time.time()
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(method='GET', endpoint='/comments', status=response.status_code).inc()
            REQUEST_DURATION.labels(endpoint='/comments').observe(duration)
            
            if response.status_code == 200:
                comments = response.json()
                logger.info(f"✅ Fetched {len(comments)} comments for post {post_id} ({duration:.3f}s)")
                return comments
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching comments: {e}")
            ERROR_COUNT.labels(endpoint='/comments', error_type='exception').inc()
            return []

def create_post(title, body, user_id):
    """Crea un nuevo post (simulado)"""
    endpoint = "/posts"
    
    with tracer.start_as_current_span("create_post") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.url", f"{API_BASE}{endpoint}")
        span.set_attribute("user.id", user_id)
        
        payload = {
            "title": title,
            "body": body,
            "userId": user_id
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=5)
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(method='POST', endpoint=endpoint, status=response.status_code).inc()
            REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
            
            if response.status_code == 201:
                post = response.json()
                logger.info(f"✅ Created post: {post['id']} ({duration:.3f}s)")
                return post
            else:
                logger.warning(f"⚠️ Failed to create post: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating post: {e}")
            ERROR_COUNT.labels(endpoint=endpoint, error_type='exception').inc()
            return None

def simulate_user_workflow():
    """Simula un flujo completo de usuario"""
    with tracer.start_as_current_span("user_workflow") as span:
        user_id = random.randint(1, 10)
        
        # 1. Obtener usuario
        logger.info(f"🔄 Starting workflow for user {user_id}")
        user = fetch_user(user_id)
        
        if not user:
            return
        
        # 2. Obtener posts
        time.sleep(0.1)  # Simular procesamiento
        posts = fetch_posts()
        
        if posts:
            # 3. Seleccionar un post aleatorio
            post = random.choice(posts[:10])
            time.sleep(0.1)
            
            # 4. Obtener comentarios del post
            comments = fetch_comments(post['id'])
            
            # 5. Crear un nuevo post
            time.sleep(0.1)
            new_post = create_post(
                title=f"Demo post by {user['name']}",
                body=f"This is a demo post created at {datetime.now()}",
                user_id=user_id
            )
        
        logger.info(f"✅ Workflow completed for user {user_id}")

def main():
    """Función principal"""
    # Iniciar servidor de métricas Prometheus
    start_http_server(8000)
    logger.info("🚀 API Demo App started")
    logger.info("📊 Metrics available at http://localhost:8000")
    logger.info("🔄 Simulating API traffic...")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"📌 Iteration {iteration} - {datetime.now()}")
            logger.info(f"{'='*60}")
            
            # Actualizar gauge de usuarios activos
            active = random.randint(1, 5)
            ACTIVE_USERS.set(active)
            
            # Simular múltiples workflows
            for i in range(active):
                simulate_user_workflow()
                time.sleep(random.uniform(0.5, 2.0))
            
            # Esperar antes de la siguiente iteración
            wait_time = random.uniform(5, 15)
            logger.info(f"⏸️  Waiting {wait_time:.1f} seconds before next iteration...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping API Demo App...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
```

---

## 🚀 PASO 2: EJECUTAR LA APP DEMO

### Opción A: Ejecutar en tu máquina

```bash
# 1. Instalar dependencias
pip install requests prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

# 2. Navegar a la carpeta
cd trial-package/examples/python

# 3. Ejecutar la app
python api-demo.py
```

### Opción B: Ejecutar en Docker (recomendado)

```bash
# 1. Crear Dockerfile
cat > trial-package/examples/python/Dockerfile.api-demo << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
RUN pip install --no-cache-dir requests prometheus-client \
    opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-grpc

# Copiar app
COPY api-demo.py .

# Exponer puerto de métricas
EXPOSE 8000

# Ejecutar
CMD ["python", "api-demo.py"]
EOF

# 2. Agregar al docker-compose.yml
# (Ver siguiente sección)
```

---

## 📝 PASO 3: AGREGAR AL DOCKER COMPOSE

Agrega este servicio al `docker-compose.yml`:

```yaml
  api-demo:
    build:
      context: ./examples/python
      dockerfile: Dockerfile.api-demo
    container_name: rhinometric-api-demo
    networks:
      - rhinometric_network
    depends_on:
      - prometheus
      - tempo
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8000"
      - "prometheus.path=/metrics"
```

---

## ✅ PASO 4: VERIFICAR OBSERVABILIDAD

### 1️⃣ Métricas en Prometheus

Abre: http://localhost:9090

**Consultas PromQL:**
```promql
# Total de requests
sum(rate(api_requests_total[1m])) by (endpoint)

# Duración promedio de requests
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# Errores por segundo
sum(rate(api_errors_total[1m])) by (endpoint)

# Usuarios activos
api_active_users
```

### 2️⃣ Logs en Loki (via Grafana)

Abre: http://localhost:3000 → Explore → Loki

**Consultas LogQL:**
```logql
{container="rhinometric-api-demo"} |= "✅"
{container="rhinometric-api-demo"} |= "❌"
{container="rhinometric-api-demo"} |~ "Fetched.*posts"
```

### 3️⃣ Traces en Tempo (via Grafana)

Abre: http://localhost:3000 → Explore → Tempo

- Busca servicios: `api-demo-app`
- Filtra por operación: `user_workflow`, `fetch_posts`, `fetch_user`
- Ver waterfall de traces

---

## 📊 PASO 5: CREAR DASHBOARD DEMO

Dashboard personalizado para monitorear la API demo.

**Paneles recomendados:**
1. **Request Rate:** `rate(api_requests_total[1m])`
2. **Error Rate:** `rate(api_errors_total[1m])`
3. **Latency P95:** `histogram_quantile(0.95, api_request_duration_seconds_bucket)`
4. **Active Users:** `api_active_users`
5. **Logs Stream:** Loki query `{container="rhinometric-api-demo"}`
6. **Recent Traces:** Tempo traces del servicio

---

## 🎯 ESCENARIOS DE TESTING

### 1. Comportamiento Normal
- La app genera tráfico constante
- Métricas estables
- Logs informativos
- Traces completos

### 2. Simular Carga Alta
```python
# Modificar api-demo.py: active = random.randint(10, 20)
```

### 3. Simular Errores
```python
# Modificar API_BASE a URL inválida temporalmente
```

### 4. Simular Latencia
```python
# Agregar time.sleep() aleatorio en las funciones
```

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] App demo ejecutándose (ver logs en `docker logs rhinometric-api-demo`)
- [ ] Métricas aparecen en Prometheus (http://localhost:9090/targets)
- [ ] Logs visibles en Grafana → Explore → Loki
- [ ] Traces visibles en Grafana → Explore → Tempo
- [ ] Dashboard muestra datos en tiempo real
- [ ] Alertas funcionan (si configuradas)

---

## 🔍 ALTERNATIVAS DE APIs PÚBLICAS

Si quieres probar con otras APIs:

### GitHub API
```python
API_BASE = "https://api.github.com"
# Endpoints: /users/{username}, /repos/{owner}/{repo}
```

### OpenWeatherMap (requiere API key gratuita)
```python
API_BASE = "https://api.openweathermap.org/data/2.5"
# Endpoints: /weather?q={city}, /forecast?q={city}
```

### REST Countries
```python
API_BASE = "https://restcountries.com/v3.1"
# Endpoints: /all, /name/{name}, /region/{region}
```

---

## 📞 SOPORTE

Si tienes problemas:
1. Verifica que Prometheus y Tempo estén corriendo
2. Revisa logs: `docker logs rhinometric-api-demo`
3. Verifica conectividad: `docker exec rhinometric-api-demo curl http://prometheus:9090/-/ready`

---

**Listo! Ahora tienes una app real generando observabilidad completa en Rhinometric** 🎉
