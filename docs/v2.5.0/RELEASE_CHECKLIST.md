# 🚀 RELEASE CHECKLIST - Rhinometric v2.5.0

## Pre-Release Verification

### ✅ Código y Funcionalidad

- [ ] **Todos los endpoints funcionan**
  ```bash
  chmod +x scripts/test_license_emails.sh
  ./scripts/test_license_emails.sh http://localhost:5000
  ```
  
- [ ] **Tests de descarga pasan**
  ```bash
  chmod +x test-download-endpoints.sh
  ./test-download-endpoints.sh http://localhost:5000
  ```

- [ ] **Sin errores de sintaxis**
  ```bash
  # Python
  python3 -m py_compile license-server-v2/main.py
  python3 -m py_compile license-server-v2/utils/email_sender.py
  
  # Check logs
  docker logs rhinometric-license-server-v2 --tail 100 | grep -i error
  ```

- [ ] **Versión actualizada en todos los archivos**
  ```bash
  grep -r "v2.1.0" --include="*.py" --include="*.md" --include="*.html"
  # Debe mostrar 0 resultados (o solo en archivos de migración/docs viejos)
  ```

---

### ⚠️ SEGURIDAD - CRÍTICO

⚠️ **ENCONTRADO:** Archivo `.env` con contraseñas reales en el repo!

**Archivos con secrets detectados:**
```
c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\.env
  ├─ GRAFANA_PASSWORD=demo123
  ├─ POSTGRES_PASSWORD=rhinometric_demo
  ├─ REDIS_PASSWORD=rhinometric_demo
  └─ SMTP_PASSWORD=271211Rc$  ⚠️ CONTRASEÑA REAL DE ZOHO
```

**⚠️ ACCIÓN REQUERIDA ANTES DE COMMIT:**

1. **ELIMINAR .env del repo**
   ```bash
   git rm --cached .env
   ```

2. **Verificar que .gitignore incluye .env**
   ```bash
   grep "^\.env$" .gitignore
   # Si no existe, añadirlo:
   echo ".env" >> .gitignore
   echo ".env.*" >> .gitignore
   ```

3. **Rotar contraseña SMTP** (compromiso de seguridad)
   - Login en Zoho Mail
   - Settings → Security → App Passwords
   - Revoke password actual: `271211Rc$`
   - Generar nuevo App Password
   - Actualizar `.env` LOCAL (no commitear)

4. **Verificar que no hay otros secrets**
   ```bash
   git grep -i "password.*=" --all-match
   git grep -i "secret.*=" --all-match
   git grep -i "api.*key.*=" --all-match
   ```

5. **Limpiar historial de Git (si .env ya fue commiteado antes)**
   ```bash
   # PELIGRO: Esto reescribe historial
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (CUIDADO: afecta a todos)
   git push origin --force --all
   git push origin --force --tags
   ```

**Checklist de seguridad:**

- [ ] `.env` eliminado del staging area
- [ ] `.gitignore` incluye `.env` y `.env.*`
- [ ] Contraseña SMTP rotada en Zoho
- [ ] `.env.example` creado SIN contraseñas reales
- [ ] Verificado con `git status` que .env no aparece
- [ ] Doble check con `git diff --cached` antes de commit

---

### 📄 Documentación

- [ ] **README.md actualizado**
  - Versión 2.5.0 visible
  - Enlaces a nuevos docs
  - Instrucciones Demo OVA + Trial

- [ ] **RELEASE_NOTES.md completo**
  - Todas las features listadas
  - Breaking changes documentados
  - Known issues actualizados

- [ ] **Docs en docs/v2.5.0/ completos**
  - [ ] DEPLOYMENT_CHECKLIST.md
  - [ ] DOWNLOAD_ENDPOINTS.md
  - [ ] EMAIL_TESTING.md
  - [ ] PUBLISHING_GUIDE.md
  - [ ] RELEASE_NOTES.md
  - [ ] RESUMEN_FINAL_v2.5.0.md

- [ ] **Scripts ejecutables**
  ```bash
  chmod +x scripts/test_license_emails.sh
  chmod +x test-download-endpoints.sh
  chmod +x test-download-endpoints.ps1
  ```

---

### 🌐 WordPress y Web

- [ ] **Archivos HTML revisados**
  - URLs correctas (no localhost)
  - Sin referencias a v2.1.0
  - Responsive en mobile

- [ ] **Páginas publicadas** (opcional pre-release)
  - https://rhinometric.com/demo
  - https://rhinometric.com/trial
  - https://rhinometric.com/documentation

---

### 🐳 Docker y Deployment

- [ ] **Docker compose válido**
  ```bash
  docker compose -f docker-compose-v2.5.0.yml config
  # No debe mostrar errores
  ```

- [ ] **Imágenes Docker buildeables**
  ```bash
  docker build -t rhinometric-license-server-v2 license-server-v2/
  docker build -t rhinometric-console-backend rhinometric-console/backend/
  docker build -t rhinometric-ai-anomaly ai-anomaly-engine/
  ```

