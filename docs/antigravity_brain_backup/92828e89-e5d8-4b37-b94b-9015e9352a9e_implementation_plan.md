# Implementation Plan - Complete JIT OTP Lifecycle and Phase 2 Device Fingerprinting

This plan addresses the gaps in the JIT OTP verification lifecycle and integrates client-side device fingerprinting as an additional security signal in the anti-hacking middleware.

## Proposed Changes

### Backend Security (Anti-Hacking & OTP Verification)

#### [MODIFY] [anti_hacking.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/middleware/anti_hacking.py)
- Update `AntiHackingContextMiddleware` to persist generated OTPs in Upstash Redis (`security:otp_pending:{admin_id}`) with a 5-minute TTL.
- Extend request signal to capture and validate `x-device-fingerprint` header, checking for mismatches (`or last.get("fingerprint") != signal["fingerprint"]`).

#### [MODIFY] [admin.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/admin.py)
- Implement `/verify-otp` POST endpoint for validating JIT OTPs, promoting successfully verified contexts to trusted status in Redis.

#### [MODIFY] [auth.py](file:///c:/Users/n/supremeai/supremeai_2.0/backend/api/routes/auth.py)
- Record the device fingerprint in Redis (`device:known:{user_id}`) during login if the `x-device-fingerprint` header is present.

---

### Frontend Integration

#### [NEW] [deviceFingerprint.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/utils/deviceFingerprint.ts)
- Implement `getDeviceFingerprint()` using browser crypto API to generate a SHA-256 hash from navigator and hardware cues.
- Expose `primeDeviceFingerprint()` to kick off the calculation on app start.

#### [MODIFY] [apiClient.ts](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/services/apiClient.ts)
- Update `getAuthHeaders` to be `async` and append the `X-Device-Fingerprint` header.
- Await `getAuthHeaders()` in `get`, `post`, `put`, and `delete` apiClient wrappers.

#### [MODIFY] [App.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/App.tsx)
- Call `primeDeviceFingerprint()` at module load to cache the hash ahead of API calls.

---

## Verification Plan

### Automated Tests
- Run the backend test suite:
  ```bash
  pnpm backend:test
  ```

### Manual Verification
- Verify fingerprint header presence in network tab.
- Test login tracking and OTP verification endpoint.
