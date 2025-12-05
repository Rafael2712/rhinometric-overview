# 🔒 AUDITORÍA DE SEGURIDAD - RHINOMETRIC TRIAL

**Fecha:** Octubre 2025  
**Versión:** Trial 1.0  
**Pregunta Crítica:** ¿Qué tan segura está la versión trial contra intentos de bypass del límite de 30 días?

---

## 📋 RESUMEN EJECUTIVO

**Estado General:** ⚠️ **VULNERABLE** - La versión trial actual tiene múltiples vectores de bypass que permitirían a un cliente malicioso:
1. ✅ Extender ilimitadamente el período trial
2. ✅ Dañar/modificar el código fuente
3. ✅ Quedarse con la versión definitivamente

**Nivel de Riesgo:** 🔴 **ALTO**

---

## 🔍 ANÁLISIS DE VULNERABILIDADES

### 1. License Server (VULNERABILIDAD CRÍTICA)

**Mecanismo Actual:**
- License-server usa JWT con SECRET_KEY hardcodeado
- Base de datos SQLite local en volumen Docker
- Validación solo comprueba timestamp de expiración JWT

**Vectores de Bypass:**

#### 1.1 Modificación de Docker Compose ⚠️
```yaml
# Cliente puede eliminar dependencia:
services:
  grafana:
    depends_on:
      # - license-server  # ← COMENTAR ESTA LÍNEA
```
**Resultado:** Todos los servicios funcionan sin validación de licencia.

#### 1.2 Cambio de Reloj del Sistema ⚠️
```bash
# Cliente ejecuta:
wsl sudo timedatectl set-ntp false
wsl sudo date -s "2025-10-22"
```
**Resultado:** El JWT nunca expira porque `exp` se compara con tiempo local.

#### 1.3 Modificación de SECRET_KEY ⚠️
```bash
# Cliente puede regenerar JWT con su propia key:
docker exec rhinometric-license-server env
# Ver: JWT_SECRET=rhinometric-trial-secret-change-this
# Generar nuevos tokens con Python + PyJWT
```
**Resultado:** Licencias "permanentes" autogeneradas.

#### 1.4 Acceso al Volumen de Datos ⚠️
```bash
# Base de datos SQLite accesible:
docker volume inspect trial-package_license_data
# Cliente puede editar directamente licenses.db
sqlite3 /var/lib/docker/volumes/trial-package_license_data/_data/licenses.db
UPDATE licenses SET expires_at = '2099-12-31' WHERE id = ...
```
**Resultado:** Licencia "permanente" en BD.

---

### 2. Código Fuente Expuesto (VULNERABILIDAD ALTA)

**Archivos Expuestos en Trial Package:**
```
trial-package/
├── docker-compose.yml          ← Toda la arquitectura visible
├── config/
│   ├── prometheus-saas.yml     ← Configuración completa
│   ├── loki-saas.yml
│   ├── tempo-saas.yml
│   └── alertmanager-saas.yml
├── grafana/provisioning/       ← Dashboards JSON editables
├── examples/                   ← Código de integración
└── INTEGRATION_GUIDE.md        ← Documentación completa
```

**Riesgos:**
- ✅ Cliente puede **copiar** toda la arquitectura
- ✅ Cliente puede **modificar** configuraciones
- ✅ Cliente puede **redistribuir** el trial
- ✅ Cliente aprende **toda la implementación**

---

### 3. Contenedores sin Hardening (VULNERABILIDAD MEDIA)

**Problemas Detectados:**

#### 3.1 Permisos Root
```bash
# Todos los contenedores corren como root (user: "0:0")
docker exec -u root rhinometric-grafana bash
# Cliente tiene acceso root completo
```

#### 3.2 Volúmenes Persistentes
```bash
# Cliente puede hacer backup completo:
docker run --rm -v trial-package_grafana_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz /data
# Restaurar en nueva instalación sin license-server
```

#### 3.3 Imágenes Modificables
```bash
# Cliente puede hacer commit de imagen modificada:
docker exec rhinometric-grafana rm -rf /etc/grafana/provisioning
docker commit rhinometric-grafana my-grafana:hacked
# Eliminar provisioning que valida licencia
```

---

### 4. No Hay Validación en Runtime (VULNERABILIDAD CRÍTICA)

**Problema:** Una vez iniciado, el sistema NO valida licencia periódicamente.

```bash
# Escenario:
1. Cliente inicia trial con licencia válida
2. Grafana, Prometheus, Tempo arrancan OK
3. Cliente para license-server: docker stop rhinometric-license-server
4. Sistema sigue funcionando indefinidamente ✅
```

