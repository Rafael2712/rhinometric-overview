# 📜 POLÍTICA DE LICENCIAMIENTO RHINOMETRIC v2.5.0
## Definición de Roles, Límites y Modalidades

**Fecha de Definición:** 16 de Enero de 2026  
**Versión:** 1.0  
**Estado:** DRAFT - Pendiente Aprobación Comercial

---

## RESUMEN EJECUTIVO

**VERSIÓN MVP 1.0 - REALISTA Y VALIDADA**

Este documento establece las reglas de licenciamiento de Rhinometric v2.5.0 **basadas en capacidad técnica PROBADA**, incluyendo:
- Roles de usuario y permisos
- Límites por tier de licencia (2 tiers para MVP)
- Definición de "host monitoreable"
- Política de sesiones concurrentes
- Modelo de pricing

**CAPACIDAD TÉCNICA VALIDADA:**
- ✅ 5 hosts: PROBADO estable (Tier 1 - Starter)
- ✅ 12 hosts: PROBADO estable con optimización (Tier 2 - Professional)
- 🚧 50+ hosts: REQUIERE arquitectura distribuida (Tier 3 - Enterprise en roadmap)

---

## 1. ROLES DE USUARIO Y PERMISOS

### 1.1) OWNER (Propietario de Cuenta)

**Cantidad por licencia:** 1 único (no ampliable)

**Permisos completos:**
- ✅ Todas las capacidades de ADMIN
- ✅ Gestión de facturación y renovación
- ✅ Transferencia de ownership (con proceso de verificación)
- ✅ Cancelación de licencia
- ✅ Creación/eliminación de usuarios (ADMIN, OPERATOR, VIEWER)
- ✅ Modificación de límites de licencia (upgrade/downgrade)
- ✅ Acceso a logs de auditoría completos
- ✅ Configuración de SSO/LDAP (Enterprise)
- ✅ API keys con permisos de escritura

**Restricciones:**
- ❌ El rol OWNER NO puede ser asignado a múltiples usuarios
- ❌ Transferencia de ownership requiere verificación por email
- ❌ Si el OWNER es eliminado, la licencia queda suspendida

**Caso de uso típico:**
- CTO / VP Engineering / Infrastructure Lead
- Responsable de contrato con Rhinometric

---
(MVP) | 1 |
| Professional (MVP) | 3 |
| Enterprise (Roadmap) | 5
**Cantidad por licencia:** Variable según tier

| Tier | ADMIN permitidos |
|------|-----------------|
| Starter | 2 |
| Professional | 5 |
| Enterprise | 10 |

**Permisos:**
- ✅ Creación/edición/eliminación de dashboards
- ✅ Configuración de alertas y reglas
- ✅ Gestión de integraciones (Slack, PagerDuty, etc.)
- ✅ Configuración de datasources
- ✅ Gestión de usuarios OPERATOR y VIEWER
- ✅ Modificación de configuración de servicios
- ✅ Acceso a logs de auditoría (solo lectura)
- ✅ API keys con permisos de escritura
- ✅ Modificación de reportes programados

**Restricciones:**
- ❌ NO puede crear otros ADMIN (solo OWNER puede)
- ❌ NO puede modificar configuración de facturación
- ❌ NO puede eliminar al OWNER
- ❌ NO puede transferir ownership
- ❌ NO puede cambiar límites de licencia

**Caso de uso típico:**
- DevOps Engineers
- SRE Team Leads
- Platform Engineers

---
(MVP) | 3 |
| Professional (MVP) | 8 |
| Enterprise (Roadmap) | 1
**Cantidad por licencia:** Variable según tier

| Tier | OPERATOR permitidos |
|------|---------------------|
| Starter | 5 |
| Professional | 10 |
| Enterprise | 25 |

