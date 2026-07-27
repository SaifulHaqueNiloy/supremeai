# Tri-Pillar CI/CD Refactoring Plan

অ্যাডমিন এবং ইউজার ট্রাফিক আলাদা লেয়ারে হ্যান্ডেল করার এই **"Tri-Pillar Distribution Strategy"** আইডিয়াটি আসলেই চমৎকার!

## 1. Updated CI/CD Architecture (`supreme-core-ci.yml`)

আমাদের `supreme-core-ci.yml` এখন ৩টি জব হ্যান্ডেল করবে:

- **deploy-backend (Render):** Docker ইমেজ বিল্ড করে GHCR-এ পুশ করবে এবং Render-এ Deploy Hook কল করবে।
- **deploy-user-dashboard (Vercel):** `apps/studio-client` কে `VITE_PORTAL_TYPE=user` মোডে বিল্ড করে Vercel-এ পুশ করবে।
- **deploy-admin-dashboard (Firebase):** `apps/studio-client` কে `VITE_PORTAL_TYPE=admin` মোডে বিল্ড করে Firebase Hosting-এ পুশ করবে।

### Conceptual YAML Structure:

```yaml
jobs:
  deploy-to-render:
    name: ⚙️ Deploy Backend (Render)
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy Hook
        run: curl ... 

  deploy-to-vercel:
    name: 🚀 Deploy User Portal (Vercel)
    needs: deploy-to-render
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: vercel --prod --token ${{ secrets.VERCEL_TOKEN }}

  deploy-frontend-prod:
    name: 🌐 Deploy Admin Dashboard (Firebase)
    needs: deploy-to-render
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Firebase Hosting
        run: firebase deploy --only hosting --token "${{ secrets.FIREBASE_TOKEN }}"
```

## 2. Current Code Configuration & Security (Critical)

আপনার প্রশ্ন অনুযায়ী আমি কোডবেস (বিশেষ করে `apps/studio-client`) অ্যানালাইজ করে কনফিগারেশন চেক করেছি। আমাদের বর্তমান সেটআপ হলো:

> [!NOTE]
> **অ্যাডমিন ড্যাশবোর্ড কানেকশন:** 
> আমাদের অ্যাডমিন ড্যাশবোর্ড কোনো Firebase Firestore ব্যবহার করছে না। এটি সম্পূর্ণভাবে Render ব্যাকএন্ডের API-এর উপর নির্ভরশীল। আমাদের ডাটাবেস হলো Supabase (PostgreSQL), যা শুধুমাত্র ব্যাকএন্ড থেকে এক্সেস করা হয়।

> [!NOTE]
> **Firebase Authentication:** 
> হ্যাঁ, আমাদের `apps/studio-client` বর্তমানে **Firebase Auth** ব্যবহার করছে (`src/hooks/useAuth.ts` এবং `src/firebase.ts` এর মাধ্যমে)। এটি Firebase থেকে লগইন করে এবং এরপর `apiClient.post('/api/admin/firebase-login')` এর মাধ্যমে সেই টোকেনটি Render ব্যাকএন্ডে পাঠিয়ে ভেরিফাই করিয়ে নেয়। 

অর্থাৎ, আমাদের **Tri-Pillar** সেটআপ একদম পারফেক্টলি কাজ করবে! 

- **API Origin Whitelisting:** Render ব্যাকএন্ডের `CORS_ORIGINS` কনফিগারেশনে Vercel এবং Firebase-এর ডোমেইন দুটি অ্যাড করা হবে।
- **Migration Isolation:** Render-এর স্টার্ট কমান্ডে `alembic upgrade head` যুক্ত করা হবে।

## 3. Maintenance Pipeline Updates

- `maintenance_pipeline.yml`-এ Firebase Hosting Purge Cache বা রিলেটেড টাস্ক যোগ করার সুযোগ থাকবে।

---

প্ল্যানটি এখন সম্পূর্ণ প্রস্তুত এবং সিকিউর। 
দয়া করে **Proceed** বাটনে ক্লিক করুন, যাতে আমি আজই আপনার `supreme-core-ci.yml` আপডেট করে দিতে পারি! 🚀
