import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import CreateLicense from '../views/CreateLicense.vue'
import ManageLicenses from '../views/ManageLicenses.vue'
import LicenseActivations from '../views/LicenseActivations.vue'
import SecurityAlerts from '../views/SecurityAlerts.vue'
import LicenseValidator from '../views/LicenseValidator.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/create',
    name: 'CreateLicense',
    component: CreateLicense
  },
  {
    path: '/manage',
    name: 'ManageLicenses',
    component: ManageLicenses
  },
  {
    path: '/activations',
    name: 'LicenseActivations',
    component: LicenseActivations
  },
  {
    path: '/security',
    name: 'SecurityAlerts',
    component: SecurityAlerts
  },
  {
    path: '/validator',
    name: 'LicenseValidator',
    component: LicenseValidator
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