**Permisos:**
- ✅ Crear/editar dashboards personales (no compartidos por defecto)
- ✅ Visualizar todos los dashboards
- ✅ Configurar alertas personales (sin Slack/PagerDuty)
- ✅ Visualizar alertas activas
- ✅ Silenciar alertas temporalmente (1-24 horas)
- ✅ Visualizar métricas, logs y traces
- ✅ Crear queries personalizadas en Grafana
- ✅ Exportar datos (CSV, JSON)
- ✅ API keys con permisos de lectura

**Restricciones:**
- ❌ NO puede eliminar dashboards compartidos
- ❌ NO puede modificar configuración de datasources
- ❌ NO puede gestionar usuarios
- ❌ NO puede modificar integraciones (Slack, etc.)
- ❌ NO puede acceder a logs de auditoría
- ❌ NO puede configurar reportes programados

**Caso de uso típico:**
- Backend/Frontend Developers
- QA Engineers
- Junior SRE

---

### 1.4) VIEWER (Observador)

**Cantidad por licencia:** Variable según tier

| Tier | VIEWER permitidos |
|------|------------------|
| Starter (MVP) | 5 |
| Professional (MVP) | 10 |
| Enterprise (Roadmap) | **ILIMITADOS** |

**Permisos:**
- ✅ Visualizar dashboards existentes
- ✅ Visualizar alertas activas
- ✅ Visualizar métricas, logs y traces (solo lectura)
- ✅ Cambiar rangos de tiempo en dashboards
- ✅ Refrescar datos
- ✅ Exportar dashboards como PDF/PNG
- ✅ Recibir notificaciones de alertas (si está suscrito)

**Restricciones:**
- ❌ NO puede crear dashboards
- ❌ NO puede editar nada
- ❌ NO puede configurar alertas
- ❌ NO puede silenciar alertas
- ❌ NO puede acceder a configuración
- ❌ NO puede gestionar usuarios
- ❌ NO tiene acceso a API keys

**Caso de uso típico:**
- Product Managers
- Business Analysts
- Executives (CEO, CFO)
- Support Teams
- Cliente final (en caso de MSP)

---

## 2. TIERS DE LICENCIAMIENTO

### 2.1) TIER 1 - STARTER (MVP v1.0)

**Target:** Startups, equipos pequeños (2-10 personas)

```
📦 STARTER LICENSE - MVP
├─ 1 OWNER
├─ 1 ADMIN
├─ 3 OPERATOR
├─ 5 VIEWER
├─ 5 hosts monitoreados ✅ CAPACIDAD PROBADA
├─ Retención: 3 días (métricas), 1 día (logs)
├─ Sesiones simultáneas: ILIMITADAS
├─ Alertas: 30 reglas máximo
├─ Integraciones: Slack, Email, Webhooks
├─ Reportes: Manuales (on-demand)
├─ Dashboards: Ilimitados
├─ Soporte: Email (48h response)
└─ Precio: $199/mes o $1,990/año (ahorro 17%)
```

**Límites técnicos (validados):**
- Máx. 50,000 métricas/minuto
- Máx. 5 GB logs/día
- Máx. 500 traces/minuto
- Dashboards ilimitados
- API calls: 5,000 requests/día
- Usuarios totales: 10 (1+1+3+5)

**Upgrade triggers:**
- Supera 5 hosts por 3 días consecutivos → notificación
- Necesita más de 5 VIEWER → upgrade a Professional
- Necesita más de 1 ADMIN → upgrade a Professional
- Requiere retención >3 días → upgrade a Professional

---

### 2.2) TIER 2 - PROFESSIONAL (MVP v1.0)

**Target:** Scale-ups, equipos medianos (10-30 personas)

```
📦 PROFESSIONAL LICENSE - MVP
├─ 1 OWNER
├─ 3 ADMIN
├─ 8 OPERATOR
├─ 10 VIEWER
├─ 12 hosts monitoreados ✅ CAPACIDAD PROBADA
├─ Retención: 7 días (métricas), 3 días (logs)
├─ Sesiones simultáneas: ILIMITADAS
├─ Alertas: 100 reglas máximo
├─ Integraciones: Slack, Email, Webhooks, PagerDuty
├─ Reportes: Manuales (PDF, HTML)
├─ API Connector: 3 integraciones (PostgreSQL, MySQL, Webhooks)
├─ Dashboard Builder: 2 plantillas predefinidas
├─ Dashboards: Ilimitados
├─ Soporte: Email + Chat (24h response)
└─ Precio: $499/mes o $4,990/año (ahorro 17%)
```