**Falta:**
- ❌ Validación cada N horas en Grafana
- ❌ Heartbeat license-server → servicios
- ❌ Watermarking de dashboards
- ❌ Rate limiting después de X días

---

### 5. Telemetría Inexistente (VULNERABILIDAD MEDIA)

**Problema:** No hay forma de detectar clones o uso post-expiración.

**Falta:**
- ❌ Phone-home a servidor central Rhinometric
- ❌ Tracking de instalaciones únicas (fingerprint)
- ❌ Logs centralizados de uso trial
- ❌ Detección de modificación de código

---

## 🛡️ RECOMENDACIONES DE HARDENING

### Nivel 1: Protecciones Básicas (Implementar Inmediato)

#### 1.1 Time-Bomb en Servicios Críticos
```python
# En Grafana entrypoint.sh:
#!/bin/bash
LICENSE_SERVER_URL=${LICENSE_SERVER_URL:-http://license-server:5000}

while true; do
    response=$(curl -s "$LICENSE_SERVER_URL/validate" \
      -H "Content-Type: application/json" \
      -d '{"license_key":"'$LICENSE_KEY'"}')
    
    valid=$(echo $response | jq -r '.valid')
    
    if [ "$valid" != "true" ]; then
        echo "⛔ Licencia inválida o expirada"
        pkill grafana-server
        exit 1
    fi
    
    sleep 3600  # Validar cada hora
done &

# Iniciar Grafana
exec /run.sh
```

#### 1.2 Hardware Fingerprinting
```python
import hashlib
import subprocess

def get_hardware_id():
    """Genera ID único basado en hardware"""
    # MAC address
    mac = subprocess.check_output("ip link show eth0", shell=True)
    # Docker host ID
    hostname = os.environ.get('HOSTNAME')
    # Timestamp de primera instalación
    install_time = open('/data/.install_time').read()
    
    fingerprint = f"{mac}{hostname}{install_time}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()

# En license-server validate():
if payload['hardware_id'] != get_hardware_id():
    return jsonify({"valid": False, "error": "Hardware mismatch"}), 403
```

#### 1.3 Ofuscación de Configuraciones
```bash
# Encriptar configs sensibles:
openssl enc -aes-256-cbc -salt \
  -in prometheus-saas.yml \
  -out prometheus-saas.yml.enc \
  -pass env:RHINOMETRIC_DECRYPT_KEY

# En entrypoint.sh:
openssl enc -d -aes-256-cbc \
  -in /config/prometheus-saas.yml.enc \
  -out /etc/prometheus/prometheus.yml \
  -pass env:RHINOMETRIC_DECRYPT_KEY
```

---

### Nivel 2: Protecciones Avanzadas (Implementar en 30 días)

#### 2.1 NTP Validation
```python
import ntplib
from datetime import datetime

def validate_system_time():
    """Verificar que el reloj no está manipulado"""
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request('pool.ntp.org', version=3)
        ntp_time = datetime.fromtimestamp(response.tx_time)
        system_time = datetime.now()
        
        diff = abs((ntp_time - system_time).total_seconds())
        
        if diff > 300:  # Más de 5 minutos de diferencia
            return False, "Time manipulation detected"
        return True, "OK"
    except:
        # Si no hay internet, permitir pero loguear
        return True, "NTP check skipped (no internet)"
```

#### 2.2 Code Signing & Integrity Checks
```python
import hashlib

EXPECTED_HASHES = {
    '/app/license_server.py': 'sha256:abc123...',
    '/etc/grafana/grafana.ini': 'sha256:def456...',
    '/etc/prometheus/prometheus.yml': 'sha256:ghi789...'
}

def verify_file_integrity():
    """Detectar modificaciones en archivos críticos"""
    for filepath, expected_hash in EXPECTED_HASHES.items():
        actual_hash = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
        if f"sha256:{actual_hash}" != expected_hash:
            print(f"⛔ File tampered: {filepath}")
            return False
    return True
```

#### 2.3 Telemetría Anónima
```python
import requests
import uuid

INSTALL_ID = str(uuid.uuid4())  # Generado en primera instalación

def phone_home():
    """Enviar heartbeat a servidor central Rhinometric"""
    try:
        payload = {
            'install_id': INSTALL_ID,
            'version': 'trial-1.0',
            'timestamp': datetime.now().isoformat(),
            'license_type': 'trial',
            'days_active': get_days_since_install(),
            'container_count': get_running_containers(),
            # NO enviar datos sensibles del cliente
        }
        
        requests.post(
            'https://telemetry.rhinometric.com/heartbeat',
            json=payload,
            timeout=5
        )
    except:
        pass  # No bloquear si falla
```

---

### Nivel 3: Protecciones Enterprise (Opcional)

