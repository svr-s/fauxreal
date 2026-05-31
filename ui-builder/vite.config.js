import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/fauxreal/', // For GitHub Pages (svr-s.github.io/fauxreal/)
  build: {
    outDir: '../docs',
    emptyOutDir: true,
  }
})
