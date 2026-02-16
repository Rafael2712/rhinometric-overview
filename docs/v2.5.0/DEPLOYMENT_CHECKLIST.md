# ✅ CHECKLIST DE DEPLOYMENT - Rhinometric v2.5.0
## Sistema de Descargas y Documentación

**Fecha inicio:** ___________________  
**Responsable:** ___________________  
**Servidor:** ___________________

---

## 🚀 FASE 1: PREPARACIÓN DE ARCHIVOS

### Archivos Necesarios

- [ ] **rhinometric-demo-2.5.0.ova** (2-4 GB)
  - Ubicación actual: ___________________
  - Checksum SHA256: ___________________
  - Tamaño: _______ MB

- [ ] **rhinometric-trial-2.5.0-install.sh** (~50 KB)
  - Ubicación actual: ___________________
  - Verificado ejecutable: [ ] Sí [ ] No
  
- [ ] **rhinometric-installation-guide-es.pdf**
  - Ubicación actual: ___________________
  - Tamaño: _______ MB
  
- [ ] **rhinometric-installation-guide-en.pdf**
  - Ubicación actual: ___________________
  - Tamaño: _______ MB
  
- [ ] **rhinometric-user-manual-es.pdf**
  - Ubicación actual: ___________________
  - Tamaño: _______ MB
  
- [ ] **rhinometric-user-manual-en.pdf**
  - Ubicación actual: ___________________
  - Tamaño: _______ MB

---

## 🖥️ FASE 2: DEPLOYMENT EN EL SERVIDOR

### 2.1 Acceso al Servidor

- [ ] Conexión SSH establecida
  ```bash
  ssh user@licensing.rhinometric.com
  ```

- [ ] Verificar Docker corriendo
  ```bash
  docker ps | grep license-server
  ```

### 2.2 Copiar Archivos

**Opción A: Desde local con SCP**

- [ ] OVA copiada
  ```bash
  scp rhinometric-demo-2.5.0.ova user@server:/app/static/downloads/
  ```

- [ ] Instalador copiado
  ```bash
  scp rhinometric-trial-2.5.0-install.sh user@server:/app/static/downloads/
  ```

- [ ] PDFs español copiados
  ```bash
  scp rhinometric-installation-guide-es.pdf user@server:/app/static/docs/es/
  scp rhinometric-user-manual-es.pdf user@server:/app/static/docs/es/
  ```

- [ ] PDFs inglés copiados
  ```bash
  scp rhinometric-installation-guide-en.pdf user@server:/app/static/docs/en/
  scp rhinometric-user-manual-en.pdf user@server:/app/static/docs/en/
  ```

**Opción B: Docker cp (si el License Server está en Docker)**

- [ ] OVA copiada al contenedor
  ```bash
  docker cp rhinometric-demo-2.5.0.ova \
    rhinometric-license-server-v2:/app/static/downloads/
  ```

- [ ] Instalador copiado al contenedor
- [ ] PDFs copiados al contenedor

### 2.3 Verificar Archivos en el Servidor

- [ ] Archivos existen en rutas correctas
  ```bash
  docker exec rhinometric-license-server-v2 \
    ls -lh /app/static/downloads/
  
  docker exec rhinometric-license-server-v2 \
    ls -lh /app/static/docs/es/
  
  docker exec rhinometric-license-server-v2 \
    ls -lh /app/static/docs/en/
  ```

- [ ] Permisos correctos (lectura para todos)
  ```bash
  docker exec rhinometric-license-server-v2 \
    chmod 644 /app/static/downloads/*
  ```

- [ ] Tamaños coinciden con archivos originales

---

## ⚙️ FASE 3: CONFIGURACIÓN

### 3.1 Variables de Entorno

- [ ] Editar `docker-compose-v2.5.0.yml` o `.env`
  
  ```env
  SERVER_BASE_URL=https://licensing.rhinometric.com:5000
  ```

- [ ] Verificar otras variables SMTP
  ```env
  SMTP_HOST=smtp.zoho.eu
  SMTP_PORT=465
  SMTP_USER=rafael.canelon@rhinometric.com
  SMTP_PASSWORD=***************
  SMTP_FROM=rafael.canelon@rhinometric.com
  ```

### 3.2 Reiniciar License Server

- [ ] Reiniciar contenedor
  ```bash
  docker compose -f docker-compose-v2.5.0.yml restart rhinometric-license-server-v2
  ```

- [ ] Verificar logs
  ```bash
  docker logs rhinometric-license-server-v2 --tail 50
  ```

- [ ] Buscar errores en logs
  - [ ] Sin errores de FileNotFound
  - [ ] Sin errores de permisos
  - [ ] Uvicorn iniciado correctamente

---

## 🧪 FASE 4: TESTING

### 4.1 Health Check

