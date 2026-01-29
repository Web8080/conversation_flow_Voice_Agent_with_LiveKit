'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string | null
  role: 'anonymous' | 'user' | 'admin'
  name?: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  getToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check for existing session on mount
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      // Check if user is authenticated (check localStorage, cookies, etc.)
      const savedUser = localStorage.getItem('user')
      if (savedUser) {
        const parsedUser = JSON.parse(savedUser)
        setUser(parsedUser)
        setIsAuthenticated(true)
      } else {
        // Set anonymous user by default
        setUser({ id: null, role: 'anonymous' })
        setIsAuthenticated(false)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser({ id: null, role: 'anonymous' })
      setIsAuthenticated(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      // TODO: Implement actual login API call
      // const response = await fetch('/api/auth/login', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ email, password })
      // })
      // const data = await response.json()
      
      // For now, simulate login
      const mockUser: User = {
        id: `user-${Date.now()}`,
        role: 'user',
        name: email.split('@')[0]
      }
      
      setUser(mockUser)
      setIsAuthenticated(true)
      localStorage.setItem('user', JSON.stringify(mockUser))
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = () => {
    setUser({ id: null, role: 'anonymous' })
    setIsAuthenticated(false)
    localStorage.removeItem('user')
    localStorage.removeItem('auth_token')
  }

  const getToken = async (): Promise<string | null> => {
    // For anonymous users, generate token on demand
    // For authenticated users, use stored token or refresh
    try {
      const authToken = localStorage.getItem('auth_token')
      if (authToken && isAuthenticated) {
        // Verify token is still valid (simplified)
        return authToken
      }
      
      // Generate new token for anonymous or refresh for authenticated
      return null
    } catch (error) {
      console.error('Token retrieval failed:', error)
      return null
    }
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}


