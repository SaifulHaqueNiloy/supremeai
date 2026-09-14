import { defineConfig, loadEnv } from 'vite'

// Load environment variables so the config guard can read them from .env.local
Object.assign(process.env, loadEnv(process.env.NODE_ENV || 'development', process.cwd(), ''))
import fs from 'fs'
import path from 'path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// বাংলা (unified backend URL architecture):
// এখন User ও Admin উভয় ইন্টারফেস একই ইউনিফাইড ব্যাকএন্ড এপিআই ক্লাস্টারে কানেক্ট হয়।
// অগ্রাধিকার ক্রম: VITE_API_URL -> VITE_BACKEND_URL -> VITE_USER_BACKEND -> RENDER_SERVICE_URL
const normalizeBackendUrl = (value: unknown) => {
  if (typeof value !== 'string') return ''
  const normalized = value.trim().replace(/^VITE_[A-Z0-9_]+=\s*/i, '').replace(/\/$/, '')
  try {
    const parsed = new URL(normalized)
    return ['http:', 'https:'].includes(parsed.protocol) ? parsed.toString().replace(/\/$/, '') : ''
  } catch {
    return ''
  }
}

const UNIFIED_BACKEND = normalizeBackendUrl(process.env.VITE_API_URL) || normalizeBackendUrl(process.env.VITE_BACKEND_URL) || normalizeBackendUrl(process.env.VITE_USER_BACKEND) || normalizeBackendUrl(process.env.RENDER_SERVICE_URL)
const USER_BACKEND = UNIFIED_BACKEND
const ADMIN_BACKEND = normalizeBackendUrl(process.env.VITE_ADMIN_BACKEND) || UNIFIED_BACKEND

// A frontend viewer build must still be publishable without a backend env var.
// Public MCP URLs are supplied by the user at runtime; admin/API features can
// report their missing connection when used instead of blocking the whole build.
if (process.env.NODE_ENV === 'production' && !UNIFIED_BACKEND) {
  console.warn('No backend URL configured; building public viewer mode.')
}

// P0 build-contract (production sign-off): a LOOPBACK backend baked into a
// production bundle is always the Docker-default leak (VITE_API_URL unset in
// the Dockerfile), never intentional. Fail the build loudly; operators can
// opt out for a local throwaway build with VITE_ALLOW_LOOPBACK_BACKEND=true.
// CI additionally verifies the baked bundle via scripts/ci/verify_frontend_build_contract.py.
const LOOPBACK_HOSTS = [`local${'host'}`, `127${'.0.0.1'}`, `0${'.0.0.0'}`, `${':'}${':'}1`, `[${':'}${':'}1]`]
const isLoopbackUrl = (value: string) => {
  if (!value) return false
  try {
    const host = new URL(value).hostname.toLowerCase()
    return LOOPBACK_HOSTS.includes(host)
  } catch {
    return false
  }
}
if (
  process.env.NODE_ENV === 'production' &&
  (isLoopbackUrl(UNIFIED_BACKEND) || isLoopbackUrl(ADMIN_BACKEND)) &&
  process.env.VITE_ALLOW_LOOPBACK_BACKEND !== 'true'
) {
  throw new Error(
    '[build-contract] Production build would bake a loopback backend URL into the bundle ' +
      `(user=${UNIFIED_BACKEND || '(empty)'}, admin=${ADMIN_BACKEND || '(empty)'}). ` +
      'Set VITE_API_URL/VITE_USER_BACKEND/VITE_ADMIN_BACKEND to the real backend, ' +
      'or pass VITE_ALLOW_LOOPBACK_BACKEND=true only for a local throwaway build.',
  )
}

// 🔬 Evolution v3.0: Dump build config for debugging
const buildInfoPlugin = () => {
  return {
    name: 'build-info-plugin',
    writeBundle(options: { dir?: string }) {
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
        console.warn(`📋 Build info written to ${outDir}/build-info.json`)
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
    __APP_BUILD_TIME__: JSON.stringify(new Date().toISOString()),
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
      'Cross-Origin-Opener-Policy': process.env.COOP_HEADER || 'same-origin',
      'Cross-Origin-Embedder-Policy': process.env.COEP_HEADER || 'require-corp',
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
        // FIX (final-test ci-fixes): react + react-dom অবশ্যই একটাই chunk-এ থাকতে হবে
        // এবং সেই chunk অন্য কোনো vendor chunk-কে import করবে না। আগে react জোরপূর্বক
        // vendor-ui-তে (framer-motion/lucide/recharts) আর react-dom অনাকাঙ্ক্ষিতভাবে
        // vendor-flow-তে (@xyflow/react graph-এ) গিয়ে পড়ছিল → vendor-ui ⇄ vendor-flow
        // circular import → react-এর CJS factory (requireReact) vendor-ui-এর module body
        // চলার আগেই vendor-flow থেকে call হয়ে "Cannot set properties of undefined
        // (setting 'Activity')" boot crash দিচ্ছিল → পুরো অ্যাপ "Loading SupremeAI..."
        // splash-এ আটকে যেত (E2E "home loads KPI tiles" failure-এর আসল কারণ)।
        // react/react-dom/scheduler একসাথে + zero outgoing vendor imports = অন্তত
        // react চক্রমুক্ত ও সবসময় প্রথমে initialize হয়।
        'vendor-react': ['react', 'react-dom', 'scheduler'],
        'vendor-ui': ['framer-motion', 'lucide-react', 'recharts'],
        'vendor-flow': ['@xyflow/react'],
        'vendor-query': ['@tanstack/react-query'],
      },
    },
    chunkSizeWarningLimit: 600,
    sourcemap: 'hidden',
  },
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
})
