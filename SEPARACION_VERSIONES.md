# 🔀 SEPARACIÓN DE VERSIONES: PRODUCCIÓN vs TRIAL

## 📋 RESUMEN

Tu plataforma Rhinometric tiene **DOS VERSIONES DIFERENTES** que deben mantenerse **completamente separadas**:

### 🟢 VERSIÓN PRODUCCIÓN (ACTUAL)
- **URL**: http://143.47.63.21:3000
- **Propósito**: Plataforma operativa real
- **Clientes**: Datos reales, producción
- **Ubicación**: Servidor remoto (Oracle Cloud)
- **Base de datos**: PostgreSQL producción
- **Puertos**: 3000 (Grafana), 9090 (Prometheus), etc.

### 🟡 VERSIÓN TRIAL (NUEVA)
- **URL**: http://localhost:3000 (en otra máquina)
- **Propósito**: Demostraciones, pruebas de 6 meses
- **Clientes**: Potenciales clientes evaluando
- **Ubicación**: Máquinas de clientes (on-premise)
- **Base de datos**: PostgreSQL trial aislada
- **Puertos**: Mismos puertos pero en diferentes servidores

---

## 🚫 NUNCA MEZCLAR

### ❌ LO QUE NO DEBES HACER:

1. **NO ejecutar `docker-compose-trial.yml` en el servidor de producción (143.47.63.21)**
2. **NO usar la misma base de datos** para producción y trial
3. **NO compartir volúmenes** entre versiones
4. **NO usar el mismo archivo `.env`**

### ✅ LO QUE SÍ DEBES HACER:

1. **Mantener archivos separados:**
   - Producción: `docker-compose.yml`, `docker-compose-saas-minimal.yml`, etc.
   - Trial: `docker-compose-trial.yml`

2. **Bases de datos independientes:**
   - Producción: `rhinometric_production` (en servidor remoto)
   - Trial: `rhinometric_trial` (en cada instalación trial)

3. **Diferentes máquinas/servidores:**
   - Producción: Oracle Cloud (143.47.63.21)
   - Trial: Laptop del cliente, servidor de prueba, etc.

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
mi-proyecto/
│
├── PRODUCCIÓN (Tu servidor actual)
│   ├── docker-compose.yml              # Compose principal producción
│   ├── docker-compose-saas-minimal.yml # Variante SaaS
│   ├── .env                            # Variables producción
│   └── data/                           # Datos producción
│
├── TRIAL (Para clientes)
│   ├── docker-compose-trial.yml        # ⭐ Compose para trial
│   ├── start-trial.sh                  # ⭐ Instalador Mac/Linux
│   ├── start-trial.ps1                 # ⭐ Instalador Windows
│   ├── config/
│   │   ├── prometheus-saas.yml
│   │   ├── loki-saas.yml
│   │   ├── tempo-saas.yml
│   │   ├── alertmanager-saas.yml
│   │   └── nginx-trial.conf
│   └── licenses/                       # Licencias trial generadas
│
└── COMPARTIDO (Configuraciones base)
    ├── licensing/                      # Sistema de licencias
    ├── license-dashboard/              # Dashboard de monitoreo
    └── rhinometric-license/            # Core de licenciamiento
```

---

## 🎯 ESCENARIOS DE USO

### ESCENARIO 1: Cliente potencial solicita prueba
```bash
# En la máquina del CLIENTE (no en tu servidor):

cd /ruta/donde/copien/los-archivos
./start-trial.sh

# Esto crea una instalación INDEPENDIENTE en su máquina
# No afecta tu producción en 143.47.63.21
```

### ESCENARIO 2: Trabajar en producción (tu servidor actual)
```bash
# En tu servidor 143.47.63.21:

ssh usuario@143.47.63.21
cd /ruta/produccion
docker-compose up -d    # O el compose que uses actualmente

# NO ejecutes docker-compose-trial.yml aquí
```

### ESCENARIO 3: Desarrollo y pruebas locales
```bash
# En tu LAPTOP/Mac para probar trial:

cd mi-proyecto
./start-trial.sh

# Accedes a http://localhost:3000
# Esto NO afecta tu producción remota
```

---

## 🔧 CÓMO INSTALAR TRIAL EN CLIENTE

### Paso 1: Preparar paquete para el cliente
```bash
# En tu máquina de desarrollo:
cd mi-proyecto

# Crear directorio limpio para trial
mkdir rhinometric-trial-package
cd rhinometric-trial-package

# Copiar solo archivos necesarios
cp ../docker-compose-trial.yml .
cp ../start-trial.sh .
cp ../start-trial.ps1 .
cp -r ../config .
cp -r ../licensing .
cp -r ../license-dashboard .
cp -r ../rhinometric-license .
cp ../RESUMEN_IMPLEMENTACION.md README.md

# Crear .env de ejemplo
cat > .env.example << 'EOF'
# Rhinometric Trial - Configurar antes de iniciar
POSTGRES_PASSWORD=cambiar_esto
GRAFANA_PASSWORD=cambiar_esto
JWT_SECRET=cambiar_esto
GRAFANA_URL=http://localhost:3000
DASHBOARD_PORT=8080
EOF
```

### Paso 2: Comprimir y enviar al cliente
```bash
cd ..
tar -czf rhinometric-trial-v1.0.tar.gz rhinometric-trial-package/

