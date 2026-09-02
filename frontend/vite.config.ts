import { defineConfig, loadEnv } from 'vite'

// Load environment variables so the config guard can read them from .env.local
Object.assign(process.env, loadEnv(process.env.NODE_ENV || 'development', process.cwd(), ''))
import fs from 'fs'
import path from 'path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// বাংলা (single-frontend migration, roadmap Phase 1/7): VITE_PORTAL_TYPE সম্পূর্ণ সরানো হয়েছে।
// একটাই build, একটাই outDir (dist/)। দুটি backend URL (user + admin) একই বান্ডলে
// embed থাকে; runtime-এ route context অনুযায়ী utils/api.ts সঠিকটি বেছে নেয়।
// 🔧 DYNAMIC CONFIG: No hardcoded URLs — Fail-Fast in production
const ADMIN_BACKEND = process.env.VITE_ADMIN_BACKEND || process.env.RENDER_SERVICE_URL || ''
const USER_BACKEND = process.env.VITE_USER_BACKEND || process.env.VITE_API_URL || process.env.RENDER_SERVICE_URL || ''

// 🔒 PRODUCTION GUARD: Missing user backend URL = Build failure (not silent wrong URL)
if (process.env.NODE_ENV === 'production' && !USER_BACKEND) {
  console.error('❌ FATAL: VITE_USER_BACKEND environment variable is required in production!')
  process.exit(1)
}
// বাংলা: admin backend এখন optional — না থাকলে runtime admin-context calls
// user backend-এ fall back করে (একই FastAPI app /admin-api ও /api/v1 দুই-ই serve করে)।
if (process.env.NODE_ENV === 'production' && !ADMIN_BACKEND) {
  console.warn('⚠️ VITE_ADMIN_BACKEND not set — admin-context API calls will fall back to the user backend.')
}

// 🔬 Evolution v3.0: Dump build config for debugging
const buildInfoPlugin = () => {
  return {
    name: 'build-info-plugin',
    writeBundle(options: any) {
      if (process.env.NODE_ENV === 'production') {
        const buildInfo = {
          timestamp: new Date().toISOString(),
          buildType: 'unified', // single frontend build (no portal split)
          userBackendUrl: USER_BACKEND,
          adminBackendUrl: ADMIN_BACKEND || USER_BACKEND,
          coopHeader: process.env.COOP_HEADER,
          coepHeader: process.env.COEP_HEADER,
        }
        const outDir = options.dir || 'dist'
        fs.writeFileSync(path.join(outDir, 'build-info.json'), JSON.stringify(buildInfo, null, 2))
        console.log(`📋 Build info written to ${outDir}/build-info.json`)
      }
    }
  }
}

const devProxy = {
  '/api': {
    target: USER_BACKEND,
    changeOrigin: true
  },
  '/admin-api': {
    target: ADMIN_BACKEND || USER_BACKEND,
    changeOrigin: true
  },
  '/auth': {
    target: USER_BACKEND,
    changeOrigin: true
  }
}

// https://vite.dev/config/
export default defineConfig({
  base: process.env.ELECTRON === 'true' ? './' : '/', // Use './' for Electron, '/' for Web to fix client-side routing and MIME issues
  define: {
    // বাংলা মন্তব্য: লগইন পেজে বিল্ড টাইম দেখানোর জন্য, যাতে প্রোডাকশনে ঠিকমতো ডিপ্লয় হয়েছে কি না বোঝা যায়
    __APP_BUILD_TIME__: JSON.stringify(new Date().toLocaleString('en-US', { timeZone: 'Asia/Dhaka' })),
  },
  plugins: [
    react({ jsxRuntime: 'automatic' }),
    tailwindcss({
      config: './tailwind.config.js',
    }),
    buildInfoPlugin()
  ],
  esbuild: {
    jsx: 'automatic',
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
  },
  resolve: {
    dedupe: ['react', 'react-dom', '@tanstack/react-query']
  },
  server: {
    // 🔧 DYNAMIC SECURITY HEADERS from environment
    headers: {
      'Cross-Origin-Embedder-Policy': process.env.COOP_HEADER || 'cross-origin',
      'Cross-Origin-Opener-Policy': process.env.COEP_HEADER || 'unsafe-none',
    },
    // বাংলা মন্তব্য: dev proxy — user API → user backend, admin API → admin backend (fallback user)
    proxy: devProxy
  },
  preview: {
    proxy: devProxy
  },
  build: {
    // বাংলা: single production artifact — User + Admin দুই context একই bundle-এ
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-ui': ['framer-motion', 'lucide-react', 'recharts'],
          'vendor-flow': ['reactflow'],
          'vendor-query': ['@tanstack/react-query'],
        },
      },
    },
    chunkSizeWarningLimit: 600,
    sourcemap: 'hidden',
  },
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
})
