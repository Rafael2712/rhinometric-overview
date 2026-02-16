import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  // Get all licenses
  async getAllLicenses() {
    const response = await api.get('/api/licenses')
    return response.data
  },

  // Get license by ID
  async getLicenseById(id) {
    const response = await api.get(`/api/licenses/${id}`)
    return response.data
  },

  // Create new license
  async createLicense(licenseData) {
    const response = await api.post('/api/licenses/trial', licenseData)
    return response.data
  },

  // Validate license
  async validateLicense(licenseKey) {
    const response = await api.post('/api/licenses/validate', { license_key: licenseKey })
    return response.data
  },

  // Get license activations
  async getLicenseActivations(licenseId) {
    const response = await api.get(`/api/licenses/${licenseId}/activations`)
    return response.data
  },

  // Get security alerts
  async getSecurityAlerts() {
    const response = await api.get('/api/security/alerts')
    return response.data
  },

  // Delete license
  async deleteLicense(id) {
    const response = await api.delete(`/api/licenses/${id}`)
    return response.data
  }
}
