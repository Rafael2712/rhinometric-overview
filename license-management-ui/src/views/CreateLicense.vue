<template>
  <div class="create-license-view">
    <div class="card">
      <h2 class="section-title">Crear Nueva Licencia</h2>
      
      <form @submit.prevent="handleSubmit" class="license-form">
        <!-- License Type Selection -->
        <div class="form-section">
          <h3>Tipo de Licencia</h3>
          <div class="license-types">
            <div 
              v-for="type in licenseTypes" 
              :key="type.value"
              class="license-type-card"
              :class="{ active: formData.licenseType === type.value }"
              @click="formData.licenseType = type.value"
            >
              <div class="type-header">
                <span class="type-icon">{{ type.icon }}</span>
                <h4>{{ type.name }}</h4>
              </div>
              <div class="type-duration">{{ type.duration }}</div>
              <div class="type-price">{{ type.price }}</div>
              <ul class="type-features">
                <li v-for="feature in type.features" :key="feature">
                  ✓ {{ feature }}
                </li>
              </ul>
            </div>
          </div>
          <div v-if="errors.licenseType" class="error-message">{{ errors.licenseType }}</div>
        </div>

        <!-- Client Information -->
        <div class="form-section">
          <h3>Información del Cliente</h3>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Nombre Completo *</label>
              <input 
                v-model="formData.clientName" 
                type="text" 
                class="form-input"
                placeholder="Juan Pérez"
                required
              >
              <div v-if="errors.clientName" class="error-message">{{ errors.clientName }}</div>
            </div>

            <div class="form-group">
              <label class="form-label">Email *</label>
              <input 
                v-model="formData.clientEmail" 
                type="email" 
                class="form-input"
                placeholder="juan@empresa.com"
                required
              >
              <div v-if="errors.clientEmail" class="error-message">{{ errors.clientEmail }}</div>
            </div>

            <div class="form-group">
              <label class="form-label">Empresa *</label>
              <input 
                v-model="formData.clientCompany" 
                type="text" 
                class="form-input"
                placeholder="Acme Corp"
                required
              >
            </div>

            <div class="form-group">
              <label class="form-label">Teléfono</label>
              <input 
                v-model="formData.clientPhone" 
                type="tel" 
                class="form-input"
                placeholder="+1 555 1234"
              >
            </div>

            <div class="form-group">
              <label class="form-label">País *</label>
              <select v-model="formData.country" class="form-select" required>
                <option value="">Seleccionar...</option>
                <option value="AR">Argentina</option>
                <option value="CL">Chile</option>
                <option value="CO">Colombia</option>
                <option value="MX">México</option>
                <option value="PE">Perú</option>
                <option value="US">Estados Unidos</option>
                <option value="ES">España</option>
                <option value="OTHER">Otro</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Ciudad</label>
              <input 
                v-model="formData.city" 
                type="text" 
                class="form-input"
                placeholder="Ciudad"
              >
            </div>
          </div>
        </div>

        <!-- Technical Information -->
        <div class="form-section">
          <h3>Información Técnica</h3>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Industria</label>
              <select v-model="formData.industry" class="form-select">
                <option value="">Seleccionar...</option>
                <option value="fintech">Fintech</option>
                <option value="ecommerce">E-commerce</option>
                <option value="saas">SaaS</option>
                <option value="healthcare">Healthcare</option>
                <option value="education">Educación</option>
                <option value="logistics">Logística</option>
                <option value="other">Otro</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Tamaño de Empresa</label>
              <select v-model="formData.companySize" class="form-select">
                <option value="">Seleccionar...</option>
                <option value="1-10">1-10 empleados</option>
                <option value="11-50">11-50 empleados</option>
                <option value="51-200">51-200 empleados</option>
                <option value="201-500">201-500 empleados</option>
                <option value="500+">500+ empleados</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Servidores a Monitorizar</label>
              <input 
                v-model.number="formData.serversCount" 
                type="number" 
                class="form-input"
                placeholder="5"
                min="1"
              >
            </div>

            <div class="form-group">
              <label class="form-label">Servicios Estimados</label>
              <input 
                v-model.number="formData.servicesCount" 
                type="number" 
                class="form-input"
                placeholder="50"
                min="1"
              >
            </div>

            <div class="form-group">
              <label class="form-label">Infraestructura</label>
              <select v-model="formData.infrastructure" class="form-select">
                <option value="">Seleccionar...</option>
                <option value="on-premise">On-Premise</option>
                <option value="cloud">Cloud</option>
                <option value="hybrid">Híbrido</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="form-section">
          <h3>Notas Adicionales</h3>
          <div class="form-group">
            <textarea 
              v-model="formData.notes" 
              class="form-textarea"
              placeholder="Información adicional sobre el cliente o requisitos especiales..."
              rows="4"
            ></textarea>
          </div>
        </div>

        <!-- Submit Buttons -->
        <div class="form-actions">
          <button 
            type="button" 
            class="btn btn-secondary"
            @click="$router.push('/')"
          >
            Cancelar
          </button>
          <button 
            type="submit" 
            class="btn btn-primary"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>✅ Crear Licencia y Enviar Email</span>
          </button>
        </div>

        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useLicenseStore } from '../store'