**Límites técnicos (validados):**
- Máx. 120,000 métricas/minuto
- Máx. 12 GB logs/día
- Máx. 1,200 traces/minuto
- Dashboards ilimitados
- API calls: 20,000 requests/día
- Usuarios totales: 22 (1+3+8+10)

**Upgrade triggers:**
- Supera 12 hosts por 3 días consecutivos → contactar ventas
- Necesita más de 10 VIEWER → contactar ventas (Enterprise en roadmap)
- Requiere retención >7 días → contactar ventas
- Requiere SSO/LDAP → contactar ventas (Enterprise en roadmap)

---
Estado:** 🚧 EN ROADMAP (Q3-Q4 2026)

**Target:** Empresas grandes (50+ personas) con necesidad de >12 hosts

```
📦 ENTERPRISE LICENSE - ROADMAP
├─ 1 OWNER
├─ 5 ADMIN
├─ 15 OPERATOR
├─ ∞ VIEWER (ILIMITADOS)
├─ 50+ hosts monitoreados (requiere arquitectura distribuida)
├─ Retención: 15 días (métricas), 7 días (logs)
├─ Sesiones simultáneas: ILIMITADAS
├─ Alertas: ILIMITADAS
├─ Integraciones: Todas + Custom webhooks
├─ Reportes: Programados (diario, semanal, mensual)
├─ API Connector: 8 integraciones completas
├─ Dashboard Builder: 5+ plantillas predefinidas
├─ SSO/LDAP: ✅ Incluido (en desarrollo)
├─ Multi-tenant: ⚠️ Roadmap
├─ Soporte: Email + Chat prioritario (8h response)
└─ Precio: Custom (desde $1,500/mes + setup fee)
```

**Requisitos técnicos (en desarrollo):**
- Prometheus Federation (4 shards)
- Loki con S3 storage
- PostgreSQL con replicas
- Infraestructura dedicada (c5.2xlarge o superior)
- Setup time: 2-3 meses

**Características en roadmap:**
- SLA 99.5% uptime
- Dedicated instance
- Custom feature development (bajo demanda)
- Account manager dedicado
- Quarterly Business Reviews

**⚠️ NOTA:** Tier Enterprise disponible Q3 2026. Actualmente en contacto con ventas para necesidades >12 hosts.l
- On-premise deployment opcional
- Custom feature development
- Quarterly Business Reviews

---

## 3. DEFINICIÓN DE "HOST MONITOREABLE"

### 3.1) ¿Qué cuenta como 1 host?

```
1 HOST = 1 instancia única enviando métricas a Rhinometric

✅ CUENTA COMO 1 HOST:
├─ 1 servidor físico (bare metal)
├─ 1 máquina virtual (VM)
├─ 1 Kubernetes node (worker node)
├─ 1 instancia EC2/Azure VM/GCP Compute
├─ 1 base de datos managed (RDS, Cloud SQL)
└─ 10 containers (ver regla de agregación)

❌ NO CUENTA COMO HOST:
├─ Servicios serverless (Lambda, Cloud Functions)
├─ CDN endpoints (CloudFront, Akamai)
├─ Load balancers (ALB, NLB)
└─ Managed services sin agent (S3, DynamoDB)
```

### 3.2) Regla de Agregación de Containers

**Problema:** Un Kubernetes cluster puede tener 500+ containers efímeros.

**Solución:** Agregación 10:1

```
10 containers activos = 1 host equivalente

Ejemplos:
- 25 containers activos → 3 hosts (redondeo arriba)
- 5 containers activos → 1 host (mínimo)
- 100 containers activos → 10 hosts
```

