# ⚠️ SECURITY REPORT - ACCIÓN INMEDIATA REQUERIDA

## 🚨 HALLAZGO CRÍTICO DE SEGURIDAD

**Fecha:** 16 Diciembre 2025  
**Severidad:** 🔴 CRÍTICA  
**Estado:** ⚠️ REQUIERE ACCIÓN ANTES DE COMMIT

---

## Problema Detectado

Se ha encontrado un archivo **`.env`** en el repositorio con **contraseñas reales en texto plano**.

### Archivo Comprometido

```
Ruta: c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\.env

Contenido sensible:
├─ GRAFANA_PASSWORD=demo123
├─ POSTGRES_PASSWORD=rhinometric_demo
├─ REDIS_PASSWORD=rhinometric_demo
└─ SMTP_PASSWORD=271211Rc$  ⚠️⚠️⚠️ CONTRASEÑA REAL DE ZOHO
```

### Impacto

🔴 **CRÍTICO:** La contraseña `SMTP_PASSWORD=271211Rc$` es la **contraseña real** de la cuenta Zoho:
- Email: `rafael.canelon@rhinometric.com`
- SMTP: `smtp.zoho.eu:465`

Si este archivo se commitea y pushea a GitHub:
- ✅ Repositorio es **PÚBLICO** → ⚠️ Contraseña expuesta a internet
- ❌ Bots escanean commits buscando secrets → Compromiso en **< 1 hora**
- ❌ Acceso no autorizado a cuenta email
- ❌ Posibilidad de envío masivo de spam
- ❌ Robo de emails históricos
- ❌ Suspensión de cuenta Zoho por abuso

---

## 🛡️ ACCIÓN INMEDIATA REQUERIDA

### Paso 1: Eliminar .env del staging (AHORA)

```bash
# Ver si .env está staged
git status

# Si aparece en "Changes to be committed":
git reset HEAD .env

# Eliminar del tracking
git rm --cached .env

# Verificar que ya no está
git status | grep ".env"
```

### Paso 2: Actualizar .gitignore (AHORA)

```bash
# Verificar que .gitignore incluye .env
grep "^\.env$" .gitignore

# Si NO aparece, añadirlo:
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore

# Añadir .gitignore al commit
git add .gitignore
```

### Paso 3: Rotar Contraseña SMTP (URGENTE - Próximas 24h)

**⚠️ La contraseña `271211Rc$` está comprometida por estar en archivos del repo**

#### En Zoho Mail:

1. Login en https://mail.zoho.eu
2. Settings → Security → App Passwords
3. **Revocar** el App Password actual
4. **Generar** nuevo App Password
5. **Copiar** el nuevo password

#### En tu servidor:

```bash
# Actualizar .env LOCAL (NO commitear)
nano .env

# Cambiar línea:
SMTP_PASSWORD=<NUEVO_PASSWORD_ZOHO>

# Guardar y salir

# Reiniciar License Server
docker compose -f docker-compose-v2.5.0.yml restart rhinometric-license-server-v2
```

### Paso 4: Crear .env.example (Sin secrets)

```bash
# Crear archivo de ejemplo
cat > .env.example << 'EOF'
# Rhinometric v2.5.0 - Environment Variables Template

# Grafana
GRAFANA_PASSWORD=changeme

# PostgreSQL
POSTGRES_PASSWORD=changeme

# Redis
REDIS_PASSWORD=changeme

# SMTP (Zoho)
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=<TU_APP_PASSWORD_ZOHO>
SMTP_FROM=rafael.canelon@rhinometric.com

# License Server
SERVER_BASE_URL=https://licensing.rhinometric.com:5000
LICENSE_KEY=RHINO-XXXX-2025-XXXXXXXXXXXX

# Database
DATABASE_URL=postgresql://rhinometric:${POSTGRES_PASSWORD}@postgres:5432/rhinometric_trial

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

# Rhinometric Mode
RHINOMETRIC_MODE=trial
EOF

# Añadir al commit
git add .env.example
```

### Paso 5: Verificar que secrets NO están en Git (ANTES DE COMMIT)

```bash
# Buscar contraseña SMTP en archivos staged
git grep "271211Rc" $(git diff --cached --name-only)

# Buscar "password=" en archivos staged
git grep -i "password.*=" $(git diff --cached --name-only) | grep -v ".env.example"

# Si CUALQUIER comando devuelve resultados → ⚠️ NO COMMITEAR
```

### Paso 6: Limpiar Historial de Git (Si .env ya fue commiteado antes)

**⚠️ PELIGRO: Esto reescribe el historial de Git**

```bash
# Ver si .env está en commits previos
git log --all --oneline --decorate -- .env

# Si aparece en commits antiguos, limpiar historial:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (CUIDADO: afecta a todos los clones)
git push origin --force --all
git push origin --force --tags

# Notificar al equipo que hagan fresh clone
```

---

## ✅ Checklist de Seguridad Pre-Commit

**ANTES de ejecutar `git commit`:**

- [ ] ⚠️ `.env` eliminado del staging area
- [ ] ⚠️ `.env` NO aparece en `git status`
- [ ] ✅ `.gitignore` incluye `.env` y `.env.*`
- [ ] ✅ `.env.example` creado SIN contraseñas reales
- [ ] ✅ Contraseña SMTP rotada en Zoho (o planificado < 24h)
- [ ] ✅ Verificado con `git grep "271211Rc"`  → 0 resultados
- [ ] ✅ Verificado con `git grep -i "smtp.*password.*=.*[^$]"`  → 0 resultados
- [ ] ✅ Double-check con `git diff --cached` → .env NO aparece

