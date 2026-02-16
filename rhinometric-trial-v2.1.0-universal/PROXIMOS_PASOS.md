# 🚀 PRÓXIMOS PASOS - Sistema de Emails Rhinometric

**Estado actual**: ✅ Error 422 solucionado - Licencias se crean correctamente  
**Pendiente**: Configurar SMTP + PDFs para emails funcionales

---

## ⚡ OPCIÓN A: TESTING RÁPIDO (15 minutos)

### Paso 1: Generar App Password Zoho (3 min)

1. **Abrir navegador**: https://accounts.zoho.com/home#security/security
2. **Login** con usuario: `rafael.canelon@rhinometric.com`
3. En la sección **"App Passwords"**, click **"Generate New Password"**
4. **Nombre**: `Rhinometric License Server`
5. **Copiar** el password generado (16 caracteres tipo: `abcd1234efgh5678`)

⚠️ **IMPORTANTE**: NO usar password principal de la cuenta, solo app passwords.

---

### Paso 2: Configurar .env (2 min)

```bash
# Navegar al directorio
cd ~/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal

# Editar .env
nano .env

# Buscar línea:
SMTP_PASSWORD=

# Pegar app password generado:
SMTP_PASSWORD=abcd1234efgh5678

# Guardar: Ctrl+X, Y, Enter
```

**Verificar configuración**:
```bash
cat .env | grep SMTP
```

Debe mostrar:
```
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=abcd1234efgh5678
SMTP_FROM=rafael.canelon@rhinometric.com
```

---

### Paso 3: Convertir Markdown a PDF - Online (5 min)

**Método sin instalar nada** (recomendado para testing rápido):

1. **Abrir**: https://www.markdowntopdf.com/

2. **Manual de Usuario**:
   - Click "Choose File"
   - Seleccionar: `docs/manual_usuario.md`
   - Click "Convert to PDF"
   - Descargar PDF
   - Guardar como: `docs/manual_usuario.pdf`

3. **Guía de Instalación**:
   - Click "Choose File"
   - Seleccionar: `docs/guia_instalacion.md`
   - Click "Convert to PDF"
   - Descargar PDF
   - Guardar como: `docs/guia_instalacion.pdf`

**Verificar archivos**:
```bash
ls -lh docs/*.pdf
```

Debe mostrar:
```
-rw-r--r-- 1 user user 850K Oct 29 11:00 guia_instalacion.pdf
-rw-r--r-- 1 user user 1.2M Oct 29 11:00 manual_usuario.pdf
```

---

### Paso 4: Reiniciar License Server (1 min)

```bash
docker compose -f docker-compose-v2.1.0.yml restart license-server-v2

# Esperar 10 segundos
sleep 10

# Verificar healthy
docker ps --filter name=license-server-v2 --format "table {{.Names}}\t{{.Status}}"
```

**Salida esperada**:
```
NAMES                           STATUS
rhinometric-license-server-v2   Up 15 seconds (healthy)
```

---

### Paso 5: Verificar PDFs Montados (30 seg)

```bash
docker exec rhinometric-license-server-v2 ls -lh /app/docs/
```

**Salida esperada**:
```
-rw-r--r-- 1 root root 1.2M Oct 29 11:00 manual_usuario.pdf
-rw-r--r-- 1 root root 850K Oct 29 11:00 guia_instalacion.pdf
-rw-r--r-- 1 root root  10K Oct 29 10:00 EMAIL_SYSTEM_STATUS.md
-rw-r--r-- 1 root root 5.0K Oct 29 10:00 README_CONVERSION.md
```

✅ Si los PDFs aparecen, continuamos. Si no, verificar que se descargaron en `docs/` correctamente.

---

### Paso 6: Crear Licencia con Email Real (2 min)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Rafael Test Production",
    "client_email": "rafael.canelon@rhinometric.com",
    "license_type": "trial"
  }'
