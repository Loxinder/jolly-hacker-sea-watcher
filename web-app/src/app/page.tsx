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
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-24 bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-lg border shadow-sm">
        <div className="p-6 space-y-1.5">
          <h2 className="text-2xl font-semibold text-center">Ship Reporting App</h2>
          <p className="text-sm text-gray-500 text-center">
            {isLoggedIn ? "Report ships you see at sea" : "Login to start reporting"}
          </p>
        </div>
        <div className="p-6">
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
