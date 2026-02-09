import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Activity, Eye, EyeOff, Mail } from 'lucide-react'

export function LoginPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Login'
  }, [])
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showForgotModal, setShowForgotModal] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotSuccess, setForgotSuccess] = useState(false)
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
        setForgotSuccess(true)
        setTimeout(() => {
          setShowForgotModal(false)
          setForgotEmail('')
          setForgotSuccess(false)
        }, 3000)
      } else {
        setForgotError('An error occurred. Please try again.')
      }
    } catch (err) {
      setForgotError('Network error. Please try again.')
    } finally {
      setForgotLoading(false)
    }
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
              onClick={() => setShowForgotModal(true)}
            >
              ¿Olvidó su contraseña?
            </button>
          </div>
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          © 2025 Rhinometric. All rights reserved.
        </p>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background-secondary rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-primary/20 rounded-lg p-2">
                <Mail className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Restablecer Contraseña</h2>
                <p className="text-sm text-text-muted">Ingresa tu correo electrónico para recibir el enlace</p>
              </div>
            </div>

            {!forgotSuccess ? (
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <div>
                  <label htmlFor="forgot-email" className="block text-sm font-medium text-text-secondary mb-2">
                    Correo Electrónico
                  </label>
                  <input
                    id="forgot-email"
                    type="email"
                    className="input w-full"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    placeholder="tucorreo@ejemplo.com"
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
                    onClick={() => {
                      setShowForgotModal(false)
                      setForgotEmail('')
                      setForgotError('')
                    }}
                    className="btn btn-secondary flex-1"
                    disabled={forgotLoading}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary flex-1"
                    disabled={forgotLoading}
                  >
                    {forgotLoading ? 'Enviando...' : 'Enviar Enlace'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="bg-success/10 border border-success text-success px-4 py-3 rounded-md">
                  <p className="font-medium">¡Revisa tu correo!</p>
                  <p className="text-sm mt-1">
                    Si tu correo está registrado, recibirás el enlace de restablecimiento en breve.
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowForgotModal(false)
                    setForgotEmail('')
                    setForgotSuccess(false)
                  }}
                  className="btn btn-primary w-full"
                >
                  Cerrar
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
