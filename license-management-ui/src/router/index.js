import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import CreateLicense from '../views/CreateLicense.vue'
import ManageLicenses from '../views/ManageLicenses.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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
