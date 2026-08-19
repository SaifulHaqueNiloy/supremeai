import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Helper to fetch configuration dynamically or fallback to Vite env vars
const getFirebaseConfig = async () => {
  try {
    const res = await fetch('/__/firebase/init.json');
    if (res.ok) {
      const data = await res.json();
      if (!data.projectId && data.authDomain) {
        data.projectId = data.authDomain.replace('.firebaseapp.com', '');
      }
      return data;
    }
  } catch (e) {
    if (import.meta.env.PROD) {
      console.error("🔥 Failed to fetch Firebase init configuration in production:", e);
      throw new Error("Firebase initialization failed: Configuration endpoint is unreachable.");
    }
  }
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Firebase config missing: VITE_FIREBASE_API_KEY not set. " +
      "Check frontend/.env.example for required variables."
    );
  }

  return {
    apiKey,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID
  };
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