**Definición de "container activo":**
- Envió métricas en las últimas 24 horas
- Cuenta única por `container_id` (no por nombre)
- Reinicio de container NO cuenta como nuevo

**Cálculo en Kubernetes:**
```
Cluster con:
├─ 5 worker nodes → 5 hosts
├─ 80 pods × 2 containers avg = 160 containers → 16 hosts
└─ TOTAL: 21 hosts facturables
```

### 3.3) Detección y Auditoría

**Método de conteo:**
1. Agent Rhinometric reporta `hostname` único
2. Backend registra en tabla `monitored_hosts`
3. Query cada hora: hosts activos últimas 24h
4. Dashboard de licencia muestra: **usado / límite**

**Notificaciones:**
- 80% de límite alcanzado → email a OWNER/ADMIN
- 95% de límite → email + banner en UI
- 100% de límite → bloqueo de nuevos agents (existentes siguen)

**Tabla de auditoría:**
```sql
CREATE TABLE host_usage_audit (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    physical_hosts INTEGER,
    virtual_hosts INTEGER,
    containers INTEGER,
    equivalent_hosts NUMERIC(10,2),  -- con agregación 10:1
    tier VARCHAR(50),
    limit_hosts INTEGER,
    usage_percent NUMERIC(5,2)
);
```

---

## 4. SESIONES SIMULTÁNEAS

### 4.1) Política: ILIMITADAS ✅

**Decisión estratégica:** NO limitar sesiones concurrentes.

**Razones:**
1. **Observabilidad es 24/7** - equipos globales necesitan acceso simultáneo
2. **Incidentes requieren colaboración** - múltiples personas investigando
3. **Mejor experiencia de usuario** - evita "kicked out" frustrante
4. **Competitividad** - Grafana Cloud, Datadog no limitan sesiones
5. **Simplicidad técnica** - no need para session management complex

**Implementación:**
- JWT tokens con expiración de **30 días**
- Renovación automática cada 7 días (refresh token)
- Sesiones inactivas >30 días → logout automático
- Dispositivo ilimitado por usuario (laptop, móvil, tablet)

**Monitoreo:**
- Tracking de sesiones activas por usuario (estadística)
- Alert si 1 usuario tiene >10 sesiones (posible compromiso)
- Dashboard de "Concurrent Users" (analytics, no enforcement)

---

## 5. MODALIDAD DE LICENCIAMIENTO

### 5.1) Modelo Elegido: **HOSTS + USUARIOS CON TIERS**

```
Pricing = f(hosts, tier)

Hosts: métrica principal (escala con infra)
Tier: define límites de usuarios y features
```

### 5.2) Comparación con Competencia

| Vendor | Modelo | Nuestra Ventaja |
|--------|--------|-----------------|
| **Datadog** | $15/host/mes + $31/APM host | ✅ Más barato, usuarios incluidos |
| **New Relic** | $0.30/GB data + $99/user full | ✅ Más predecible, sin sorpresas |
| **Grafana Cloud** | $8/active series + $0.50/GB logs | ✅ Más simple, no need calcular series |
| **Dynatrace** | $0.08/hora host + $11/user | ✅ Más transparente, factura fija |
| **Elastic** | $95/mes + $0.11/GB | ✅ Mejor UI, mejor soporte |

### 5.3) Ejemplos de Pricing