- [ ] **Stack completo inicia sin errores**
  ```bash
  docker compose -f docker-compose-v2.5.0.yml up -d
  sleep 60
  docker compose -f docker-compose-v2.5.0.yml ps
  # Todos los servicios deben estar "Up" o "healthy"
  ```

---

## Git Workflow

### 1. Verificar Estado Actual

```bash
# Ver archivos modificados
git status

# Ver cambios no staged
git diff

# Ver cambios staged
git diff --cached
```

**Esperado:**
```
Archivos modificados:
  modified:   license-server-v2/main.py
  modified:   license-server-v2/utils/email_sender.py
  
Archivos nuevos:
  new file:   docs/v2.5.0/DEPLOYMENT_CHECKLIST.md
  new file:   docs/v2.5.0/DOWNLOAD_ENDPOINTS.md
  new file:   docs/v2.5.0/EMAIL_TESTING.md
  new file:   docs/v2.5.0/PUBLISHING_GUIDE.md
  new file:   docs/v2.5.0/RELEASE_NOTES.md
  new file:   docs/v2.5.0/RESUMEN_FINAL_v2.5.0.md
  new file:   docs/v2.5.0/wordpress/01-demo-ova-page.html
  new file:   docs/v2.5.0/wordpress/02-trial-linux-page.html
  new file:   docs/v2.5.0/wordpress/03-documentation-page.html
  new file:   docs/v2.5.0/wordpress/README.md
  new file:   scripts/test_license_emails.sh
  new file:   test-download-endpoints.sh
  new file:   test-download-endpoints.ps1
  modified:   README.md
```

### 2. Añadir Cambios

```bash
# Añadir archivos modificados
git add license-server-v2/main.py
git add license-server-v2/utils/email_sender.py
git add README.md

# Añadir nueva documentación
git add docs/v2.5.0/

# Añadir WordPress files
git add docs/v2.5.0/wordpress/

# Añadir scripts
git add scripts/test_license_emails.sh
git add test-download-endpoints.sh
git add test-download-endpoints.ps1

# Verificar staging area
git status
```

**⚠️ IMPORTANTE: NO AÑADIR .env**
```bash
# SI .env aparece en "Changes to be committed":
git reset HEAD .env
git rm --cached .env
```

### 3. Commit

```bash
git commit -m "chore: prepare Rhinometric v2.5.0 production release

Major updates:
- License Server v2 with FastAPI rewrite
- New download/documentation endpoints (5 endpoints)
- Email system with dynamic URLs and HTML templates
- Console v3 (Vue.js + FastAPI)
- AI Anomaly Detection Engine (Prophet + IsolationForest)
- Demo OVA and Trial Installer distribution formats
- 3 WordPress landing pages (demo, trial, docs)
- Comprehensive documentation (10+ guides)

Breaking changes:
- License API endpoints moved to /api/admin/licenses
- New environment variables required (SERVER_BASE_URL)
- Docker compose file renamed to docker-compose-v2.5.0.yml

See docs/v2.5.0/RELEASE_NOTES.md for full changelog.
"
```

### 4. Crear Tag Anotado

```bash
git tag -a v2.5.0 -m "Rhinometric v2.5.0 - Production Release

Release highlights:
✨ Console v3 visual management dashboard
🤖 AI-powered anomaly detection  
📦 Multi-format distribution (OVA, Installer, Source)
🌐 Professional WordPress landing pages
📧 Transactional email system with downloads
📚 Comprehensive multilanguage documentation

Full release notes: docs/v2.5.0/RELEASE_NOTES.md
"
```

### 5. Verificar Tag

```bash
# Ver tag creado
git tag -l v2.5.0

# Ver mensaje del tag
git show v2.5.0

# Listar todos los tags
git tag -l
```

### 6. Push a GitHub

**⚠️ ANTES DE PUSH: VERIFICACIÓN FINAL**

```bash
# 1. Ver exactamente qué se va a pushear
git log origin/main..HEAD --oneline

# 2. Ver archivos en el commit
git show --name-only

# 3. Buscar secrets una última vez
git grep -i "271211Rc" HEAD
git grep -i "smtp.*password.*=" HEAD
# NO debe mostrar resultados

# 4. Si todo OK, proceder
```

**Push commit:**
```bash
git push origin main
```

**Push tags:**
```bash
git push origin --tags
```

**O push todo junto:**
```bash
git push && git push origin --tags
```

### 7. Crear GitHub Release

1. **Ir a GitHub repo**
   ```
   https://github.com/Rafael2712/rhinometric-overview/releases
   ```

2. **Click "Draft a new release"**

3. **Configurar release:**
   - **Tag version:** `v2.5.0` (seleccionar del dropdown)
   - **Release title:** `Rhinometric v2.5.0 - Console & AI Engine`
   - **Description:** Copiar contenido de `docs/v2.5.0/RELEASE_NOTES.md`
   
4. **Adjuntar archivos** (opcional):
   - [ ] `rhinometric-v2.5.0-stable.tar.gz` (si tienes empaquetado)
   - [ ] `rhinometric-demo-2.5.0.ova` (muy pesado, mejor usar cloud storage)
   - [ ] `rhinometric-trial-2.5.0-install.sh`

