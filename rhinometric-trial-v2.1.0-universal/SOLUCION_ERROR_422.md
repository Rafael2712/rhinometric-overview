# 🔧 SOLUCION ERROR 422 - License Creation

**Fecha**: 29 de octubre de 2025  
**Estado**: ✅ RESUELTO

---

## 🐛 Problema Original

Al intentar crear una licencia desde la UI (http://localhost:8092), el endpoint POST `/api/admin/licenses` retornaba:

```
Error: Request failed with status code 422
```

**Logs del servidor**:
```
INFO: 172.21.0.1:50886 - "POST /api/admin/licenses HTTP/1.1" 422 Unprocessable Entity
```

---

## 🔍 Diagnóstico

Error 422 (Unprocessable Entity) en FastAPI indica **validación fallida** en el modelo Pydantic.

**Causa raíz**: El modelo `LicenseCreateRequest` tenía el campo `client_company` como **requerido**:

```python
class LicenseCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    client_email: EmailStr
    client_company: str  # ❌ REQUERIDO - causaba 422
    license_type: str = Field(..., pattern="^(trial|annual|permanent)$")
```

Pero la UI solo enviaba:
```json
{
  "customer_name": "Test User",
  "client_email": "test@example.com",
  "license_type": "trial"
  // ❌ Faltaba client_company
}
```

---

## ✅ Solución Implementada

Cambié `client_company` a **opcional** con valor por defecto:

```python
class LicenseCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    client_email: EmailStr
    client_company: Optional[str] = ""  # ✅ OPCIONAL
    license_type: str = Field(..., pattern="^(trial|annual|permanent)$")
```

**Archivo modificado**: `license-server-v2/main.py` (línea 131)

---

## 🚀 Pasos de Implementación

### 1. Modificación del Código

```bash
# Editar main.py
nano license-server-v2/main.py

# Línea 131: Cambiar
client_company: str
# Por:
client_company: Optional[str] = ""
```

### 2. Rebuild del Contenedor

```bash
cd rhinometric-trial-v2.1.0-universal
docker compose -f docker-compose-v2.1.0.yml up -d --build license-server-v2
```

**Resultado**:
```
[+] Running 4/4
 ✔ rhinometric-trial-v210-universal-license-server-v2  Built
 ✔ Container rhinometric-redis                         Healthy
 ✔ Container rhinometric-postgres                      Healthy
 ✔ Container rhinometric-license-server-v2             Started
```

### 3. Testing

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User",
    "client_email": "test@example.com",
    "license_type": "trial"
  }'
```

**Respuesta exitosa** (200 OK):
```json
{
  "id": 37,
  "customer_name": "Test User",
  "license_key": "RHINO-TRIAL-2025-TCMWCFHGWQ6N",
  "license_type": "trial",
  "client_email": "test@example.com",
  "client_company": "",
  "status": "active",
  "created_at": "2025-10-29T10:54:48.872442",
  "expires_at": "2025-11-28T10:54:48.872442",
  "days_remaining": 30,
  "is_active": true,
  "email_sent": false
}
```

**Nota**: `email_sent: false` es esperado porque `SMTP_PASSWORD` no está configurado.

---

## 📊 Verificación

### Logs del Servidor

```bash
docker logs rhinometric-license-server-v2 --tail 30 | grep -i email
```

**Salida**:
```
2025-10-29 10:54:48,962 - rhinometric.email - WARNING - SMTP password not configured - Email not sent to test@example.com
```

✅ **Sistema funcionando correctamente** - solo falta configurar SMTP para envío de emails.

### Base de Datos

```bash
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric_trial -c "SELECT id, customer_name, license_key, license_type FROM licenses WHERE id=37;"
```

**Salida esperada**:
```
 id |  customer_name | license_key              | license_type 
----+----------------+--------------------------+--------------
 37 | Test User      | RHINO-TRIAL-2025-TCMWC... | trial