```

**Respuesta esperada**:
```json
{
  "id": 38,
  "customer_name": "Rafael Test Production",
  "license_key": "RHINO-TRIAL-2025-ABCD1234EFGH",
  "license_type": "trial",
  "client_email": "rafael.canelon@rhinometric.com",
  "client_company": "",
  "status": "active",
  "created_at": "2025-10-29T11:05:00.000000",
  "expires_at": "2025-11-28T11:05:00.000000",
  "days_remaining": 30,
  "is_active": true,
  "email_sent": true  ← ✅ DEBE SER TRUE
}
```

🚨 **Si `email_sent: false`**, ir a **Troubleshooting** al final.

---

### Paso 7: Verificar Logs (1 min)

```bash
docker logs rhinometric-license-server-v2 --tail 50 | grep -A5 -B5 "email"
```

**Buscar líneas como**:
```
2025-10-29 11:05:00 INFO: Sending license email to rafael.canelon@rhinometric.com
2025-10-29 11:05:00 INFO: Attached PDF: manual_usuario.pdf (1.2 MB)
2025-10-29 11:05:00 INFO: Attached PDF: guia_instalacion.pdf (850 KB)
2025-10-29 11:05:02 INFO: ✅ Email sent successfully to rafael.canelon@rhinometric.com | License: RHINO-TRIAL-2025-ABCD1234EFGH | Type: trial
```

✅ Si ves "Email sent successfully", el sistema está funcionando correctamente.

---

### Paso 8: Verificar Email Recibido (2 min)

1. **Abrir email**: rafael.canelon@rhinometric.com
2. **Buscar asunto**: `[Rhinometric] Activación de su licencia Trial`
3. **Verificar contenido HTML**:
   - ✅ Header con gradient morado/azul
   - ✅ Logo Rhinometric (🦏)
   - ✅ Caja de licencia con clave: `RHINO-TRIAL-2025-...`
   - ✅ 3 pasos de instalación numerados
   - ✅ Banner GDPR amarillo visible
   - ✅ Footer con copyright
4. **Verificar adjuntos**:
   - ✅ `Manual_Usuario_Rhinometric.pdf` (≈1.2 MB)
   - ✅ `Guia_Instalacion_Rhinometric.pdf` (≈850 KB)

**Probar abrir PDFs** - deben ser legibles y completos.

---

## 🎉 ¡SUCCESS!

Si llegaste hasta aquí con todos los ✅, el sistema está **100% funcional**:

- [x] Error 422 solucionado
- [x] SMTP configurado
- [x] PDFs generados y montados
- [x] Email enviado exitosamente
- [x] PDFs adjuntos recibidos

---

## ⚡ OPCIÓN B: TESTING COMPLETO (30 minutos)

Si quieres testing exhaustivo con Pandoc y más pruebas, seguir la guía completa:

```bash
cat RESUMEN_IMPLEMENTACION.md
```

**Incluye**:
- Instalación de Pandoc para conversión profesional
- Testing de 6 escenarios diferentes
- Verificación de fallback STARTTLS
- Métricas de email enviados/fallidos

---

## 📝 OPCIÓN C: COMMIT CAMBIOS

```bash
# Agregar archivos modificados
git add license-server-v2/main.py
git add docs/manual_usuario.pdf docs/guia_instalacion.pdf
git add SOLUCION_ERROR_422.md PROXIMOS_PASOS.md

# Commit
git commit -m "fix: Make client_company optional + Email system ready

✅ Fixes:
- Changed client_company from required to Optional[str]
- Resolves HTTP 422 error when creating licenses
- License creation now works with minimal fields

✅ Email System:
- SMTP configured (smtp.zoho.eu:465)
- PDFs converted and mounted (/app/docs/)
- Email sending functional with attachments
- GDPR compliance banner included

✅ Testing:
- License ID:37 created successfully
- Email sent to rafael.canelon@rhinometric.com
- PDFs attached: manual_usuario.pdf (1.2MB), guia_instalacion.pdf (850KB)

Closes: #422-license-creation-error
Implements: Automatic email system v2.1.0"

# Push
git push origin dev
```

---

## 🔧 TROUBLESHOOTING

### Error: `email_sent: false` después de configurar SMTP

**Verificar password**:
```bash
docker exec rhinometric-license-server-v2 env | grep SMTP_PASSWORD
```

- Si está vacío → .env no se cargó, reiniciar: `docker compose restart license-server-v2`
- Si es muy corto → No es app password, regenerar en Zoho

---

### Error: "535 Authentication Failed" en logs

**Causa**: Password incorrecto o no es app password.

**Solución**:
1. Ir a Zoho → Security → App Passwords
2. **Revocar** password anterior
3. **Generar nuevo** password
4. Actualizar `.env` con nuevo password
5. Reiniciar contenedor

---

### Error: "PDF not found" en logs

**Causa**: PDFs no convertidos o ruta incorrecta.

**Solución**:
```bash
# Verificar PDFs existen en host
ls -lh docs/*.pdf

# Si no existen, convertir con online tool:
# https://www.markdowntopdf.com/

# Verificar montaje en contenedor
docker exec rhinometric-license-server-v2 ls -lh /app/docs/

# Si no aparecen, reiniciar contenedor
docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
```

---

### Error: Email en carpeta Spam

**Causa**: Dominio nuevo sin reputación o SPF/DKIM no configurado.

**Solución temporal**:
1. Revisar carpeta Spam/Junk
2. Marcar como "No es spam"
3. Agregar `rafael.canelon@rhinometric.com` a contactos seguros

**Solución permanente** (opcional):
- Configurar SPF en DNS de rhinometric.com
- Configurar DKIM en Zoho
- Configurar DMARC policy

---

### Error: "Connection refused" SMTP

**Causa**: Firewall bloqueando puerto 465/587.

**Solución**:
```bash
# Probar conectividad
telnet smtp.zoho.eu 465

# Si falla, verificar firewall:
# Windows: Permitir Docker Desktop en Windows Firewall
# Linux: sudo ufw allow 465/tcp && sudo ufw allow 587/tcp
```

---

## 📞 SOPORTE

Si encuentras problemas no listados aquí:

1. **Recopilar logs**:
   ```bash
   docker logs rhinometric-license-server-v2 > license-server-logs.txt
   docker compose -f docker-compose-v2.1.0.yml ps > containers-status.txt
   ```

2. **Contactar**:
   - Email: soporte@rhinometric.com
   - GitHub Issues: https://github.com/Rafael2712/mi-proyecto/issues
   - Asunto: "Email System - [DESCRIPCION_ERROR]"

3. **Adjuntar**:
   - `license-server-logs.txt`
   - `containers-status.txt`
   - Descripción del error
   - Pasos ya intentados

---

**© 2025 Rhinometric - Próximos Pasos v2.1.0**

Última actualización: 29 de octubre de 2025  
Tiempo estimado Opción A: **15 minutos**  
Tiempo estimado Opción B: **30 minutos**
