import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuration Vite pour production - sans TypeScript strict
export default defineConfig({
  plugins: [react()],
  base: '/shopping/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // Skip TypeScript errors
    rollupOptions: {
      onwarn: () => {} // Ignore warnings
    }
  },
  esbuild: {
    // Disable strict TypeScript checking
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  },
  server: {
    port: 5173,
    host: '0.0.0.0'
  }
})