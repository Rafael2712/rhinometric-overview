# 📋 Instrucciones para Instalar el Proxy PHP en WordPress

## ⚠️ IMPORTANTE
El formulario de trial ya está actualizado en WordPress, pero necesita el archivo proxy PHP para funcionar.

## 🎯 Pasos a seguir

### Opción A: Subir archivo via SSH (RECOMENDADO)

1. **Conectar al servidor WordPress (París - 15.236.157.190)**
   ```bash
   ssh ubuntu@15.236.157.190 -i /ruta/a/tu/llave.pem
   ```

2. **Navegar al directorio del tema activo**
   ```bash
   cd /var/www/html/wp-content/themes
   ls -la  # Ver qué tema está activo
   ```

3. **Subir el archivo proxy al tema activo**
   
   Si el tema es `twentytwentyfour` (por ejemplo):
   ```bash
   # Desde tu máquina local, subir el archivo
   scp -i /ruta/a/tu/llave.pem wordpress-trial-proxy.php ubuntu@15.236.157.190:/tmp/
   
   # Desde el servidor, moverlo al tema
   sudo mv /tmp/rhinometric-trial-proxy.php /var/www/html/wp-content/themes/twentytwentyfour/
   sudo chown www-data:www-data /var/www/html/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php
   sudo chmod 644 /var/www/html/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php
   ```

4. **Verificar que funciona**
   ```bash
   curl -X POST https://rhinometric.com/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php \
     -H "Content-Type: application/json" \
     -d '{"customer_name":"Test User","client_email":"test@example.com","client_company":"Test Corp"}'
   ```

### Opción B: Subir archivo via FTP/SFTP

1. Usar FileZilla o WinSCP
2. Conectar a `15.236.157.190` con credenciales SSH
3. Navegar a `/var/www/html/wp-content/themes/[TEMA_ACTIVO]/`
4. Subir `wordpress-trial-proxy.php`
5. Cambiar permisos a 644

### Opción C: Usar WordPress File Manager Plugin

1. Instalar plugin "File Manager" en WordPress
2. Ir a `wp-content/themes/[TEMA_ACTIVO]/`
3. Upload `wordpress-trial-proxy.php`
4. Cambiar permisos a 644

## 🔍 Verificación

Una vez subido el archivo, el formulario debería funcionar automáticamente.

**Test manual:**
```bash
curl -X POST https://rhinometric.com/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Juan Pérez",
    "client_email": "juan.perez@ejemplo.com",
    "client_company": "Ejemplo SL"
  }'
```

**Respuesta esperada:** JSON con la licencia creada + email enviado

## 📝 Archivos involucrados

1. **wordpress-trial-proxy.php** ← Proxy PHP que se conecta internamente al License Server
   - Ubicación final: `/var/www/html/wp-content/themes/[TEMA]/rhinometric-trial-proxy.php`
   - Propósito: Evitar Mixed Content (HTTPS → HTTP) y problemas de CORS

2. **02-trial-linux-page.html** ← Formulario actualizado en WordPress
   - Ya publicado en: https://rhinometric.com/trial/
   - Llama al proxy en lugar del puerto 5000 directamente

## 🔐 Seguridad

El proxy PHP tiene las siguientes medidas de seguridad:
- ✅ Valida que solo sean requests POST
- ✅ Valida formato de email
- ✅ Valida campos requeridos
- ✅ Solo permite CORS desde rhinometric.com
- ✅ Timeout de 30 segundos
- ✅ Logs de errores para debugging

## 🚨 Solución de problemas

### Problema: "Could not connect to license server"
**Causa:** El servidor WordPress (París) no puede conectarse al License Server (Virginia) en el puerto 5000.

**Soluciones:**
1. Verificar que el puerto 5000 esté abierto en el firewall de AWS Lightsail del License Server
2. Verificar que no haya firewall interno (ufw/iptables) bloqueando
3. Probar conectividad desde el servidor de WordPress:
   ```bash
   ssh ubuntu@15.236.157.190
   curl -v http://54.197.192.198:5000/api/health
   ```

### Problema: "404 Not Found" al enviar formulario
**Causa:** El archivo proxy no está en la ruta correcta o el tema no es el esperado.

**Solución:**
1. Verificar tema activo en WordPress: Apariencia → Temas
2. Actualizar la ruta en `02-trial-linux-page.html`:
   ```javascript
   fetch('/wp-content/themes/[TEMA_CORRECTO]/rhinometric-trial-proxy.php', ...)
   ```

### Problema: "500 Internal Server Error"
**Causa:** Error de PHP o permisos incorrectos.

**Solución:**
1. Verificar logs de PHP:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   # o
   sudo tail -f /var/log/apache2/error.log
   ```
2. Verificar permisos: `sudo chmod 644 rhinometric-trial-proxy.php`

## 📞 Contacto

Si tienes problemas, escribe a rafael.canelon@rhinometric.com