**Caso 1: Startup con 4 servers**
```
Infra:
- 3 EC2 instances (web, api, db)
- 10 containers (1 host equivalente)
- Total: 4 hosts

Usuarios:
- 1 CTO (OWNER)
- 1 DevOps (ADMIN)
- 2 Developers (OPERATOR)
- 3 PMs (VIEWER)

License: STARTER ($199/mes) ✅
Sobra capacidad: 1 host, 1 operator, 2 viewers
Costo por host: $49.75/host
```
infraestructura creciente**
```
Infra:
- 5 Kubernetes nodes
- 50 containers (5 hosts equivalentes)
- 2 databases RDS (2 hosts)
- Total: 12 hosts

Usuarios:
- 1 VP Engineering (OWNER)
- 2 SRE (ADMIN)
- 6 Backend devs (OPERATOR)
- 8 stakeholders (VIEWER)

License: PROFESSIONAL ($499/mes) ✅
Uso óptimo: 12/12 hosts, margen en usuarios
Costo por host: $41.58/host
Sobra capacidad: 20 hosts, 2 operators, 3 viewers
```mpresa que superó Professional (contacto ventas)**
```
Infra:
- 25 EC2 instances
- 80 containers (8 hosts equiv.)
- 5 RDS databases
- Total: 38 hosts

Usuarios:
- 1 CTO (OWNER)
- 4 Platform leads (ADMIN)
- 12 Engineers (OPERATOR)
- 20+ stakeholders (VIEWER)

⚠️ SUPERA CAPACIDAD MVP (12 hosts Professional)

Opciones:
1. Contactar ventas para Enterprise (roadmap Q3 2026)
2. Multi-licencia: 3x Professional ($1,497/mes) temporalmente
3. Esperar arquitectura distribuida (6 meses)

Nota: Enterprise requiere inversión en infraestructura
License: ENTERPRISE (custom ~$2,500/mes) ✅
Viewers ilimitados incluidos
```

---

## 6. REGLAS DE UPGRADE/DOWNGRADE

### 6.1) Upgrade Automático (Opt-in)

**Configuración en license:**
```json
{
  "auto_upgrade_enabled": true,
  "upgrade_threshold_percent": 90,
  "upgrade_grace_period_hours": 72
}
```

**Flujo:**
1. Usuario supera 90% del límite de hosts
2. Sistema envía email: "Alcanzaste 9/10 hosts, upgrade a Professional?"
3. Grace period de 72 horas
4. Si acepta → upgrade automático, prorratea factura
5. Si rechaza → bloqueo de nuevos hosts al llegar a límite

### 6.2) Downgrade (Manual)

**Restricciones:**
- Solo OWNER puede solicitar downgrade
- Debe reducir hosts/usuarios primero
- No hay reembolso prorrateado en downgrades
- Downgrade efectivo en próxima renovación

**Proceso:**
1. OWNER va a Settings → Billing → Request Downgrade
2. Sistema valida: hosts actuales < límite nuevo tier
3. Sistema valida: usuarios actuales < límite nuevo tier
4. Si pasa validación → downgrade agendado
5. Email de confirmación con fecha efectiva

---

## 7. ENFORCEMENT Y VALIDACIÓN

### 7.1) Validación en Backend

**Middleware de autorización:**
```python
@app.middleware("http")
async def validate_license_limits(request: Request, call_next):
    user = get_current_user(request)
    license = get_license_for_user(user)
    
    # Validar rol vs. acción
    action = get_action_from_request(request)
    if not has_permission(user.role, action):
        raise HTTPException(403, "Insufficient permissions")
    
    # Validar límites de licencia
    if action == "create_dashboard":
        if license.tier == "starter" and count_dashboards() >= 50:
            raise HTTPException(402, "Dashboard limit reached, upgrade required")
    
    return await call_next(request)
```

### 7.2) Validación de Hosts

**Agent Registration:**
```python
@app.post("/api/agents/register")
async def register_agent(hostname: str, license_key: str):
    license = validate_license_key(license_key)
    
    active_hosts = count_active_hosts(license)
    
    if active_hosts >= license.host_limit:
        # Verificar si es host existente (re-registro)
        if is_existing_host(hostname, license):
            return {"status": "ok", "message": "Re-registered"}
        else:
            # Nuevo host, límite alcanzado
            send_alert_to_owner(license, "Host limit reached")
            raise HTTPException(402, f"License limit reached ({license.host_limit} hosts)")
    
    register_host(hostname, license)
    return {"status": "ok", "message": "Agent registered"}
```