**DESPUÉS de commit:**

- [ ] Verificar GitHub: archivo .env NO visible
- [ ] Verificar GitHub: .env.example SÍ visible con placeholders
- [ ] Verificar servidor: License Server funciona con nueva password SMTP

---

## 📊 Otros Hallazgos de Seguridad (Menor Prioridad)

### Contraseñas por Defecto en docker-compose

**Archivos afectados:**
- `docker-compose-SIMPLE.yml`
- `docker-compose-NO-HEALTHCHECK.yml`
- `docker-compose-v2.5.0.yml`

**Contraseñas débiles encontradas:**
```yaml
SMTP_PASSWORD: ${SMTP_PASSWORD:-271211Rc$}  # ⚠️ Fallback a contraseña real
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-rhinometric}  # Débil
REDIS_PASSWORD: ${REDIS_PASSWORD:-rhinometric}  # Débil
GRAFANA_PASSWORD: ${GRAFANA_PASSWORD:-admin}  # MUY DÉBIL
```

**Recomendación:**
```yaml
# Cambiar fallbacks a valores aleatorios o quitar fallback
SMTP_PASSWORD: ${SMTP_PASSWORD}  # Sin fallback → fuerza configurar
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
REDIS_PASSWORD: ${REDIS_PASSWORD}
GRAFANA_PASSWORD: ${GRAFANA_PASSWORD}
```

**Acción:** Revisar antes de v2.6.0

---

## 🔐 Best Practices de Seguridad (Implementar)

### 1. Usar Secrets Management

**Opción A: Docker Secrets**
```yaml
secrets:
  smtp_password:
    file: ./secrets/smtp_password.txt

services:
  license-server:
    secrets:
      - smtp_password
    environment:
      SMTP_PASSWORD_FILE: /run/secrets/smtp_password
```

**Opción B: Hashicorp Vault**
```bash
vault kv put secret/rhinometric smtp_password=<PASSWORD>
```

### 2. Encriptar .env Local

```bash
# Instalar git-crypt
sudo apt-get install git-crypt

# Inicializar
git-crypt init

# Configurar .gitattributes
echo ".env filter=git-crypt diff=git-crypt" >> .gitattributes

# Añadir clave GPG permitida
git-crypt add-gpg-user <EMAIL>
```

### 3. Pre-commit Hooks

Crear `.git/hooks/pre-commit`:
```bash
#!/bin/bash

# Detectar secrets antes de commit
if git diff --cached --name-only | grep -q "\.env$"; then
    echo "❌ ERROR: .env file detected in commit!"
    echo "Run: git reset HEAD .env"
    exit 1
fi

# Detectar passwords en código
if git diff --cached | grep -qiE "(password|secret|api[_-]?key).*=.*[\"'][^\"']+[\"']"; then
    echo "⚠️  WARNING: Possible secret detected in code!"
    echo "Review changes carefully."
fi

exit 0
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## 📝 Resumen Ejecutivo

### Qué se encontró

- ✅ Archivo `.env` con contraseña SMTP real
- ✅ Contraseñas débiles en docker-compose
- ✅ Falta de secrets management

### Qué se debe hacer AHORA

1. **Eliminar .env del repo** (git rm --cached)
2. **Actualizar .gitignore**
3. **Crear .env.example** sin secrets
4. **Rotar contraseña SMTP** en Zoho

### Qué se debe hacer en 24-48h

1. Cambiar contraseñas débiles (Grafana, PostgreSQL, Redis)
2. Implementar pre-commit hooks
3. Documentar proceso de rotación de secrets

### Qué se debe hacer en v2.6.0

1. Migrar a Docker Secrets o Vault
2. Remover fallbacks de passwords en docker-compose
3. Añadir security scanning al CI/CD

---

## 🆘 Si Ya Commiteaste .env Por Error

### Escenario 1: Commit local, NO pusheado

```bash
# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Eliminar .env del staging
git rm --cached .env

# Commit de nuevo SIN .env
git commit -m "..."
```

### Escenario 2: Ya pusheado a GitHub (Repositorio Privado)

```bash
# Limpiar historial
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
git push origin --force --tags

# Rotar TODAS las contraseñas expuestas
```

### Escenario 3: Ya pusheado a GitHub (Repositorio PÚBLICO)

🚨 **CRÍTICO: Considerar todos los secrets comprometidos**

1. **Rotar INMEDIATAMENTE:**
   - Contraseña SMTP Zoho
   - Contraseñas de PostgreSQL
   - Contraseñas de Redis
   - API keys (si hubiera)

2. **Revisar logs de acceso** en Zoho, PostgreSQL, etc.

3. **Notificar al equipo** del incidente

4. **Documentar** el incidente para auditoría

5. **Limpiar historial** de GitHub (ver Escenario 2)

6. **Considerar cambiar** cuentas de email si hay evidencia de compromiso

---

## 📞 Contacto en Caso de Dudas

**Fecha:** 16 Diciembre 2025  
**Para soporte:** rafael.canelon@rhinometric.com

---

**ACCIÓN REQUERIDA:** Antes de continuar con `git commit`, ejecutar los 6 pasos de "ACCIÓN INMEDIATA REQUERIDA" descritos arriba.

**NO PROCEDER CON GIT PUSH HASTA QUE TODOS LOS CHECKBOXES ESTÉN MARCADOS.**
