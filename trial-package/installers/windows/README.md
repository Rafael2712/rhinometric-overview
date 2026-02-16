# 🦏 Rhinometric Trial - Instalador Windows

Instalador gráfico para Windows con wizard paso a paso.

## 📋 Requisitos para Construir el Instalador

### Software Necesario

1. **Node.js 18+**
   - Descarga: https://nodejs.org/
   
2. **Visual Studio Build Tools** (para compilar módulos nativos)
   - Descarga: https://visualstudio.microsoft.com/downloads/
   - Instalar: "Desktop development with C++"

### Dependencias

```bash
cd trial-package/installers/windows
npm install
```

## 🔨 Construcción del Instalador

### Desarrollo (Test local)

```bash
npm start
```

Esto abrirá el instalador en modo desarrollo con DevTools.

### Build para Producción

```bash
# Solo Windows 64-bit
npm run build:win

# Windows 64-bit y 32-bit
npm run build:all
```

El instalador se generará en `dist/`:
- `Rhinometric Trial Setup 1.0.0.exe` (64-bit)
- `Rhinometric Trial Setup 1.0.0-ia32.exe` (32-bit)

## 📦 Estructura del Instalador

```
windows/
├── installer.js          # Proceso principal Electron
├── package.json          # Configuración y dependencias
├── ui/
│   ├── index.html        # Interfaz del wizard
│   ├── styles.css        # Estilos
│   └── app.js            # Lógica frontend
├── scripts/
│   ├── check-docker.ps1  # Verificar Docker Desktop
│   ├── start-trial.ps1   # Instalación principal
│   └── copy-files.ps1    # Copiar archivos
└── build/
    └── icon.ico          # Icono del instalador (pendiente)
```

## ⚙️ Funcionalidades

### Wizard de 5 Pasos

1. **Bienvenida**
   - Presentación de Rhinometric
   - Características principales
   - Información de licencia

2. **Verificación de Requisitos**
   - Check RAM (mínimo 8GB)
   - Check Docker Desktop
   - Check WSL2
   - Instalación automática de Docker si falta

3. **Configuración**
   - Nombre de empresa/organización
   - Carpeta de instalación
   - Opciones (shortcut, licencia)

4. **Instalación**
   - Barra de progreso
   - Log en tiempo real
   - Descarga imágenes Docker
   - Inicio de servicios

5. **Completado**
   - Credenciales de acceso
   - Próximos pasos
   - Botón para abrir Grafana

### Características Técnicas

- ✅ Interfaz gráfica moderna y responsive
- ✅ Verificación automática de requisitos
- ✅ Instalación de Docker Desktop si falta
- ✅ Instalación de WSL2 si falta (Windows 10/11)
- ✅ Generación de contraseñas seguras
- ✅ Generación de licencia trial
- ✅ Logs detallados de instalación
- ✅ Barra de progreso en tiempo real
- ✅ Apertura automática de Grafana al terminar

## 🔍 Testing

### Test Local

```bash
npm start
```

### Test del .exe

```bash
npm run build:win
cd dist
.\Rhinometric Trial Setup 1.0.0.exe
```

### Casos de Prueba

1. **Docker ya instalado y corriendo**
   - Debe detectarlo y continuar

2. **Docker instalado pero detenido**
   - Debe pedir iniciar Docker Desktop

3. **Docker no instalado**
   - Debe ofrecer instalarlo automáticamente

4. **RAM < 8GB**
   - Debe mostrar advertencia pero permitir continuar

5. **Instalación completa**
   - Debe copiar archivos
   - Debe iniciar 15 contenedores
   - Debe generar credenciales
   - Debe abrir Grafana

## 🐛 Debugging

### Logs de Electron

Los logs se guardan en:
```
%APPDATA%\rhinometric-trial-installer\logs\main.log
```

### Logs de PowerShell

Los scripts PowerShell escriben a stdout/stderr, visibles en el log del instalador.

### DevTools

En modo desarrollo (npm start), las DevTools están habiertas automáticamente.

## 📝 Notas de Desarrollo

### Variables de Entorno

```bash
# Modo desarrollo
set NODE_ENV=development
npm start

# Modo producción
set NODE_ENV=production
npm run build
```

### Configuración de Electron Builder

Ver `package.json` sección `build`:
- `appId`: ID único de la app
- `win.target`: nsis (instalador Windows)
- `nsis.oneClick`: false (wizard multi-paso)
- `files`: Archivos a incluir en el instalador
- `extraResources`: Trial package completo

## 🚀 Distribución

### Generar .exe Firmado

Para evitar advertencias de Windows SmartScreen:

1. Obtener certificado de firma de código
   - Proveedores: DigiCert, Sectigo
   - Costo: ~$100-500/año

2. Configurar en `package.json`:
   ```json
   "win": {
     "certificateFile": "path/to/cert.pfx",
     "certificatePassword": "password"
   }
   ```

3. Build:
   ```bash
   npm run build:win
   ```

### Checksums

Generar SHA256 para verificación:

```bash
certutil -hashfile "Rhinometric Trial Setup 1.0.0.exe" SHA256
```

## 📧 Soporte

- **Bugs**: Reportar en GitHub Issues
- **Email**: soporte@rhinometric.com
- **Documentación**: Ver README.md principal

---

© 2025 Rhinometric. Todos los derechos reservados.
