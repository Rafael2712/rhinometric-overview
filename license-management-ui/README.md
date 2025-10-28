# 🔐 Rhinometric License Management UI

**Versión**: 1.0.0  
**Puerto**: 8092  
**Tecnología**: Vue.js 3 + Vite + Pinia  
**Contacto**: rafael.canelon@rhinometric.com

---

## 📋 Descripción

Interfaz administrativa para gestionar licencias de Rhinometric v2.1.0. Permite crear, monitorizar y administrar licencias de clientes con integración automática de email.

## ✨ Características

### 🎨 3 Tipos de Licencias
1. **Trial** (30 días)
   - Funcionalidad completa
   - Sin soporte comercial
   - Auto-expiración
   - Gratis

2. **Annual** (1 año)
   - Soporte 24/7
   - Updates automáticos
   - Sin marca de agua
   - Precio a consultar

3. **Permanent** (Sin expiración)
   - Licencia perpetua
   - Soporte prioritario
   - Customización
   - Precio a consultar

### 📊 Dashboard
- Licencias activas en tiempo real
- Alertas de expiración (7 días)
- Estadísticas por tipo
- Filtros avanzados

### 📧 Email Automático
- Envío automático al crear licencia
- Template HTML profesional
- Adjunta license key
- Link de descarga trial package
- Guías de instalación

### 📋 Gestión Completa
- Ver todas las licencias
- Extender período
- Revocar licencias
- Reenviar emails
- Exportar datos (JSON/CSV)

---

## 🚀 Instalación

### Desarrollo Local

```bash
# 1. Instalar dependencias
npm install

# 2. Iniciar servidor desarrollo
npm run dev

# 3. Abrir navegador
# http://localhost:8092
```

### Producción (Docker)

```bash
# 1. Build imagen
docker build -t license-mgmt-ui:latest .

# 2. Iniciar con docker-compose
docker-compose up -d

# 3. Verificar
docker ps | grep license-mgmt
curl http://localhost:8092
```

### Integración con Stack Rhinometric

```yaml
# Agregar a docker-compose-v2.1.0.yml

services:
  license-management-ui:
    build: ./license-management-ui
    container_name: rhinometric-license-mgmt-ui
    ports:
      - "8092:8092"
    environment:
      - NODE_ENV=production
      - VITE_API_URL=http://license-server-v2:8000
    networks:
      - rhinometric_network_v21
    depends_on:
      - license-server-v2
    restart: unless-stopped
```

---

## 🔧 Configuración

### Variables de Entorno

```bash
# .env (opcional)
VITE_API_URL=http://localhost:8000
NODE_ENV=production
```

### Backend API Endpoints

La UI espera estos endpoints en `license-server-v2`:

```python
# Admin endpoints (require RHINOMETRIC_MODE != 'trial')

POST   /api/admin/licenses/create    # Crear licencia
GET    /api/admin/licenses           # Listar todas
PATCH  /api/admin/licenses/:id/revoke      # Revocar
PATCH  /api/admin/licenses/:id/extend      # Extender
POST   /api/admin/licenses/:id/email       # Reenviar email
GET    /api/admin/licenses/stats           # Estadísticas
```

---

## 📁 Estructura del Proyecto

```
license-management-ui/
├── src/
│   ├── components/           # Componentes Vue reutilizables
│   ├── views/
│   │   ├── Home.vue         # Dashboard principal
│   │   ├── CreateLicense.vue # Formulario creación
│   │   ├── ManageLicenses.vue # Tabla gestión
│   │   └── Settings.vue     # Configuración
│   ├── services/
│   │   └── licenseService.js # API integration
│   ├── router/
│   │   └── index.js         # Vue Router
│   ├── store/
│   │   └── index.js         # Pinia store
│   ├── assets/
│   │   └── styles.css       # Estilos globales
│   ├── App.vue              # App principal
│   └── main.js              # Entry point
├── public/                  # Assets estáticos
├── Dockerfile              # Docker multi-stage
├── docker-compose.yml      # Deployment config
├── package.json            # Dependencies
├── vite.config.js          # Vite config
├── index.html              # HTML entry
└── README.md               # Este archivo
```