#### 3.1 Licencia Online Obligatoria
- Validación contra servidor central Rhinometric cada 24h
- Sin internet = modo degradado (solo lectura)
- Detección de clones por install_id

#### 3.2 Watermarking Dinámico
```javascript
// Inyectar en dashboards Grafana:
{
  "type": "text",
  "content": "RHINOMETRIC TRIAL - Expires: 2025-04-20 - InstallID: abc-123"
}
```

#### 3.3 Rate Limiting Progresivo
```python
# Después de 150 días:
if days_active > 150:
    # Limitar queries/hora
    max_queries = 100
    # Agregar delays
    time.sleep(2)
    # Mostrar banners de expiración
```

---

## 📊 COMPARACIÓN NIVELES DE SEGURIDAD

| Protección | Actual | Nivel 1 | Nivel 2 | Nivel 3 |
|-----------|--------|---------|---------|---------|
| Bypass por modificar docker-compose | ✅ Fácil | ⚠️ Medio | ❌ Difícil | ❌ Muy Difícil |
| Bypass por cambiar reloj sistema | ✅ Fácil | ✅ Fácil | ❌ Difícil | ❌ Imposible |
| Bypass por modificar BD | ✅ Fácil | ⚠️ Medio | ❌ Difícil | ❌ Muy Difícil |
| Copiar código completo | ✅ Trivial | ✅ Trivial | ⚠️ Parcial | ❌ Difícil |
| Detección de modificaciones | ❌ No | ⚠️ Básica | ✅ Avanzada | ✅ Completa |
| Detectar clones | ❌ No | ❌ No | ⚠️ Limitado | ✅ Sí |

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### Corto Plazo (Esta Semana)

1. ✅ **Implementar Time-Bomb básico** (Nivel 1.1)
   - Validación horaria en Grafana
   - Auto-shutdown si license-server no responde

2. ✅ **Hardware Fingerprinting** (Nivel 1.2)
   - Vincular licencia a MAC + hostname
   - Bloquear uso en otro host

3. ✅ **Documentar Limitaciones**
   - Agregar a WELCOME.html advertencia clara
   - Terms & Conditions explícitos

### Mediano Plazo (Próximas 2 Semanas)

4. ✅ **NTP Validation** (Nivel 2.1)
5. ✅ **File Integrity Checks** (Nivel 2.2)
6. ✅ **Telemetría Básica** (Nivel 2.3)

### Largo Plazo (Próximo Mes)

7. ⚠️ **Evaluar Licencia Online** (Nivel 3.1)
8. ⚠️ **Watermarking Dashboards** (Nivel 3.2)
9. ⚠️ **Rate Limiting** (Nivel 3.3)

---

## 💼 TRADE-OFFS: SEGURIDAD vs USABILIDAD

### Consideraciones de Negocio:

**Pro-Seguridad Extrema:**
- ✅ Protege IP de Rhinometric
- ✅ Fuerza conversión a licencia paga
- ❌ Experiencia trial frustrante
- ❌ Posibles falsos positivos
- ❌ Requiere internet constante

**Pro-Usabilidad:**
- ✅ Trial fácil de probar
- ✅ No requiere internet
- ✅ Sin fricciones técnicas
- ❌ Fácil de piratear
- ❌ Pérdida de conversiones legítimas

### Recomendación Balanceada:

**Implementar Nivel 1 + Nivel 2 Parcial:**
- Time-bomb con validación cada 6 horas
- Hardware fingerprinting flexible (permitir 2 hosts)
- NTP validation con fallback graceful
- Telemetría opt-out
- Watermarking discreto

**NO Implementar (demasiado agresivo para trial):**
- ❌ Licencia online obligatoria
- ❌ Rate limiting antes de expiración
- ❌ Auto-destrucción de datos

---

## 🚨 CONCLUSIÓN

**Respuesta a tu pregunta:**

> ¿Qué tan segura está la versión trial contra un cliente que quiera vulnerar los 6 meses?

**Respuesta:** Actualmente **MUY VULNERABLE**. Un cliente con conocimientos básicos de Docker puede:
- Eliminar el license-server en 1 línea
- Cambiar el reloj del sistema
- Copiar toda la arquitectura
- Usar indefinidamente sin conversión

**Recomendación Urgente:** Implementar **Nivel 1** (Time-Bomb + Hardware Fingerprinting) ANTES de distribuir trial a clientes reales.

**Tiempo estimado:** 2-3 días desarrollo + 1 día testing = **1 semana** para versión minimamente segura.

---

**Autor:** GitHub Copilot  
**Revisión:** Pendiente  
**Próxima Acción:** Decidir nivel de hardening a implementar