- [ ] API Health responde
  ```bash
  curl https://licensing.rhinometric.com:5000/api/health
  ```
  
  **Resultado esperado:** `{"status":"healthy",...}`

### 4.2 Metadata Endpoint

- [ ] Endpoint `/downloads/info` funciona
  ```bash
  curl https://licensing.rhinometric.com:5000/downloads/info | jq
  ```

- [ ] JSON muestra todos los archivos como `"available": true`

### 4.3 Download Endpoints

- [ ] Demo OVA descarga (test con HEAD)
  ```bash
  curl -I https://licensing.rhinometric.com:5000/downloads/demo-ova
  ```
  
  **Resultado esperado:** `HTTP/1.1 200 OK` + `Content-Type: application/octet-stream`

- [ ] Trial Installer descarga
  ```bash
  curl -L -o test-installer.sh \
    https://licensing.rhinometric.com:5000/downloads/trial-installer
  
  head -10 test-installer.sh
  ```
  
  **Verificar:** Es un script bash válido (empieza con `#!/bin/bash`)

### 4.4 Documentation Endpoints

- [ ] Guía instalación (ES)
  ```bash
  curl -I https://licensing.rhinometric.com:5000/docs/installation-guide?lang=es
  ```
  
  **Resultado esperado:** `HTTP/1.1 200 OK` + `Content-Type: application/pdf`

- [ ] Guía instalación (EN)
  ```bash
  curl -I https://licensing.rhinometric.com:5000/docs/installation-guide?lang=en
  ```

- [ ] Manual usuario (ES)
  ```bash
  curl -I https://licensing.rhinometric.com:5000/docs/user-manual?lang=es
  ```

- [ ] Manual usuario (EN)
  ```bash
  curl -I https://licensing.rhinometric.com:5000/docs/user-manual?lang=en
  ```

### 4.5 Script de Verificación Automático

- [ ] Ejecutar script bash (Linux/Mac)
  ```bash
  chmod +x test-download-endpoints.sh
  ./test-download-endpoints.sh https://licensing.rhinometric.com:5000
  ```

- [ ] Ejecutar script PowerShell (Windows)
  ```powershell
  .\test-download-endpoints.ps1 https://licensing.rhinometric.com:5000
  ```

- [ ] Todos los tests pasan ✓

### 4.6 Email de Prueba

- [ ] Crear licencia trial de prueba
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

- [ ] Email recibido en bandeja
- [ ] Email contiene:
  - [ ] Botón de descarga con URL correcta
  - [ ] Enlaces a PDFs (ES/EN)
  - [ ] PDFs adjuntos (legacy)
  
- [ ] Click en botón de descarga → archivo se descarga
- [ ] Click en enlace PDF → PDF se descarga

---

## 🌐 FASE 5: WORDPRESS

### 5.1 Acceso y Preparación

- [ ] Acceso a wp-admin
  ```
  https://rhinometric.com/wp-admin
  ```
  
  Usuario: ___________________

- [ ] Archivos HTML listos:
  - [ ] `docs/v2.5.0/wordpress/01-demo-ova-page.html`
  - [ ] `docs/v2.5.0/wordpress/02-trial-linux-page.html`
  - [ ] `docs/v2.5.0/wordpress/03-documentation-page.html`

### 5.2 Página 1: Demo OVA

- [ ] **Páginas** → **Añadir nueva**
- [ ] Título: "Demo Rhinometric - Descarga OVA"
- [ ] **Tres puntos** → **Editar como HTML**
- [ ] Pegar contenido de `01-demo-ova-page.html`
- [ ] Ajustar URL si es necesario:
  
  Buscar y reemplazar:
  ```
  https://licensing.rhinometric.com:5000
  →
  https://TU-SERVIDOR:5000
  ```

- [ ] **Vista previa** → Verificar diseño
- [ ] **Publicar**
- [ ] Configurar permalink: `/demo`

### 5.3 Página 2: Trial Linux

- [ ] **Páginas** → **Añadir nueva**
- [ ] Título: "Trial Rhinometric 14 días"
- [ ] Pegar contenido de `02-trial-linux-page.html`
- [ ] Ajustar URL si es necesario
- [ ] **Publicar**
- [ ] Configurar permalink: `/trial`

### 5.4 Página 3: Documentación

- [ ] **Páginas** → **Añadir nueva**
- [ ] Título: "Documentación Rhinometric"
- [ ] Pegar contenido de `03-documentation-page.html`
- [ ] Ajustar URL si es necesario
- [ ] **Publicar**
- [ ] Configurar permalink: `/documentation` o `/docs`

### 5.5 Menú Principal

- [ ] **Apariencia** → **Menús**
- [ ] Añadir páginas al menú:
  - [ ] Demo OVA (4h)
  - [ ] Trial Linux (14 días)
  - [ ] Documentación
  