### 7.3) UI de Licencia

**Dashboard en Console:**
```
┌─────────────────────────────────────────┐
│  📊 License Usage - PROFESSIONAL       │
├─────────────────────────────────────────┤
│                                         │
│  Hosts:      32 / 50  ████████░░  64%  │
│  OWNER:       1 / 1   ██████████ 100%  │
│  ADMIN:       4 / 5   ████████░░  80%  │
│  OPERATOR:    7 / 10  ███████░░░  70%  │
│  VIEWER:     12 / 15  ████████░░  80%  │
│                                         │
│  Next billing: Feb 16, 2026            │
│  Monthly cost: $999                     │
│                                         │
│  [ Upgrade to Enterprise ]              │
└─────────────────────────────────────────┘
```

---

## 8. CASOS ESPECIALES

### 8.1) MSP (Managed Service Providers)

**Problema:** MSP gestiona Rhinometric para 10 clientes diferentes.

**Solución:** License por cliente (multi-tenant)

```
MSP Company X:
├─ Tenant: Cliente A (10 hosts, STARTER)
├─ Tenant: Cliente B (50 hosts, PROFESSIONAL)
├─ Tenant: Cliente C (200 hosts, ENTERPRISE)
└─ OWNER del MSP: acceso cross-tenant
```

**Pricing MSP:**
- 15% descuento en todas las licenses
- 1 OWNER del MSP puede gestionar todos los tenants
- Factura consolidada mensual

### 8.2) Ambiente de Staging/Dev

**Problema:** Cliente quiere monitorear dev + staging + prod.

**Opción 1:** Cuenta como hosts normales
```
Prod: 30 hosts
Staging: 10 hosts
Dev: 5 hosts
TOTAL: 45 hosts → Professional License
```

**Opción 2:** License separada para non-prod (50% descuento)
```
Prod License: Professional ($999/mes)
Dev License: Starter ($150/mes, 50% off)
TOTAL: $1,149/mes
```

### 8.3) Spike Temporal de Hosts

**Problema:** Black Friday, cliente escala de 50 hosts a 150 hosts por 3 días.

**Solución:** Grace period de 7 días

```
Política:
- Si superas límite por <7 días consecutivos → NO cobro adicional
- Si superas límite por >7 días → auto-upgrade o notificación
```

---

## 9. MIGRACIÓN DESDE HARDCODED ADMIN

### 9.1) Plan de Migración

**Usuario actual:**
```python
user_store = {
    "admin": {
        "username": "admin",
        "password": "admin",
        "role": "admin"
    }
}
```

**Transformación a DB:**
```sql
-- Migración inicial
INSERT INTO users (username, email, password_hash, created_at)
VALUES ('admin', 'admin@company.com', '<bcrypt_hash>', NOW())
RETURNING id;

INSERT INTO user_roles (user_id, role_id)
VALUES (<user_id>, (SELECT id FROM roles WHERE name = 'OWNER'));

-- Default license
INSERT INTO licenses (type, tier, host_limit, status)
VALUES ('trial', 'starter', 10, 'active')
RETURNING id;

UPDATE users SET license_id = <license_id> WHERE username = 'admin';
```

**Comunicación a clientes existentes:**
```
Email Template:
---
Asunto: Actualización Rhinometric - Nuevo Sistema de Usuarios

Hola,

Hemos actualizado Rhinometric con un nuevo sistema de gestión de usuarios.

Tu usuario actual "admin" ha sido migrado automáticamente con rol OWNER.

ACCIÓN REQUERIDA:
1. Inicia sesión en: https://rhinometric.company.com
2. Ve a Settings → Users
3. Actualiza tu email y contraseña
4. Invita a tu equipo (ADMIN, OPERATOR, VIEWER)

Tu licencia actual: STARTER (10 hosts, 2 ADMIN, 5 VIEWER)

Si necesitas más capacidad, contáctanos: sales@rhinometric.com
```

---

## 10. MÉTRICAS DE ÉXITO

