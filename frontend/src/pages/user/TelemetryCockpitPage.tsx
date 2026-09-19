// RESTORE-AND-WIRE (2026-09-14): adapter page for the restored
// AgentExecutionTelemetryCockpit. The cockpit needs the raw auth token for its
// WebSocket/SSE telemetry streams; the auth store intentionally does not expose
// it as state, so we read the canonical token key (same one apiClient uses) and
// keep it in sync via the auth-changed event.
import React, { useEffect, useState } from 'react';
import AgentExecutionTelemetryCockpit from '../../components/dashboard/AgentExecutionTelemetryCockpit';
import { getUserToken } from '../../services/tokenStorage';

const readToken = (): string =>
  // Issue #521 (FE-04): canonical token via tokenStorage — sessionStorage-first,
  // legacy localStorage entries migrated/swept on read.
  getUserToken() || '';

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
