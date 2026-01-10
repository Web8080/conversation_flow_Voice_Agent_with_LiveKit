'use client'

import { ReactNode } from 'react'
import { useAuth } from './AuthProvider'
import { useRouter } from 'next/navigation'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'user' | 'admin'
  fallback?: ReactNode
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  fallback 
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuth()
  const router = useRouter()

  // Check authentication
  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>
    }
    router.push('/login')
    return null
  }

  // Check role if required
  if (requiredRole) {
    const roleHierarchy: Record<string, number> = {
      'anonymous': 0,
      'user': 1,
      'admin': 2
    }

    const userRoleLevel = roleHierarchy[user?.role || 'anonymous'] || 0
    const requiredRoleLevel = roleHierarchy[requiredRole] || 0

    if (userRoleLevel < requiredRoleLevel) {
      return (
        <div className="p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            You don't have permission to access this page.
          </p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Go Home
          </button>
        </div>
      )
    }
  }

  return <>{children}</>
}

