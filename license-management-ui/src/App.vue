<template>
  <div id="app" class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <svg class="rhino-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          </svg>
          <h1>Rhinometric License Management</h1>
        </div>
        <nav class="nav-menu">
          <router-link to="/" class="nav-link">Home</router-link>
          <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/create" class="nav-link">Crear Licencia</router-link>
          <router-link to="/manage" class="nav-link">Gestionar</router-link>
          <router-link to="/activations" class="nav-link">Activaciones</router-link>
          <router-link to="/security" class="nav-link security-link">
            Seguridad
            <span v-if="securityAlertCount > 0" class="alert-badge">{{ securityAlertCount }}</span>
          </router-link>
          <router-link to="/validator" class="nav-link">Validar</router-link>
          <router-link to="/settings" class="nav-link">Configuración</router-link>
        </nav>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>

    <footer class="app-footer">
      <p>&copy; 2025 Rhinometric v2.1.0 - rafael.canelon@rhinometric.com</p>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed } from 'vue'
import { useLicenseStore } from './store'

const licenseStore = useLicenseStore()

const securityAlertCount = computed(() => licenseStore.securityAlertCount)

onMounted(() => {
  // Load licenses on app mount
  licenseStore.fetchLicenses()
  // Start security alert polling
  licenseStore.startSecurityPolling()
})

onUnmounted(() => {
  // Stop polling when app unmounts
  licenseStore.stopSecurityPolling()
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  padding: 1rem 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rhino-icon {
  width: 40px;
  height: 40px;
  color: #667eea;
}

.logo h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.nav-menu {
  display: flex;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: #4a5568;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background: #667eea;
  color: white;
}

.security-link {
  position: relative;
}

.alert-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

.app-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 2rem auto;
  padding: 0 2rem;
}

.app-footer {
  background: rgba(255, 255, 255, 0.95);
  padding: 1rem;
  text-align: center;
  color: #4a5568;
  font-size: 0.875rem;
}
</style>
