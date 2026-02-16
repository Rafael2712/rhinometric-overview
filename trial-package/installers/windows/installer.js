/**
 * 🦏 RHINOMETRIC TRIAL - INSTALADOR WINDOWS
 * Instalador Electron para Windows con wizard gráfico
 * © 2025 Rhinometric. All rights reserved.
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const log = require('electron-log');

// Configurar logging
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

let mainWindow;
let installationProcess = null;

// Banner de inicio
const BANNER = `
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🦏 RHINOMETRIC TRIAL INSTALLER v1.0               ║
║        Windows Installation Wizard                       ║
║        © 2025 Rhinometric. All rights reserved.          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
`;

log.info(BANNER);

/**
 * Crear ventana principal del instalador
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    resizable: false,
    frame: true,
    icon: path.join(__dirname, 'build', 'icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'ui', 'index.html'));
  
  // Abrir DevTools en desarrollo
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  log.info('Ventana principal creada');
}

/**
 * Verificar si Docker Desktop está instalado
 */
async function checkDockerInstalled() {
  return new Promise((resolve) => {
    exec('docker --version', (error, stdout) => {
      if (error) {
        log.warn('Docker no encontrado:', error.message);
        resolve(false);
      } else {
        log.info('Docker detectado:', stdout.trim());
        resolve(true);
      }
    });
  });
}

/**
 * Verificar si Docker Desktop está corriendo
 */
async function checkDockerRunning() {
  return new Promise((resolve) => {
    exec('docker ps', (error) => {
      if (error) {
        log.warn('Docker no está corriendo:', error.message);
        resolve(false);
      } else {
        log.info('Docker está corriendo correctamente');
        resolve(true);
      }
    });
  });
}

/**
 * Verificar si WSL2 está instalado
 */
async function checkWSL2Installed() {
  return new Promise((resolve) => {
    exec('wsl --status', (error, stdout) => {
      if (error) {
        log.warn('WSL2 no encontrado:', error.message);
        resolve(false);
      } else {
        log.info('WSL2 detectado:', stdout.trim());
        resolve(true);
      }
    });
  });
}

/**
 * Obtener información del sistema
 */
async function getSystemInfo() {
  return new Promise((resolve) => {
    exec('systeminfo', (error, stdout) => {
      if (error) {
        log.error('Error obteniendo info del sistema:', error);
        resolve({});
      } else {
        const info = {};
        
        // Extraer RAM
        const ramMatch = stdout.match(/Total Physical Memory:.*?([0-9,]+) MB/);
        if (ramMatch) {
          info.totalRAM = parseInt(ramMatch[1].replace(/,/g, ''));
        }
        
        // Extraer OS
        const osMatch = stdout.match(/OS Name:\s+(.+)/);
        if (osMatch) {
          info.osName = osMatch[1].trim();
        }
        
        log.info('Info del sistema:', info);
        resolve(info);
      }
    });
  });
}

/**
 * Descargar Docker Desktop
 */
async function downloadDockerDesktop(progressCallback) {
  const url = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe';
  const outputPath = path.join(app.getPath('temp'), 'DockerDesktopInstaller.exe');
  
  log.info('Descargando Docker Desktop desde:', url);
  progressCallback({ status: 'downloading', progress: 0, message: 'Descargando Docker Desktop...' });
  
  return new Promise((resolve, reject) => {
    const axios = require('axios');
    const writer = fs.createWriteStream(outputPath);
    
    axios({
      method: 'get',
      url: url,
      responseType: 'stream',
      onDownloadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        progressCallback({ 
          status: 'downloading', 
          progress: percentCompleted, 
          message: `Descargando Docker Desktop... ${percentCompleted}%` 
        });
      }
    })
    .then((response) => {
      response.data.pipe(writer);
      
      writer.on('finish', () => {
        log.info('Docker Desktop descargado en:', outputPath);
        progressCallback({ status: 'downloaded', progress: 100, message: 'Descarga completada' });
        resolve(outputPath);
      });
      
      writer.on('error', (err) => {
        log.error('Error escribiendo archivo:', err);
        reject(err);
      });
    })
    .catch((err) => {
      log.error('Error descargando Docker Desktop:', err);
      reject(err);
    });
  });
}

/**
 * Instalar Docker Desktop
 */
async function installDockerDesktop(installerPath, progressCallback) {
  log.info('Instalando Docker Desktop desde:', installerPath);
  progressCallback({ status: 'installing', progress: 0, message: 'Instalando Docker Desktop...' });
  
  return new Promise((resolve, reject) => {
    const installer = spawn(installerPath, ['install', '--quiet', '--accept-license'], {
      shell: true
    });
    
    installer.stdout.on('data', (data) => {
      log.info('Docker installer stdout:', data.toString());
    });
    
    installer.stderr.on('data', (data) => {
      log.warn('Docker installer stderr:', data.toString());
    });
    
    installer.on('close', (code) => {
      if (code === 0) {
        log.info('Docker Desktop instalado exitosamente');
        progressCallback({ status: 'installed', progress: 100, message: 'Docker Desktop instalado' });
        resolve(true);
      } else {
        log.error('Error instalando Docker Desktop, código:', code);
        reject(new Error(`Instalación falló con código ${code}`));
      }
    });
  });
}

/**
 * Copiar archivos del trial package
 */
