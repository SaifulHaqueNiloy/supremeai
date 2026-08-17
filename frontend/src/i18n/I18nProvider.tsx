import React, { useState } from 'react';
import { useTranslation } from '../hooks/useTranslation';
import { I18nContext } from './I18nContext';

// বাংলা মন্তব্য: I18nContext একে অপর ফাইল থেকে ইম্পোর্ট করা হয়েছে, যাতে react-refresh সতর্কতা দূর হয়
export const TranslationProvider = ({ locale: initialLocale, children }: { locale: string; children: React.ReactNode }) => {
  const [locale, setLocaleState] = useState(initialLocale || localStorage.getItem('supreme_lang') || 'en');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { t } = useTranslation(locale as any);

  const setLocale = (newLocale: string) => {
    localStorage.setItem('supreme_lang', newLocale);
    setLocaleState(newLocale);
  };

  return (
     
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    <I18nContext.Provider value={{ t: t as any, locale, setLocale: setLocale as any }}>
      {children}
    </I18nContext.Provider>
  );
};
