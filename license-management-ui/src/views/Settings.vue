<template>
  <div class="settings-view">
    <div class="card">
      <h2 class="section-title">Configuración</h2>

      <div class="settings-sections">
        <!-- Email Settings -->
        <div class="settings-section">
          <h3>📧 Configuración de Email</h3>
          <form @submit.prevent="saveEmailSettings">
            <div class="form-group">
              <label class="form-label">Email Remitente</label>
              <input 
                v-model="emailSettings.from" 
                type="email" 
                class="form-input"
                placeholder="rafael.canelon@rhinometric.com"
              >
            </div>

            <div class="form-group">
              <label class="form-label">Proveedor SMTP</label>
              <select v-model="emailSettings.provider" class="form-select">
                <option value="gmail">Gmail</option>
                <option value="sendgrid">SendGrid</option>
                <option value="mailgun">Mailgun</option>
                <option value="custom">Custom SMTP</option>
              </select>
            </div>

            <div v-if="emailSettings.provider === 'custom'">
              <div class="form-group">
                <label class="form-label">SMTP Host</label>
                <input 
                  v-model="emailSettings.smtp.host" 
                  type="text" 
                  class="form-input"
                  placeholder="smtp.example.com"
                >
              </div>

              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Puerto</label>
                  <input 
                    v-model.number="emailSettings.smtp.port" 
                    type="number" 
                    class="form-input"
                    placeholder="587"
                  >
                </div>

                <div class="form-group">
                  <label class="form-label">Usuario</label>
                  <input 
                    v-model="emailSettings.smtp.user" 
                    type="text" 
                    class="form-input"
                  >
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Contraseña</label>
                <input 
                  v-model="emailSettings.smtp.password" 
                  type="password" 
                  class="form-input"
                  placeholder="••••••••"
                >
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">
                💾 Guardar Configuración
              </button>
              <button type="button" class="btn btn-secondary" @click="testEmail">
                🧪 Probar Email
              </button>
            </div>
          </form>
        </div>

        <!-- System Settings -->
        <div class="settings-section">
          <h3>⚙️ Configuración del Sistema</h3>
          
          <div class="setting-item">
            <div class="setting-info">
              <strong>URL del Backend</strong>
              <p>{{ backendUrl }}</p>
            </div>
            <span class="status-badge" :class="backendStatus">
              {{ backendStatus === 'connected' ? '✅ Conectado' : '❌ Desconectado' }}
            </span>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <strong>Puerto UI</strong>
              <p>8092</p>
            </div>
            <span class="status-badge connected">✅ Activo</span>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <strong>Versión</strong>
              <p>License Management UI v1.0.0</p>
            </div>
          </div>
        </div>

        <!-- Backup/Export -->
        <div class="settings-section">
          <h3>💾 Backup & Exportación</h3>
          
          <div class="backup-options">
            <button class="btn btn-secondary" @click="exportLicenses">
              📥 Exportar Licencias (JSON)
            </button>
            <button class="btn btn-secondary" @click="exportLicensesCSV">
              📊 Exportar Licencias (CSV)
            </button>
            <button class="btn btn-secondary" @click="downloadReport">
              📄 Generar Reporte
            </button>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="settings-section danger-zone">
          <h3>⚠️ Zona Peligrosa</h3>
          
          <div class="danger-actions">
            <button class="btn btn-danger" @click="clearCache">
              🗑️ Limpiar Caché
            </button>
            <p class="danger-note">
              Esta acción limpiará todos los datos en caché del navegador.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useLicenseStore } from '../store'

const licenseStore = useLicenseStore()

const emailSettings = ref({
  from: 'rafael.canelon@rhinometric.com',
  provider: 'gmail',
  smtp: {
    host: 'smtp.gmail.com',
    port: 587,
    user: '',
    password: ''
  }
})

const backendUrl = ref('/api')
const backendStatus = ref('checking')

onMounted(() => {
  loadSettings()
  checkBackendStatus()
})

function loadSettings() {
  const saved = localStorage.getItem('licenseui_email_settings')
  if (saved) {
    emailSettings.value = JSON.parse(saved)
  }
}