### 10.1) KPIs de Licenciamiento

**Tracking en Prometheus:**
```promql
# Usuarios por tier
rhinometric_users_total{tier="starter", role="admin"}
rhinometric_users_total{tier="professional", role="viewer"}

# Utilización de licencia
rhinometric_license_usage_percent{tier="starter", resource="hosts"}
rhinometric_license_usage_percent{tier="professional", resource="viewers"}

# Upgrades
rhinometric_license_upgrades_total{from="starter", to="professional"}

# Revenue
rhinometric_mrr_total{tier="professional"} = count * 999
```

### 10.2) Alertas de Negocio

```yaml
- alert: HighLicenseUsage
  expr: rhinometric_license_usage_percent{resource="hosts"} > 85
  annotations:
    message: "Cliente {{ $labels.license_id }} alcanzó {{ $value }}% de hosts, oportunidad de upsell"

- alert: TrialExpiringSoon
  expr: rhinometric_license_days_until_expiry < 7 and rhinometric_license_type == "trial"
  annotations:
    message: "Trial de {{ $labels.license_id }} expira en {{ $value }} días"
```

---

## 11. PREGUNTAS FRECUENTES

**Q: ¿Puedo tener múltiples OWNER?**  
A: No. Solo 1 OWNER por licencia por razones de responsabilidad legal. El OWNER puede transferir ownership a otro usuario.

**Q: ¿Qué pasa si elimino al OWNER?**  
A: La licencia queda suspendida hasta que se designe un nuevo OWNER (proceso con verificación).

**Q: ¿Los containers consumen hosts?**  
A: Sí, pero con agregación 10:1. Cada 10 containers = 1 host.

**Q: ¿Puedo tener 5 usuarios conectados simultáneamente en STARTER?**  
A: Sí, sesiones simultáneas son ilimitadas en todos los tiers.

**Q: ¿Qué pasa si supero el límite de hosts?**  
A: Nuevos agents no se pueden registrar, pero los existentes siguen funcionando. Recibes notificación de upgrade.

**Q: ¿Puedo downgrade en medio del mes?**  
A: Downgrade es efectivo en la próxima renovación, no hay reembolso prorrateado.

**Q: ¿VIEWER puede ver datos sensibles (logs)?**  
A: Sí, VIEWER puede ver todo excepto editar. Si necesitas control granular, usa OPERATOR y limita dashboards compartidos.

**Q: ¿Puedo tener license separada para dev/staging?**  
A: Sí, ofrecemos license de no-producción con 50% descuento.

---

## 12. PRÓXIMOS PASOS

### Fase 1: Implementación RBAC (2 semanas)
- [ ] Crear tablas SQL (users, roles, licenses, user_roles)
- [ ] Implementar validación de límites en backend
- [ ] Crear UI de gestión de usuarios
- [ ] Migrar usuario "admin" hardcoded a DB

### Fase 2: Licenciamiento (1 semana)
- [ ] Crear tabla `licenses` con tiers
- [ ] Implementar conteo de hosts (agent registration)
- [ ] Dashboard de "License Usage" en Console
- [ ] Alertas de límites alcanzados

### Fase 3: Comercial (ongoing)
- [ ] Definir pricing final con equipo comercial
- [ ] Crear página de pricing en website
- [ ] Implementar flujo de upgrade self-service
- [ ] Integración con Stripe/billing

---

## APROBACIONES REQUERIDAS

| Stakeholder | Área | Estado | Fecha |
|-------------|------|--------|-------|
| **CTO** | Arquitectura técnica | ⏳ Pendiente | - |
| **CFO** | Pricing y revenue | ⏳ Pendiente | - |
| **VP Sales** | Go-to-market | ⏳ Pendiente | - |
| **Legal** | Términos de licencia | ⏳ Pendiente | - |

---

**Documento preparado por:** Arquitectura Rhinometric  
**Próxima revisión:** Post-implementación RBAC (Febrero 2026)
