import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/cases': 'http://localhost:8000',
      '/goblins': 'http://localhost:8000',
    },
  },
})
