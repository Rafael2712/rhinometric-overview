import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api/admin'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  async getAllLicenses() {
    const response = await api.get('/licenses')
    // Transform API response (snake_case) to UI format (camelCase)
    return response.data.map(license => ({
      id: license.id,
      clientName: license.customer_name,
      clientEmail: license.client_email,
      clientCompany: license.client_company,
      clientPhone: license.client_phone,
      country: license.client_country,
      city: license.client_city,
      industry: license.industry,
      companySize: license.company_size,
      serversCount: license.servers_count,
      servicesCount: license.services_count,
      infrastructure: license.infrastructure_type,
      notes: license.notes,
      licenseType: license.license_type,
      licenseKey: license.license_key,
      status: license.status,
      createdAt: license.created_at,
      expiresAt: license.expires_at,
      daysRemaining: license.days_remaining,
      isActive: license.is_active,
      emailSent: license.email_sent
    }))
  },

  async createLicense(licenseData) {
    // Mapear campos del formulario al formato esperado por la API
    const payload = {
      customer_name: licenseData.clientName,
      client_email: licenseData.clientEmail,
      client_company: licenseData.clientCompany || '',  // Opcional
      client_phone: licenseData.clientPhone || null,
      client_country: licenseData.country || null,
      client_city: licenseData.city || null,
      industry: licenseData.industry || null,
      company_size: licenseData.companySize || null,
      servers_count: licenseData.serversCount || null,
      services_count: licenseData.servicesCount || null,
      infrastructure_type: licenseData.infrastructure || null,
      notes: licenseData.notes || null,
      license_type: licenseData.licenseType
    }
    
    const response = await api.post('/licenses', payload)
    return response.data
  },

  async revokeLicense(licenseKey) {
    const response = await api.post(`/licenses/${licenseKey}/revoke`)
    return response.data
  },

  async extendLicense(licenseId, additionalDays) {
    // Por ahora simular, luego implementar PATCH /api/admin/licenses/:id/extend
    return { success: true, message: `Licencia extendida ${additionalDays} días (próximamente)` }
  },

  async sendEmail(licenseId) {
    // Por ahora simular, luego implementar POST /api/admin/licenses/:id/resend
    return { success: true, message: 'Email reenviado (próximamente)' }
  },

  async getStats() {
    const response = await api.get('/licenses/stats')
    return response.data
  },

  async getLicenseStats() {
    // Alias for compatibility
    return this.getStats()
  },

  async getLicenseActivations(licenseKey) {
    const response = await api.get(`/licenses/${licenseKey}/activations`, {
      baseURL: 'http://localhost:5000/api'  // Note: no /admin prefix
    })
    return response.data
  },

  async getSecurityAlerts() {
    const response = await api.get('/licenses/security')
    return response.data
  },

  async validateLicense(licenseKey, hardwareId, ipAddress, hostname) {
    const payload = {
      license_key: licenseKey,
      hardware_id: hardwareId,
      user_agent: 'License-UI/1.0'
    }
    
    if (ipAddress) payload.ip_address = ipAddress
    if (hostname) payload.hostname = hostname
    
    const response = await api.post('/licenses/validate', payload, {
      baseURL: 'http://localhost:5000/api'  // Note: no /admin prefix
    })
    return response.data
  }
}