5. **Checkbox:**
   - [ ] ✅ Set as latest release
   - [ ] ❌ NO marcar "This is a pre-release" (es estable)

6. **Publish release**

---

## Post-Release

### 1. Verificar GitHub

- [ ] **Release publicado**
  ```
  https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0
  ```

- [ ] **Tag visible en lista**
  ```
  https://github.com/Rafael2712/rhinometric-overview/tags
  ```

- [ ] **Código actualizado en main**
  ```
  https://github.com/Rafael2712/rhinometric-overview/tree/main
  ```

### 2. Actualizar Servicios

- [ ] **Subir archivos al License Server**
  ```bash
  # OVA (si tienes)
  scp rhinometric-demo-2.5.0.ova user@server:/app/static/downloads/
  
  # Installer
  scp rhinometric-trial-2.5.0-install.sh user@server:/app/static/downloads/
  
  # PDFs
  scp docs/*.pdf user@server:/app/static/docs/es/
  scp docs/*.pdf user@server:/app/static/docs/en/
  ```

- [ ] **Reiniciar License Server**
  ```bash
  ssh user@server
  cd /path/to/rhinometric
  docker compose -f docker-compose-v2.5.0.yml restart rhinometric-license-server-v2
  ```

- [ ] **Test endpoints**
  ```bash
  curl https://licensing.rhinometric.com:5000/api/health
  curl https://licensing.rhinometric.com:5000/downloads/info
  ```

### 3. Publicar WordPress (si no hecho)

- [ ] Página Demo → `https://rhinometric.com/demo`
- [ ] Página Trial → `https://rhinometric.com/trial`
- [ ] Página Docs → `https://rhinometric.com/documentation`

### 4. Comunicación

- [ ] **Email al equipo**
  ```
  Subject: 🚀 Rhinometric v2.5.0 Released!
  
  Team,
  
  Rhinometric v2.5.0 is now live!
  
  🎯 What's new:
  - Console v3 for visual management
  - AI Anomaly Detection Engine
  - Demo OVA (4h evaluation)
  - Trial Installer (14 days)
  
  📚 Docs: https://rhinometric.com/documentation
  🐙 GitHub: https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0
  
  Rafael
  ```

- [ ] **Update LinkedIn/Twitter** (si aplica)

### 5. Monitoring

- [ ] **Dashboard de descargas**
  - Monitorear cuántas veces se descarga OVA/Installer
  - Ver logs de License Server

- [ ] **Emails enviados**
  - Verificar tasa de entrega (Zoho Mail → Sent folder)

- [ ] **Errores**
  ```bash
  docker logs rhinometric-license-server-v2 -f | grep -i error
  ```

---

## Rollback Plan (Si algo sale mal)

### Revertir a v2.1.0

```bash
# 1. Parar v2.5.0
docker compose -f docker-compose-v2.5.0.yml down

# 2. Volver a v2.1.0
cd ../rhinometric-v2.1.0
docker compose -f docker-compose.yml up -d

# 3. Restaurar DB (si hubo migrations)
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric < backup-v2.1.0.sql
```

### Revertir Git

```bash
# Revertir commit (crea nuevo commit de reversión)
git revert HEAD

# O reset hard (PELIGRO: pierde cambios)
git reset --hard HEAD~1

# Eliminar tag
git tag -d v2.5.0
git push origin :refs/tags/v2.5.0
```

---

## Checklist Final

**ANTES de hacer `git push`:**

- [ ] ⚠️ `.env` NO está en staging area
- [ ] ⚠️ Contraseña SMTP rotada
- [ ] ⚠️ `.gitignore` actualizado
- [ ] ✅ Todos los tests pasan
- [ ] ✅ Docker compose válido
- [ ] ✅ Docs completas
- [ ] ✅ README actualizado
- [ ] ✅ Versión 2.5.0 en archivos
- [ ] ✅ Commit message descriptivo
- [ ] ✅ Tag anotado creado

**DESPUÉS de `git push`:**

- [ ] ✅ Release publicado en GitHub
- [ ] ✅ Archivos subidos al servidor
- [ ] ✅ WordPress páginas publicadas
- [ ] ✅ Equipo notificado

---

## Comandos Rápidos (Copy-Paste)

```bash
# Preparar commit
git add license-server-v2/main.py license-server-v2/utils/email_sender.py README.md
git add docs/v2.5.0/ scripts/test_license_emails.sh test-download-endpoints.sh test-download-endpoints.ps1

# Verificar que .env NO está
git status | grep -q ".env" && echo "⚠️ PELIGRO: .env detectado!" || echo "✅ OK"

# Commit
git commit -m "chore: prepare Rhinometric v2.5.0 production release"

# Tag
git tag -a v2.5.0 -m "Rhinometric v2.5.0 - Production Release"

# Push
git push && git push origin --tags

# Verificar en GitHub
xdg-open https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0  # Linux
open https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0     # macOS
start https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0    # Windows
```

---

**Última actualización:** 16 Diciembre 2025  
**Versión:** 2.5.0  
**Preparado por:** Rafael Canelón
