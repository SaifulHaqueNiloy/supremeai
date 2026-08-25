import React, { useEffect, useState } from 'react';
import { ThemeSyncContext } from './ThemeSyncContext';
import { getApiBaseUrl } from '../utils/api';
import { getRawToken } from '../services/apiClient';


import { createSecureEventSource } from '../lib/secureSse';

// বাংলা মন্তব্য: ThemeSyncContext একে অপর ফাইল থেকে ইম্পোর্ট করা হয়েছে, যাতে react-refresh সতর্কতা দূর হয়
// useThemeSync hook একে অপর ফাইলে সরানো হয়েছে (useThemeSync.ts)
export const ThemeSyncProvider: React.FC<{ children: React.ReactNode; userId?: string }> = ({
  children,
  userId = 'default'
}) => {
  const [theme, setThemeState] = useState<string>('dark');

  useEffect(() => {
    // Listen for Server-Sent Events from FastAPI
    const token = getRawToken();
    const eventSource = createSecureEventSource(`${getApiBaseUrl()}/api/preferences/${userId}/stream`, token, {
      onMessage: (event) => {
        try {
          const data = JSON.parse(event.data);
          // fetchEventSource passes event.type via event.type property now if we matched it, or we check data.event
          if ((event.type === 'theme_changed' || data.event === 'theme_changed') && data.theme) {
            console.warn('[ThemeSync] Theme updated via SSE:', data.theme);
            setThemeState(data.theme);
          }
        } catch (err) {
          console.error('[ThemeSync] Error parsing SSE message:', err);
        }
      },
      onOpen: () => {
        console.warn('[ThemeSync] Connected to SSE Stream for user:', userId);
      },
      onError: (err) => {
        console.error('[ThemeSync] SSE Connection Error:', err);
      }
    });

    return () => {
      eventSource.close();
    };
  }, [userId]);

  // Apply theme class to HTML body/root whenever it changes
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark', 'light', 'sunset');

    // Add the new theme class if it's not the default root theme
    if (theme === 'dark' || theme === 'sunset') {
      root.classList.add(theme);
    }
  }, [theme]);

  const setTheme = async (newTheme: string) => {
    setThemeState(newTheme);
    // Push the change to backend
    try {
      await fetch(`${getApiBaseUrl()}/api/preferences/?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: newTheme }),
      });
    } catch (err) {
      console.error('[ThemeSync] Failed to push theme to API:', err);
    }
  };

  return (
    <ThemeSyncContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeSyncContext.Provider>
  );
};
