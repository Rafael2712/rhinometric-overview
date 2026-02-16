<template>
  <div class="manage-licenses-view">
    <div class="card">
      <div class="header-actions">
        <h2 class="section-title">Gestionar Licencias</h2>
        <button class="btn btn-primary" @click="$router.push('/create')">
          ➕ Nueva Licencia
        </button>
      </div>

      <!-- Filters -->
      <div class="filters">
        <div class="filter-group">
          <label>Tipo:</label>
          <select v-model="filters.type" class="form-select">
            <option value="">Todos</option>
            <option value="trial">Trial</option>
            <option value="annual">Annual</option>
            <option value="permanent">Permanent</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Estado:</label>
          <select v-model="filters.status" class="form-select">
            <option value="">Todos</option>
            <option value="active">Activo</option>
            <option value="expiring">Por Expirar</option>
            <option value="expired">Expirado</option>
            <option value="revoked">Revocado</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Buscar:</label>
          <input 
            v-model="filters.search" 
            type="text" 
            class="form-input"
            placeholder="Cliente, email, empresa..."
          >
        </div>

        <button class="btn btn-secondary" @click="resetFilters">
          🔄 Limpiar
        </button>
      </div>

      <!-- Loading/Error States -->
      <div v-if="licenseStore.loading" class="loading">Cargando licencias...</div>
      <div v-else-if="licenseStore.error" class="error-message">
        {{ licenseStore.error }}
      </div>

      <!-- Licenses Table -->
      <div v-else-if="filteredLicenses.length === 0" class="empty-state">
        <p>No se encontraron licencias</p>
        <button class="btn btn-primary" @click="$router.push('/create')">
          Crear Primera Licencia
        </button>
      </div>

      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Creada</th>
              <th>Expira</th>
              <th>Días Restantes</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="license in paginatedLicenses" :key="license.id">
              <td>
                <div class="client-info">
                  <div class="client-name">{{ license.clientName }}</div>
                  <div class="client-email">{{ license.clientEmail }}</div>
                  <div class="client-company">{{ license.clientCompany }}</div>
                </div>
              </td>
              <td>
                <span class="badge" :class="`badge-${license.licenseType}`">
                  {{ license.licenseType }}
                </span>
              </td>
              <td>
                <span class="badge" :class="`badge-${getStatus(license)}`">
                  {{ getStatusLabel(license) }}
                </span>
              </td>
              <td>{{ formatDate(license.createdAt) }}</td>
              <td>
                <span v-if="license.licenseType === 'permanent'">
                  ♾️ Sin expiración
                </span>
                <span v-else :class="{ 'text-warning': isExpiringSoon(license) }">
                  {{ formatDate(license.expiryDate) }}
                </span>
              </td>
              <td>
                <span v-if="license.licenseType === 'permanent'">-</span>
                <span v-else :class="getDaysLeftClass(license)">
                  {{ getDaysLeft(license) }}
                </span>
              </td>
              <td>
                <div class="action-buttons">
                  <button 
                    class="btn-icon" 
                    title="Ver detalles"
                    @click="viewDetails(license)"
                  >
                    👁️
                  </button>
                  <button 
                    class="btn-icon" 
                    title="Reenviar email"
                    @click="resendEmail(license)"
                    :disabled="sending === license.id"
                  >
                    📧
                  </button>
                  <button 
                    v-if="license.licenseType !== 'permanent' && getStatus(license) === 'active'"
                    class="btn-icon" 
                    title="Extender"
                    @click="showExtendModal(license)"
                  >
                    ⏱️
                  </button>
                  <button 
                    v-if="getStatus(license) === 'active'"
                    class="btn-icon danger" 
                    title="Revocar"
                    @click="showRevokeModal(license)"
                  >
                    🚫
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="pagination">
          <button 
            class="btn btn-secondary"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            ← Anterior
          </button>
          <span class="page-info">
            Página {{ currentPage }} de {{ totalPages }} ({{ filteredLicenses.length }} licencias)
          </span>
          <button 
            class="btn btn-secondary"
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>{{ modalTitle }}</h3>
        <div class="modal-body">
          {{ modalMessage }}
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">Cancelar</button>
          <button 
            class="btn"
            :class="modalAction === 'revoke' ? 'btn-danger' : 'btn-primary'"
            @click="confirmAction"
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useLicenseStore } from '../store'

const licenseStore = useLicenseStore()

const filters = ref({
  type: '',
  status: '',
  search: ''
})

const currentPage = ref(1)
const pageSize = 10
const sending = ref(null)

const showModal = ref(false)
const modalTitle = ref('')
const modalMessage = ref('')
const modalAction = ref(null)
const selectedLicense = ref(null)

onMounted(() => {
  licenseStore.fetchLicenses()
})

