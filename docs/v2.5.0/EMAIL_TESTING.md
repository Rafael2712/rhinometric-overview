# 📧 EMAIL TESTING GUIDE - Rhinometric v2.5.0

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Pre-requisitos](#pre-requisitos)
3. [Configuración Inicial](#configuración-inicial)
4. [Ejecutar Tests](#ejecutar-tests)
5. [Qué Verificar en el Email](#qué-verificar-en-el-email)
6. [Troubleshooting](#troubleshooting)
7. [Validación de Enlaces](#validación-de-enlaces)

---

## Resumen Ejecutivo

Este documento explica cómo probar end-to-end el sistema de licencias y emails de Rhinometric v2.5.0.

**Flujo completo:**
1. Script crea licencia → License Server genera clave
2. License Server envía email vía Zoho SMTP
3. Usuario recibe email con logo, licencia y botones de descarga
4. Usuario hace click → descarga archivos desde endpoints FastAPI

**Archivos involucrados:**
- `scripts/test_license_emails.sh` - Script de prueba automatizado
- `license-server-v2/main.py` - Endpoints de descarga
- `license-server-v2/utils/email_sender.py` - Generación y envío de emails

---

## Pre-requisitos

### Software Necesario

```bash
# Linux/macOS
curl --version       # Transfer data from/to servers
jq --version         # JSON processor (opcional pero recomendado)

# Windows (PowerShell)
# curl viene incluido en Windows 10+
# jq se puede descargar desde: https://stedolan.github.io/jq/
```

### Configuración del License Server

Asegúrate de que el License Server esté corriendo y tenga estas variables de entorno configuradas:

```env
# SMTP Configuration (Zoho)
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=<TU_APP_PASSWORD_ZOHO>
SMTP_FROM=rafael.canelon@rhinometric.com

# Server URL for download links
SERVER_BASE_URL=https://licensing.rhinometric.com:5000

# Database
DATABASE_URL=postgresql://rhinometric:rhinometric@postgres:5432/rhinometric_trial

# Redis
REDIS_URL=redis://redis:6379
```

**⚠️ CRÍTICO: SMTP_PASSWORD**

Debes obtener un **App Password** de Zoho:
1. Login en Zoho Mail
2. Settings → Security → App Passwords
3. Genera un password específico para Rhinometric
4. Cópialo en la variable `SMTP_PASSWORD`

---

## Configuración Inicial

### 1. Editar Script de Test

Abre el archivo `scripts/test_license_emails.sh`:

```bash
nano scripts/test_license_emails.sh
```

**Busca la línea 27 y cambia el email:**

```bash
# ⚠️ MODIFICA ESTO CON TU EMAIL REAL
TEST_EMAIL="${TEST_EMAIL:-your-email@example.com}"
```

**Cámbialo a:**

```bash
TEST_EMAIL="${TEST_EMAIL:-tu-email-real@gmail.com}"
```

### 2. Dar permisos de ejecución

```bash
chmod +x scripts/test_license_emails.sh
```

### 3. Verificar que el License Server está corriendo

```bash
# Verificar container Docker
docker ps | grep license-server

# Verificar endpoint health
curl http://localhost:5000/api/health
```

**Respuesta esperada:**

```json
{
  "status": "healthy",
  "version": "2.5.0",
  "service": "rhinometric-license-server",
  "timestamp": "2025-12-16T10:30:00",
  "database": "connected",
  "redis": "connected"
}
```

---

## Ejecutar Tests

### Opción 1: Servidor Local (Desarrollo)

```bash
./scripts/test_license_emails.sh http://localhost:5000
```

### Opción 2: Servidor de Producción

```bash
./scripts/test_license_emails.sh https://licensing.rhinometric.com:5000
```

### Opción 3: Usando variable de entorno

```bash
export TEST_EMAIL="tu-email@gmail.com"
./scripts/test_license_emails.sh http://localhost:5000
```

---

## Qué Verificar en el Email

El script creará **2 licencias** y enviará **2 emails**:

### Email 1: Licencia TRIAL (14 días)

**Asunto:**  
`[Rhinometric] Activación de su licencia Trial`

**Contenido esperado:**

✅ **Logo Rhinometric** - SVG embebido con gradiente cyan/azul  
✅ **Clave de licencia** - Formato: `RHINO-TRIA-2025-XXXXXXXXXXXX`  
✅ **Fecha de expiración** - 14 días desde hoy  
✅ **Botón de descarga** - "Descargar Instalador Linux (14 días)"  
✅ **URL del botón** - `https://licensing.rhinometric.com:5000/downloads/trial-installer`  
✅ **Enlaces a PDFs:**
  - Guía Instalación (ES) → `/docs/installation-guide?lang=es`
  - Guía Instalación (EN) → `/docs/installation-guide?lang=en`
  - Manual Usuario (ES) → `/docs/user-manual?lang=es`
  - Manual Usuario (EN) → `/docs/user-manual?lang=en`  
✅ **Descripción del descargable** - "Script de instalación automática para Ubuntu, Debian o CentOS. Requiere Docker 24.0+ y 8GB RAM."  
✅ **GDPR notice** - Caja amarilla con información de privacidad  
✅ **Footer** - Rhinometric v2.5.0, copyright, links legales

**Diseño esperado:**
- Header con gradiente púrpura
- Logo SVG animado (floating effect)
- License card con fondo gradiente
- Pasos de instalación numerados (1, 2, 3)
- Botón con sombra y hover effect (aunque no visible en email)

---

### Email 2: Licencia DEMO (4 horas - simulada como TRIAL)

**Asunto:**  
`[Rhinometric] Activación de su licencia Trial`

**Contenido esperado:**

Mismo diseño que TRIAL, pero con:

✅ **Botón diferente** - "Descargar OVA Demo (4 horas)"  
✅ **URL diferente** - `https://licensing.rhinometric.com:5000/downloads/demo-ova`  
✅ **Descripción diferente** - "Archivo OVA listo para importar en VirtualBox o VMware. Incluye todo el stack Rhinometric pre-configurado."

---

## Validación de Enlaces

Una vez recibas los emails, haz click en cada enlace y verifica:

### 1. Botón de Descarga TRIAL

**Click en:** "Descargar Instalador Linux (14 días)"

**Qué debe pasar:**
- ✅ Navegador descarga archivo: `rhinometric-trial-2.5.0-install.sh`
- ✅ Tamaño: ~50 KB
- ✅ Tipo de archivo: Shell script (`.sh`)
- ✅ Contenido: Script bash válido (empieza con `#!/bin/bash`)

**Verificar archivo descargado:**

```bash
head -20 rhinometric-trial-2.5.0-install.sh
```

Debe mostrar:
```bash
#!/bin/bash
# Rhinometric Trial Installer v2.5.0
# ...
```

**Si obtienes 404:**
→ El archivo `rhinometric-trial-2.5.0-install.sh` no está en `/app/static/downloads/` del servidor  
→ Ver sección [Troubleshooting](#troubleshooting)

---

### 2. Botón de Descarga DEMO

**Click en:** "Descargar OVA Demo (4 horas)"

**Qué debe pasar:**
- ✅ Navegador descarga archivo: `rhinometric-demo-2.5.0.ova`
- ✅ Tamaño: 2-4 GB (archivo grande, puede tardar varios minutos)
- ✅ Tipo de archivo: OVA (Open Virtual Appliance)

**⚠️ NOTA:** Este archivo es muy grande. Si aún no lo has subido al servidor, verás un **404**.

**Si obtienes 404:**
→ Archivo OVA no subido aún  
→ Ver [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) Fase 2 para instrucciones de cómo subir el OVA

---

### 3. Enlaces a PDFs

**Click en:** "Guía Instalación (ES)"

**Qué debe pasar:**
- ✅ Navegador abre PDF: `rhinometric-installation-guide-es.pdf`
- ✅ O descarga el archivo si el navegador no tiene visor de PDFs

**Verificar otros PDFs:**
- Guía Instalación (EN) → archivo en inglés
- Manual Usuario (ES) → manual completo en español
- Manual Usuario (EN) → manual completo en inglés

**Si obtienes 404:**
→ Los archivos PDF no están en `/app/static/docs/es/` o `/app/static/docs/en/`  
→ Ver [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) para copiar los PDFs

---

## Troubleshooting

### Problema 1: No recibo emails

**Síntomas:**
- Script dice "Email sent: true"
- Pero no llega nada a la bandeja de entrada

**Soluciones:**

1. **Revisar carpeta de spam/correo no deseado**
   ```
   Gmail → Más → Spam
   Outlook → Correo no deseado
   ```

2. **Verificar configuración SMTP en el servidor**
   ```bash
   docker logs rhinometric-license-server-v2 | grep -i smtp
   ```
   
   Busca errores como:
   - `Authentication failed`
   - `Connection refused`
   - `SSL handshake failed`

3. **Probar SMTP manualmente**
   ```bash
   docker exec rhinometric-license-server-v2 python3 << EOF
   import smtplib
   smtp = smtplib.SMTP_SSL('smtp.zoho.eu', 465)
   smtp.login('rafael.canelon@rhinometric.com', 'TU_PASSWORD')
   print("✅ SMTP Login OK")
   smtp.quit()
   EOF
   ```

4. **Verificar Zoho Mail Settings**
   - Login en Zoho Mail
   - Settings → Mail Accounts → Outgoing
   - Verificar que App Password es válido
   - Verificar que no hay límites de envío (Zoho Free: 10 emails/día)

---

### Problema 2: Email llega pero sin logo

**Síntomas:**
- Email se ve bien pero logo no aparece

**Causa:**
- Algunos clientes de email bloquean SVG por seguridad

**Solución:**
- El logo es un SVG inline, debería funcionar en la mayoría de clientes
- Si no aparece, considera convertir a PNG base64:
  ```bash
  # Generar PNG del logo y convertir a base64
  base64 logo.png > logo-base64.txt
  ```

---

### Problema 3: Enlaces no funcionan (404)

**Síntomas:**
- Click en botón → "404 Not Found"

**Diagnóstico:**

1. **Verificar que endpoints existen en el código:**
   ```bash
   grep -n "downloads/demo-ova" license-server-v2/main.py
   grep -n "downloads/trial-installer" license-server-v2/main.py
   ```

2. **Verificar archivos en el servidor:**
   ```bash
   docker exec rhinometric-license-server-v2 ls -lh /app/static/downloads/
   docker exec rhinometric-license-server-v2 ls -lh /app/static/docs/es/
   docker exec rhinometric-license-server-v2 ls -lh /app/static/docs/en/
   ```

3. **Copiar archivos si faltan:**
   ```bash
   # Desde tu máquina local al servidor
   scp rhinometric-demo-2.5.0.ova user@server:/tmp/
   
   # Luego dentro del servidor
   docker cp /tmp/rhinometric-demo-2.5.0.ova \
     rhinometric-license-server-v2:/app/static/downloads/
   ```

4. **Verificar permisos:**
   ```bash
   docker exec rhinometric-license-server-v2 \
     chmod 644 /app/static/downloads/*
   ```

---

### Problema 4: URL incorrecta en el email

**Síntomas:**
- Email muestra URL tipo: `http://localhost:5000/downloads/...`
- Debería ser: `https://licensing.rhinometric.com:5000/downloads/...`

**Causa:**
- Variable `SERVER_BASE_URL` no configurada correctamente

**Solución:**

1. **Editar docker-compose.yml o .env:**
   ```yaml
   services:
     rhinometric-license-server-v2:
       environment:
         - SERVER_BASE_URL=https://licensing.rhinometric.com:5000
   ```

2. **Reiniciar License Server:**
   ```bash
   docker compose -f docker-compose-v2.5.0.yml restart rhinometric-license-server-v2
   ```

3. **Crear nueva licencia de prueba** (las antiguas tendrán URL vieja)

---

### Problema 5: Email se ve roto en cliente

**Síntomas:**
- Email no tiene formato (todo texto plano)
- O diseño se ve mal

**Diagnóstico:**

1. **Verificar que email tiene HTML:**
   ```bash
   docker logs rhinometric-license-server-v2 | grep "Email sent"
   ```

2. **Probar en diferentes clientes:**
   - Gmail web (mejor soporte)
   - Outlook web
   - Apple Mail
   - Thunderbird

**Nota:** Todos los estilos en el email son inline CSS para máxima compatibilidad.

---

## Validación Completa - Checklist

Usa este checklist para validar que TODO funciona:

- [ ] **Script ejecuta sin errores**
  - [ ] Health check pasa (HTTP 200)
  - [ ] Licencia TRIAL creada (HTTP 200/201)
  - [ ] Licencia DEMO creada (HTTP 200/201)

- [ ] **Emails recibidos**
  - [ ] Email TRIAL en bandeja de entrada
  - [ ] Email DEMO en bandeja de entrada
  - [ ] Emails no en spam

- [ ] **Diseño del email**
  - [ ] Logo Rhinometric visible (SVG cyan/azul)
  - [ ] Gradiente púrpura en header
  - [ ] License card con datos correctos
  - [ ] Botón de descarga con color gradient
  - [ ] Pasos de instalación numerados
  - [ ] GDPR notice amarillo
  - [ ] Footer con v2.5.0

- [ ] **Enlaces funcionan - TRIAL**
  - [ ] Botón descarga → `rhinometric-trial-2.5.0-install.sh` (HTTP 200)
  - [ ] PDF Instalación ES → abre PDF (HTTP 200)
  - [ ] PDF Instalación EN → abre PDF (HTTP 200)
  - [ ] PDF Manual ES → abre PDF (HTTP 200)
  - [ ] PDF Manual EN → abre PDF (HTTP 200)

- [ ] **Enlaces funcionan - DEMO**
  - [ ] Botón descarga → `rhinometric-demo-2.5.0.ova` (HTTP 200 o 404 si no subido)
  - [ ] PDFs funcionan igual que TRIAL

- [ ] **Contenido correcto**
  - [ ] Clave de licencia visible y copiable
  - [ ] Fecha de expiración correcta (14 días desde hoy)
  - [ ] Nombre del cliente correcto
  - [ ] URLs apuntan a `SERVER_BASE_URL` configurado

---

## Siguientes Pasos

Una vez validado que los emails funcionan:

1. **Probar con clientes reales** (beta testers)
2. **Configurar dominio personalizado** (si `SERVER_BASE_URL` es temporal)
3. **Subir archivos grandes a servidor** (OVA 3GB)
4. **Configurar SPF/DKIM en DNS** para mejor deliverability
5. **Monitorear logs de SMTP** para ver tasa de entrega

---

## Recursos Adicionales

- [DOWNLOAD_ENDPOINTS.md](DOWNLOAD_ENDPOINTS.md) - Documentación técnica completa de endpoints
- [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) - Checklist de deployment completo
- [test_license_emails.sh](../../scripts/test_license_emails.sh) - Script de testing automatizado
- [Zoho SMTP Documentation](https://www.zoho.com/mail/help/adminconsole/smtp-service.html) - Configuración SMTP

---

## Soporte

Si encuentras problemas no documentados aquí:

**Email:** rafael.canelon@rhinometric.com  
**Logs del servidor:** `docker logs rhinometric-license-server-v2 -f`  
**Código:** `license-server-v2/utils/email_sender.py`

---

**Última actualización:** 16 Diciembre 2025  
**Versión:** 2.5.0  
**Autor:** Rafael Canelón
