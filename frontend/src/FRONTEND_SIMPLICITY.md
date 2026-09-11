# Frontend simplicity contract

The frontend is a viewer and interaction layer, not a second backend.

## Rules for future changes

- The backend remains authoritative for authorization, policy, orchestration, memory, audit, and operational hardening.
- Prefer one readable viewer path: one URL, one API boundary, one auth state, and one navigation registry.
- The normal user navigation should contain only understandable, working viewer destinations.
- Do not add MCP server management, memory management, policy editing, topology controls, or global realtime infrastructure to the viewer flow unless the product request explicitly requires it.
- Keep advanced/admin routes isolated and reachable only when their audience and use case are clear.
- For read-only data screens, implement only loading, connected/loaded, empty, and backend-error states.
- Prefer local component state for page data. Add global state only for genuinely cross-page concerns such as auth or theme.
- Comments should explain architectural boundaries, not repeat JSX or migration history.

## Viewer journey

1. Open the app or a shared URL.
2. Show a clear loading state while the backend is contacted.
3. Render all data returned for the viewer role in a readable, read-only format.
4. Show a useful empty state when the backend returns no data.
5. Show a plain error and retry action when the backend cannot be reached.

If a proposed frontend change makes this journey harder to understand, stop and simplify it before adding more infrastructure.

## Explicit non-goals

Do not introduce a new MCP server, memory server, client-side policy engine, duplicate API client, or global websocket/SSE connection for the simple viewer experience.

// Future agents: keep this file short and consult it before adding frontend infrastructure.
// Backend complexity may remain behind the API boundary; it does not belong in the viewer UI.
