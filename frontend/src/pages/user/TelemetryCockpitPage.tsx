// RESTORE-AND-WIRE (2026-09-14): adapter page for the restored
// AgentExecutionTelemetryCockpit. The cockpit needs the raw auth token for its
// WebSocket/SSE telemetry streams; the auth store intentionally does not expose
// it as state, so we read the canonical token key (same one apiClient uses) and
// keep it in sync via the auth-changed event.
import React, { useEffect, useState } from 'react';
import AgentExecutionTelemetryCockpit from '../../components/dashboard/AgentExecutionTelemetryCockpit';

const TOKEN_KEY = 'supremeai_auth_token';

const readToken = (): string =>
  (typeof localStorage !== 'undefined' && localStorage.getItem(TOKEN_KEY)) || '';

export const TelemetryCockpitPage: React.FC = () => {
  const [authToken, setAuthToken] = useState<string>(readToken);

  useEffect(() => {
    const sync = () => setAuthToken(readToken());
    window.addEventListener('storage', sync);
    window.addEventListener('supremeai:auth-changed', sync);
    return () => {
      window.removeEventListener('storage', sync);
      window.removeEventListener('supremeai:auth-changed', sync);
    };
  }, []);

  return <AgentExecutionTelemetryCockpit authToken={authToken} />;
};

export default TelemetryCockpitPage;
