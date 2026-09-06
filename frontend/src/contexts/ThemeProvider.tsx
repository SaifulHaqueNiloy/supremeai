import React, { useEffect, useState } from 'react';
import { adminTokenStore } from '../services/adminTokenStore';
import { getApiBaseUrl } from '../utils/api';
import { THEME_ORDER } from './ThemeConstants';
import { ThemeContext } from './ThemeContext';
import type { Theme } from './ThemeConstants';
import { apiClient } from '../services/apiClient';
import { eventBus, Events } from '../lib/componentEventBus';

// বাংলা মন্তব্য: ThemeContext একে অপর ফাইল থেকে ইম্পোর্ট করা হয়েছে, যাতে react-refresh সতর্কতা দূর হয়
// useTheme hook একে অপর ফাইলে সরানো হয়েছে (useTheme.ts)
export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('dark'); // ডিফল্ট Deep Space (dark)

  useEffect(() => {
    // বাংলা মন্তব্য: Race Condition এড়াতে AbortController ব্যবহার করা হয়েছে
    const controller = new AbortController();
    const token = adminTokenStore.getDecodedToken();
    const storageKey = 'supremeai-theme-storage';
    const stored = localStorage.getItem(storageKey);
    const legacy = localStorage.getItem('supremeai_theme');
    const localTheme = stored ? JSON.parse(stored)?.state?.theme : legacy;
    if (localTheme && THEME_ORDER.includes(localTheme as Theme)) {
      setTheme(localTheme as Theme);
      localStorage.removeItem('supremeai_theme');
    }

    const loadTheme = async () => {
      if (!token) return;
      try {
        const response = await apiClient.get<any>('/api/v1/preferences', { signal: controller.signal });
        const remoteTheme = response.data?.theme;
        if (remoteTheme && THEME_ORDER.includes(remoteTheme as Theme)) {
          setTheme(remoteTheme as Theme);
        }
      } catch (err: any) {
        if (err.name !== 'AbortError' && err.name !== 'CanceledError') console.error('Theme sync failed:', err);
      }
    };

    loadTheme();

    const unsub = eventBus.subscribe(Events.THEME_CHANGED, (data) => {
      if (data.theme && THEME_ORDER.includes(data.theme as Theme)) setTheme(data.theme as Theme);
    });

    return () => {
      controller.abort();
      unsub();
    }; // কম্পোনেন্ট আনমাউন্ট হলে রিকোয়েস্ট বাতিল
  }, []);

  useEffect(() => {
    // বাংলা মন্তব্য: HTML root এলিমেন্টে থিম ক্লাস অ্যাড করা হচ্ছে
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark', 'sunset', 'matrix');
    root.classList.add(theme);
    root.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    // বাংলা মন্তব্য: পরবর্তী থিমে সাইকেল করা হচ্ছে (dark → light → sunset → matrix → dark)
    const currentIndex = THEME_ORDER.indexOf(theme);
    const nextIndex = (currentIndex + 1) % THEME_ORDER.length;
    const newTheme = THEME_ORDER[nextIndex];

    // Optimistic UI Update
    setTheme(newTheme);
    localStorage.setItem('supremeai-theme-storage', JSON.stringify({ state: { theme: newTheme }, version: 0 }));
    localStorage.removeItem('supremeai_theme');

    // ব্যাকএন্ডে async সিঙ্ক করা
    apiClient.post('/api/v1/preferences', { theme: newTheme })
      .catch(err => console.error('Failed to sync theme to DB:', err));

    eventBus.emit(Events.THEME_CHANGED, {
      theme: newTheme,
      isDark: newTheme === 'dark' || newTheme === 'matrix',
      timestamp: Date.now(),
      source: 'theme_provider',
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
