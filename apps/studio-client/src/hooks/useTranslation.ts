import { locales, type Locale } from '../i18n/config';
import { translations } from '../i18n/translations';

type TranslationKey = keyof typeof translations.en;

export function useTranslation(locale: Locale = 'en') {
  const t = (key: TranslationKey, params?: Record<string, string | number>) => {
    const current = locales.includes(locale) ? locale : 'en';
    let value = translations[current][key] ?? translations.en[key] ?? key;
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        value = value.replace(`{${k}}`, String(v));
      });
    }
    return value;
  };

  return { t, locale, setLocale: (_next: Locale) => {} };
}

