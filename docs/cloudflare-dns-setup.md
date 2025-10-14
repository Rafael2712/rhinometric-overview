# Configuración de Subdominios rhinometric.com en Cloudflare

## 📋 Subdominios Requeridos

### Ambientes de la API:
- **Producción**: `api.rhinometric.com` → Oracle Cloud IP:3000
- **Staging**: `staging-api.rhinometric.com` → Oracle Cloud IP:3002  
- **Desarrollo**: `dev-api.rhinometric.com` → Oracle Cloud IP:3001

### Frontend (futuro):
- **Producción**: `rhinometric.com` → Oracle Cloud IP:80/443
- **Staging**: `staging.rhinometric.com` → Oracle Cloud IP:8002
- **Desarrollo**: `dev.rhinometric.com` → Oracle Cloud IP:8001

## 🔧 Configuración en Cloudflare

### Paso 1: Obtener la IP de Oracle Cloud

```bash
# Si estás en Oracle Cloud VM:
curl ifconfig.me

# Si estás en local y necesitas la IP de Oracle Cloud:
# La IP estática de tu VM debe estar en tu panel de Oracle Cloud
```

### Paso 2: Configurar DNS en Cloudflare

1. **Accede a Cloudflare Dashboard**:
   - Ve a https://dash.cloudflare.com
   - Selecciona tu dominio `rhinometric.com`

2. **Agregar registros DNS**:
   - Ve a la pestaña **DNS**
   - Agregar los siguientes registros **A**:

#### Registros A para API:
```dns
Tipo: A
Nombre: api
IPv4: [TU-IP-ORACLE-CLOUD]
Proxy: 🟠 Desactivado (solo DNS)
TTL: Auto
```

```dns
Tipo: A  
Nombre: staging-api
IPv4: [TU-IP-ORACLE-CLOUD]
Proxy: 🟠 Desactivado (solo DNS)
TTL: Auto
```

```dns
Tipo: A
Nombre: dev-api  
IPv4: [TU-IP-ORACLE-CLOUD]
Proxy: 🟠 Desactivado (solo DNS)
TTL: Auto
```

#### Registros A para Frontend:
```dns
Tipo: A
Nombre: @
IPv4: [TU-IP-ORACLE-CLOUD] 
Proxy: 🟡 Activado (con proxy de Cloudflare)
TTL: Auto
```

```dns
Tipo: A
Nombre: staging
IPv4: [TU-IP-ORACLE-CLOUD]
Proxy: 🟡 Activado (con proxy de Cloudflare)  
TTL: Auto
```

```dns
Tipo: A
Nombre: dev
IPv4: [TU-IP-ORACLE-CLOUD]
Proxy: 🟡 Activado (con proxy de Cloudflare)
TTL: Auto
```

### Paso 3: Configurar Nginx Reverse Proxy en Oracle Cloud

Una vez configurado DNS, necesitarás configurar Nginx para enrutar correctamente:

```nginx
# /etc/nginx/sites-available/rhinometric-api
server {
    listen 80;
    server_name api.rhinometric.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name staging-api.rhinometric.com;
    
    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name dev-api.rhinometric.com;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Paso 4: Configurar SSL (Certificados Let's Encrypt)

```bash
# Instalar Certbot
sudo dnf install -y certbot python3-certbot-nginx

# Generar certificados para todos los subdominios
sudo certbot --nginx -d api.rhinometric.com -d staging-api.rhinometric.com -d dev-api.rhinometric.com -d rhinometric.com -d staging.rhinometric.com -d dev.rhinometric.com
```

## 🧪 Verificación

Una vez configurado, podrás probar:

```bash
# Test de producción
curl https://api.rhinometric.com/api/v1/health

# Test de staging  
curl https://staging-api.rhinometric.com/api/v1/health

# Test de desarrollo
curl https://dev-api.rhinometric.com/api/v1/health
```

## 📝 Notas Importantes

1. **Propagación DNS**: Puede tomar 5-10 minutos en propagarse
2. **Proxy Cloudflare**: Para APIs, mantén el proxy desactivado para evitar limitaciones
3. **SSL/TLS**: Configura en modo "Full (strict)" en Cloudflare una vez tengas certificados
4. **Firewall**: Asegúrate que Oracle Cloud Security List permita tráfico HTTP/HTTPS

## 🚀 Próximos Pasos

1. Configurar los DNS records en Cloudflare
2. Configurar Nginx reverse proxy en Oracle Cloud
3. Instalar certificados SSL
4. Probar todos los endpoints
5. Actualizar las URLs en los archivos .env de producción