"use client"

import { useState } from "react"
import LoginForm from "@/components/login-form"
import ShipReportForm from "@/components/ship-report-form"

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<{ id: string; name: string; score: number } | null>(null)

  // Mock login function - in a real app, this would connect to your backend
  const handleLogin = (userData: { id: string; name: string; score: number }) => {
    setIsLoggedIn(true)
    setUser(userData)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24 bg-secondary transition-colors">
      <div className="w-full max-w-md bg-white dark:bg-secondary rounded-lg border border-custom shadow-sm transition-colors">
        <div className="p-6">
          <h2 className="text-2xl font-semibold text-center mb-6" style={{ color: 'var(--foreground)' }}>Report Ship Activity</h2>
          {isLoggedIn ? (
            <ShipReportForm
              user={user}
              onLogout={() => {
                setIsLoggedIn(false)
                setUser(null)
              }}
            />
          ) : (
            <LoginForm onLogin={handleLogin} />
          )}
        </div>
      </div>
    </main>
  )
}
