// SupremeAI Studio Client v0.0.1
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App.tsx'
import { GlobalErrorBoundary } from './components/GlobalErrorBoundary';
import { getApiBaseUrl } from './utils/api';
import { setupGlobalFetchInterceptor } from './utils/apiInterceptor';
import { ToastProvider } from './contexts/ToastProvider';

setupGlobalFetchInterceptor();

import { startAntiSleepHeartbeat } from './services/heartbeat';
if (import.meta.env.PROD) {
  startAntiSleepHeartbeat();
}

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
