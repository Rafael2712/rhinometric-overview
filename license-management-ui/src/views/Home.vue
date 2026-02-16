<template>
  <div class="home-view">
    <h2 class="page-title">Dashboard de Licencias</h2>
    
    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card active">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ licenseStore.activeLicenses }}</div>
          <div class="stat-label">Licencias Activas</div>
        </div>
      </div>

      <div class="stat-card expiring">
        <div class="stat-icon">⚠️</div>
        <div class="stat-content">
          <div class="stat-value">{{ licenseStore.expiringSoon }}</div>
          <div class="stat-label">Por Expirar (7 días)</div>
        </div>
      </div>

      <div class="stat-card trial">
        <div class="stat-icon">🔬</div>
        <div class="stat-content">
          <div class="stat-value">{{ licenseStore.activeTrials }}</div>
          <div class="stat-label">Trials Activos</div>
        </div>
      </div>

      <div class="stat-card permanent">
        <div class="stat-icon">♾️</div>
        <div class="stat-content">
          <div class="stat-value">{{ licenseStore.permanentLicenses }}</div>
          <div class="stat-label">Licencias Permanentes</div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions card">
      <h3>Acciones Rápidas</h3>
      <div class="actions-grid">
        <button class="btn btn-primary" @click="$router.push('/create')">
          ➕ Nueva Licencia
        </button>
        <button class="btn btn-secondary" @click="licenseStore.fetchLicenses()">
          🔄 Actualizar
        </button>
        <button class="btn btn-secondary" @click="$router.push('/manage')">
          📋 Ver Todas
        </button>
      </div>
    </div>

    <!-- Recent Licenses -->
    <div class="recent-licenses card">
      <h3>Licencias Recientes</h3>
      <div v-if="licenseStore.loading">Cargando...</div>
      <div v-else-if="licenseStore.error" class="error-message">
        {{ licenseStore.error }}
      </div>
      <div v-else-if="recentLicenses.length === 0">
        No hay licencias creadas aún.
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
            </tr>
          </thead>
          <tbody>
            <tr v-for="license in recentLicenses" :key="license.id">
              <td>
                <div class="client-info">
                  <div class="client-name">{{ license.clientName }}</div>
                  <div class="client-email">{{ license.clientEmail }}</div>
                </div>
              </td>
              <td>
                <span class="badge" :class="`badge-${license.licenseType}`">
                  {{ license.licenseType }}
                </span>
              </td>
              <td>
                <span class="badge" :class="`badge-${license.status}`">
                  {{ license.status }}
                </span>
              </td>
              <td>{{ formatDate(license.createdAt) }}</td>
              <td>
                <span v-if="license.licenseType === 'permanent'">
                  ♾️ Sin expiración
                </span>
                <span v-else :class="{ 'text-warning': isExpiringSoon(license) }">
                  {{ formatDate(license.expiryDate) }}
                  <span v-if="isExpiringSoon(license)"> ({{ daysLeft(license) }} días)</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useLicenseStore } from '../store'

const licenseStore = useLicenseStore()

const recentLicenses = computed(() => 
  licenseStore.licenses.slice(0, 5)
)

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('es-ES')
}

function isExpiringSoon(license) {
  if (!license.expiryDate || license.licenseType === 'permanent') return false
  const daysLeft = Math.ceil((new Date(license.expiryDate) - new Date()) / (1000 * 60 * 60 * 24))
  return daysLeft <= 7 && daysLeft > 0
}

function daysLeft(license) {
  if (!license.expiryDate) return 0
  return Math.ceil((new Date(license.expiryDate) - new Date()) / (1000 * 60 * 60 * 24))
}
</script>

<style scoped>
.home-view {
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 2rem;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 12px rgba(0,0,0,0.15);
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2d3748;
}

.stat-label {
  font-size: 0.875rem;
  color: #718096;
  margin-top: 0.25rem;
}

.quick-actions {
  margin-bottom: 2rem;
}

.quick-actions h3 {
  margin-bottom: 1rem;
  color: #2d3748;
}

.actions-grid {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.recent-licenses h3 {
  margin-bottom: 1rem;
  color: #2d3748;
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

.text-warning {
  color: #d97706;
  font-weight: 600;
}
</style>
