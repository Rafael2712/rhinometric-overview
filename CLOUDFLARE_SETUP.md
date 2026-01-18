# 🌐 Configuración Cloudflare para RHINOMETRIC

## 📊 Arquitectura de Dominios

```
rhinometric.com
├── rhinometric.com           → WordPress (sitio público)
├── app.rhinometric.com       → Plataforma Grafana (puerto 80)
├── license.rhinometric.com   → Sistema de licencias (puerto 5000)
└── api.rhinometric.com       → API Proxy (puerto 8081) [opcional]
```

---

## ✅ OPCIÓN 1: Cloudflare Tunnel (RECOMENDADO)

**Ventajas:**
- ✅ No necesitas IP pública estática
- ✅ SSL automático y gratuito
- ✅ No necesitas abrir puertos en router
- ✅ Protección DDoS incluida
- ✅ Conexión directa y segura desde tu PC

### Paso 1: Instalar Cloudflare Tunnel en WSL

```bash
# En Ubuntu-22.04 (WSL)
wsl -d Ubuntu-22.04 -- bash -c "
  curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && 
  sudo dpkg -i cloudflared.deb &&
  rm cloudflared.deb
"
```

### Paso 2: Autenticar con Cloudflare

```bash
wsl -d Ubuntu-22.04 -- cloudflared tunnel login
```

Esto abrirá tu navegador para autenticarte.

### Paso 3: Crear el Tunnel

```bash
# Crear tunnel llamado "rhinometric"
wsl -d Ubuntu-22.04 -- cloudflared tunnel create rhinometric

# Copiar el TUNNEL_ID que aparece
```

### Paso 4: Configurar el Tunnel

Crear archivo `/home/rafael/.cloudflared/config.yml`:

```yaml
tunnel: <TU_TUNNEL_ID>
credentials-file: /home/rafael/.cloudflared/<TU_TUNNEL_ID>.json

ingress:
  # Plataforma principal (Grafana)
  - hostname: app.rhinometric.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
  
  # Sistema de licencias
  - hostname: license.rhinometric.com
    service: http://localhost:5000
    originRequest:
      noTLSVerify: true
  
  # API Proxy (opcional)
  - hostname: api.rhinometric.com
    service: http://localhost:8081
    originRequest:
      noTLSVerify: true
  
  # Catch-all (necesario)
  - service: http_status:404
```

### Paso 5: Crear rutas DNS en Cloudflare

```bash
# Crear registros DNS automáticamente
wsl -d Ubuntu-22.04 -- bash -c "
  cloudflared tunnel route dns rhinometric app.rhinometric.com &&
  cloudflared tunnel route dns rhinometric license.rhinometric.com &&
  cloudflared tunnel route dns rhinometric api.rhinometric.com
"
```

### Paso 6: Ejecutar el Tunnel

**Opción A: Ejecutar manualmente (para pruebas)**
```bash
wsl -d Ubuntu-22.04 -- cloudflared tunnel run rhinometric
```

**Opción B: Instalar como servicio (producción)**
```bash
wsl -d Ubuntu-22.04 -- sudo cloudflared service install
wsl -d Ubuntu-22.04 -- sudo systemctl start cloudflared
wsl -d Ubuntu-22.04 -- sudo systemctl enable cloudflared
```

---

## 🔧 OPCIÓN 2: DNS Directo (Requiere IP pública estática)

**Ventajas:**
- ⚡ Conexión directa sin intermediarios
- 🎮 Control total sobre la infraestructura

**Desventajas:**
- ❌ Necesitas IP pública estática (puede costar dinero adicional a ISP)
- ❌ Debes abrir puertos en router (seguridad)
- ❌ SSL manual (certificados Let's Encrypt)

### Paso 1: Obtener tu IP pública

```bash
curl -s ifconfig.me
```

### Paso 2: Configurar DNS en Cloudflare

En el panel de Cloudflare DNS:

1. **app.rhinometric.com**
   - Tipo: `A`
   - Nombre: `app`
   - Contenido: `TU_IP_PÚBLICA`
   - Proxy: ✅ Activado (naranja)
   - TTL: Auto

2. **license.rhinometric.com**
   - Tipo: `A`
   - Nombre: `license`
   - Contenido: `TU_IP_PÚBLICA`
   - Proxy: ✅ Activado
   - TTL: Auto

### Paso 3: Configurar Port Forwarding en Router

En tu router (acceder a 192.168.1.1 o similar):

- Puerto `80` → `172.24.31.144:80` (nginx)
- Puerto `5000` → `172.24.31.144:5000` (license-server)
- Puerto `443` → `172.24.31.144:443` (nginx SSL)

**⚠️ PROBLEMA**: La IP de WSL (`172.24.31.144`) **cambia cada vez que reinicias Windows**.

**SOLUCIÓN**: Fijar IP de WSL en `.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
networkAddress=172.24.31.144  # Fijar esta IP
```

### Paso 4: Configurar SSL con Cloudflare

Cloudflare → SSL/TLS:
- Modo de cifrado: **Flexible** (para empezar)
- Más adelante: **Full (strict)** con certificados Let's Encrypt

---

## 🎯 Recomendación Final

**PARA PRUEBAS INMEDIATAS**: Cloudflare Tunnel (Opción 1)
- No necesitas configurar router
- Funciona desde cualquier red
- SSL incluido
- Gratis

**PARA PRODUCCIÓN A LARGO PLAZO**: Evaluar ambas
- Tunnel: Más fácil de mantener
- DNS Directo: Mejor rendimiento (eliminación de intermediarios)

---

## 🧪 Verificación

Una vez configurado, prueba:

```bash
# Desde cualquier computadora con internet
curl -I https://app.rhinometric.com
curl https://license.rhinometric.com/api/health
```

Deberías ver:
- `app.rhinometric.com` → Redirige a `/login` de Grafana
- `license.rhinometric.com` → `{"status":"healthy"}`

---

## 📞 Soporte

- Documentación Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Dashboard Cloudflare: https://dash.cloudflare.com/
