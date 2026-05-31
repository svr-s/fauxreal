import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/fauxreal/',
  plugins: [
    react(),
    tailwindcss()
  ],
  build: {
    outDir: '../docs',
    emptyOutDir: false,
  }
})
