import React, { useEffect, useRef, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketManager, type WsStatus } from './websocketManager';
import { SseBridges } from './sseBridges';
import { getChannelMapping } from './channelRegistry';
import { useCommandCenterStore } from '../state/useCommandCenterStore';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — Realtime Provider
// বাংলা মন্তব্য: WS + SSE → React Query cache — একটিই রেন্ডার পাইপলাইন
// ═══════════════════════════════════════════════════════════════════════════

interface CommandCenterRealtimeProviderProps {
  children: ReactNode;
}

export function CommandCenterRealtimeProvider({ children }: CommandCenterRealtimeProviderProps) {
  const qc = useQueryClient();
  const { setWsStatus, setLastSyncAt } = useCommandCenterStore();
  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const sseBridgesRef = useRef<SseBridges | null>(null);

  useEffect(() => {
    // WS Manager
    const wsManager = new WebSocketManager({
      onStatusChange: (status: WsStatus) => {
        setWsStatus(status);
        if (status === 'open') {
          setLastSyncAt(Date.now());
        }
      },
      onEvent: (type, payload) => {
        const mapping = getChannelMapping(type);
        if (!mapping) return;

        setLastSyncAt(Date.now());

        if (mapping.merge === 'replace') {
          qc.setQueryData(mapping.queryKey, payload);
        } else if (mapping.merge === 'append') {
          qc.setQueryData(mapping.queryKey, (old: unknown) => {
            if (Array.isArray(old)) {
              return [payload, ...old].slice(0, 100);
            }
            return [payload];
          });
        } else if (mapping.merge === 'patch') {
          qc.setQueryData(mapping.queryKey, (old: unknown) => {
            if (old && typeof old === 'object' && payload && typeof payload === 'object') {
              return { ...(old as object), ...(payload as object) };
            }
            return payload;
          });
        }
      },
      onError: (error) => {
        console.error('[CommandCenter WS]', error.message);
      },
    });

    // SSE Bridges
    const sseBridges = new SseBridges({
      onLog: (log) => {
        qc.setQueryData(['cmd', 'logs'], (old: unknown) => {
          if (Array.isArray(old)) {
            return [log, ...old].slice(0, 200);
          }
          return [log];
        });
      },
      onEvent: (event) => {
        qc.setQueryData(['cmd', 'events'], (old: unknown) => {
          if (Array.isArray(old)) {
            return [event, ...old].slice(0, 100);
          }
          return [event];
        });
      },
      onError: (error) => {
        console.error('[CommandCenter SSE]', error.message);
      },
    });

    wsManagerRef.current = wsManager;
    sseBridgesRef.current = sseBridges;

    wsManager.connect();
    sseBridges.connect();

    return () => {
      wsManager.disconnect();
      sseBridges.disconnect();
      wsManagerRef.current = null;
      sseBridgesRef.current = null;
    };
  }, [qc, setWsStatus, setLastSyncAt]);

  return <>{children}</>;
}