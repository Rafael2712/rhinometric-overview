# Fase C - Deployment a Producción

**Fecha:** 16 Diciembre 2025  
**Versión:** Rhinometric v2.5.0  
**Autor:** Rafael Canelón

## 🎯 Objetivo

Desplegar Rhinometric v2.5.0 al servidor de producción y verificar que todos los endpoints y el sistema de emails funcionan correctamente.

---

## 📋 Pre-requisitos

### En tu máquina local:
- ✅ Fase A completa (docs limpios)
- ✅ Fase B completa (seguridad: .env rotado)
- ✅ Git commit hecho (NO pusheado aún)
- ✅ Contraseña SMTP actualizada: `041080Fe#`

### Archivos necesarios (algunos opcionales):
- ✅ `rhinometric-demo-2.5.0.ova` (~3GB) - **Opcional**
- ✅ `rhinometric-trial-2.5.0-install.sh` - **Opcional**
- ✅ PDFs de documentación (ES/EN) - **Opcional**

**Nota:** Si no tienes los archivos .ova/.sh/PDFs, los endpoints devolverán 404 pero el sistema de emails funcionará igual.

---

## 🚀 Opción 1: Deploy Automático (Recomendado)

### Paso 1: Configurar credenciales SSH

```bash
# Configurar variables de entorno (ajusta según tu servidor)
export SERVER_USER=root
export SERVER_HOST=licensing.rhinometric.com
export SERVER_PORT=22
```

### Paso 2: Ejecutar script de deploy

```bash
chmod +x deploy-to-production.sh
./deploy-to-production.sh
```

El script hará:
1. ✅ Verificar conexión SSH
2. ✅ Crear directorios en `/app/static/`
3. ✅ Subir archivos (si existen)
4. ✅ Configurar `SERVER_BASE_URL` en `.env` del servidor
5. ✅ Reiniciar License Server
6. ✅ Verificar que todo está correcto

---

## 🔧 Opción 2: Deploy Manual

Si prefieres control total o el script falla:

### Paso 1: Conectar por SSH

```bash
ssh root@licensing.rhinometric.com
```

### Paso 2: Crear directorios

```bash
mkdir -p /app/static/downloads
mkdir -p /app/static/docs/es
mkdir -p /app/static/docs/en
chmod -R 755 /app/static
```

### Paso 3: Subir archivos (desde tu máquina local)

```bash
# Demo OVA (opcional, ~3GB)
scp rhinometric-demo-2.5.0.ova root@licensing.rhinometric.com:/app/static/downloads/

# Trial Installer (opcional)
scp rhinometric-trial-2.5.0-install.sh root@licensing.rhinometric.com:/app/static/downloads/
ssh root@licensing.rhinometric.com "chmod +x /app/static/downloads/rhinometric-trial-2.5.0-install.sh"

# PDFs (opcional)
scp rhinometric-installation-guide-es.pdf root@licensing.rhinometric.com:/app/static/docs/es/
scp rhinometric-installation-guide-en.pdf root@licensing.rhinometric.com:/app/static/docs/en/
```

### Paso 4: Configurar .env en el servidor

```bash
# SSH al servidor
ssh root@licensing.rhinometric.com

# Editar .env
cd /app
nano .env  # o vim .env
```

**Asegurar que tenga:**
```env
SERVER_BASE_URL=https://licensing.rhinometric.com:5000
SMTP_PASSWORD=041080Fe#
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_FROM=rafael.canelon@rhinometric.com
```

### Paso 5: Reiniciar License Server

```bash
# Encontrar el contenedor
docker ps | grep license

# Reiniciar (usa el nombre correcto del contenedor)
docker restart rhinometric-license-server-v2

# Verificar que arrancó
docker logs -f rhinometric-license-server-v2
```

Deberías ver:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

## ✅ Verificación Post-Deploy

### Test 1: Health Check

```bash
curl https://licensing.rhinometric.com:5000/health
```

**Esperado:**
```json
{"status": "healthy", "version": "2.5.0"}
```

### Test 2: Download Endpoints

```bash
# Desde tu máquina local
./test-download-endpoints.sh https://licensing.rhinometric.com:5000
```

**Esperado:**
```
✅ GET /downloads/demo-ova → 200 OK (o 404 si no subiste el .ova)
✅ GET /downloads/trial-installer → 200 OK (o 404 si no subiste el .sh)
✅ GET /docs/installation-guide?lang=es → 200 OK (o 404 si no subiste PDF)
✅ GET /docs/installation-guide?lang=en → 200 OK (o 404 si no subiste PDF)
✅ GET /docs/api-reference → 200 OK
```

### Test 3: Email System (CRÍTICO)

```bash
# Desde tu máquina local
./scripts/test_license_emails.sh https://licensing.rhinometric.com:5000
```

**Esperado:**
```
Testing Demo License Email...
✅ Demo email sent successfully

Testing Trial License Email...
✅ Trial email sent successfully

Testing Annual License Email...
✅ Annual email sent successfully
```

**Verificar en tu email** `rafael.canelon@rhinometric.com`:
- Deberías recibir 3 emails
- Cada email tiene logo SVG
- Los links de descarga apuntan a `https://licensing.rhinometric.com:5000/downloads/...`
- Los PDFs apuntan a `https://licensing.rhinometric.com:5000/docs/...`

---

## 🐛 Troubleshooting

### Error: "Connection refused" al hacer curl

**Causa:** Firewall bloquea puerto 5000

**Solución:**
```bash
# En el servidor
ufw allow 5000/tcp
ufw reload
```

### Error: "SMTP authentication failed"

**Causa:** Password incorrecto o no configurado

**Solución:**
```bash
# En el servidor
nano /app/.env
# Asegurar: SMTP_PASSWORD=041080Fe#

docker restart rhinometric-license-server-v2
```

### Error: 404 en /downloads/demo-ova

**Causa:** Archivo .ova no subido

**Opciones:**
1. **Subir el .ova** (si lo tienes):
   ```bash
   scp rhinometric-demo-2.5.0.ova root@licensing.rhinometric.com:/app/static/downloads/
   ```

2. **Omitir por ahora** - El sistema de emails funciona igual, solo que el link de descarga dará 404. Puedes subir el .ova después.

### Error: Emails no llegan

**Diagnóstico:**
```bash
# Ver logs del License Server
docker logs rhinometric-license-server-v2 | grep -i smtp

# Buscar errores como:
# - "Authentication failed" → password incorrecto
# - "Connection timeout" → firewall bloquea puerto 465
# - "Recipient rejected" → email destino inválido
```

---

## 📊 Criterios de Éxito

Fase C está completa cuando:

- [x] SSH al servidor funciona
- [x] Directorios `/app/static/*` creados
- [x] `.env` configurado con `SERVER_BASE_URL` y `SMTP_PASSWORD`
- [x] License Server reiniciado sin errores
- [x] Health check responde 200 OK
- [x] Test de emails envía 3 correos exitosamente
- [x] Emails llegan con logo y URLs correctas de producción

**Archivos opcionales:**
- [ ] Demo OVA subido (opcional - puede hacerse después)
- [ ] Trial Installer subido (opcional - puede hacerse después)
- [ ] PDFs subidos (opcional - puede hacerse después)

---

## 🎯 Siguiente Paso: Fase D

Una vez que **todos los tests pasen**, proceder a:

**Fase D - WordPress + GitHub Release:**
1. Publicar 3 páginas WordPress
2. Crear GitHub Release v2.5.0
3. `git push` del commit de Fase A+B
4. Comunicar lanzamiento

---

**Última actualización:** 16 Diciembre 2025  
**Autor:** Rafael Canelón
