/**
 * 🦏 RHINOMETRIC TRIAL INSTALLER - FRONTEND
 * © 2025 Rhinometric
 */

const { ipcRenderer } = require('electron');
const path = require('path');
const os = require('os');

// Estado del instalador
let currentStep = 1;
let maxSteps = 5;
let requirements = {};
let installPath = path.join(os.homedir(), 'Rhinometric');

// Referencias a elementos del DOM
const stepContents = document.querySelectorAll('.step-content');
const stepIndicators = document.querySelectorAll('.wizard-steps .step');
const backBtn = document.getElementById('back-btn');
const nextBtn = document.getElementById('next-btn');
const cancelBtn = document.getElementById('cancel-btn');

// ============================================================================
// NAVEGACIÓN
// ============================================================================

function showStep(step) {
    // Ocultar todos los pasos
    stepContents.forEach(content => content.classList.remove('active'));
    stepIndicators.forEach(indicator => indicator.classList.remove('active'));
    
    // Mostrar paso actual
    document.getElementById(`step-${step}`).classList.add('active');
    document.querySelector(`.wizard-steps .step[data-step="${step}"]`).classList.add('active');
    
    // Actualizar botones
    backBtn.disabled = step === 1;
    
    if (step === maxSteps) {
        nextBtn.style.display = 'none';
    } else {
        nextBtn.style.display = 'block';
        nextBtn.textContent = step === maxSteps - 1 ? 'Instalar' : 'Siguiente →';
    }
    
    // Acciones específicas por paso
    if (step === 2) {
        checkRequirements();
    } else if (step === 3) {
        prepareConfiguration();
    } else if (step === 4) {
        startInstallation();
    }
    
    currentStep = step;
}

