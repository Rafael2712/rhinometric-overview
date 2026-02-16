# 🚀 GUÍA DE EMPAQUETADO - Rhinometric Trial

## 📦 Cómo preparar el paquete para distribución

### PASO 1: Verificar estructura completa

Desde tu directorio `trial-package/`, verifica que tienes:

```bash
rhinometric-trial/
├── README.md                           ✅
├── start-trial.sh                      ✅
├── docker-compose.yml                  ✅
├── .env.example                        ✅
├── config/
│   ├── prometheus.yml                  ✅
│   ├── loki.yml                        ✅
│   ├── tempo.yml                       ✅
│   ├── alertmanager.yml                ✅
│   └── nginx.conf                      ✅
├── licensing/
│   ├── Dockerfile                      ✅
│   └── license_server.py               ✅
├── dashboard/
│   ├── Dockerfile                      ✅
│   ├── app.py                          ✅
│   └── templates/
│       └── index.html                  ✅
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml         ✅
│       └── dashboards/
│           └── dashboard-provider.yml  ✅
├── init-db/
│   └── 01-init.sql                     ✅
└── docs/
    ├── FAQ.md                          ⏳ (opcional)
    └── TROUBLESHOOTING.md              ⏳ (opcional)
```

### PASO 2: Dar permisos al script

```bash
cd trial-package
chmod +x start-trial.sh
```

### PASO 3: Probar en local ANTES de distribuir

```bash
# Desde trial-package/
./start-trial.sh

# Verificar que funciona
# - Grafana en http://localhost:3000
# - Todos los servicios levantan
# - No hay errores

# Limpiar después de probar
docker compose down -v
rm -rf licenses/ data/ .env credentials.txt
```

### PASO 4: Empaquetar

#### Opción A: ZIP (macOS)

```bash
# Ir al directorio padre
cd ..

# Crear ZIP
zip -r rhinometric-trial-v1.0.zip rhinometric-trial/ \
    -x "rhinometric-trial/data/*" \
    -x "rhinometric-trial/licenses/*" \
    -x "rhinometric-trial/.env" \
    -x "rhinometric-trial/credentials.txt"

# Verificar tamaño
ls -lh rhinometric-trial-v1.0.zip
# Debería ser ~300-500 KB
```

#### Opción B: TAR.GZ (Linux/macOS)

```bash
# Ir al directorio padre
cd ..

# Crear tarball
tar -czf rhinometric-trial-v1.0.tar.gz \
    --exclude='rhinometric-trial/data' \
    --exclude='rhinometric-trial/licenses' \
    --exclude='rhinometric-trial/.env' \
    --exclude='rhinometric-trial/credentials.txt' \
    rhinometric-trial/

# Verificar tamaño
ls -lh rhinometric-trial-v1.0.tar.gz
```

### PASO 5: Verificar el paquete

```bash
# Descomprimir en directorio temporal
mkdir /tmp/test-trial
cd /tmp/test-trial

# Descomprimir
unzip ~/ruta/rhinometric-trial-v1.0.zip
# o
tar -xzf ~/ruta/rhinometric-trial-v1.0.tar.gz

# Probar instalación
cd rhinometric-trial
./start-trial.sh
```

---

## 📤 Métodos de Distribución

### 1. Email / WeTransfer

```bash
# Archivo comprimido es pequeño (~500 KB)
# Enviar directamente por email o WeTransfer
```

**Email de ejemplo**:

```
Asunto: Rhinometric Trial - Paquete de Instalación

Hola [Cliente],

Adjunto encontrarás el paquete Rhinometric Trial (versión 180 días).

Instrucciones:
1. Asegúrate de tener Docker Desktop instalado
2. Descomprime el archivo adjunto
3. Abre Terminal y navega a la carpeta descomprimida
4. Ejecuta: ./start-trial.sh

Documentación completa en el archivo README.md incluido.

Soporte: soporte@rhinometric.com

Saludos,
Equipo Rhinometric
```

### 2. GitHub Release (Recomendado)

```bash
# Crear repositorio limpio
git init rhinometric-trial
cd rhinometric-trial

# Copiar archivos del paquete
cp -r ../trial-package/* .

# Crear .gitignore
cat > .gitignore << 'EOF'
.env
credentials.txt
data/
licenses/
*.log
EOF

# Commit inicial
git add .
git commit -m "Initial release: Rhinometric Trial v1.0"

# Crear repo en GitHub (vía web) y conectar
git remote add origin https://github.com/TU-ORG/rhinometric-trial.git
git branch -M main
git push -u origin main

# Crear tag y release
git tag v1.0.0
git push origin v1.0.0

# En GitHub web: Create Release desde el tag
```