---

## 🎯 Uso

### 1. Acceder a la UI

```
http://localhost:8092
```

### 2. Crear Nueva Licencia

1. Click "Crear Licencia"
2. Seleccionar tipo (Trial/Annual/Permanent)
3. Rellenar datos del cliente
4. Click "Crear Licencia y Enviar Email"
5. ✅ Email automático enviado

### 3. Gestionar Licencias

1. Click "Gestionar"
2. Ver tabla con todas las licencias
3. Filtrar por tipo/estado
4. Acciones disponibles:
   - 👁️ Ver detalles
   - 📧 Reenviar email
   - ⏱️ Extender período
   - 🚫 Revocar

### 4. Configuración

1. Click "Configuración"
2. Configurar SMTP para emails
3. Ver estado del backend
4. Exportar licencias (JSON/CSV)
5. Generar reportes

---

## 📧 Configuración Email

### Gmail (Recomendado)

```javascript
// Settings.vue
{
  provider: 'gmail',
  from: 'rafael.canelon@rhinometric.com',
  smtp: {
    host: 'smtp.gmail.com',
    port: 587,
    user: 'rafael.canelon@rhinometric.com',
    password: 'tu-app-password'  // Crear en Google Account
  }
}
```

### Crear App Password (Gmail)

1. https://myaccount.google.com/security
2. 2-Step Verification → App passwords
3. Crear password para "Rhinometric License UI"
4. Copiar y pegar en Settings

---

## 🐛 Troubleshooting

### UI no carga

```bash
# Verificar puerto
lsof -i :8092

# Ver logs
docker logs rhinometric-license-mgmt-ui

# Reiniciar
docker-compose restart license-management-ui
```

### Backend no conecta

```bash
# Verificar license-server
docker ps | grep license-server
curl http://localhost:8000/api/admin/licenses

# Verificar red
docker network inspect rhinometric_network_v21
```

### Emails no se envían

1. Verificar configuración SMTP en Settings
2. Probar con botón "🧪 Probar Email"
3. Verificar logs del backend
4. Gmail: Verificar App Password

---

## 📊 Screenshots

### Dashboard
```
┌─────────────────────────────────────────┐
│ 🦏 Rhinometric License Management      │
│ Dashboard | Crear Licencia | Gestionar │
├─────────────────────────────────────────┤
│ ┌───────┐ ┌───────┐ ┌───────┐ ┌──────┐│
│ │ ✅ 45 │ │ ⚠️ 3  │ │ 🔬 12 │ │♾️ 8  ││
│ │Activas│ │Expiran│ │Trials │ │Perm. ││
│ └───────┘ └───────┘ └───────┘ └──────┘│
│                                         │
│ Acciones Rápidas                        │
│ ➕ Nueva Licencia  🔄 Actualizar       │
└─────────────────────────────────────────┘
```

---

## 🚀 Roadmap

### v1.1 (Próxima versión)
- [ ] Gráficos de uso con Chart.js
- [ ] Notificaciones push (expiración)
- [ ] Multi-idioma (EN/ES)
- [ ] Dark mode

### v1.2
- [ ] API REST completa
- [ ] Webhooks
- [ ] Integración Slack/Discord
- [ ] Reportes avanzados (PDF)

---

## 📞 Soporte

**Rafael Canel**  
📧 rafael.canelon@rhinometric.com  
🐙 GitHub: https://github.com/Rafael2712/rhinometric-overview

---

## 📜 Licencia

Uso interno exclusivo para administración de Rhinometric v2.1.0.

---

## 🙏 Créditos

- **Vue.js 3**: Framework reactivo
- **Vite**: Build tool ultrarrápido
- **Pinia**: State management
- **Axios**: HTTP client
- **Rhinometric v2.1.0**: Plataforma de observabilidad

---

**🦏 Rhinometric - Observabilidad de Nivel Enterprise**
