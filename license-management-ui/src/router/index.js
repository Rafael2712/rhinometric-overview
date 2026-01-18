import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/create-license',
    name: 'CreateLicense',
    component: () => import('../views/CreateLicense.vue')
  },
  {
    path: '/manage-licenses',
    name: 'ManageLicenses',
    component: () => import('../views/ManageLicenses.vue')
  },
  {
    path: '/validator',
    name: 'LicenseValidator',
    component: () => import('../views/LicenseValidator.vue')
  },
  {
    path: '/activations',
    name: 'LicenseActivations',
    component: () => import('../views/LicenseActivations.vue')
  },
  {
    path: '/security',
    name: 'SecurityAlerts',
    component: () => import('../views/SecurityAlerts.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
