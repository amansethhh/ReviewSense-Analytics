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
    port: 5173,
    proxy: {
      // Proxy all /api/* requests to the backend
      // during dev to avoid CORS browser blocks
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // BUG-6 FIX: Disable CSS code splitting to prevent animation
    // flickering when stylesheets load at different times
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor:   ['react', 'react-dom',
                     'react-router-dom'],
          recharts: ['recharts'],
        },
      },
    },
  },
})
