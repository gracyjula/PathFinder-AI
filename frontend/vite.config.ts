import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,          // bind to 0.0.0.0 — works on both IPv4 and IPv6
    port: 5173,
    proxy: {
      // All /api/* requests are forwarded to the FastAPI backend.
      // Using 127.0.0.1 explicitly (not localhost) avoids Windows IPv6 issues.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
