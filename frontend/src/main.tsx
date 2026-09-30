// SupremeAI Studio Client v0.0.1
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App.tsx'
import { GlobalErrorBoundary } from './components/GlobalErrorBoundary';
import { setupGlobalFetchInterceptor } from './utils/apiInterceptor';
import { ToastProvider } from './contexts/ToastProvider';

setupGlobalFetchInterceptor();

// Issue #1528 (LOW): background services (SSE watchers, heartbeat, telemetry)
// float promises; any rejection surfaced as a raw "Uncaught (in promise)" and
// QA read the console as broken on a healthy load. The handler does NOT
// swallow the signal — it logs a single structured line so real bugs remain
// debuggable — but it stops the default uncaught-error noise.
window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason instanceof Error ? event.reason.message : String(event.reason ?? 'unknown');
  console.warn(`[async] Unhandled promise rejection (handled by global guard): ${reason}`);
});

import { startAntiSleepHeartbeat } from './services/heartbeat';
if (import.meta.env.PROD) {
  startAntiSleepHeartbeat();
}

// ROOT-CAUSE FIX (#2734): Firebase App+Auth eager init loaded 60-70KB auth SDK
// on every guest boot — even the `/` funnel which never touches auth. Now:
// Firebase is lazy-imported on the auth path (login/ProtectedRoute/AdminLogin).
// The lazy caller already awaits init via `initFirebase()` which is idempotent.
// Static import removed; dynamic import happens on first auth-path render.
// বাংলা: গেস্ট বুটে Firebase SDK আর eager লোড হয় না — auth path-এ lazy import।

import { ThemeProvider } from './contexts/ThemeProvider'
// Shared providers (react-query, monaco defaults)
import { SharedProviders } from '@supremeai/ui-components'
import { BrowserRouter } from 'react-router-dom'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <ThemeProvider>
        <SharedProviders>
          <BrowserRouter>
            <GlobalErrorBoundary>
              <App />
            </GlobalErrorBoundary>
          </BrowserRouter>
        </SharedProviders>
      </ThemeProvider>
    </ToastProvider>
  </StrictMode>,
)

// Register Service Worker for offline PWA capabilities
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      // বাংলা মন্তব্য: no-console রুল শুধু warn/error অনুমোদন করে, তাই log-এর বদলে warn ব্যবহার করা হলো।
      console.warn('[PWA] Service Worker registered:', reg.scope);
    }).catch((err) => {
      console.warn('[PWA] Service Worker registration failed:', err);
    });
  });
}
