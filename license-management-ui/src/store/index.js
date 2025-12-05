import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import licenseService from '../services/licenseService'

export const useLicenseStore = defineStore('license', () => {
  const licenses = ref([])
  const loading = ref(false)
  const error = ref(null)
  const securityAlerts = ref(null)
  const securityAlertCount = ref(0)
  let securityPollingInterval = null

  // Computed
  const activeLicenses = computed(() => 
    licenses.value.filter(l => l.status === 'active').length
  )

  const expiringSoon = computed(() => 
    licenses.value.filter(l => {
      if (!l.expiryDate || l.licenseType === 'permanent') return false
      const daysLeft = Math.ceil((new Date(l.expiryDate) - new Date()) / (1000 * 60 * 60 * 24))
      return daysLeft <= 7 && daysLeft > 0
    }).length
  )

  const activeTrials = computed(() =>
    licenses.value.filter(l => l.licenseType === 'trial' && l.status === 'active').length
  )

  const permanentLicenses = computed(() =>
    licenses.value.filter(l => l.licenseType === 'permanent').length
  )

  // Actions
  async function fetchLicenses() {
    loading.value = true
    error.value = null
    try {
      licenses.value = await licenseService.getAllLicenses()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function createLicense(licenseData) {
    loading.value = true
    error.value = null
    try {
      const newLicense = await licenseService.createLicense(licenseData)
      licenses.value.push(newLicense)
      return newLicense
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function revokeLicense(licenseId) {
    loading.value = true
    error.value = null
    try {
      await licenseService.revokeLicense(licenseId)
      const index = licenses.value.findIndex(l => l.id === licenseId)
      if (index !== -1) {
        licenses.value[index].status = 'revoked'
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function extendLicense(licenseId, additionalDays) {
    loading.value = true
    error.value = null
    try {
      const updated = await licenseService.extendLicense(licenseId, additionalDays)
      const index = licenses.value.findIndex(l => l.id === licenseId)
      if (index !== -1) {
        licenses.value[index] = updated
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function sendLicenseEmail(licenseId) {
    loading.value = true
    error.value = null
    try {
      await licenseService.sendEmail(licenseId)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSecurityAlerts() {
    try {
      const alerts = await licenseService.getSecurityAlerts()
      securityAlerts.value = alerts
      
      // Calculate total alert count
      const suspiciousCount = alerts.suspicious_activations?.length || 0
      const recentFailuresCount = alerts.recent_failures?.filter(f => f.is_suspicious).length || 0
      securityAlertCount.value = suspiciousCount + recentFailuresCount
    } catch (err) {
      console.error('Failed to fetch security alerts:', err)
    }
  }

  function startSecurityPolling() {
    // Fetch immediately
    fetchSecurityAlerts()
    
    // Poll every 30 seconds
    securityPollingInterval = setInterval(fetchSecurityAlerts, 30000)
  }

  function stopSecurityPolling() {
    if (securityPollingInterval) {
      clearInterval(securityPollingInterval)
      securityPollingInterval = null
    }
  }

  return {
    licenses,
    loading,
    error,
    securityAlerts,
    securityAlertCount,
    activeLicenses,
    expiringSoon,
    activeTrials,
    permanentLicenses,
    fetchLicenses,
    createLicense,
    revokeLicense,
    extendLicense,
    sendLicenseEmail,
    fetchSecurityAlerts,
    startSecurityPolling,
    stopSecurityPolling
  }
})