async function copyTrialPackage(destinationPath, progressCallback) {
  const sourcePath = path.join(process.resourcesPath, 'trial-package');
  
  log.info('Copiando trial package desde:', sourcePath);
  log.info('Destino:', destinationPath);
  
  progressCallback({ status: 'copying', progress: 0, message: 'Copiando archivos...' });
  
  return new Promise((resolve, reject) => {
    // Crear directorio destino si no existe
    if (!fs.existsSync(destinationPath)) {
      fs.mkdirSync(destinationPath, { recursive: true });
    }
    
    // Copiar recursivamente
    const scriptPath = path.join(__dirname, 'scripts', 'copy-files.ps1');
    const ps = spawn('powershell.exe', [
      '-ExecutionPolicy', 'Bypass',
      '-File', scriptPath,
      '-Source', sourcePath,
      '-Destination', destinationPath
    ]);
    
    ps.stdout.on('data', (data) => {
      log.info('Copy script stdout:', data.toString());
      progressCallback({ 
        status: 'copying', 
        progress: 50, 
        message: 'Copiando archivos...' 
      });
    });
    
    ps.stderr.on('data', (data) => {
      log.warn('Copy script stderr:', data.toString());
    });
    
    ps.on('close', (code) => {
      if (code === 0) {
        log.info('Archivos copiados exitosamente');
        progressCallback({ status: 'copied', progress: 100, message: 'Archivos copiados' });
        resolve(destinationPath);
      } else {
        log.error('Error copiando archivos, código:', code);
        reject(new Error(`Copia falló con código ${code}`));
      }
    });
  });
}

/**
 * Ejecutar instalación de Rhinometric
 */
async function installRhinometric(installPath, customerName, progressCallback) {
  const scriptPath = path.join(installPath, 'scripts', 'start-trial.ps1');
  
  log.info('Ejecutando instalación en:', installPath);
  log.info('Cliente:', customerName);
  
  progressCallback({ status: 'installing', progress: 0, message: 'Iniciando instalación...' });
  
  return new Promise((resolve, reject) => {
    const ps = spawn('powershell.exe', [
      '-ExecutionPolicy', 'Bypass',
      '-File', scriptPath,
      '-CustomerName', customerName,
      '-AutoInstall'
    ], {
      cwd: installPath
    });
    
    ps.stdout.on('data', (data) => {
      const output = data.toString();
      log.info('Install script:', output);
      
      // Parsear progreso
      if (output.includes('Downloading')) {
        progressCallback({ status: 'downloading', progress: 30, message: 'Descargando imágenes Docker...' });
      } else if (output.includes('Starting')) {
        progressCallback({ status: 'starting', progress: 70, message: 'Iniciando servicios...' });
      } else if (output.includes('Success')) {
        progressCallback({ status: 'completed', progress: 100, message: '¡Instalación completada!' });
      }
    });
    
    ps.stderr.on('data', (data) => {
      log.warn('Install script stderr:', data.toString());
    });
    
    ps.on('close', (code) => {
      if (code === 0) {
        log.info('Rhinometric instalado exitosamente');
        resolve(true);
      } else {
        log.error('Error instalando Rhinometric, código:', code);
        reject(new Error(`Instalación falló con código ${code}`));
      }
    });
  });
}

/**
 * Abrir Grafana en navegador
 */
function openGrafana() {
  const url = 'http://localhost:3000';
  log.info('Abriendo Grafana en:', url);
  require('electron').shell.openExternal(url);
}

// ============================================================================
// IPC HANDLERS - Comunicación con UI
// ============================================================================

ipcMain.handle('check-requirements', async () => {
  log.info('Verificando requisitos del sistema...');
  
  const systemInfo = await getSystemInfo();
  const dockerInstalled = await checkDockerInstalled();
  const dockerRunning = dockerInstalled ? await checkDockerRunning() : false;
  const wsl2Installed = await checkWSL2Installed();
  
  const requirements = {
    systemInfo,
    dockerInstalled,
    dockerRunning,
    wsl2Installed,
    meetsRequirements: systemInfo.totalRAM >= 8192 // 8GB mínimo
  };
  
  log.info('Requisitos verificados:', requirements);
  return requirements;
});

ipcMain.handle('install-docker', async (event) => {
  try {
    log.info('Iniciando instalación de Docker Desktop...');
    
    const installerPath = await downloadDockerDesktop((progress) => {
      event.sender.send('installation-progress', progress);
    });
    
    await installDockerDesktop(installerPath, (progress) => {
      event.sender.send('installation-progress', progress);
    });
    
    return { success: true };
  } catch (error) {
    log.error('Error instalando Docker:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('start-installation', async (event, { installPath, customerName }) => {
  try {
    log.info('Iniciando instalación completa...');
    log.info('Ruta instalación:', installPath);
    log.info('Cliente:', customerName);
    
    // Copiar archivos
    await copyTrialPackage(installPath, (progress) => {
      event.sender.send('installation-progress', progress);
    });
    
    // Ejecutar instalación
    await installRhinometric(installPath, customerName, (progress) => {
      event.sender.send('installation-progress', progress);
    });
    
    return { success: true, installPath };
  } catch (error) {
    log.error('Error en instalación:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('open-grafana', () => {
  openGrafana();
  return { success: true };
});

ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Seleccionar carpeta de instalación',
    defaultPath: path.join(require('os').homedir(), 'Rhinometric')
  });
  
  if (!result.canceled && result.filePaths.length > 0) {
    return { success: true, path: result.filePaths[0] };
  }
  
  return { success: false };
});

// ============================================================================
// APP LIFECYCLE
// ============================================================================

app.whenReady().then(() => {
  log.info('Aplicación iniciada');
  createWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (installationProcess) {
    installationProcess.kill();
  }
});

log.info('Instalador Rhinometric iniciado');
