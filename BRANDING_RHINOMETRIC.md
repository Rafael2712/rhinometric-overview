# 🦏 RHINOMETRIC - ESPECIFICACIONES DE BRANDING

## 📋 Información de la Marca

### Nombre Oficial
**Rhinometric**

### Descripción
Plataforma de Observabilidad Completa - Unificando Métricas, Logs y Trazas

### URL Oficial
**rhinometric.com** (en desarrollo - AWS Lightsail + WordPress)

### Contacto
- **Soporte**: soporte@rhinometric.com
- **Ventas**: ventas@rhinometric.com
- **General**: info@rhinometric.com

---

## ⚖️ AVISOS LEGALES PARA VERSIÓN TRIAL

### 1. Aviso de Licencia Trial (Banner Principal)

```
════════════════════════════════════════════════════════════════
🦏 RHINOMETRIC - VERSIÓN TRIAL
Plataforma de Observabilidad
Válido por 180 días (6 meses)
════════════════════════════════════════════════════════════════
```

### 2. Disclaimer de Propiedad

```
Esta plataforma es propiedad y está gestionada por Rhinometric.
Aunque utiliza componentes open source (Grafana, Prometheus, Loki, Tempo),
la integración, configuración y soporte son proporcionados por Rhinometric.

© 2025 Rhinometric. Todos los derechos reservados.
```

### 3. Información de Licencia (Para archivos .lic)

```
RHINOMETRIC TRIAL LICENSE
════════════════════════════════════════════════════════════════

Producto:     Rhinometric Observability Platform
Versión:      Trial
Licenciado a: [Nombre del Cliente]
Tipo:         Uso exclusivo para evaluación
Duración:     180 días (6 meses)
Generado:     [Fecha]
Expira:       [Fecha]

════════════════════════════════════════════════════════════════
TÉRMINOS DE USO
════════════════════════════════════════════════════════════════

✅ PERMITIDO:
- Evaluación del producto
- Testing en entornos no productivos
- Demos comerciales

❌ NO PERMITIDO:
- Uso en entornos de producción
- Redistribución o reventa
- Modificación del código sin autorización
- Uso después de la fecha de expiración

════════════════════════════════════════════════════════════════
COMPONENTES OPEN SOURCE
════════════════════════════════════════════════════════════════

Esta plataforma integra los siguientes proyectos open source:

- Grafana (Apache License 2.0)
  → https://grafana.com/oss/grafana/

- Prometheus (Apache License 2.0)
  → https://prometheus.io/

- Loki (Apache License 2.0)
  → https://grafana.com/oss/loki/

- Tempo (Apache License 2.0)
  → https://grafana.com/oss/tempo/

- PostgreSQL (PostgreSQL License)
  → https://www.postgresql.org/

- Redis (BSD License)
  → https://redis.io/

La integración, configuración, dashboards personalizados, sistema de
licencias y soporte son proporcionados por Rhinometric.

════════════════════════════════════════════════════════════════
SOPORTE Y CONTACTO
════════════════════════════════════════════════════════════════

Soporte Técnico: soporte@rhinometric.com
Comercial:       ventas@rhinometric.com
Web:             https://rhinometric.com

Para convertir a licencia comercial, contacta con nuestro equipo.

════════════════════════════════════════════════════════════════
```

---

## 🎨 ELEMENTOS VISUALES

### 1. Login Page de Grafana (Personalización)

Agregar en `grafana/grafana.ini`:

```ini
[auth]
login_logo = /public/img/rhinometric-logo.png

[branding]
app_title = Rhinometric Observability
footer = Powered by Rhinometric - Trial Version (180 days)
```

### 2. Watermark en Dashboards

Agregar panel de texto en cada dashboard:

```json
{
  "type": "text",
  "title": "🦏 RHINOMETRIC TRIAL",
  "gridPos": {"h": 2, "w": 24, "x": 0, "y": 0},
  "options": {
    "content": "**Rhinometric Observability Platform** - Versión Trial (180 días) | [Licencia](#) | [Soporte](mailto:soporte@rhinometric.com)",
    "mode": "markdown"
  },
  "transparent": true
}
```

### 3. Headers HTTP (Nginx)

Agregar en `nginx.conf`:

```nginx
add_header X-Powered-By "Rhinometric Observability Platform" always;
add_header X-Rhinometric-Version "Trial-180days" always;
add_header X-Rhinometric-License "Trial" always;
```

### 4. Footer en HTML (License Dashboard)

```html
<footer style="text-align: center; padding: 20px; background: #667eea; color: white;">
  <p><strong>Rhinometric Observability Platform</strong></p>
  <p>Versión Trial - 180 días</p>
  <p>© 2025 Rhinometric. Todos los derechos reservados.</p>
  <p>
    <a href="mailto:soporte@rhinometric.com" style="color: white;">Soporte</a> | 
    <a href="mailto:ventas@rhinometric.com" style="color: white;">Ventas</a> | 
    <a href="https://rhinometric.com" style="color: white;">Web</a>
  </p>
  <p style="font-size: 0.85em; margin-top: 10px;">
    Powered by open source: Grafana • Prometheus • Loki • Tempo
  </p>
</footer>
```

