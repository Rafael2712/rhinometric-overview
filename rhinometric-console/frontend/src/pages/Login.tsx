import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Activity, LogIn } from 'lucide-react'

/**
 * Login page - Phase 1: Keycloak OIDC redirect.
 * If OIDC is enabled, shows a "Sign in with SSO" button that redirects to Keycloak.
 * Falls back to legacy login form if OIDC is disabled.
 */
export function LoginPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Login'
  }, [])

  const navigate = useNavigate()
  const {
    isAuthenticated,
    mustChangePassword,
    authMode,
    loginWithKeycloak,
  } = useAuthStore()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !mustChangePassword) {
      navigate('/', { replace: true })
    } else if (isAuthenticated && mustChangePassword) {
      navigate('/change-password', { replace: true })
    }
  }, [isAuthenticated, mustChangePassword, navigate])

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

          {authMode === 'oidc' ? (
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
          ) : (
            <LegacyLoginForm />
          )}
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          &copy; {new Date().getFullYear()} Rhinometric. All rights reserved.
        </p>
      </div>
    </div>
  )
}

/**
 * Legacy login form (fallback when OIDC is disabled).
 */
import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

function LegacyLoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
    } catch {
      setError('Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-text-secondary mb-2">
          Email or Username
        </label>
        <input
          id="username"
          type="text"
          className="input w-full"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter your email or username"
          required
          autoComplete="email username"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            className="input w-full pr-10"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-error/10 border border-error text-error px-4 py-2 rounded-md text-sm">
          {error}
        </div>
      )}

      <button type="submit" className="btn btn-primary w-full" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  )
}
