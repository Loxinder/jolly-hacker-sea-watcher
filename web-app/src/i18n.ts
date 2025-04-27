import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import es from './locales/es.json';
import ar from './locales/ar.json';
import zh from './locales/zh.json';
import pt from './locales/pt.json';
import uk from './locales/uk.json';
import pl from './locales/pl.json';

const resources = {
  en: { translation: en },
  es: { translation: es },
  ar: { translation: ar },
  zh: { translation: zh },
  pt: { translation: pt },
  uk: { translation: uk },
  pl: { translation: pl },
};

const supportedLngs = ['en', 'es', 'ar', 'zh', 'pt', 'uk', 'pl'];

function detectBrowserLanguage() {
  if (typeof window !== 'undefined') {
    const browserLang = navigator.language.split('-')[0];
    if (supportedLngs.includes(browserLang)) {
      return browserLang;
    }
  }
  return 'en';
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: detectBrowserLanguage(),
    fallbackLng: 'en',
    supportedLngs,
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