const filteredLicenses = computed(() => {
  let licenses = licenseStore.licenses

  // Filter by type
  if (filters.value.type) {
    licenses = licenses.filter(l => l.licenseType === filters.value.type)
  }

  // Filter by status
  if (filters.value.status) {
    licenses = licenses.filter(l => getStatus(l) === filters.value.status)
  }

  // Search
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    licenses = licenses.filter(l => 
      l.clientName?.toLowerCase().includes(search) ||
      l.clientEmail?.toLowerCase().includes(search) ||
      l.clientCompany?.toLowerCase().includes(search)
    )
  }

  return licenses
})

const totalPages = computed(() => 
  Math.ceil(filteredLicenses.value.length / pageSize)
)

const paginatedLicenses = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredLicenses.value.slice(start, end)
})

function getStatus(license) {
  if (license.status === 'revoked') return 'revoked'
  if (license.licenseType === 'permanent') return 'active'
  
  const daysLeft = getDaysLeftNumber(license)
  if (daysLeft < 0) return 'expired'
  if (daysLeft <= 7) return 'expiring'
  return 'active'
}

function getStatusLabel(license) {
  const status = getStatus(license)
  const labels = {
    active: 'Activo',
    expiring: 'Por Expirar',
    expired: 'Expirado',
    revoked: 'Revocado'
  }
  return labels[status]
}

function getDaysLeftNumber(license) {
  if (!license.expiryDate || license.licenseType === 'permanent') return Infinity
  return Math.ceil((new Date(license.expiryDate) - new Date()) / (1000 * 60 * 60 * 24))
}

function getDaysLeft(license) {
  const days = getDaysLeftNumber(license)
  if (days === Infinity) return '-'
  if (days < 0) return 'Expirado'
  return `${days} días`
}

function getDaysLeftClass(license) {
  const days = getDaysLeftNumber(license)
  if (days < 0) return 'text-danger'
  if (days <= 7) return 'text-warning'
  return ''
}

function isExpiringSoon(license) {
  const days = getDaysLeftNumber(license)
  return days <= 7 && days > 0
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('es-ES')
}

function resetFilters() {
  filters.value = { type: '', status: '', search: '' }
  currentPage.value = 1
}

function viewDetails(license) {
  alert(`Detalles de licencia:\n\nCliente: ${license.clientName}\nEmail: ${license.clientEmail}\nEmpresa: ${license.clientCompany}\nTipo: ${license.licenseType}\nLicense Key: ${license.licenseKey || 'N/A'}`)
}

async function resendEmail(license) {
  sending.value = license.id
  try {
    await licenseStore.sendLicenseEmail(license.id)
    alert('✅ Email reenviado correctamente')
  } catch (error) {
    alert(`❌ Error al enviar email: ${error.message}`)
  } finally {
    sending.value = null
  }
}

function showExtendModal(license) {
  selectedLicense.value = license
  modalTitle.value = 'Extender Licencia'
  modalMessage.value = `¿Extender la licencia de ${license.clientName} por 30 días adicionales?`
  modalAction.value = 'extend'
  showModal.value = true
}

function showRevokeModal(license) {
  selectedLicense.value = license
  modalTitle.value = 'Revocar Licencia'
  modalMessage.value = `¿Estás seguro de revocar la licencia de ${license.clientName}? Esta acción no se puede deshacer.`
  modalAction.value = 'revoke'
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  selectedLicense.value = null
  modalAction.value = null
}

async function confirmAction() {
  if (modalAction.value === 'extend') {
    try {
      await licenseStore.extendLicense(selectedLicense.value.id, 30)
      alert('✅ Licencia extendida 30 días')
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    }
  } else if (modalAction.value === 'revoke') {
    try {
      await licenseStore.revokeLicense(selectedLicense.value.id)
      alert('✅ Licencia revocada')
    } catch (error) {
      alert(`❌ Error: ${error.message}`)
    }
  }
  closeModal()
}
</script>

<style scoped>
.manage-licenses-view {
  animation: fadeIn 0.5s;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
}

.client-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.client-name {
  font-weight: 600;
  color: #2d3748;
}

.client-email {
  font-size: 0.875rem;
  color: #718096;
}

.client-company {
  font-size: 0.875rem;
  color: #a0aec0;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.3s;
}

.btn-icon:hover {
  background: #e2e8f0;
  transform: scale(1.1);
}

.btn-icon.danger:hover {
  background: #fed7d7;
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.text-warning {
  color: #d97706;
  font-weight: 600;
}

.text-danger {
  color: #dc2626;
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 2px solid #e2e8f0;
}

.page-info {
  color: #718096;
  font-size: 0.875rem;
}

.loading,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #718096;
}

.empty-state p {
  margin-bottom: 1rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

.modal-content {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.modal-content h3 {
  margin: 0 0 1rem 0;
  color: #2d3748;
}

.modal-body {
  margin-bottom: 1.5rem;
  color: #4a5568;
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
