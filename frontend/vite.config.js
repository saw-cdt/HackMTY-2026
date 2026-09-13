import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // sql.js emite un warning de buffer para el wasm; no rompe el build.
  build: {
    chunkSizeWarningLimit: 1500,
  },
})