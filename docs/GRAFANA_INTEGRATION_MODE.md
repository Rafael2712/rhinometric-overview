# Grafana Integration Mode - Rhinometric v2.5.1

**Last Updated**: 23 Enero 2026  
**Status**: Production (Hetzner)  
**Mode**: Direct Links (Port 3000)

---

## Overview

En Rhinometric v2.5.1 desplegado en Hetzner Cloud, la integración con Grafana utiliza **links directos** en lugar de un reverse proxy embebido.

### Arquitectura Actual

```
┌─────────────────────────────────────────┐
│ Console Frontend (Port 3002)            │
│ ┌─────────────────────────────────────┐ │
│ │ Dashboards Page                     │ │
│ │ Logs Page                           │ │
│ │ Traces Page                         │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  │
                  │ window.open(...)
                  ↓
┌─────────────────────────────────────────┐
│ Grafana (Port 3000)                     │
│ - Public access: http://89.167.6.43:3000│
│ - Anonymous auth: Admin role            │
│ - No RBAC required for this version     │
└─────────────────────────────────────────┘
```

### ¿Por Qué Esta Decisión?

Durante la migración a Hetzner, se identificaron desafíos técnicos complejos al integrar Grafana detrás del reverse proxy FastAPI `/api/grafana/`:

1. **Configuración Subpath Compleja**: Alinear `GF_SERVER_ROOT_URL`, `GF_SERVER_SERVE_FROM_SUB_PATH` y el proxy causó múltiples iteraciones fallidas.
2. **Asset Loading Issues**: CSS/JS de Grafana fallaban con 404 debido a desajustes entre `<base href>` y rutas reales.
3. **Time to Market**: La plataforma necesitaba estar operativa para continuar desarrollo de features (AI Anomaly, Web corporativa, etc.).

**Decisión estratégica**: Priorizar funcionalidad sobre arquitectura ideal. El proxy embebido se abordará en v2.6.x cuando haya tiempo para una integración con RBAC completo.

---

## Implementación Técnica

### Frontend Utilities

Archivo: `rhinometric-console/frontend/src/utils/grafana.ts`

```typescript
const GRAFANA_PUBLIC_URL = 
  import.meta.env.VITE_GRAFANA_PUBLIC_URL || "http://89.167.6.43:3000";

export function openGrafanaDashboard(uid: string, params?: string) {
  const url = `${GRAFANA_PUBLIC_URL}/d/${uid}${params ? `?${params}` : ""}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

export function openGrafanaExplore(extraPath: string) {
  const url = `${GRAFANA_PUBLIC_URL}/explore${extraPath}`;
  window.open(url, "_blank", "noopener,noreferrer");
}
```

### Grafana Configuration

```yaml
# docker-compose-v2.5.0-core.yml
grafana:
  environment:
    - GF_SERVER_ROOT_URL=http://89.167.6.43:3000/
    - GF_SERVER_SERVE_FROM_SUB_PATH=false
    - GF_AUTH_ANONYMOUS_ENABLED=true
    - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    - GF_SECURITY_ALLOW_EMBEDDING=true
  ports:
    - "3000:3000"
```

**Nota**: `ROOT_URL` sin subpath porque acceso es directo, no a través del proxy.

### Firewall Rules

```bash
# UFW en Hetzner VM
ufw allow 3000/tcp  # Grafana público
ufw allow 3002/tcp  # Console frontend
```

### Security Model (v2.5.1)

- **Authentication**: Anonymous con rol Admin (desarrollo/demo)
- **Network**: Puerto 3000 expuesto públicamente
- **RBAC**: No implementado en esta versión
- **Token-based auth**: No requerido (acceso directo)

⚠️ **Advertencia**: Esta configuración es apropiada para entornos de desarrollo y demo. Para producción con clientes, considerar implementar RBAC en v2.6.x.

---

## User Experience

### Dashboards Page

1. Usuario ve lista de dashboards en Console
2. Click en dashboard → **Nueva pestaña** se abre en `http://89.167.6.43:3000/d/{uid}?kiosk=tv`
3. Dashboard renderiza completamente en Grafana sin proxy intermedio

### Logs Page

1. Usuario configura query LogQL en Console
2. Click "View in Grafana" → **Nueva pestaña** con Grafana Explore + Loki datasource
3. Query pre-cargada, usuario puede refinar en Grafana

### Traces Page

1. Usuario ve lista de traces en Console
2. Click en trace → Modal con waterfall chart
3. Click "View in Grafana" → **Nueva pestaña** con Grafana Explore + Jaeger datasource
4. Trace ID pre-cargado