- [ ] Organizar en secciones:
  ```
  Productos
    ├── Demo OVA (4h)
    └── Trial Linux (14 días)
  Recursos
    ├── Documentación
    └── Soporte
  ```

- [ ] **Guardar menú**

### 5.6 Verificación WordPress

- [ ] Página Demo accesible: https://rhinometric.com/demo
- [ ] Página Trial accesible: https://rhinometric.com/trial
- [ ] Página Docs accesible: https://rhinometric.com/documentation

- [ ] Diseño responsive (verificar en mobile)
- [ ] Enlaces de descarga funcionan
- [ ] Sin errores de consola JavaScript

---

## 🎯 FASE 6: VERIFICACIÓN FINAL

### 6.1 Flujo Completo (End-to-End)

**Escenario: Usuario solicita licencia demo**

1. [ ] Usuario llena formulario en rhinometric.com/demo
2. [ ] Sistema crea licencia `demo_cloud`
3. [ ] Email enviado automáticamente
4. [ ] Usuario recibe email con:
   - [ ] Clave de licencia
   - [ ] Botón "Descargar OVA Demo"
   - [ ] Enlaces a PDFs
5. [ ] Usuario hace click en botón
6. [ ] OVA se descarga correctamente (2-4 GB)
7. [ ] Usuario verifica checksum (opcional)
8. [ ] Usuario importa OVA en VirtualBox
9. [ ] Usuario accede a Rhinometric en VM

**Escenario: Usuario solicita licencia trial**

1. [ ] Usuario llena formulario en rhinometric.com/trial
2. [ ] Sistema crea licencia `trial`
3. [ ] Email enviado automáticamente
4. [ ] Usuario recibe email con:
   - [ ] Clave de licencia
   - [ ] Botón "Descargar Instalador Linux"
   - [ ] Enlaces a PDFs
5. [ ] Usuario hace click en botón
6. [ ] Script `.sh` se descarga
7. [ ] Usuario ejecuta script en servidor Linux
8. [ ] Rhinometric se instala correctamente
9. [ ] Usuario activa con clave de licencia

### 6.2 Performance

- [ ] Descarga de OVA (3GB) termina en tiempo razonable:
  - [ ] Con 10 Mbps: ~40 minutos
  - [ ] Con 100 Mbps: ~4 minutos
  - [ ] Con 1 Gbps: ~30 segundos

- [ ] PDFs se abren correctamente en navegador
- [ ] No hay timeouts en descargas grandes

### 6.3 Seguridad

- [ ] Firewall permite puerto 5000
  ```bash
  sudo ufw allow 5000/tcp
  ```

- [ ] HTTPS configurado (Let's Encrypt)
  - [ ] Certificado válido
  - [ ] Sin warnings de "Not Secure"

- [ ] No hay leaks de información sensible en logs

### 6.4 Monitoreo

- [ ] Configurar alerta si License Server cae
- [ ] Configurar alerta si disco se llena (OVA ocupa espacio)
- [ ] Logs rotando correctamente (no llenan disco)

---

## 📊 FASE 7: DOCUMENTACIÓN

### 7.1 Documentación Interna

- [ ] Actualizar README del proyecto con nuevos endpoints
- [ ] Documentar proceso de actualización de PDFs
- [ ] Documentar cómo reemplazar OVA por nueva versión

### 7.2 Comunicación

- [ ] Notificar al equipo de ventas:
  - [ ] URLs de páginas WordPress
  - [ ] Proceso de solicitud de licencias
  
- [ ] Notificar al equipo de soporte:
  - [ ] Endpoints disponibles
  - [ ] Troubleshooting común

### 7.3 Backups

- [ ] Backup de archivos (OVA, PDFs) en ubicación segura
- [ ] Backup de docker volumes del License Server
- [ ] Backup de páginas WordPress (exportar HTML)

---

## ✅ SIGN-OFF FINAL

### Aprobaciones

- [ ] **Técnico:** ___________________  
      Fecha: ___________________
      
- [ ] **Product Owner:** ___________________  
      Fecha: ___________________

### Notas Finales

____________________________________________________________

____________________________________________________________

____________________________________________________________

____________________________________________________________

---

## 📞 SOPORTE

**Si encuentras problemas:**

- **Email:** rafael.canelon@rhinometric.com
- **Documentación:**
  - `docs/v2.5.0/DOWNLOAD_ENDPOINTS.md` (guía técnica)
  - `docs/v2.5.0/wordpress/README.md` (guía WordPress)
- **Scripts:**
  - `test-download-endpoints.sh` (Linux/Mac)
  - `test-download-endpoints.ps1` (Windows)

---

**Deployment completado:** ___________________  
**Fecha go-live:** ___________________  
**Status:** [ ] ✅ En Producción [ ] 🚧 En Progreso [ ] ❌ Rollback

---

**Preparado por:** Rafael Canelón  
**Versión:** 2.5.0

