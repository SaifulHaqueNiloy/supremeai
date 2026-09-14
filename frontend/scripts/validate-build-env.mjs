#!/usr/bin/env node
/**
 * FINAL-TEST P0 FIX — Frontend → Backend URL deployment contract guard.
 *
 * Vite inlines `import.meta.env.VITE_*` values at BUILD time. If a production
 * bundle is built without the real backend URLs (or worse, with the Dockerfile
 * default http://localhost:8080), the deployed app silently falls back to
 * "degraded viewer mode" — the exact deployment incident this guard prevents.
 *
 * Contract (mirrors frontend/src/utils/api.ts):
 *   USER backend  ← VITE_USER_BACKEND | VITE_API_BASE | VITE_API_URL | VITE_BACKEND_URL
 *   ADMIN backend ← VITE_ADMIN_BACKEND (falls back to the user backend)
 *   Same-host     ← VITE_USE_RELATIVE_PATH=true (nginx/vercel proxy serves /api)
 *
 * Enforcement (when NODE_ENV=production or VITE_FORCE_CONTRACT_CHECK=true):
 *   1. At least one user-backend variable must be non-empty, OR
 *      VITE_USE_RELATIVE_PATH=true, OR the explicit escape hatch
 *      VITE_ALLOW_LOCAL_BACKEND=true is set (local Docker testing only).
 *   2. No localhost/127.0.0.1/[::1] URL may be baked into a production build
 *      unless VITE_ALLOW_LOCAL_BACKEND=true.
 *
 * Exit code 1 fails the Docker build / CI job with an actionable message.
 */

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '::1']);

const env = { ...process.env };

function pick(...keys) {
  for (const k of keys) {
    const raw = (env[k] || '').trim().replace(/^VITE_[A-Z0-9_]+=\s*/i, '');
    if (raw) return raw;
  }
  return '';
}

function isLocal(url) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    return LOCAL_HOSTS.has(parsed.hostname.toLowerCase());
  } catch {
    return LOCAL_HOSTS.has(url.replace(/^\w+:\/\//, '').split(':')[0].toLowerCase());
  }
}

const isProd = env.NODE_ENV === 'production' || env.VITE_FORCE_CONTRACT_CHECK === 'true';
const allowLocal = env.VITE_ALLOW_LOCAL_BACKEND === 'true';
const useRelative = env.VITE_USE_RELATIVE_PATH === 'true';

const userBackend = pick(
  'VITE_USER_BACKEND',
  'VITE_API_BASE',
  'VITE_API_URL',
  'VITE_BACKEND_URL',
);
const adminBackend = pick('VITE_ADMIN_BACKEND') || userBackend;

const contract = {
  VITE_USER_BACKEND: userBackend || '(unset)',
  VITE_ADMIN_BACKEND: adminBackend || '(unset)',
  VITE_USE_RELATIVE_PATH: String(useRelative),
  VITE_ALLOW_LOCAL_BACKEND: String(allowLocal),
};

console.log('┌─ Frontend → Backend deployment contract ─────────────');
for (const [k, v] of Object.entries(contract)) {
  console.log(`│  ${k} = ${v}`);
}
console.log('└───────────────────────────────────────────────────────');

if (!isProd) {
  console.log('✅ Contract check skipped (non-production build).');
  process.exit(0);
}

const errors = [];

if (!userBackend && !useRelative) {
  errors.push(
    'No backend URL configured. Set VITE_USER_BACKEND (or VITE_API_URL) to the ' +
      'production backend origin — otherwise the built app ships in degraded viewer mode.',
  );
}

for (const [name, url] of [
  ['VITE_USER_BACKEND', userBackend],
  ['VITE_ADMIN_BACKEND', adminBackend],
]) {
  if (url && isLocal(url) && !allowLocal) {
    errors.push(
      `${name} points at a loopback host (${url}). A production bundle must call ` +
        `the real backend origin. Fix the deployment env, or set ` +
        `VITE_ALLOW_LOCAL_BACKEND=true if this image is intentionally for local testing.`,
    );
  }
}

if (errors.length > 0) {
  console.error('\n❌ PRODUCTION BUILD BLOCKED — frontend/backend URL contract violated:');
  for (const e of errors) console.error(`   • ${e}`);
  console.error(
    '\n   Fix: pass the real URLs as build args, e.g.\n' +
      '        docker build --build-arg VITE_API_URL=https://api.example.com ...\n' +
      '   Local Docker testing escape hatch: VITE_ALLOW_LOCAL_BACKEND=true\n',
  );
  process.exit(1);
}

console.log('✅ Frontend → Backend contract OK for production build.');
