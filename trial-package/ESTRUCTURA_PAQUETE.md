# 📦 ESTRUCTURA DEL PAQUETE RHINOMETRIC TRIAL

## 🎯 Objetivo
Paquete autónomo para que un cliente pueda instalar Rhinometric Trial en su Mac **sin tener nada previo**.

## 📁 Estructura de Directorios

```
rhinometric-trial/
│
├── README.md                          # Guía principal para el cliente
├── start-trial.sh                     # Script de instalación (ejecutable)
├── docker-compose.yml                 # Orquestación de servicios
├── .env.example                       # Variables de entorno (plantilla)
│
├── config/                            # Configuraciones de servicios
│   ├── prometheus.yml
│   ├── loki.yml
│   ├── tempo.yml
│   ├── alertmanager.yml
│   └── nginx.conf
│
├── licensing/                         # Sistema de licencias
│   ├── Dockerfile
│   └── license_server.py
│
├── dashboard/                         # Dashboard de licencias
│   ├── Dockerfile
│   ├── app.py
│   └── templates/
│       └── index.html
│
├── grafana/                          # Configuración Grafana
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml
│       └── dashboards/
│           └── dashboard-provider.yml
│
├── init-db/                          # Scripts inicialización DB
│   └── 01-init.sql
│
└── docs/                             # Documentación adicional
    ├── TROUBLESHOOTING.md
    └── FAQ.md
```

## 📦 Archivos que se auto-generan durante instalación
- `.env` (generado desde .env.example)
- `licenses/` (directorio creado por script)
- `certs/` (directorio creado por script)
- `data/` (volúmenes de datos)

## 🎁 Cómo empaquetar para distribución

```bash
# Desde el directorio donde creaste rhinometric-trial/
tar -czf rhinometric-trial-v1.0.tar.gz rhinometric-trial/

# O crear ZIP
zip -r rhinometric-trial-v1.0.zip rhinometric-trial/
```

## 📤 Cómo entregar al cliente

**Opción 1: Email/WeTransfer**
```bash
# Comprimir
zip -r rhinometric-trial-v1.0.zip rhinometric-trial/

# Enviar rhinometric-trial-v1.0.zip (tamaño: ~50-100KB sin imágenes Docker)
```

**Opción 2: GitHub Release**
```bash
# Crear repositorio limpio
git init rhinometric-trial
cd rhinometric-trial
cp -r ../trial-package/* .
git add .
git commit -m "Initial Rhinometric Trial v1.0"
git remote add origin https://github.com/tu-org/rhinometric-trial.git
git push -u origin main

# Crear release tag
git tag v1.0.0
git push origin v1.0.0
```

**Opción 3: Repositorio privado + token de descarga**
```bash
# Cliente ejecuta:
curl -L https://github.com/tu-org/rhinometric-trial/archive/refs/tags/v1.0.0.tar.gz -o rhinometric-trial.tar.gz
tar -xzf rhinometric-trial.tar.gz
cd rhinometric-trial-1.0.0
./start-trial.sh
```

## ✅ Checklist antes de enviar

- [ ] Probado en Mac limpio (sin proyecto previo)
- [ ] `start-trial.sh` tiene permisos ejecutables
- [ ] `.env.example` contiene valores por defecto funcionales
- [ ] Todos los paths son relativos (no absolutos)
- [ ] README.md claro para no técnicos
- [ ] docker-compose.yml validado (`docker compose config`)
- [ ] Licencias de software incluidas si es necesario
- [ ] Contacto de soporte incluido en README

## 📏 Tamaño estimado del paquete

- Archivos de configuración: ~50 KB
- Scripts Python: ~100 KB
- Templates HTML: ~50 KB
- Documentación: ~100 KB
- **Total comprimido**: ~300 KB (sin imágenes Docker)

Las imágenes Docker se descargan automáticamente durante instalación.
