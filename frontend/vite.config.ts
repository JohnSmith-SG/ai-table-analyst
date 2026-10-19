import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Запросы /api/* уходят на Flask-бэкенд (порт 5000)
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:5000' } },
})
