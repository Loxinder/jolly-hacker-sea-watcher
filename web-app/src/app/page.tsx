"use client"

import { useState } from "react"
import LoginForm from "@/components/login-form"
import ShipReportForm from "@/components/ship-report-form"
import '../i18n';
import { useTranslation } from 'react-i18next';
import languageNames from '../locales/languageNames';

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<{ id: string; name: string; score: number } | null>(null)
  const { t, i18n } = useTranslation();
  const [language, setLanguage] = useState(i18n.language);

  const languages = [
    { code: 'en', label: languageNames['en'] },
    { code: 'es', label: languageNames['es'] },
    { code: 'ar', label: languageNames['ar'] },
    { code: 'zh', label: languageNames['zh'] },
    { code: 'pt', label: languageNames['pt'] },
    { code: 'uk', label: languageNames['uk'] },
    { code: 'pl', label: languageNames['pl'] },
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
          <select
            value={language}
            onChange={e => {
              const newLang = e.target.value;
              i18n.changeLanguage(newLang);
              setLanguage(newLang);
            }}
            className="mb-4 px-4 py-2 rounded bg-blue-200 hover:bg-blue-300"
            style={{ width: 180 }}
          >
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.label}</option>
            ))}
          </select>
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
