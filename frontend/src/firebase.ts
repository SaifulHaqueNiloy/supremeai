import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// VERIFIED (final-test 2026-09-13) against the project's own
// https://supremeai-a.firebaseapp.com/__/firebase/init.json endpoint.
// Firebase web config values are PUBLIC client identifiers (not secrets) —
// they are designed to be embedded in browser apps. The previous VITE_* env
// fallback values were placeholders (appId "abcd1234efgh5678", wrong senderId,
// wrong storage bucket suffix) and broke every non-Firebase-Hosting deployment
// (e.g. Vercel), where the /__/firebase/init.json fetch also 404s.
const VERIFIED_FIREBASE_CONFIG = {
  apiKey: 'AIzaSyCib1UPogwLoAshIWm9YQJB_RR0UxC07i8',
  authDomain: 'supremeai-a.firebaseapp.com',
  databaseURL: 'https://supremeai-a-default-rtdb.asia-southeast1.firebasedatabase.app',
  projectId: 'supremeai-a',
  storageBucket: 'supremeai-a.firebasestorage.app',
  messagingSenderId: '565236080752',
  appId: '1:565236080752:web:572bb9313db9afb355d4b5',
  measurementId: 'G-KR71C451BR',
};

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
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || VERIFIED_FIREBASE_CONFIG.apiKey,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || VERIFIED_FIREBASE_CONFIG.authDomain,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || VERIFIED_FIREBASE_CONFIG.projectId,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || VERIFIED_FIREBASE_CONFIG.storageBucket,
    messagingSenderId:
      import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || VERIFIED_FIREBASE_CONFIG.messagingSenderId,
    appId: import.meta.env.VITE_FIREBASE_APP_ID || VERIFIED_FIREBASE_CONFIG.appId,
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