```

---

## 🎯 Próximos Pasos

### A. Configurar SMTP Password (5 min)

1. Ir a: https://accounts.zoho.com/home#security/security
2. Generar app password para "Rhinometric License Server"
3. Editar `.env`:
   ```bash
   SMTP_PASSWORD=tu_app_password_generado
   ```
4. Reiniciar:
   ```bash
   docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
   ```

### B. Convertir Markdown a PDF (10 min)

**Opción 1: Pandoc**
```bash
cd docs/
pandoc manual_usuario.md -o manual_usuario.pdf --toc --pdf-engine=xelatex
pandoc guia_instalacion.md -o guia_instalacion.pdf --toc --pdf-engine=xelatex
```

**Opción 2: Online**
- https://www.markdowntopdf.com/
- Subir `manual_usuario.md` → Descargar PDF
- Subir `guia_instalacion.md` → Descargar PDF

### C. Verificar PDFs Montados (1 min)

```bash
docker exec rhinometric-license-server-v2 ls -lh /app/docs/
```

Debe mostrar:
- `manual_usuario.pdf`
- `guia_instalacion.pdf`

### D. Testing Email End-to-End (5 min)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Rafael Test",
    "client_email": "rafael.canelon@rhinometric.com",
    "license_type": "trial"
  }'
```

Verificar:
1. `"email_sent": true` en respuesta
2. Logs: `docker logs rhinometric-license-server-v2 | grep "Email sent successfully"`
3. Inbox con email + PDFs adjuntos

### E. Commit Cambios (2 min)

```bash
git add license-server-v2/main.py
git commit -m "fix: Make client_company optional in LicenseCreateRequest

- Changed client_company from required to Optional[str] with empty default
- Resolves HTTP 422 error when creating licenses without company info
- Allows UI to create licenses with minimal fields
- Email functionality preserved (warns if SMTP not configured)

Tested: License creation successful (ID:37, KEY:RHINO-TRIAL-2025-TCMWCFHGWQ6N)"

git push origin dev
```

---

## 📝 Cambios en Código

### Antes (❌ Causaba error 422):

```python
class LicenseCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    client_email: EmailStr
    client_company: str  # REQUERIDO
    license_type: str = Field(..., pattern="^(trial|annual|permanent)$")
```

### Después (✅ Funciona):

```python
class LicenseCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    client_email: EmailStr
    client_company: Optional[str] = ""  # OPCIONAL con default
    license_type: str = Field(..., pattern="^(trial|annual|permanent)$")
```

---

## 🧪 Testing Adicional

### Test 1: Con company (retrocompatibilidad)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User 2",
    "client_email": "test2@example.com",
    "client_company": "Test Corp",
    "license_type": "trial"
  }'
```

✅ **Debe funcionar** (company incluida en respuesta)

### Test 2: Sin company (caso original)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test User 3",
    "client_email": "test3@example.com",
    "license_type": "annual"
  }'
```

✅ **Debe funcionar** (company="")

### Test 3: License types

```bash
# Trial (30 días)
{"license_type": "trial", ...}

# Annual (365 días)
{"license_type": "annual", ...}

# Permanent (100 años)
{"license_type": "permanent", ...}
```

---

## 📚 Documentación Relacionada

- `RESUMEN_IMPLEMENTACION.md` - Testing completo del sistema
- `QUICK_START_EMAILS.md` - Referencia rápida
- `docs/EMAIL_SYSTEM_STATUS.md` - Documentación técnica

---

## ✅ Checklist de Resolución

- [x] Identificar causa raíz (client_company requerido)
- [x] Modificar modelo a Optional
- [x] Rebuild contenedor
- [x] Testing con curl (exitoso)
- [x] Verificar logs (warning SMTP esperado)
- [x] Documentar solución
- [ ] Configurar SMTP_PASSWORD
- [ ] Convertir PDFs
- [ ] Testing end-to-end con emails
- [ ] Commit y push

---

**© 2025 Rhinometric - Error 422 Resolved**

Tiempo total de resolución: **15 minutos**  
Complejidad: **Baja** (cambio de 1 línea)  
Impacto: **Alto** (desbloquea testing completo)
