"use client"

import type React from "react"
import { useState } from "react"

interface LoginFormProps {
  onLogin: (user: { id: string; name: string; score: number }) => void
}

export default function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Simulate API call delay
    setTimeout(() => {
      // Mock user data - in a real app, this would come from your backend
      const mockUser = {
        id: "user-123",
        name: username,
        score: 3,
      }

      onLogin(mockUser)
      setIsLoading(false)
    }, 1000)
  }

  const handleSkip = () => {
    onLogin({
      id: "guest",
      name: "Guest User",
      score: 0,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 pt-4">
      <div className="space-y-2">
        <label htmlFor="username" className="block text-sm font-medium" style={{ color: 'var(--foreground)' }}>
          Username
        </label>
        <input
          id="username"
          className="w-full rounded-md border border-custom px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <label htmlFor="password" className="block text-sm font-medium" style={{ color: 'var(--foreground)' }}>
          Password
        </label>
        <input
          id="password"
          type="password"
          className="w-full rounded-md border border-custom px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <div className="flex flex-col space-y-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-2 rounded-md transition-colors bg-[var(--button-bg)] text-[var(--button-text)] hover:bg-[var(--button-hover-bg)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "Logging in..." : "Login"}
        </button>
        <button
          type="button"
          onClick={handleSkip}
          className="w-full border border-custom px-4 py-2 rounded-md hover:bg-secondary transition-colors"
        >
          Continue as Guest
        </button>
      </div>
    </form>
  )
}
