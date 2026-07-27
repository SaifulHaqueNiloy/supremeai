# 🔧 Fix: Admin Dashboard 401/429 Request Storm

## Root Cause Analysis

The console errors showed a **cascading failure pattern**:

1. **Initial 401s** on `/admin-api/security-scan` and `/admin-api/health-map` — auth token not yet available when queries fire
2. **429 avalanche** — 7+ React Query hooks fire simultaneously on mount, overwhelming Cloud Run's rate limiter
3. **Retry amplification** — React Query retried 429s (only 401/403 were excluded from retry), doubling the request volume
4. **Duplicate fetches** — `useAdminApi.ts` used raw `fetch()` bypassing `apiClient` (no auth headers, no throttle), AND used different `queryKey`s for the same endpoints as `useDashboardData.ts`, so React Query didn't deduplicate
5. **SW crash** — `cache.addAll()` tried to cache `/offline.html` and `/favicon.ico` which don't exist → atomic failure

## Changes Made

### 1. [apiClient.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/services/apiClient.ts) — Request Throttle + Typed Errors

- Added **`ApiError` class** with `.status` property so React Query's retry logic can reliably detect HTTP status codes
- Added **concurrency limiter** (max 3 concurrent requests) with a FIFO queue — prevents the initial mount stampede
- All errors now throw `ApiError` instead of generic `Error`

### 2. [App.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/App.tsx#L6-L24) — QueryClient Retry Config

- Added **429 to non-retriable statuses** (alongside 401/403)
- Also checks error message strings for "Rate limit" / "Unauthorized" as fallback
- Added **exponential backoff with jitter** for retryDelay
- Added global `staleTime: 30s` to prevent duplicate fetches on component remount

### 3. [useDashboardData.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/hooks/useDashboardData.ts) — Auth-Gate + Staggered Intervals

- All queries now have **`enabled: hasToken()`** — won't fire until admin token exists in session storage
- Added per-query `staleTime` values
- **Staggered refetch intervals** (15s, 20s, 30s, 45s, 60s, 120s) so queries don't sync up
- Security scan interval increased from 30s → 120s (it's expensive)
- Events interval increased from 10s → 30s

### 4. [useAdminApi.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/hooks/useAdminApi.ts) — Eliminated Raw Fetch + Fixed Duplicate Keys

- **Replaced all raw `fetch/fetchJSON/postJSON/delJSON`** with centralized `apiClient` calls (now gets auth headers + throttle)
- **Aligned query keys** with `useDashboardData.ts` (e.g. `['costs']` → `['dashboard', 'costs']`) so React Query deduplicates instead of firing parallel requests
- Added auth-gating and `staleTime` to all admin-api queries

### 5. [sw.js](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/public/sw.js) — Service Worker Cache Fix

- Replaced atomic `cache.addAll()` with **`Promise.allSettled` + individual cache.put** — one missing asset no longer breaks entire SW install
- Removed non-existent `/offline.html` and `/favicon.ico` from precache list
- Bumped cache version to `v2` to force SW update
- **Excluded `/admin-api/` and `/api/` routes from SW caching** — prevents stale API data
- Fixed potential crash in fetch handler: `event.request.headers.get('accept')?.includes(...)` (optional chaining)

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Requests on mount | ~14 simultaneous | Max 3 concurrent (queued) |
| 429 retry | Yes (up to 1 retry) | No (immediate abort) |
| Auth-gated queries | No | Yes (all admin-api) |
| Duplicate query keys | Yes (costs, health, ci-logs) | No (unified keys) |
| SW install | Crashes if any asset 404 | Graceful per-asset fallback |
| Raw fetch bypassing auth | Yes (useAdminApi.ts) | No (all via apiClient) |

## Verification

- ✅ TypeScript compiles clean (`tsc --noEmit`)
- ⏳ Vite production build (running)
