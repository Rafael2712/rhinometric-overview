# Configuración de Email Zoho para License Management

## 📧 Paso 1: Configurar contraseña en `.env`

Edita el archivo `.env` en la raíz del proyecto:

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
nano .env
```

Reemplaza `TU_CONTRASEÑA_DE_ZOHO_AQUI` con tu contraseña real de Zoho:

```properties
# Zoho Mail SMTP (Para envío de licencias)
ZOHO_PASSWORD=tu_contraseña_real_aqui
```

**IMPORTANTE:** 
- Usa la contraseña de tu cuenta Zoho Mail (rafael.canelon@rhinometric.com)
- NO uses comillas ni espacios
- Guarda el archivo (Ctrl+O, Enter, Ctrl+X en nano)

---

## 🔐 Paso 2: Si tienes autenticación de dos factores (2FA)

Si tu cuenta Zoho tiene 2FA habilitado, necesitas una **contraseña de aplicación**:

### Generar contraseña de aplicación en Zoho:

1. Inicia sesión en https://accounts.zoho.com
2. Ve a **Seguridad** → **Contraseñas de aplicación**
3. Click en **Generar nueva contraseña**
4. Nombre: "Rhinometric License Server"
5. Copia la contraseña generada
6. Pégala en `.env`:

```properties
ZOHO_PASSWORD=abcd-efgh-ijkl-mnop
```

---

## 🚀 Paso 3: Reiniciar el servicio

Una vez configurada la contraseña:

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal

# Reiniciar el license-server con la nueva configuración
docker compose -f docker-compose-v2.1.0.yml up -d license-server-v2

# Esperar 5 segundos
sleep 5

# Verificar que esté funcionando
curl http://localhost:5000/api/health
```

---

## ✅ Paso 4: Probar envío de email

### Opción A: Desde la UI

1. Abre http://localhost:8092
2. Ve a "Crear Licencia"
3. Llena el formulario con datos reales
4. Click "Crear Licencia"
5. Verifica que `email_sent: true` en la respuesta
6. Revisa el inbox del cliente

### Opción B: Desde la terminal

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Cliente Prueba",
    "client_email": "tu_email_de_prueba@gmail.com",
    "client_company": "Test Corp",
    "license_type": "trial"
  }'
```

Deberías ver:
```json
{
  "email_sent": true,
  ...
}
```

---

## 🔍 Verificar logs

Si hay problemas, revisa los logs:

```bash
docker logs rhinometric-license-server-v2 --tail 50 | grep -i "email\|smtp"
```

**Mensajes de éxito:**
```
✅ Email enviado exitosamente a cliente@ejemplo.com
```

**Mensajes de error comunes:**

1. **"SMTP_PASSWORD no configurado"**
   - Solución: Configura `ZOHO_PASSWORD` en `.env`

2. **"Authentication failed"**
   - Solución: Verifica usuario/contraseña correctos
   - Si tienes 2FA, usa contraseña de aplicación

3. **"Connection refused"**
   - Solución: Verifica que `smtp.zoho.com` sea accesible
   - Puerto correcto: 587

---

## 📋 Configuración SMTP de Zoho (referencia)

```yaml
SMTP_HOST: smtp.zoho.com
SMTP_PORT: 587
SMTP_USER: rafael.canelon@rhinometric.com
SMTP_PASSWORD: [tu contraseña o contraseña de aplicación]
Seguridad: STARTTLS
```

---

## 📧 Contenido del email enviado

El cliente recibirá un email con:

- **Asunto:** "Tu licencia Rhinometric [TIPO] está lista"
- **De:** rafael.canelon@rhinometric.com
- **Contenido:**
  - Clave de licencia única
  - Instrucciones completas de instalación
  - Comandos de descarga y despliegue
  - URLs de acceso a componentes
  - Documentación
  - Información de soporte

---

## 🆘 Soporte

Si tienes problemas:

1. Verifica que la contraseña en `.env` sea correcta
2. Revisa los logs: `docker logs rhinometric-license-server-v2`
3. Prueba autenticarte manualmente en Zoho Mail
4. Verifica que no haya firewall bloqueando puerto 587

---

**Última actualización:** 28 de octubre de 2025
