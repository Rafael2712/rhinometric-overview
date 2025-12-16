# Rhinometric v2.5.0 - Download & Documentation Endpoints

## 📋 Tabla de Contenidos

- [Resumen Ejecutivo](#resumen-ejecutivo)
- [Arquitectura de Endpoints](#arquitectura-de-endpoints)
- [Endpoints de Descarga](#endpoints-de-descarga)
- [Endpoints de Documentación](#endpoints-de-documentación)
- [Deployment y Configuración](#deployment-y-configuración)
- [Integración con Emails](#integración-con-emails)
- [Testing y Verificación](#testing-y-verificación)
- [WordPress Integration](#wordpress-integration)
- [Troubleshooting](#troubleshooting)

---

## Resumen Ejecutivo

Rhinometric v2.5.0 implementa un sistema completo de distribución de archivos y documentación a través del **License Server v2** (FastAPI, puerto 5000). Este servidor centraliza:

- ✅ Descarga de OVA demo (4 horas)
- ✅ Descarga de instalador trial Linux (14 días)
- ✅ Servicio de PDFs de documentación (ES/EN)
- ✅ Enlaces automáticos en emails de licencia
- ✅ Páginas HTML listas para WordPress

**Ventajas:**
- Control total sobre distribución de archivos
- No dependemos de la API de WordPress (bloqueada)
- URLs estables y predecibles
- Streaming eficiente para archivos grandes (OVA ~3GB)
- Multilenguaje (ES/EN) para documentación

---

## Arquitectura de Endpoints

### Base URL

```
Production:  https://licensing.rhinometric.com:5000
Development: http://localhost:5000
Docker:      http://rhinometric-license-server-v2:5000
```

Configuración en `.env` del License Server:

```env
SERVER_BASE_URL=https://licensing.rhinometric.com:5000
```

### Estructura de Archivos en Disco

```
/app/
├── static/
│   ├── downloads/
│   │   ├── rhinometric-demo-2.5.0.ova                    # ~2-4 GB
│   │   └── rhinometric-trial-2.5.0-install.sh            # ~50 KB
│   └── docs/
│       ├── es/
│       │   ├── rhinometric-installation-guide-es.pdf     # Guía instalación español
│       │   └── rhinometric-user-manual-es.pdf            # Manual usuario español
│       └── en/
│           ├── rhinometric-installation-guide-en.pdf     # Installation guide English
│           └── rhinometric-user-manual-en.pdf            # User manual English
└── docs/
    ├── manual_usuario.pdf                                 # Legacy (para email attachments)
    └── guia_instalacion.pdf                               # Legacy (para email attachments)
```

**IMPORTANTE:** Los directorios se crean automáticamente al arrancar el License Server. Solo debes copiar los archivos en las rutas correctas.

---

## Endpoints de Descarga

### 1. Demo OVA (4 horas)

**Endpoint:** `GET /downloads/demo-ova`

**Descripción:** Descarga la máquina virtual OVA pre-configurada con todo el stack Rhinometric.

**Respuesta:**
- **Content-Type:** `application/octet-stream`
- **Content-Disposition:** `attachment; filename="rhinometric-demo-2.5.0.ova"`
- **Streaming:** Sí (chunks de 8MB para archivos grandes)

**Ejemplo curl:**

```bash
curl -L -o rhinometric-demo.ova \
  https://licensing.rhinometric.com:5000/downloads/demo-ova
```

**Ejemplo wget:**

```bash
wget https://licensing.rhinometric.com:5000/downloads/demo-ova \
  -O rhinometric-demo-2.5.0.ova
```

**Errores posibles:**

- **404 Not Found:** El archivo OVA no está en `/app/static/downloads/rhinometric-demo-2.5.0.ova`
  ```json
  {
    "detail": "Demo OVA file not found. Please contact support@rhinometric.com"
  }
  ```

**Casos de uso:**
- Usuario descarga desde página WordPress (Demo OVA)
- Email automático de licencia `demo_cloud` incluye este enlace
- Descargas directas para evaluaciones rápidas

---

### 2. Trial Installer (14 días)

**Endpoint:** `GET /downloads/trial-installer`

**Descripción:** Descarga el script de instalación automática para Linux.

**Respuesta:**
- **Content-Type:** `application/x-sh`
- **Content-Disposition:** `attachment; filename="rhinometric-trial-2.5.0-install.sh"`

**Ejemplo curl:**

```bash
curl -L -o rhinometric-install.sh \
  https://licensing.rhinometric.com:5000/downloads/trial-installer

chmod +x rhinometric-install.sh
sudo ./rhinometric-install.sh
```

**Ejemplo wget:**

```bash
wget https://licensing.rhinometric.com:5000/downloads/trial-installer \
  -O rhinometric-trial-install.sh

chmod +x rhinometric-trial-install.sh
sudo ./rhinometric-trial-install.sh
```

**Errores posibles:**

- **404 Not Found:** El script no está en `/app/static/downloads/rhinometric-trial-2.5.0-install.sh`
  ```json
  {
    "detail": "Trial installer not found. Please contact support@rhinometric.com"
  }
  ```

**Casos de uso:**
- Usuario descarga desde página WordPress (Trial Linux)
- Email automático de licencia `trial` incluye este enlace
- Instalaciones remotas vía SSH

---

### 3. Info de Descargas

**Endpoint:** `GET /downloads/info`

**Descripción:** Devuelve metadatos sobre todos los archivos disponibles (tamaño, disponibilidad, descripción).

**Respuesta JSON:**

```json
{
  "downloads": {
    "demo_ova": {
      "available": true,
      "type": "Virtual Machine (OVA)",
      "description": "4-hour demo for VirtualBox/VMware - ready to import and test",
      "size_mb": 3072.45,
      "path": "rhinometric-demo-2.5.0.ova"
    },
    "trial_installer": {
      "available": true,
      "type": "Shell Script (.sh)",
      "description": "14-day trial installer for Linux servers (Ubuntu/Debian/CentOS)",
      "size_mb": 0.05,
      "path": "rhinometric-trial-2.5.0-install.sh"
    }
  },
  "documentation": {
    "installation_guide_es": {
      "available": true,
      "type": "PDF Document",
      "description": "Guía completa de instalación en español",
      "size_mb": 2.34,
      "path": "rhinometric-installation-guide-es.pdf"
    },
    "installation_guide_en": {
      "available": true,
      "type": "PDF Document",
      "description": "Complete installation guide in English",
      "size_mb": 2.30,
      "path": "rhinometric-installation-guide-en.pdf"
    },
    "user_manual_es": {
      "available": true,
      "type": "PDF Document",
      "description": "Manual de usuario de Rhinometric Console en español",
      "size_mb": 3.12,
      "path": "rhinometric-user-manual-es.pdf"
    },
    "user_manual_en": {
      "available": true,
      "type": "PDF Document",
      "description": "Rhinometric Console user manual in English",
      "size_mb": 3.08,
      "path": "rhinometric-user-manual-en.pdf"
    }
  },
  "server_info": {
    "version": "2.5.0",
    "base_url": "http://[SERVER]:5000",
    "endpoints": {
      "demo_ova": "/downloads/demo-ova",
      "trial_installer": "/downloads/trial-installer",
      "installation_guide": "/docs/installation-guide?lang=es|en",
      "user_manual": "/docs/user-manual?lang=es|en"
    }
  }
}
```

**Ejemplo curl:**

```bash
curl https://licensing.rhinometric.com:5000/downloads/info | jq
```

**Casos de uso:**
- Verificación automática de disponibilidad antes de enlazar en WordPress
- Dashboards de status interno
- Scripts de monitoring

---

## Endpoints de Documentación

### 1. Guía de Instalación

**Endpoint:** `GET /docs/installation-guide?lang={es|en}`

**Parámetros query:**
- `lang` (opcional): `es` (default) o `en`

**Respuesta:**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="rhinometric-installation-guide-{lang}.pdf"`

**Ejemplos:**

```bash
# Español (default)
curl -L -o guia-instalacion.pdf \
  https://licensing.rhinometric.com:5000/docs/installation-guide

# Inglés
curl -L -o installation-guide.pdf \
  https://licensing.rhinometric.com:5000/docs/installation-guide?lang=en
```

**Contenido del PDF:**
- Requisitos de sistema
- Instalación en Ubuntu/Debian/CentOS
- Configuración de Docker y Docker Compose
- Configuración de licencias
- Troubleshooting común
- Alta disponibilidad (HA)

**Errores posibles:**

- **404 Not Found:** PDF no encontrado en `/app/static/docs/{lang}/rhinometric-installation-guide-{lang}.pdf`
  ```json
  {
    "detail": "Installation guide (es) not found. Please contact support@rhinometric.com"
  }
  ```

---

### 2. Manual de Usuario

**Endpoint:** `GET /docs/user-manual?lang={es|en}`

**Parámetros query:**
- `lang` (opcional): `es` (default) o `en`

**Respuesta:**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="rhinometric-user-manual-{lang}.pdf"`

**Ejemplos:**

```bash
# Español
curl -L -o manual-usuario.pdf \
  https://licensing.rhinometric.com:5000/docs/user-manual

# Inglés
curl -L -o user-manual.pdf \
  https://licensing.rhinometric.com:5000/docs/user-manual?lang=en
```

**Contenido del PDF:**
- Navegación en Grafana y Rhinometric Console
- Configuración de data sources
- Creación de dashboards personalizados
- Sistema de alertas (Alertmanager)
- API Connector - Integración de APIs externas
- AI Anomaly Engine - Detección de anomalías
- Gestión de licencias
- Drilldown (métricas → logs → trazas)

**Errores posibles:**

- **404 Not Found:** PDF no encontrado

---

## Deployment y Configuración

### Paso 1: Preparar Archivos

En tu servidor de producción donde corre el License Server:

```bash
# Crear estructura de directorios (automática, pero puedes hacerlo manualmente)
mkdir -p /app/static/downloads
mkdir -p /app/static/docs/es
mkdir -p /app/static/docs/en

# Verificar permisos
ls -la /app/static/
```

### Paso 2: Copiar Archivos

#### Opción A: SCP desde tu máquina local

```bash
# Subir OVA demo (archivo grande, puede tardar)
scp rhinometric-demo-2.5.0.ova \
  user@licensing.rhinometric.com:/app/static/downloads/

# Subir instalador trial
scp rhinometric-trial-2.5.0-install.sh \
  user@licensing.rhinometric.com:/app/static/downloads/

# Subir PDFs español
scp rhinometric-installation-guide-es.pdf \
  user@licensing.rhinometric.com:/app/static/docs/es/

scp rhinometric-user-manual-es.pdf \
  user@licensing.rhinometric.com:/app/static/docs/es/

# Subir PDFs inglés
scp rhinometric-installation-guide-en.pdf \
  user@licensing.rhinometric.com:/app/static/docs/en/

scp rhinometric-user-manual-en.pdf \
  user@licensing.rhinometric.com:/app/static/docs/en/
```

#### Opción B: Descargar desde GitHub Releases

```bash
# Si tienes los archivos en GitHub Releases
cd /app/static/downloads

wget https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.5.0/rhinometric-demo-2.5.0.ova

wget https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.5.0/rhinometric-trial-2.5.0-install.sh
```

#### Opción C: Dentro del contenedor Docker

```bash
# Si el License Server corre en Docker, copia al contenedor
docker cp rhinometric-demo-2.5.0.ova \
  rhinometric-license-server-v2:/app/static/downloads/

docker cp rhinometric-trial-2.5.0-install.sh \
  rhinometric-license-server-v2:/app/static/downloads/

# PDFs
docker cp docs/es/rhinometric-installation-guide-es.pdf \
  rhinometric-license-server-v2:/app/static/docs/es/

docker cp docs/es/rhinometric-user-manual-es.pdf \
  rhinometric-license-server-v2:/app/static/docs/es/

docker cp docs/en/rhinometric-installation-guide-en.pdf \
  rhinometric-license-server-v2:/app/static/docs/en/

docker cp docs/en/rhinometric-user-manual-en.pdf \
  rhinometric-license-server-v2:/app/static/docs/en/
```

### Paso 3: Verificar Archivos en el Servidor

```bash
# Conectar al contenedor (si Docker)
docker exec -it rhinometric-license-server-v2 bash

# Listar archivos
ls -lh /app/static/downloads/
ls -lh /app/static/docs/es/
ls -lh /app/static/docs/en/

# Verificar tamaños
du -sh /app/static/downloads/*
du -sh /app/static/docs/es/*
du -sh /app/static/docs/en/*
```

**Tamaños esperados:**
- `rhinometric-demo-2.5.0.ova`: 2-4 GB
- `rhinometric-trial-2.5.0-install.sh`: ~50 KB
- PDFs: 1-5 MB cada uno

### Paso 4: Configurar Variables de Entorno

En tu `docker-compose-v2.5.0.yml` o `.env` del License Server:

```env
# Base URL para enlaces en emails
SERVER_BASE_URL=https://licensing.rhinometric.com:5000

# O si usas IP pública
SERVER_BASE_URL=http://203.0.113.45:5000
```

### Paso 5: Reiniciar License Server

```bash
# Si Docker Compose
docker compose -f docker-compose-v2.5.0.yml restart rhinometric-license-server-v2

# Verificar logs
docker logs rhinometric-license-server-v2 --tail 50
```

### Paso 6: Persistencia con Volumes (Recomendado)

Para evitar perder archivos al actualizar el contenedor, usa volúmenes:

**docker-compose-v2.5.0.yml:**

```yaml
services:
  rhinometric-license-server-v2:
    image: rhinometric/license-server:2.5.0
    ports:
      - "5000:5000"
    volumes:
      # Persistir archivos de descarga
      - ./rhinometric_static_downloads:/app/static/downloads
      - ./rhinometric_static_docs:/app/static/docs
      # Otros volúmenes...
    environment:
      - SERVER_BASE_URL=https://licensing.rhinometric.com:5000
```

Ahora los archivos están en:
```
./rhinometric_static_downloads/rhinometric-demo-2.5.0.ova
./rhinometric_static_downloads/rhinometric-trial-2.5.0-install.sh
./rhinometric_static_docs/es/rhinometric-installation-guide-es.pdf
./rhinometric_static_docs/en/rhinometric-user-manual-en.pdf
```

---

## Integración con Emails

El sistema de emails (`utils/email_sender.py`) ya está configurado para usar estos endpoints.

### Flujo Automático

1. Usuario solicita licencia (POST `/api/admin/licenses`)
2. License Server genera license key
3. Email se envía automáticamente con:
   - **demo_cloud:** Enlace a `/downloads/demo-ova`
   - **trial:** Enlace a `/downloads/trial-installer`
   - **annual_standard:** Enlace a GitHub Releases (producción)
4. PDFs adjuntos + enlaces online a `/docs/installation-guide` y `/docs/user-manual`

### Ejemplo de Email Generado

Para una licencia **trial**:

```html
<a href="https://licensing.rhinometric.com:5000/downloads/trial-installer" class="btn">
    📥 Descargar Instalador Linux (14 días)
</a>

<p>Script de instalación automática para Ubuntu, Debian o CentOS. Requiere Docker 24.0+ y 8GB RAM.</p>

<!-- Enlaces a documentación -->
<a href="https://licensing.rhinometric.com:5000/docs/installation-guide?lang=es">
    📘 Guía Instalación (ES)
</a>
<a href="https://licensing.rhinometric.com:5000/docs/user-manual?lang=en">
    📗 User Manual (EN)
</a>
```

### Personalización de URLs

Si necesitas cambiar el `SERVER_BASE_URL` (por ejemplo, para desarrollo local):

```bash
# En .env del License Server
SERVER_BASE_URL=http://localhost:5000

# O en producción con dominio custom
SERVER_BASE_URL=https://downloads.rhinometric.io
```

Los emails se generarán con la nueva URL automáticamente.

---

## Testing y Verificación

### Test 1: Verificar Disponibilidad de Archivos

```bash
curl https://licensing.rhinometric.com:5000/downloads/info | jq '.downloads'
```

**Resultado esperado:**
```json
{
  "demo_ova": {
    "available": true,
    "size_mb": 3072.45
  },
  "trial_installer": {
    "available": true,
    "size_mb": 0.05
  }
}
```

### Test 2: Descargar Demo OVA (muestra progreso)

```bash
wget --progress=bar:force \
  https://licensing.rhinometric.com:5000/downloads/demo-ova \
  -O test-demo.ova
```

**Validar:**
```bash
# Verificar tamaño
ls -lh test-demo.ova

# Verificar integridad (si tienes checksum)
sha256sum test-demo.ova
```

### Test 3: Descargar Trial Installer

```bash
curl -L -o test-installer.sh \
  https://licensing.rhinometric.com:5000/downloads/trial-installer

# Verificar que sea un script válido
file test-installer.sh
head -20 test-installer.sh
```

### Test 4: Descargar PDFs

```bash
# Español
curl -L -o test-guide-es.pdf \
  https://licensing.rhinometric.com:5000/docs/installation-guide?lang=es

# Inglés
curl -L -o test-manual-en.pdf \
  https://licensing.rhinometric.com:5000/docs/user-manual?lang=en

# Verificar PDFs válidos
file test-guide-es.pdf
pdfinfo test-guide-es.pdf
```

### Test 5: Simular Email de Licencia

Crear licencia de prueba y verificar que el email llegue con enlaces correctos:

```bash
curl -X POST https://licensing.rhinometric.com:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "client_email": "tu-email@ejemplo.com",
    "license_type": "trial",
    "client_company": "Test Company"
  }'
```

**Verificar:**
1. Email recibido en tu bandeja
2. Botón de descarga apunta a: `https://licensing.rhinometric.com:5000/downloads/trial-installer`
3. Enlaces de PDFs apuntan a: `/docs/installation-guide?lang=es` y `/docs/user-manual?lang=es`
4. Click en enlaces descarga archivos correctamente

### Test 6: Performance y Streaming (OVA grande)

```bash
# Medir tiempo de descarga
time curl -L -o test-ova.ova \
  https://licensing.rhinometric.com:5000/downloads/demo-ova

# Verificar que no consume toda la RAM del servidor
# (debe usar streaming, no cargar todo en memoria)
```

---

## WordPress Integration

### Páginas HTML Listas

En `docs/v2.5.0/wordpress/` tienes 3 archivos HTML listos para pegar en WordPress:

1. **01-demo-ova-page.html** → Página "Demo Rhinometric - Descarga OVA"
2. **02-trial-linux-page.html** → Página "Trial 14 días - Instalación Linux"
3. **03-documentation-page.html** → Página "Documentación Rhinometric"

### Pasos para Crear Páginas en WordPress

#### Paso 1: Acceder a wp-admin

```
https://rhinometric.com/wp-admin
```

Login con credenciales de administrador.

#### Paso 2: Crear Nueva Página

1. **Páginas** → **Añadir nueva**
2. **Título:** "Demo Rhinometric - Descarga OVA" (o según corresponda)
3. Click en **tres puntos** (arriba derecha) → **Editar como HTML**
4. **Borrar todo** el contenido actual
5. **Pegar** el contenido de `01-demo-ova-page.html`

#### Paso 3: Ajustar URLs (si es necesario)

Buscar en el HTML pegado:

```html
href="https://licensing.rhinometric.com:5000/downloads/demo-ova"
```

Si tu servidor tiene otra URL, reemplazar globalmente:

```
https://licensing.rhinometric.com:5000 → https://tu-servidor.com:5000
```

#### Paso 4: Publicar

1. **Vista previa** para verificar diseño
2. **Publicar**
3. **Ver página** para verificar en producción

#### Paso 5: Configurar Permalink (opcional)

En **Ajustes** → **Enlaces permanentes**, configurar URLs amigables:

```
https://rhinometric.com/demo
https://rhinometric.com/trial
https://rhinometric.com/docs
```

### URLs de las Páginas WordPress

Una vez publicadas:

```
https://rhinometric.com/demo          → 01-demo-ova-page.html
https://rhinometric.com/trial         → 02-trial-linux-page.html
https://rhinometric.com/documentation → 03-documentation-page.html
```

### Actualizar Enlaces en el Sitio

Actualiza el menú principal de WordPress para incluir:

- **Productos**
  - Demo OVA (4h) → `/demo`
  - Trial Linux (14 días) → `/trial`
- **Recursos**
  - Documentación → `/documentation`
  - Soporte → `mailto:rafael.canelon@rhinometric.com`

---

## Troubleshooting

### Problema 1: 404 al descargar archivos

**Síntoma:**
```json
{"detail":"Demo OVA file not found. Please contact support@rhinometric.com"}
```

**Causa:** Archivo no está en la ruta esperada.

**Solución:**
```bash
# Verificar que el archivo existe
docker exec rhinometric-license-server-v2 ls -la /app/static/downloads/

# Si no existe, copiarlo
docker cp rhinometric-demo-2.5.0.ova \
  rhinometric-license-server-v2:/app/static/downloads/
```

### Problema 2: Descarga muy lenta (OVA)

**Síntoma:** OVA de 3GB tarda más de 1 hora en descargar.

**Causas posibles:**
- Ancho de banda del servidor limitado
- Throttling de hosting provider
- No está usando streaming (carga todo en RAM primero)

**Solución:**

Verificar que el código usa `StreamingResponse` (ya implementado):

```python
def iterfile():
    with open(DEMO_OVA_FILE, mode="rb") as file_like:
        chunk_size = 8192 * 1024  # 8MB chunks
        while chunk := file_like.read(chunk_size):
            yield chunk

return StreamingResponse(iterfile(), ...)
```

Si sigue lento, considera usar CDN:
- Cloudflare R2
- Amazon S3 + CloudFront
- DigitalOcean Spaces

### Problema 3: PDFs corruptos al descargar

**Síntoma:** PDF descargado no abre o dice "archivo corrupto".

**Causa:** Codificación incorrecta o Content-Type erróneo.

**Solución:**

Verificar Content-Type en respuesta:

```bash
curl -I https://licensing.rhinometric.com:5000/docs/installation-guide
```

Debe incluir:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="rhinometric-installation-guide-es.pdf"
```

Si falta, revisar código del endpoint.

### Problema 4: Enlaces en email no funcionan

**Síntoma:** Click en botón de descarga en email → error 404.

**Causa:** `SERVER_BASE_URL` mal configurado.

**Solución:**

```bash
# Verificar variable de entorno en el contenedor
docker exec rhinometric-license-server-v2 printenv | grep SERVER_BASE_URL

# Debe mostrar:
# SERVER_BASE_URL=https://licensing.rhinometric.com:5000
```

Si está mal o no existe:

```bash
# Editar docker-compose-v2.5.0.yml
services:
  rhinometric-license-server-v2:
    environment:
      - SERVER_BASE_URL=https://licensing.rhinometric.com:5000

# Reiniciar
docker compose restart rhinometric-license-server-v2
```

### Problema 5: Firewall bloquea puerto 5000

**Síntoma:** Desde fuera del servidor no se puede acceder a `http://SERVER:5000`.

**Causa:** Firewall bloqueando puerto 5000.

**Solución:**

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5000/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload

# Verificar
curl http://EXTERNAL-IP:5000/api/health
```

### Problema 6: Volúmenes no persisten archivos

**Síntoma:** Después de `docker compose down`, los archivos desaparecen.

**Causa:** No estás usando volúmenes persistentes.

**Solución:**

Configurar volúmenes en `docker-compose-v2.5.0.yml`:

```yaml
services:
  rhinometric-license-server-v2:
    volumes:
      - ./rhinometric_static:/app/static
```

Ahora los archivos están en `./rhinometric_static/` y sobreviven a reinicios.

---

## Checklist Final de Deployment

Antes de dar por completado el deployment, verifica:

- [ ] Archivos copiados al servidor:
  - [ ] `rhinometric-demo-2.5.0.ova` (2-4 GB)
  - [ ] `rhinometric-trial-2.5.0-install.sh` (~50 KB)
  - [ ] `rhinometric-installation-guide-es.pdf`
  - [ ] `rhinometric-installation-guide-en.pdf`
  - [ ] `rhinometric-user-manual-es.pdf`
  - [ ] `rhinometric-user-manual-en.pdf`

- [ ] Endpoints funcionando:
  - [ ] `GET /downloads/demo-ova` → 200 OK
  - [ ] `GET /downloads/trial-installer` → 200 OK
  - [ ] `GET /docs/installation-guide?lang=es` → 200 OK
  - [ ] `GET /docs/installation-guide?lang=en` → 200 OK
  - [ ] `GET /docs/user-manual?lang=es` → 200 OK
  - [ ] `GET /docs/user-manual?lang=en` → 200 OK
  - [ ] `GET /downloads/info` → JSON correcto

- [ ] Emails configurados:
  - [ ] Variable `SERVER_BASE_URL` configurada
  - [ ] Email de prueba enviado y recibido
  - [ ] Enlaces en email funcionan correctamente
  - [ ] PDFs adjuntos en email (legacy)

- [ ] WordPress:
  - [ ] Página "Demo OVA" publicada
  - [ ] Página "Trial Linux" publicada
  - [ ] Página "Documentación" publicada
  - [ ] Menú principal actualizado con enlaces

- [ ] Testing:
  - [ ] Descarga completa de OVA desde navegador
  - [ ] Descarga de instalador con wget/curl
  - [ ] Apertura de PDFs descargados
  - [ ] Verificación de integridad (checksums)

---

## Referencias

- **License Server v2:** `license-server-v2/main.py`
- **Email Sender:** `license-server-v2/utils/email_sender.py`
- **Docker Compose:** `docker-compose-v2.5.0.yml`
- **WordPress HTML:** `docs/v2.5.0/wordpress/*.html`
- **API Docs:** `https://licensing.rhinometric.com:5000/api/docs`

---

**Documentación creada:** 16 de Diciembre de 2025  
**Versión:** Rhinometric v2.5.0  
**Autor:** Rafael Canelón  
**Contacto:** rafael.canelon@rhinometric.com

---

## Próximos Pasos Sugeridos

1. **Generar checksums SHA256** de los archivos para verificación de integridad
2. **Configurar CDN** (Cloudflare/AWS) para OVA si descargas son lentas
3. **Monitorizar descargas** con métricas en Prometheus
4. **Crear landing page** dedicada en rhinometric.com con estos enlaces
5. **Video tutorial** de instalación subido a YouTube
6. **Automatizar generación de PDFs** desde Markdown con CI/CD
7. **Implementar rate limiting** para evitar abuso de descargas
8. **Configurar HTTPS** con Let's Encrypt para el License Server

