import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from '../hooks/useTranslation';
import { I18nContext } from './I18nContext';
import { locales, type Locale } from './config';
import { apiClient } from '../services/apiClient';

const LOCALE_KEY = 'supreme_lang';

function readStoredLocale(fallback: Locale): Locale {
  if (typeof window === 'undefined') return fallback;
  const stored = window.localStorage.getItem(LOCALE_KEY);
  return stored && locales.includes(stored as Locale) ? (stored as Locale) : fallback;
}

export const TranslationProvider = ({ locale: initialLocale, children }: { locale?: Locale; children: React.ReactNode }) => {
  const fallbackLocale = initialLocale ?? 'en';
  const [locale, setLocaleState] = useState<Locale>(() => readStoredLocale(fallbackLocale));
  const { t } = useTranslation(locale);

  useEffect(() => {
    if (typeof window !== 'undefined') window.localStorage.setItem(LOCALE_KEY, locale);
  }, [locale]);

  const setLocale = (next: Locale) => {
    if (!locales.includes(next)) return;
    setLocaleState(next);
    void apiClient.put('/api/user/preferences', {
      preferred_language: next,
      updatedAt: new Date().toISOString(),
    }).catch(() => {
      // Local state remains usable when the account is offline or unauthenticated.
    });
  };

  const value = useMemo(() => ({ t, locale, setLocale }), [locale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};
