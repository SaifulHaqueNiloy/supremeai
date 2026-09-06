import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Helper to fetch configuration dynamically or fallback to Vite env vars
const getFirebaseConfig = async () => {
  try {
    const res = await fetch('/__/firebase/init.json');
    if (res.ok) {
      const data = await res.json();
      if (!data.projectId && data.authDomain) {
        // ডোমেইন সাফিক্স হার্ডকোড না করে প্রথম অংশ থেকে projectId বের করা হচ্ছে
        data.projectId = data.authDomain.split('.')[0];
      }
      return data;
    }
  } catch (e) {
    if (import.meta.env.PROD) {
      console.error("🔥 Failed to fetch Firebase init configuration in production:", e);
      throw new Error("Firebase initialization failed: Configuration endpoint is unreachable.");
    }
  }
  const config = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
  };
  const missingKeys = Object.entries(config)
    .filter(([, value]) => !value)
    .map(([key]) => key);
  if (missingKeys.length > 0) {
    throw new Error(`Firebase configuration is incomplete: ${missingKeys.join(", ")}`);
  }
  return config;
};

// Initialize Firebase app asynchronously or return existing instance
export const initFirebase = async () => {
  if (getApps().length > 0) {
    return getApp();
  }
  const config = await getFirebaseConfig();
  return initializeApp(config);
};

export const getFirebaseAuth = async () => {
  const app = await initFirebase();
  return getAuth(app);
};
