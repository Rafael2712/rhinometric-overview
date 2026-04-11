import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Activity, LogIn } from 'lucide-react'

/**
 * Login page — Keycloak SSO only.
 * Redirects to Keycloak for authentication.
 */
export function LoginPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Login'
  }, [])

  const navigate = useNavigate()
  const {
    isAuthenticated,
    authMode,
    loginWithKeycloak,
  } = useAuthStore()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  // Show loading while OIDC initializes
  if (authMode === 'initializing') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-gray-400 text-sm">Initializing authentication...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex flex-col items-center mb-8">
            <div className="bg-primary rounded-lg p-3 mb-4">
              <Activity className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Rhinometric</h1>
            <p className="text-text-muted mt-2">AI-Powered Observability Platform</p>
          </div>

          <div className="space-y-4">
            <button
              onClick={loginWithKeycloak}
              className="btn btn-primary w-full flex items-center justify-center gap-2"
            >
              <LogIn className="w-5 h-5" />
              Sign in with SSO
            </button>
            <p className="text-center text-text-muted text-xs">
              You will be redirected to the identity provider
            </p>
          </div>
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          &copy; {new Date().getFullYear()} Rhinometric. All rights reserved.
        </p>
      </div>
    </div>
  )
}