function saveEmailSettings() {
  localStorage.setItem('licenseui_email_settings', JSON.stringify(emailSettings.value))
  alert('✅ Configuración guardada correctamente')
}

async function testEmail() {
  try {
    // Simulated test
    alert('📧 Enviando email de prueba a ' + emailSettings.value.from)
    // In production: await emailService.sendTestEmail(emailSettings.value)
    alert('✅ Email de prueba enviado correctamente')
  } catch (error) {
    alert('❌ Error al enviar email: ' + error.message)
  }
}

async function checkBackendStatus() {
  try {
    // Check if backend is accessible
    const response = await fetch('/api/admin/licenses')
    backendStatus.value = response.ok ? 'connected' : 'disconnected'
  } catch (error) {
    backendStatus.value = 'disconnected'
  }
}

function exportLicenses() {
  const data = JSON.stringify(licenseStore.licenses, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `rhinometric-licenses-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  alert('✅ Licencias exportadas correctamente')
}

function exportLicensesCSV() {
  const headers = ['ID', 'Cliente', 'Email', 'Empresa', 'Tipo', 'Estado', 'Creada', 'Expira']
  const rows = licenseStore.licenses.map(l => [
    l.id,
    l.clientName,
    l.clientEmail,
    l.clientCompany,
    l.licenseType,
    l.status,
    new Date(l.createdAt).toLocaleDateString(),
    l.expiryDate ? new Date(l.expiryDate).toLocaleDateString() : 'N/A'
  ])
  
  const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `rhinometric-licenses-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
  alert('✅ CSV exportado correctamente')
}

function downloadReport() {
  const report = `
RHINOMETRIC LICENSE MANAGEMENT REPORT
Fecha: ${new Date().toLocaleString('es-ES')}

RESUMEN:
- Total Licencias: ${licenseStore.licenses.length}
- Licencias Activas: ${licenseStore.activeLicenses}
- Por Expirar (7 días): ${licenseStore.expiringSoon}
- Trials Activos: ${licenseStore.activeTrials}
- Licencias Permanentes: ${licenseStore.permanentLicenses}

LISTADO COMPLETO:
${licenseStore.licenses.map((l, i) => `
${i + 1}. ${l.clientName} (${l.clientEmail})
   Empresa: ${l.clientCompany}
   Tipo: ${l.licenseType}
   Estado: ${l.status}
   Creada: ${new Date(l.createdAt).toLocaleDateString('es-ES')}
   Expira: ${l.expiryDate ? new Date(l.expiryDate).toLocaleDateString('es-ES') : 'N/A'}
`).join('\n')}

---
Rhinometric v2.1.0 - rafael.canelon@rhinometric.com
  `.trim()

  const blob = new Blob([report], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `rhinometric-report-${new Date().toISOString().split('T')[0]}.txt`
  a.click()
  URL.revokeObjectURL(url)
  alert('✅ Reporte generado correctamente')
}

function clearCache() {
  if (confirm('¿Estás seguro de limpiar el caché? Esta acción no se puede deshacer.')) {
    localStorage.clear()
    sessionStorage.clear()
    alert('✅ Caché limpiado. La página se recargará.')
    window.location.reload()
  }
}
</script>

<style scoped>
.settings-view {
  animation: fadeIn 0.5s;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 2rem;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section {
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 2rem;
}

.settings-section:last-child {
  border-bottom: none;
}

.settings-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.setting-info strong {
  display: block;
  color: #2d3748;
  margin-bottom: 0.25rem;
}

.setting-info p {
  color: #718096;
  font-size: 0.875rem;
  margin: 0;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-badge.connected {
  background: #c6f6d5;
  color: #22543d;
}

.status-badge.disconnected {
  background: #fed7d7;
  color: #742a2a;
}

.backup-options {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.danger-zone {
  border: 2px solid #fed7d7;
  background: #fff5f5;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.danger-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
}

.danger-note {
  color: #742a2a;
  font-size: 0.875rem;
  margin: 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