# O en Windows:
# Comprimir carpeta "rhinometric-trial-package" a ZIP
```

### Paso 3: Cliente descomprime e instala
```bash
# Cliente ejecuta en su Mac:
tar -xzf rhinometric-trial-v1.0.tar.gz
cd rhinometric-trial-package
chmod +x start-trial.sh
./start-trial.sh
```

---

## ⚙️ DIFERENCIAS TÉCNICAS

| Característica | PRODUCCIÓN | TRIAL |
|----------------|------------|-------|
| **Docker Compose** | `docker-compose.yml` | `docker-compose-trial.yml` |
| **Base de datos** | `rhinometric_production` | `rhinometric_trial` |
| **Retención datos** | 30+ días | 7 días |
| **Máx usuarios** | Ilimitado | 5 usuarios |
| **Licencia** | Permanente/Anual | 180 días |
| **Puertos** | Producción (fijos) | Localhost (flexibles) |
| **SSL/TLS** | Certificado real | Auto-firmado/ninguno |
| **Backups** | Automáticos | No incluidos |
| **Soporte** | 24/7 | Básico |
| **Marca** | Rhinometric | Rhinometric Trial + Watermark |

---

## 🔒 SEGURIDAD: MANTENER SEPARADAS

### Contraseñas/Secretos diferentes:
```bash
# PRODUCCIÓN: .env en servidor 143.47.63.21
POSTGRES_PASSWORD=produccion_super_secreta_123
JWT_SECRET=produccion_jwt_secret_xyz

# TRIAL: .env generado automáticamente en cada instalación
POSTGRES_PASSWORD=trial_generado_abc
JWT_SECRET=trial_generado_def
```

### Bases de datos aisladas:
- **Producción**: PostgreSQL en `143.47.63.21:5432` → `rhinometric_production`
- **Trial Cliente A**: PostgreSQL en `localhost:5432` → `rhinometric_trial` (máquina cliente)
- **Trial Cliente B**: PostgreSQL en `localhost:5432` → `rhinometric_trial` (otra máquina)

**No hay conexión** entre estas bases de datos.

---

## 🧪 PRUEBAS ANTES DE ENTREGAR A CLIENTE

### En tu Mac local:
```bash
# 1. Detener cualquier servicio previo
docker-compose -f docker-compose-trial.yml down -v

# 2. Iniciar trial limpio
./start-trial.sh

# 3. Verificar servicios
docker-compose -f docker-compose-trial.yml ps

# 4. Probar acceso
curl http://localhost:3000    # Grafana
curl http://localhost:9090    # Prometheus
curl http://localhost:8080    # License Dashboard

# 5. Verificar logs por errores
docker-compose -f docker-compose-trial.yml logs | grep -i error

# 6. Detener para no interferir con producción
docker-compose -f docker-compose-trial.yml stop
```

---

## ❓ FAQ

### ¿Puedo tener producción Y trial en la misma máquina?
**SÍ**, pero con precauciones:
- Usar **puertos diferentes** (ej: trial en 3001, 9091, etc.)
- **Volúmenes diferentes** (ej: `trial_postgres_data` vs `prod_postgres_data`)
- **Networks diferentes** (ej: `rhinometric_trial` vs `rhinometric_prod`)

### ¿El trial puede "contaminar" producción?
**NO**, si:
- Usas `docker-compose-trial.yml` (nombre único)
- Los volúmenes son independientes
- No compartes `.env`

### ¿Cómo sé qué versión está corriendo?
```bash
# Producción
docker ps | grep rhinometric | grep -v trial

# Trial
docker ps | grep rhinometric-trial
```

### ¿Puedo convertir un trial a producción?
**NO directamente**. Son arquitecturas diferentes:
- Trial: Stack simplificado, single-tenant
- Producción: Multi-tenant, alta disponibilidad, backups

Para migrar, contacta con el equipo técnico.

---

## 📞 CONTACTO

- **Dudas sobre separación**: soporte@rhinometric.com
- **Problemas con trial**: trial-support@rhinometric.com
- **Urgencias producción**: produccion@rhinometric.com

---

## ✅ CHECKLIST DE VALIDACIÓN

Antes de entregar trial a cliente:

- [ ] `docker-compose-trial.yml` funciona en máquina limpia
- [ ] `start-trial.sh` ejecuta sin errores en Mac
- [ ] Todos los servicios inician correctamente
- [ ] Grafana accesible en http://localhost:3000
- [ ] License dashboard muestra licencia generada
- [ ] No hay conflictos de puertos
- [ ] Documentación incluida (RESUMEN_IMPLEMENTACION.md)
- [ ] `.env` se genera automáticamente
- [ ] Licencia trial de 180 días creada correctamente
- [ ] Puedes detener/reiniciar sin errores

**Solo después de validar**, envía paquete al cliente.