const router = useRouter()
const licenseStore = useLicenseStore()

const licenseTypes = [
  {
    value: 'trial',
    name: 'Trial',
    icon: '🔬',
    duration: '30 días',
    price: 'Gratis',
    features: [
      'Funcionalidad completa',
      'Sin soporte comercial',
      'Documentación incluida',
      'Auto-expiración 30 días'
    ]
  },
  {
    value: 'annual',
    name: 'Annual',
    icon: '📅',
    duration: '1 año',
    price: 'A consultar',
    features: [
      'Soporte 24/7',
      'Updates incluidos',
      'Sin marca de agua',
      'Soporte prioritario'
    ]
  },
  {
    value: 'permanent',
    name: 'Permanent',
    icon: '♾️',
    duration: 'Sin expiración',
    price: 'A consultar',
    features: [
      'Licencia perpetua',
      'Soporte prioritario',
      'Customización',
      'Updates lifetime'
    ]
  }
]

const formData = reactive({
  licenseType: '',
  clientName: '',
  clientEmail: '',
  clientCompany: '',
  clientPhone: '',
  country: '',
  city: '',
  industry: '',
  companySize: '',
  serversCount: null,
  servicesCount: null,
  infrastructure: '',
  notes: ''
})

const errors = reactive({})
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const isFormValid = computed(() => {
  return formData.licenseType && 
         formData.clientName && 
         formData.clientEmail && 
         formData.clientCompany &&
         formData.country
})

async function handleSubmit() {
  errors.value = {}
  successMessage.value = ''
  errorMessage.value = ''

  // Validation
  if (!formData.clientEmail.includes('@')) {
    errors.clientEmail = 'Email inválido'
    return
  }

  if (!formData.licenseType) {
    errors.licenseType = 'Selecciona un tipo de licencia'
    return
  }

  loading.value = true

  try {
    const newLicense = await licenseStore.createLicense(formData)
    
    // Send email
    await licenseStore.sendLicenseEmail(newLicense.id)

    successMessage.value = `✅ Licencia creada y email enviado a ${formData.clientEmail}`
    
    setTimeout(() => {
      router.push('/manage')
    }, 2000)
  } catch (error) {
    errorMessage.value = `Error: ${error.message}`
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-license-view {
  animation: fadeIn 0.5s;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 2rem;
}

.license-form {
  max-width: 1200px;
}

.form-section {
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #e2e8f0;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.license-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.license-type-card {
  border: 3px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.license-type-card:hover {
  border-color: #cbd5e0;
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.license-type-card.active {
  border-color: #667eea;
  background: #f7faff;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
}

.type-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.type-icon {
  font-size: 2rem;
}

.type-header h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.type-duration {
  font-size: 0.875rem;
  color: #718096;
  margin-bottom: 0.5rem;
}

.type-price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 1rem;
}

.type-features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.type-features li {
  font-size: 0.875rem;
  color: #4a5568;
  margin-bottom: 0.5rem;
  padding-left: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
