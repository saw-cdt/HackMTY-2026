import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Todo el bundle debe funcionar sin red: sin CDN, sin fuentes remotas.
export default defineConfig({
  plugins: [react()],
  base: './',
})