---

## 📄 DOCUMENTACIÓN

### 1. README.md (Trial Package)

Debe incluir:

```markdown
# 🦏 Rhinometric Trial - Plataforma de Observabilidad

**Versión Trial: 180 días (6 meses)**

Bienvenido a Rhinometric, la plataforma completa de observabilidad que integra
métricas, logs y trazas distribuidas en una solución unificada.

---

## ⚖️ Licencia y Legal

Esta versión Trial es proporcionada bajo licencia restringida:

- ✅ **Permitido**: Evaluación, testing, demos
- ❌ **No permitido**: Uso en producción, reventa, modificación

**Términos completos**: Ver `LICENSE.txt`

---

## 🔓 Open Source

Rhinometric utiliza y agradece a los siguientes proyectos open source:

- **Grafana** - Visualización de datos
- **Prometheus** - Métricas
- **Loki** - Logs
- **Tempo** - Trazas distribuidas

La integración, configuración y soporte son proporcionados por Rhinometric.

---

© 2025 Rhinometric. Todos los derechos reservados.
```

### 2. Archivo LICENSE.txt

```
RHINOMETRIC TRIAL LICENSE AGREEMENT

Copyright © 2025 Rhinometric. All rights reserved.

GRANT OF LICENSE:
Rhinometric grants you a non-exclusive, non-transferable, limited license
to use this software solely for evaluation purposes for a period of 180 days.

RESTRICTIONS:
- You may NOT use this software in production environments
- You may NOT redistribute, sublicense, or sell this software
- You may NOT modify or create derivative works
- You may NOT remove or alter any proprietary notices

OPEN SOURCE COMPONENTS:
This software incorporates open source components, each governed by its
own license terms. See THIRD_PARTY_LICENSES.txt for details.

DISCLAIMER:
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.

TERMINATION:
This license automatically terminates after 180 days or upon breach of terms.

For commercial licensing, contact: ventas@rhinometric.com
```

---

## 🚀 IMPLEMENTACIÓN EN FASE 1

### Prioridades

#### Alta Prioridad (Crítico)
1. ✅ Avisos en archivos de licencia (.lic)
2. ✅ Footer en license-dashboard
3. ✅ README.md con branding completo
4. ✅ Headers HTTP en nginx.conf
5. ✅ Archivo LICENSE.txt

#### Media Prioridad
6. ⏳ Watermark en dashboards principales
7. ⏳ Personalización login Grafana (si es posible)
8. ⏳ Splash screen en start-trial.sh

#### Baja Prioridad (Futuro)
9. ⏸️ Logo personalizado (cuando tengas el .png)
10. ⏸️ Temas personalizados Grafana
11. ⏸️ Certificado SSL con dominio rhinometric.com

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Archivos a modificar:

- [ ] `trial-package/start-trial.sh` - Agregar banner Rhinometric
- [ ] `trial-package/README.md` - Sección de branding
- [ ] `trial-package/dashboard/templates/index.html` - Footer completo
- [ ] `trial-package/config/nginx.conf` - Headers HTTP
- [ ] `trial-package/licensing/license_server.py` - Generar .lic con branding
- [ ] `trial-package/LICENSE.txt` - Crear archivo
- [ ] `trial-package/THIRD_PARTY_LICENSES.txt` - Listar OSS
- [ ] `nginx/nginx.conf` (raíz) - Headers HTTP
- [ ] `grafana/grafana.ini` - Título y footer (si existe)

---

## 📝 NOTAS IMPORTANTES

### Sobre rhinometric.com

- **Estado**: En desarrollo (WordPress + AWS Lightsail)
- **Recomendación**: NO incluir en documentación trial hasta que esté production-ready
- **Alternativa**: Usar solo emails de contacto por ahora

### Sobre Logo

- **Pendiente**: Proporcionarás logo más adelante
- **Placeholder**: Usar emoji 🦏 mientras tanto
- **Formato esperado**: PNG transparente, SVG vectorial

### Sobre Empresa

- **No constituida formalmente** (validando mercado primero)
- **No incluir**: NIF, CIF, razón social completa
- **Usar**: Marca "Rhinometric" sin detalles corporativos

---

## ✅ CONFIRMACIÓN

Este documento refleja la implementación recomendada de branding para:

1. ✅ Indicar claramente que es propiedad de Rhinometric
2. ✅ Especificar versión trial de 6 meses (180 días)
3. ✅ Licencia de uso exclusivo para el cliente
4. ✅ Disclaimer de componentes open source
5. ✅ Información de contacto profesional
6. ✅ Sin información corporativa prematura

**¿Proceder con implementación?**
