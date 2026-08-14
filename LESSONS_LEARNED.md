# LESSONS_LEARNED

<!-- বাংলা নোট: প্রতিটি ফিক্স ব্লকই সংযোজনীয় — পুরনো এন্ট্রি মুছবেন না। -->

## 2026-08-14 — Admin Console Error Sweep

### সমস্যা ১: Service Worker — `Failed to convert value to 'Response'`
- **উৎস:** `frontend/public/sw.js` — `fetch` handler-এর `.catch()`-এ ক্যাশ মিস হলে `undefined` return হতো।
- **ফিক্স:** LAST-RESORT হিসেবে `new Response('', { status: 503 })` return-এর pledge। পাশাপাশি থার্ড-পার্টি ডোমেইন (`api.qrserver.com`, `chart.googleapis.com`) এবং `/api/` / `/admin-api/` path গুলো SW `fetch` handler থেকে skip।
- **লেসন:** `event.respondWith()` কখনোই `undefined`/`Promise<undefined>` রিসলভ করতে পারে না। Fallback chain এ সর্বদা একটি concrete `Response` অবজেক্টে শেষ করুন।

### সমস্যা ২: QR Code — `api.qrserver.com` CORS/network failure
- **উৎস:** `frontend/src/components/admin/AdminLogin.tsx` — SW দ্বারা intercept+ CORS ব্লক।
- **ফিক্স:** প্রাইমারি **Google Charts QR API**, fail-এ `api.qrserver.com` fallback (dual-provider onError chain)। `loading="lazy"` যোগ।
- **লেসন:** 3rd-party ইমেজ/API রিসোর্সগুলো PWA Service Worker-এর ক্যাশ/ইন্টারসেপ্ট পথে না দিয়ে সরাসরি ব্রাউজারে যেতে দিন (CORS স্টেটমেন্টের বাইরে)।

### সমস্যা ৩: API 401 Recursive Logout Loop
- **উৎস:** `frontend/src/utils/apiInterceptor.ts` — logout endpoint নিজে 401 দিলে interceptor আবার `handleAdminLogout()` call করত → infinite loop।
- **ফিক্স:** logout URL-এ 401/403 এ auto-logout guard যুক্ত (skip recursion)।
- **লেসন:** কোনো FXception handler-কে নিজেই উপসর্গ-ট্রিগার করা endpoint-এ re-invoke করবেন না — recursion guard অপরিহার্য।

### সমস্যা ৪: 401 Storm — Admin queries টোকেন ছাড়াই চলত
- **উৎস:** `frontend/src/components/admin/ModelRouter.tsx` — `useQuery()`-তে `enabled` guard ছিল না।
- **ফিক্স:** `enabled: hasToken()` + `staleTime` (codebase-wide pattern) যোগ।
- **লেসন:** admin/auth-gated endpoint গুলোতে সর্বদা `enabled: hasToken()` ব্যবহার করুন, নচেৎ লগইন ফর্মেই 401 স্টর্ম হবে।

### সমস্যা ৫: `/api/admin/logout` 401 (endpoint-ই নাই)
- **উৎস:** backend-এ কোনো logout route নেই (নিশ্চিত খোঁজ), তবে frontend call করছিল → guaranteed fail। তাছাড়া logout-এ ভুল token key (`adminToken`) remove হতো, সঠিক key (`supreme_admin_jwt`) রয়ে যেত।
- **ফিক্স:** `handleAdminLogout` থেকে dead backend call সরানো; সব token key (`adminToken`, `supreme_admin_jwt`, `supremeai_auth_token`) পরিষ্কার করা; state সম্পূর্ণ reset।
- **লেসন:** লোকাল স্টোরেজ কৌশলের client logout-এ JWT স্ট্যাটেলেস হলে ব্যাকএন্ড call না করলেই চলে — তবে soap key consistency মেনে চলতে হবে (ADMIN_TOKEN_KEY = `supreme_admin_jwt`)।

### Blindspot নোট
- ~~`frontend/src/store/adminStore.ts`-য়ে login-এ token সেভ হয় `adminToken` key-তে~~ ✅ **ফিক্সড**

## 2026-08-14 (৩য় ধাপ) — CORS Block (Firebase Proxy বাইপাস)

### সমস্যা ৮: Firebase Hosting-এ CORS Error Storm
- **উৎস:** `frontend/src/utils/api.ts`-এ `getApiBaseUrl()` Firebase hosting-এ (`web.app` / `firebaseapp.com`) relative path (`''`) ব্যবহারের কোড **comment out** করা ছিল। ফলে ব্রাউজার `supremeai-admin.onrender.com`-এ সরাসরি cross-origin fetch করত (Firebase proxy বাইপাস) → CORS policy block।
- **ফিক্স:** `getApiBaseUrl()`-এ Firebase hosting detection পুনরুদ্ধার — `''` return করে, ব্রাউজার same-origin request পাঠায়, `firebase.json`-এর rewrite rules server-side proxy করে Render-এ (CORS সমস্যা নেই)। পাশাপাশি `getWebSocketBaseUrl()`-এ WebSocket-এর জন্য (যা Firebase rewrite proxy দিয়ে যায় না) `BACKEND_URL` থেকে `wss://` URL generate করা হচ্ছে।
- **লেসন:** Firebase hosting + Render free tier-এ CORS এড়ানোর নির্ভরযোগ্য উপায় হলো `firebase.json` rewrite proxy। absolute backend URL ব্যবহার মানেই cross-origin CORS — বিশেষ করে Render-এ যেখানে CORS middleware-এর আগে `TrustedOriginMiddleware` OPTIONS request ব্লক করতে পারে। সর্বদা Firebase `web.app` -> `''` -> rewrite proxy পদ্ধতি অনুসরণ করুন।

## 2026-08-14 (২য় ধাপ) — Admin Auth Token Consistency

### সমস্যা ৬: Admin JWT ভুল key-তে সেভ হতো
- **উৎস:** `adminStore.ts`-য়ে login-এ `data.token` সেভ হতো `adminToken`-এ, অথচ গোটা কোডবেস (`adminTokenStore`, WebSocket, SSE, SkillGraph, `useStore`) `supreme_admin_jwt` পড়ে। ফলে `hasToken()` সবসময় false ফিরত এবং admin JWT WebSocket/SSE-এ সঞ্চালিত হতো না।
- **ফিক্স:** `localStorage.setItem('supreme_admin_jwt', data.token)` (সঠিক key) + backward-compat `adminToken`। Logout-এ আগে থেকেই সব key পরিষ্কার হয় (সমস্যা ৫)।
- **লেসন:** Projekt-wide জুড়ে একটি একক admin token key (`supreme_admin_jwt`) ব্যাবহার করুন; কোথাও ভিন্ন key-তে সেভ/রিড করলে auth validity চেক ও realtime চ্যানেল নীরবে ভেঙে যায়।

### সমস্যা ৭: admin-api Bearer header-এ admin JWT যাচ্ছিল না
- **উৎস:** `apiClient.getAuthHeaders()` শুধু `supremeai_auth_token` (user token) পড়ত, admin JWT নয় → `/admin-api/*` ও `/api/admin/*` (require_admin_token) 401।
- **ফিক্স:** admin-role JWT (`supreme_admin_jwt`) থাকলে তাকে Bearer-preফারেন্স হিসেবে পাঠানো; নচেৎ user token fallback।
- **লেসন:** getAuthHeaders সর্বদা admin token-কে অগ্রাধিকার দাও, কারণ এটি সবচেয়ে privileged; user flow-এ তা না থাকলে user token-ই যথেষ্ট।