---

## Roadmap para v2.6.x

### Objetivos: Proxy Embebido con RBAC

**Fase 1: Estabilizar Proxy** (2-3 días)
- [ ] Documentar configuración correcta de SERVE_FROM_SUB_PATH
- [ ] Crear tests automatizados para proxy HTTP
- [ ] Implementar reescritura correcta de headers `Location`
- [ ] Manejar rutas de assets (`/public/...`) correctamente

**Fase 2: Implementar RBAC** (3-5 días)
- [ ] Grafana Service Accounts en lugar de Anonymous
- [ ] Token-based authentication en proxy
- [ ] Mapeo de roles Console → Grafana
- [ ] Permisos por dashboard basados en licencia/tier

**Fase 3: Producción Segura** (2 días)
- [ ] Cerrar puerto 3000 públicamente (solo acceso interno Docker)
- [ ] Nginx reverse proxy delante de FastAPI para mayor rendimiento
- [ ] Rate limiting y protección contra abuso
- [ ] Monitoreo de proxy response times

### Alternativa: Nginx desde el Principio

Si el proxy FastAPI sigue siendo problemático:

```nginx
location /api/grafana/ {
    proxy_pass http://rhinometric-grafana:3000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Asset handling
    sub_filter_once off;
    sub_filter 'href="/' 'href="/api/grafana/';
    sub_filter 'src="/' 'src="/api/grafana/';
}
```

**Ventaja**: Nginx es industry standard para reverse proxy, documentación extensa, performance superior.

---

## Lessons Learned

### ❌ Errores Evitados

1. **No pelear con configuración compleja bajo presión**: Si algo no funciona después de 5 intentos, cambiar estrategia.
2. **Time-box technical debt**: Invertir 3+ horas en un problema bloqueante sin resultados es señal de cambiar enfoque.
3. **Pragmatismo sobre pureza arquitectónica**: Un sistema funcionando con workarounds es mejor que un diseño ideal que no funciona.

### ✅ Aprendizajes Técnicos

1. **`GF_SERVER_SERVE_FROM_SUB_PATH`** requiere que:
   - ROOT_URL contenga el subpath completo (`http://domain:port/api/grafana/`)
   - Proxy envíe requests A ese subpath (`http://grafana:3000/api/grafana/...`)
   - Ambos lados estén alineados o Grafana generará HTML con base href incorrecta

2. **Grafana assets siempre se cargan relativos a `<base href>`**:
   - Con SERVE_FROM_SUB_PATH=false: Assets en `/public/...`
   - Con SERVE_FROM_SUB_PATH=true: Assets en `/api/grafana/public/...`
   - Desajuste = 404s masivos en browser

3. **Dashboard UIDs duplicados impiden provisioning**:
   - Grafana logs: "the same UID is used more than once"
   - Resultado: Dashboards no se escriben a DB
   - Solución: Verificar archivos JSON antes de desplegar

---

## Testing Checklist (Antes de Desplegar v2.6.x)

### Grafana Direct Access
- [ ] `curl http://89.167.6.43:3000/api/health` → `{"database":"ok"}`
- [ ] Browser a `http://89.167.6.43:3000` → Login page o home
- [ ] Dashboard directo: `http://89.167.6.43:3000/d/{uid}` → Renderiza con CSS/JS

### Console Integration
- [ ] Dashboards page lista todos los dashboards (no 0)
- [ ] Click en dashboard → Nueva pestaña abre Grafana
- [ ] Logs "View in Grafana" → Explore con query LogQL pre-cargada
- [ ] Traces "View in Grafana" → Explore con trace ID pre-cargado

### Proxy Embebido (v2.6.x)
- [ ] `/api/grafana/d/{uid}` → HTML completo (no "Not found")
- [ ] CSS/JS cargan sin 404s (DevTools Network tab)
- [ ] Location header reescrito correctamente (no loops)
- [ ] Token authentication funciona
- [ ] RBAC: Admin ve todos dashboards, Viewer ve solo permitidos

---

## Contact & Support

**Implementación**: Claude (GitHub Copilot)  
**Rama**: `feature/use-direct-grafana-links`  
**Docs**: `docs/GRAFANA_INTEGRATION_MODE.md`  
**Related**: `AUDITORIA_MIGRACION_GRAFANA.md`

Para preguntas sobre esta arquitectura o roadmap de v2.6.x, consultar con el equipo de ingeniería.
