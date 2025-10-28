import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 8092,
    proxy: {
      '/api': {
        target: 'http://license-server-v2:8000',
        changeOrigin: true
      }
    }
  }
})
