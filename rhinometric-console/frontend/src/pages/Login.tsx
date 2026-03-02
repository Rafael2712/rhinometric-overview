import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Activity, Eye, EyeOff, Mail, ArrowLeft } from 'lucide-react'

type ViewMode = 'login' | 'forgot-password'

export function LoginPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Login'
  }, [])

  const [view, setView] = useState<ViewMode>('login')

  // Login state
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Forgot password state
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotSuccess, setForgotSuccess] = useState(false)
  const [emailAvailable, setEmailAvailable] = useState(true)
  const [forgotError, setForgotError] = useState('')

  const navigate = useNavigate()
  const { login, isAuthenticated, mustChangePassword } = useAuthStore()

  // Redirect to home if already authenticated
  useEffect(() => {
    if (isAuthenticated && !mustChangePassword) {
      navigate('/', { replace: true })
    } else if (isAuthenticated && mustChangePassword) {
      navigate('/change-password', { replace: true })
    }
  }, [isAuthenticated, mustChangePassword, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      // Navigation handled by useEffect after login
    } catch (err) {
      setError('Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setForgotError('')
    setForgotSuccess(false)
    setForgotLoading(true)

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail })
      })

      if (response.ok) {
        const data = await response.json()
        setEmailAvailable(data.email_available !== false)
        setForgotSuccess(true)
      } else if (response.status === 422) {
        setForgotError('Please enter a valid email address.')
      } else if (response.status === 429) {
        setForgotError('Too many requests. Please wait a few minutes before trying again.')
      } else {
        // Even on server error, show generic message for security
        setForgotSuccess(true)
      }
    } catch (err) {
      setForgotError('Network error. Please check your connection and try again.')
    } finally {
      setForgotLoading(false)
    }
  }

  const switchToForgot = () => {
    setView('forgot-password')
    setForgotEmail('')
    setForgotError('')
    setForgotSuccess(false)
    setEmailAvailable(true)
  }

  const switchToLogin = () => {
    setView('login')
    setForgotEmail('')
    setForgotError('')
    setForgotSuccess(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md">
        {view === 'login' && (
          <div className="card">
            <div className="flex flex-col items-center mb-8">
              <div className="bg-primary rounded-lg p-3 mb-4">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-white">Rhinometric</h1>
              <p className="text-text-muted mt-2">AI-Powered Observability Platform</p>
            </div>

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
                    type={showPassword ? "text" : "password"}
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
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-error/10 border border-error text-error px-4 py-2 rounded-md text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="btn btn-primary w-full"
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                className="text-sm text-primary hover:text-primary-dark transition-colors"
                onClick={switchToForgot}
              >
                Forgot your password?
              </button>
            </div>
          </div>
        )}

        {view === 'forgot-password' && (
          <div className="card">
            <div className="flex flex-col items-center mb-8">
              <div className="bg-primary/20 rounded-lg p-3 mb-4">
                <Mail className="w-8 h-8 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-white">Reset Password</h1>
              <p className="text-text-muted mt-2">Enter your email to receive a reset link</p>
            </div>

            {!forgotSuccess ? (
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div>
                  <label htmlFor="forgot-email" className="block text-sm font-medium text-text-secondary mb-2">
                    Email Address
                  </label>
                  <input
                    id="forgot-email"
                    type="email"
                    className="input w-full"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    autoFocus
                  />
                </div>

                {forgotError && (
                  <div className="bg-error/10 border border-error text-error px-4 py-2 rounded-md text-sm">
                    {forgotError}
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={switchToLogin}
                    className="btn btn-secondary flex-1"
                    disabled={forgotLoading}
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary flex-1"
                    disabled={forgotLoading}
                  >
                    {forgotLoading ? 'Sending...' : 'Send Reset Link'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                {emailAvailable ? (
                  <div className="bg-success/10 border border-success text-success px-4 py-3 rounded-md">
                    <p className="font-medium">Check your inbox</p>
                    <p className="text-sm mt-1">
                      If an account exists with that email, you will receive a password reset link shortly.
                    </p>
                  </div>
                ) : (
                  <div className="bg-warning/10 border border-warning text-warning px-4 py-3 rounded-md">
                    <p className="font-medium">Email service unavailable</p>
                    <p className="text-sm mt-1">
                      The email delivery system is currently not available.
                      Please contact your system administrator to reset your password.
                    </p>
                  </div>
                )}
                <button
                  onClick={switchToLogin}
                  className="btn btn-primary w-full"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Sign In
                </button>
              </div>
            )}
          </div>
        )}

        <p className="text-center text-text-muted text-sm mt-6">
          &copy; {new Date().getFullYear()} Rhinometric. All rights reserved.
        </p>
      </div>
    </div>
  )
}
