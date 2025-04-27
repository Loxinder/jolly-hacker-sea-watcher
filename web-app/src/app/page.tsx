"use client"

import { useState, useEffect } from "react"
import LoginForm from "@/components/login-form"
import ShipReportForm from "@/components/ship-report-form"
import '../i18n';
import { useTranslation } from 'react-i18next';

const supportedLngs = ['en', 'es', 'ar', 'zh', 'pt', 'uk', 'pl', 'tl', 'vi', 'th', 'tw', 'ja', 'id'];

const languageNames: Record<string, string> = {
  en: 'English',
  es: 'Español',
  ar: 'العربية',
  zh: '中文',
  pt: 'Português',
  uk: 'Українська',
  pl: 'Polski',
  tl: 'Tagalog',
  vi: 'Tiếng Việt',
  th: 'ไทย',
  tw: '繁體中文',
  ja: '日本語',
  id: 'Bahasa Indonesia',
};

function detectBrowserLanguage() {
  if (typeof window !== 'undefined') {
    const browserLang = navigator.language.split('-')[0];
    if (supportedLngs.includes(browserLang)) {
      return browserLang;
    }
  }
  return 'en';
}

export default function Home() {
  const { t, i18n } = useTranslation();
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<{ id: string; name: string; score: number } | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme, mounted]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    i18n.changeLanguage(e.target.value);
  };

  const languages = [
    { code: 'en', label: languageNames['en'] },
    { code: 'es', label: languageNames['es'] },
    { code: 'ar', label: languageNames['ar'] },
    { code: 'zh', label: languageNames['zh'] },
    { code: 'pt', label: languageNames['pt'] },
    { code: 'uk', label: languageNames['uk'] },
    { code: 'pl', label: languageNames['pl'] },
    { code: 'tl', label: languageNames['tl'] },
    { code: 'vi', label: languageNames['vi'] },
    { code: 'th', label: languageNames['th'] },
    { code: 'tw', label: languageNames['tw'] },
    { code: 'ja', label: languageNames['ja'] },
    { code: 'id', label: languageNames['id'] },
  ];

  // Mock login function - in a real app, this would connect to your backend
  const handleLogin = (userData: { id: string; name: string; score: number }) => {
    setIsLoggedIn(true)
    setUser(userData)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24 bg-secondary transition-colors">
      <div className="w-full max-w-md bg-white dark:bg-secondary rounded-lg border border-custom shadow-sm transition-colors">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <select
              value={i18n.language}
              onChange={handleLanguageChange}
              className="px-4 py-2 rounded bg-blue-200 hover:bg-blue-300"
              style={{ width: 180 }}
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.label}</option>
              ))}
            </select>
            {mounted && (
              <button
                type="button"
                onClick={toggleTheme}
                className="ml-4 px-3 py-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-600 transition-colors"
                aria-label="Toggle dark/light mode"
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {theme === 'dark' ? '🌙 Dark' : '☀️ Light'}
              </button>
            )}
          </div>
          <h2 className="text-2xl font-semibold text-center mb-6" style={{ color: 'var(--foreground)', opacity: 1 }}>{t('reportShipActivity')}</h2>
          {isLoggedIn ? (
            <ShipReportForm
              user={user}
              onLogout={() => {
                setIsLoggedIn(false)
                setUser(null)
              }}
              t={t}
            />
          ) : (
            <LoginForm onLogin={handleLogin} t={t} />
          )}
        </div>
      </div>
    </main>
  )
}