function nextStep() {
    if (currentStep < maxSteps) {
        // Validar antes de avanzar
        if (validateCurrentStep()) {
            showStep(currentStep + 1);
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        showStep(currentStep - 1);
    }
}

function validateCurrentStep() {
    if (currentStep === 2) {
        // Validar requisitos
        if (!requirements.meetsRequirements) {
            alert('Tu sistema no cumple los requisitos mínimos (8GB RAM requeridos)');
            return false;
        }
        if (!requirements.dockerRunning) {
            alert('Docker Desktop debe estar instalado y corriendo antes de continuar');
            return false;
        }
        return true;
    } else if (currentStep === 3) {
        // Validar configuración
        const customerName = document.getElementById('customer-name').value.trim();
        const acceptLicense = document.getElementById('accept-license').checked;
        
        if (!customerName) {
            alert('Por favor, introduce el nombre de tu empresa u organización');
            return false;
        }
        if (!acceptLicense) {
            alert('Debes aceptar los términos de la licencia trial');
            return false;
        }
        return true;
    }
    return true;
}

// ============================================================================
// PASO 2: VERIFICACIÓN DE REQUISITOS
// ============================================================================

async function checkRequirements() {
    addLog('Verificando requisitos del sistema...');
    
    try {
        requirements = await ipcRenderer.invoke('check-requirements');
        
        // RAM
        const reqRam = document.getElementById('req-ram');
        const ramDetails = document.getElementById('ram-details');
        if (requirements.meetsRequirements) {
            reqRam.classList.add('success');
            reqRam.querySelector('.req-icon').className = 'req-icon success';
            ramDetails.textContent = `${(requirements.systemInfo.totalRAM / 1024).toFixed(1)} GB disponibles ✓`;
        } else {
            reqRam.classList.add('error');
            reqRam.querySelector('.req-icon').className = 'req-icon error';
            ramDetails.textContent = `${(requirements.systemInfo.totalRAM / 1024).toFixed(1)} GB (mínimo 8 GB requeridos)`;
        }
        
        // Docker
        const reqDocker = document.getElementById('req-docker');
        const dockerDetails = document.getElementById('docker-details');
        if (requirements.dockerInstalled && requirements.dockerRunning) {
            reqDocker.classList.add('success');
            reqDocker.querySelector('.req-icon').className = 'req-icon success';
            dockerDetails.textContent = 'Docker Desktop instalado y corriendo ✓';
            document.getElementById('docker-install-section').classList.add('hidden');
        } else if (requirements.dockerInstalled && !requirements.dockerRunning) {
            reqDocker.classList.add('error');
            reqDocker.querySelector('.req-icon').className = 'req-icon error';
            dockerDetails.textContent = 'Docker Desktop instalado pero no está corriendo. Por favor, inícialo.';
            document.getElementById('docker-install-section').classList.add('hidden');
        } else {
            reqDocker.classList.add('error');
            reqDocker.querySelector('.req-icon').className = 'req-icon error';
            dockerDetails.textContent = 'Docker Desktop no detectado';
            document.getElementById('docker-install-section').classList.remove('hidden');
        }
        
        // WSL2
        const reqWsl = document.getElementById('req-wsl');
        const wslDetails = document.getElementById('wsl-details');
        if (requirements.wsl2Installed) {
            reqWsl.classList.add('success');
            reqWsl.querySelector('.req-icon').className = 'req-icon success';
            wslDetails.textContent = 'WSL2 instalado ✓';
        } else {
            reqWsl.classList.add('error');
            reqWsl.querySelector('.req-icon').className = 'req-icon error';
            wslDetails.textContent = 'WSL2 no detectado (se instalará con Docker Desktop)';
        }
        
        addLog('Verificación de requisitos completada');
        
    } catch (error) {
        console.error('Error verificando requisitos:', error);
        addLog('❌ Error verificando requisitos: ' + error.message);
    }
}

async function installDocker() {
    const btn = document.getElementById('install-docker-btn');
    btn.disabled = true;
    btn.textContent = 'Instalando Docker Desktop...';
    
    addLog('Iniciando instalación de Docker Desktop...');
    
    try {
        const result = await ipcRenderer.invoke('install-docker');
        
        if (result.success) {
            addLog('✅ Docker Desktop instalado exitosamente');
            addLog('⚠️ Por favor, reinicia este instalador para continuar');
            btn.textContent = 'Docker Desktop instalado - Reiniciar instalador';
        } else {
            addLog('❌ Error instalando Docker Desktop: ' + result.error);
            btn.textContent = 'Error - Intentar de nuevo';
            btn.disabled = false;
        }
    } catch (error) {
        console.error('Error instalando Docker:', error);
        addLog('❌ Error: ' + error.message);
        btn.disabled = false;
        btn.textContent = 'Intentar de nuevo';
    }
}

// ============================================================================
// PASO 3: CONFIGURACIÓN
// ============================================================================

function prepareConfiguration() {
    // Establecer ruta por defecto
    document.getElementById('install-path').value = installPath;
}

async function browseDirectory() {
    const result = await ipcRenderer.invoke('select-directory');
    
    if (result.success) {
        installPath = result.path;
        document.getElementById('install-path').value = installPath;
    }
}

function viewLicense() {
    // Abrir LICENSE.txt en ventana modal o externa
    const shell = require('electron').shell;
    const licensePath = path.join(__dirname, '..', '..', 'LICENSE.txt');
    shell.openPath(licensePath);
}

// ============================================================================
// PASO 4: INSTALACIÓN
// ============================================================================

async function startInstallation() {
    const customerName = document.getElementById('customer-name').value.trim();
    const createShortcut = document.getElementById('create-desktop-shortcut').checked;
    
    addLog('🚀 Iniciando instalación de Rhinometric Trial...');
    addLog(`Cliente: ${customerName}`);
    addLog(`Ruta: ${installPath}`);
    
    nextBtn.disabled = true;
    backBtn.disabled = true;
    cancelBtn.disabled = true;
    
    try {
        const result = await ipcRenderer.invoke('start-installation', {
            installPath,
            customerName,
            createShortcut
        });
        
        if (result.success) {
            addLog('✅ Instalación completada exitosamente');
            document.getElementById('credentials-path').textContent = path.join(result.installPath, 'credentials.txt');
            
            // Esperar 2 segundos y pasar al siguiente paso
            setTimeout(() => {
                showStep(5);
            }, 2000);
        } else {
            addLog('❌ Error en la instalación: ' + result.error);
            alert('Error durante la instalación. Por favor, revisa el log y contacta con soporte.');
            nextBtn.disabled = false;
            backBtn.disabled = false;
            cancelBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Error en instalación:', error);
        addLog('❌ Error crítico: ' + error.message);
        alert('Error crítico durante la instalación. Por favor, contacta con soporte@rhinometric.com');
    }
}

function updateProgress(data) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    
    progressFill.style.width = data.progress + '%';
    progressText.textContent = data.message;
    progressPercentage.textContent = data.progress + '%';
    
    addLog(`[${data.progress}%] ${data.message}`);
}

function addLog(message) {
    const logContainer = document.getElementById('installation-log');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// ============================================================================
// PASO 5: COMPLETADO
// ============================================================================

async function openGrafana() {
    addLog('Abriendo Grafana en navegador...');
    
    try {
        await ipcRenderer.invoke('open-grafana');
        addLog('✅ Grafana abierto');
    } catch (error) {
        console.error('Error abriendo Grafana:', error);
        addLog('❌ Error abriendo Grafana: ' + error.message);
    }
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

backBtn.addEventListener('click', prevStep);
nextBtn.addEventListener('click', nextStep);

cancelBtn.addEventListener('click', () => {
    if (confirm('¿Estás seguro de que deseas cancelar la instalación?')) {
        window.close();
    }
});

document.getElementById('install-docker-btn')?.addEventListener('click', installDocker);
document.getElementById('browse-btn')?.addEventListener('click', browseDirectory);
document.getElementById('view-license')?.addEventListener('click', (e) => {
    e.preventDefault();
    viewLicense();
});

document.getElementById('open-grafana-btn')?.addEventListener('click', openGrafana);

// IPC Listeners
ipcRenderer.on('installation-progress', (event, data) => {
    updateProgress(data);
});

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Instalador Rhinometric Trial iniciado');
    showStep(1);
});
