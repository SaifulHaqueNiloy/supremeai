# Client-Side Render Failover & Interceptor Plan

আপনি যে `determineActiveBackend` লজিকটি দিয়েছেন সেটি দারুণ! তবে `getApiBaseUrl()` কে `async` বানালে অ্যাপের অনেক জায়গায় (যেমন `EventSource` বা রিয়েক্ট হুকস) সিঙ্ক্রোনাস কোড ব্রেক করতে পারে। তাই আমরা `apiClient.ts` এর ভেতরে একটি স্মার্ট ইন্টারসেপ্টর (Interceptor) ইমপ্লিমেন্ট করব, যা সিঙ্ক্রোনাস স্ট্রাকচার ঠিক রেখে ব্যাকগ্রাউন্ডে ফেইলওভার ম্যানেজ করবে।

## User Review Required

> [!IMPORTANT]
> **আপনার প্রশ্নের উত্তর (Secret Key Synchronization):** 
> যেহেতু আমরা JWT (JSON Web Token) ব্যবহার করছি, এটি স্টেটলেস (Stateless)। অর্থাৎ, দুটি রেন্ডার অ্যাকাউন্টের ব্যাকএন্ডে যদি একই `ENCRYPTION_KEY` এবং `JWT_SECRET` এনভায়রনমেন্ট ভেরিয়েবল সেট করা থাকে, তবে একটি সার্ভার ডাউন হলে ইউজার যখন দ্বিতীয় সার্ভারে রিকোয়েস্ট পাঠাবে, দ্বিতীয় সার্ভারটি সেই একই টোকেন ভ্যালিডেট করতে পারবে। ইউজার কোনোভাবেই লগ-আউট হবে না!
> 
> তাই আমরা সরাসরি **ইন্টারসেপ্টর (Interceptor)** যুক্ত করার কাজটিতে হাত দিতে পারি।

## Proposed Implementation

### ১. `apps/studio-client/src/utils/api.ts` আপডেট
আমরা সার্ভার লিস্ট এবং স্টোরেজ লজিকটি সিঙ্ক্রোনাস রাখবো, কিন্তু একটি গ্লোবাল মেথড রাখবো যা ফেইল করলে কারেন্ট সার্ভার পাল্টে দেবে।

```typescript
export const RENDER_BACKENDS = [
  'https://supremeai-backend-08zd.onrender.com', // Primary
  'https://supremeai-backend-secondary.onrender.com' // Fallback
];

export const switchActiveBackend = () => {
  const current = sessionStorage.getItem('supremeai_active_backend');
  const next = current === RENDER_BACKENDS[0] ? RENDER_BACKENDS[1] : RENDER_BACKENDS[0];
  sessionStorage.setItem('supremeai_active_backend', next);
  console.log(`[Failover] Switched backend to: ${next}`);
  return next;
};
```

### ২. `apiClient.ts` এ Interceptor (Retry Logic)
`apiClient.ts`-এর `throttledFetch` ফাংশনে আমরা `try-catch` ব্লক আপডেট করবো। যদি কোনো রিকোয়েস্ট 503 (Service Unavailable), 502 (Bad Gateway), বা Timeout এর কারণে ফেইল করে, তখন:
- এটি `switchActiveBackend()` কল করে সার্ভার সুইচ করবে।
- রিকোয়েস্টটি নতুন সার্ভারের ইউআরএলে পুনরায় (Retry) করবে।

```typescript
const throttledFetch = async (url: string, options: RequestInit): Promise<Response> => {
  return requestQueue.add(async () => {
    let currentUrl = url;
    let attempts = 0;
    
    while (attempts < 2) {
      try {
        const res = await fetch(currentUrl, options);
        // 502/503/504 পেলে রেন্ডার সার্ভার স্লিপিং বা ডাউন
        if (res.status >= 502 && res.status <= 504) {
          throw new Error("Server sleeping or down");
        }
        return res;
      } catch (e) {
        attempts++;
        if (attempts >= 2) throw e;
        
        // ফেইলওভার ট্রিগার করা
        const newBase = switchActiveBackend();
        // পুরনো বেইজ ইউআরএল রিপ্লেস করে নতুন ইউআরএল তৈরি
        const path = currentUrl.replace(/^https?:\/\/[^\/]+/, '');
        currentUrl = `${newBase}${path}`;
        
        // স্লিপিং থেকে ওঠার জন্য ১ সেকেন্ড অপেক্ষা করে রিট্রাই
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    throw new Error("All backends failed");
  }) as Promise<Response>;
};
```

## Verification Plan
1. আমি এই লজিকটি ইমপ্লিমেন্ট করার পর আপনি আপনার সেকেন্ডারি রেন্ডার অ্যাকাউন্টটি সেটআপ করে নিতে পারবেন। 
2. ফেইলওভার কাজ করছে কিনা তা দেখতে প্রাইমারি অ্যাকাউন্টের ওয়েব সার্ভিসটি পজ (Pause) করে চেক করতে পারবেন।
