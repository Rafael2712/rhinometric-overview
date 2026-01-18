# 🔑 CÓMO OBTENER GRAFANA API TOKEN

## Paso 1: Acceder a Grafana

Abre tu navegador en: **http://localhost:80**

- **Usuario**: `admin`
- **Contraseña**: `admin`

---

## Paso 2: Crear API Token

1. En el menú lateral, haz clic en **⚙️ Configuration** → **API Keys**
2. Haz clic en **➕ Add API Key**
3. Configura el token:
   - **Name**: `rhinometric-connector`
   - **Role**: **Admin**
   - **Time to live**: Dejar en blanco (sin expiración)
4. Haz clic en **Add**
5. **¡IMPORTANTE!** Copia el token generado (solo se muestra una vez)

---

## Paso 3: Actualizar archivos .env

### API Connector

Edita: `api-connector/.env`

```env
GRAFANA_URL=http://rhinometric-grafana:3000
GRAFANA_API_TOKEN=TU_TOKEN_AQUI
DATABASE_URL=postgresql://rhinometric:rhinometric2024@rhinometric-postgres:5432/rhinometric
```

### Dashboard Builder

Edita: `dashboard-builder/.env`

```env
GRAFANA_URL=http://rhinometric-grafana:3000
GRAFANA_API_TOKEN=TU_TOKEN_AQUI
DATABASE_URL=postgresql://rhinometric:rhinometric2024@rhinometric-postgres:5432/rhinometric
```

---

## Paso 4: Reiniciar servicios

```bash
docker compose -f docker-compose-v2.2.0.yml restart api-connector dashboard-builder
```

---

## ✅ Verificación

1. **API Connector**: http://localhost:8000
   - Crea una conexión
   - Haz clic en "🔗 Crear Datasource en Grafana"
   - Deberías ver: ✅ Datasource creado con UID

2. **Dashboard Builder**: http://localhost:8001
   - Selecciona un template
   - Agrega paneles
   - Haz clic en "🚀 Crear en Grafana"
   - Deberías ver: ✅ Dashboard creado con UID

3. **Grafana**: http://localhost:80
   - Ve a Dashboards
   - Deberías ver el dashboard creado
   - Ve a Datasources
   - Deberías ver el datasource creado

---

## 🔒 Seguridad

⚠️ **IMPORTANTE**: Este token tiene privilegios de Admin.

- **No lo compartas**
- **No lo commits en Git**
- Los archivos `.env` están en `.gitignore`
- En producción, usa secrets management (Vault, K8s Secrets, etc.)

---

## 🐛 Troubleshooting

### Error: "GRAFANA_API_TOKEN not configured"
- Verifica que el token esté en el `.env`
- Reinicia los contenedores

### Error: "Invalid username or password"
- Las credenciales son: admin / admin
- Si cambiaste la contraseña, usa la nueva

### Error: "Cannot connect to Grafana"
- Verifica que Grafana esté corriendo: `docker ps | grep grafana`
- Verifica la URL: debe ser `http://rhinometric-grafana:3000` (dentro de Docker)
