import axios from 'axios'

const API_BASE_URL = '/api/admin'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  async getAllLicenses() {
    const response = await api.get('/licenses')
    return response.data
  },

  async createLicense(licenseData) {
    const response = await api.post('/licenses/create', licenseData)
    return response.data
  },

  async revokeLicense(licenseId) {
    const response = await api.patch(`/licenses/${licenseId}/revoke`)
    return response.data
  },

  async extendLicense(licenseId, additionalDays) {
    const response = await api.patch(`/licenses/${licenseId}/extend`, { additionalDays })
    return response.data
  },

  async sendEmail(licenseId) {
    const response = await api.post(`/licenses/${licenseId}/email`)
    return response.data
  },

  async getLicenseStats() {
    const response = await api.get('/licenses/stats')
    return response.data
  }
}
