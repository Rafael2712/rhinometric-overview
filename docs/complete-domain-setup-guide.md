# 🌐 Guía Completa: Configuración rhinometric.com

## 📋 Resumen del Proceso

Esta guía te llevará paso a paso para configurar los subdominios de `rhinometric.com` con Cloudflare y Oracle Cloud.

## 🎯 Objetivos

- **api.rhinometric.com** → Producción (puerto 3000)
- **staging-api.rhinometric.com** → Staging (puerto 3002)  
- **dev-api.rhinometric.com** → Desarrollo (puerto 3001)

---

## 🔧 Paso 1: Obtener IP de Oracle Cloud

### Si estás EN Oracle Cloud VM:
```bash
# Ejecutar en tu VM de Oracle Cloud:
curl ifconfig.me

# O usar nuestro helper:
./infrastructure/oracle-dns-helper.sh discover
```

### Si estás en local (como ahora):
1. Ve al **Oracle Cloud Console**
2. **Compute** → **Instances** 
3. Click en tu instancia
4. Copia la **"Public IP Address"**

**📝 Anota tu IP aquí:** `___________________`

---

## 🌐 Paso 2: Configurar DNS en Cloudflare

### 2.1 Acceder a Cloudflare
1. Ve a https://dash.cloudflare.com
2. Inicia sesión con tu cuenta
3. Selecciona el dominio **rhinometric.com**

### 2.2 Agregar Registros DNS
Ve a la pestaña **DNS** → **Records** y agrega estos registros **A**:

#### Para las APIs:
```
Tipo: A    | Nombre: api           | IPv4: [TU-IP-ORACLE]  | Proxy: 🟠 DNS only | TTL: Auto
Tipo: A    | Nombre: staging-api   | IPv4: [TU-IP-ORACLE]  | Proxy: 🟠 DNS only | TTL: Auto  
Tipo: A    | Nombre: dev-api       | IPv4: [TU-IP-ORACLE]  | Proxy: 🟠 DNS only | TTL: Auto
```

#### Para Frontend (futuro):
```
Tipo: A    | Nombre: @             | IPv4: [TU-IP-ORACLE]  | Proxy: 🟡 Proxied  | TTL: Auto
Tipo: A    | Nombre: staging       | IPv4: [TU-IP-ORACLE]  | Proxy: 🟡 Proxied  | TTL: Auto
Tipo: A    | Nombre: dev           | IPv4: [TU-IP-ORACLE]  | Proxy: 🟡 Proxied  | TTL: Auto
```

**⚠️ IMPORTANTE:** Las APIs usan "DNS only" para acceso directo sin proxy.

### 2.3 Verificar Configuración
- **Guardad cada registro** haciendo click en "Save"
- **Espera 5-10 minutos** para propagación DNS

---

## 🔥 Paso 3: Configurar Nginx en Oracle Cloud

### 3.1 Subir archivos a Oracle Cloud
```bash
# Desde tu máquina local, sube los archivos:
scp -r infrastructure/ opc@[TU-IP-ORACLE]:~/rhinometric-setup/

# O clona el repo directamente en Oracle Cloud:
ssh opc@[TU-IP-ORACLE]
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto
```

### 3.2 Ejecutar configuración de Nginx
```bash
# En Oracle Cloud VM:
sudo ./infrastructure/configure-nginx-domains.sh
```

Este script hará automáticamente:
- ✅ Instalar Nginx y Certbot
- ✅ Configurar reverse proxy para los 3 ambientes  
- ✅ Configurar firewall (puertos 80, 443)
- ✅ Instalar certificados SSL Let's Encrypt
- ✅ Configurar renovación automática

---

## 🧪 Paso 4: Verificar Configuración

### 4.1 Verificar DNS (desde cualquier lugar):
```bash
# Usar nuestro helper:
./infrastructure/oracle-dns-helper.sh test-dns

# O manualmente:
nslookup api.rhinometric.com
nslookup staging-api.rhinometric.com  
nslookup dev-api.rhinometric.com
```

### 4.2 Probar APIs (después de configurar Nginx):
```bash
# Probar endpoints:
curl https://api.rhinometric.com/api/v1/health
curl https://staging-api.rhinometric.com/api/v1/health
curl https://dev-api.rhinometric.com/api/v1/health

# O usar nuestro helper:
./infrastructure/oracle-dns-helper.sh test-api
```

---

## 🚀 Paso 5: Desplegar Ambientes en Oracle Cloud

### 5.1 Ejecutar deployment completo:
```bash
# En Oracle Cloud VM:
./deploy.sh deploy        # Todos los ambientes
# O individualmente:
./deploy.sh deploy prod     # Solo producción
./deploy.sh deploy staging  # Solo staging
./deploy.sh deploy dev      # Solo desarrollo
```

### 5.2 Verificar estado:
```bash
./deploy.sh status
```

---

## 📝 Paso 6: Actualizar Configuración de Entornos

### 6.1 Actualizar CORS en archivos .env:

#### Production (.env.production):
```env
ALLOWED_ORIGINS=https://rhinometric.com,https://api.rhinometric.com
```

#### Staging (.env.staging):
```env
ALLOWED_ORIGINS=https://staging.rhinometric.com,https://staging-api.rhinometric.com
```

#### Development (.env.development):
```env
ALLOWED_ORIGINS=https://dev.rhinometric.com,https://dev-api.rhinometric.com
```

### 6.2 Reiniciar servicios:
```bash
./deploy.sh restart prod
./deploy.sh restart staging  
./deploy.sh restart dev
```

---

## ✅ Checklist de Verificación

- [ ] **DNS configurado** en Cloudflare (6 registros A)
- [ ] **Nginx configurado** en Oracle Cloud
- [ ] **SSL certificados** instalados
- [ ] **Ambientes desplegados** (dev, staging, prod)
- [ ] **APIs respondiendo** en los 3 subdominios
- [ ] **CORS actualizado** en archivos .env

---

## 🛠️ Comandos de Troubleshooting

### Verificar Nginx:
```bash
sudo nginx -t                    # Test configuración
sudo systemctl status nginx      # Estado del servicio
sudo systemctl reload nginx      # Recargar configuración
```

### Verificar Certificados SSL:
```bash
sudo certbot certificates        # Ver certificados instalados
sudo certbot renew --dry-run     # Test renovación
```

### Logs útiles:
```bash
sudo tail -f /var/log/nginx/error.log    # Errores de Nginx
sudo tail -f /var/log/nginx/access.log   # Accesos de Nginx
docker logs rhinometric-api-prod         # Logs de producción
docker logs rhinometric-api-staging      # Logs de staging
docker logs rhinometric-api-dev          # Logs de desarrollo
```

---

## 🎯 Resultado Final

Una vez completado todo, tendrás:

```
✅ https://api.rhinometric.com/api/v1/health           (Producción)
✅ https://staging-api.rhinometric.com/api/v1/health   (Staging) 
✅ https://dev-api.rhinometric.com/api/v1/health       (Desarrollo)
```

**¡Tu SaaS estará listo para producción con ambientes separados y SSL!** 🚀