**Cliente descargará**:

```bash
curl -L https://github.com/TU-ORG/rhinometric-trial/archive/refs/tags/v1.0.0.tar.gz -o rhinometric-trial.tar.gz
tar -xzf rhinometric-trial.tar.gz
cd rhinometric-trial-1.0.0
./start-trial.sh
```

### 3. Servidor Web / S3

```bash
# Subir a S3 (ejemplo AWS)
aws s3 cp rhinometric-trial-v1.0.zip s3://rhinometric-releases/

# Cliente descarga
curl -O https://rhinometric-releases.s3.amazonaws.com/rhinometric-trial-v1.0.zip
```

### 4. Docker Hub (Alternativo - solo imágenes)

Si prefieres distribuir imágenes pre-construidas:

```bash
# Build y push imágenes
docker build -t rhinometric/license-server:trial ./licensing
docker build -t rhinometric/license-dashboard:trial ./dashboard

docker push rhinometric/license-server:trial
docker push rhinometric/license-dashboard:trial

# Actualizar docker-compose.yml para usar imágenes remotas
```

---

## ✅ Checklist Pre-Distribución

Antes de enviar a cliente:

- [ ] `start-trial.sh` tiene permisos ejecutables
- [ ] Probado en Mac limpio (sin proyecto previo)
- [ ] `README.md` claro y completo
- [ ] Todos los paths son relativos (no `/Users/...`)
- [ ] `.env.example` existe (pero NO `.env`)
- [ ] No incluir `data/`, `licenses/`, `credentials.txt`
- [ ] Validado con `docker compose config`
- [ ] Tamaño del ZIP razonable (<1 MB)
- [ ] Versión documentada (v1.0, v1.1, etc.)
- [ ] Changelog si hay updates
- [ ] Fecha de expiración clara (180 días)
- [ ] Contacto de soporte incluido

---

## 📝 Documentos a Entregar

### Paquete Principal
1. `rhinometric-trial-v1.0.zip` (o .tar.gz)

### Documentos Adicionales (Opcionales)
1. **PDF de Quick Start**
2. **Video tutorial** (opcional)
3. **Presentación comercial** (PPT/PDF)
4. **Contrato de Trial** (legal)

---

## 🔄 Actualizaciones del Paquete

### Versionado Semántico

- **v1.0.0**: Release inicial
- **v1.0.1**: Bug fixes menores
- **v1.1.0**: Nuevas características
- **v2.0.0**: Cambios mayores

### Crear nueva versión

```bash
# Hacer cambios necesarios
# Actualizar README.md con CHANGELOG

# Nuevo tag
git tag v1.0.1
git push origin v1.0.1

# Nuevo release en GitHub
# O nuevo ZIP con nombre actualizado
zip -r rhinometric-trial-v1.0.1.zip rhinometric-trial/
```

---

## 📊 Tracking de Distribuciones

Mantén registro de:

```
Cliente          | Fecha Envío | Versión | Fecha Exp.  | Estado
-----------------|-------------|---------|-------------|--------
Acme Corp        | 2025-01-15  | v1.0.0  | 2025-07-15  | Activo
TechStart Inc    | 2025-01-20  | v1.0.0  | 2025-07-20  | Activo
GlobalSys Ltd    | 2025-02-01  | v1.0.1  | 2025-08-01  | Activo
```

---

## 🆘 Soporte Post-Distribución

### Email Template de Seguimiento

```
Asunto: Rhinometric Trial - Seguimiento

Hola [Cliente],

Espero que la instalación de Rhinometric Trial haya ido bien.

¿Necesitas ayuda con:
- Instalación o configuración
- Integración con tus sistemas
- Preguntas sobre funcionalidades
- Upgrade a versión comercial

No dudes en contactarme.

Saludos,
[Tu nombre]
soporte@rhinometric.com
```

---

## 🎯 Conversión a Cliente

### Indicadores de Interés

Monitor al cliente que:
- ✅ Solicita soporte frecuentemente (está usando activamente)
- ✅ Pregunta sobre características enterprise
- ✅ Menciona escalamiento/producción
- ✅ Solicita extensión del trial

### Momento de Contacto Comercial

- **Día 30**: Email de check-in
- **Día 90**: Mitad del trial, ofrecer demo de versión completa
- **Día 150**: Recordatorio de expiración, proceso de compra
- **Día 170**: Último aviso, oferta especial

---

## 📞 Contacto

Dudas sobre empaquetado o distribución:

📧 **interno@rhinometric.com**  
💬 **Slack**: #trial-distribution

---

**Última actualización**: 2025-10-17
