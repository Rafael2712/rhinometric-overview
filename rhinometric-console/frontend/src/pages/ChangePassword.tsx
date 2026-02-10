import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Lock, CheckCircle2, AlertCircle } from 'lucide-react'

export function ChangePasswordPage() {
  useEffect(() => {
    document.title = 'Change Password - Rhinometric'
  }, [])

  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { token, logout } = useAuthStore()

  // Password validation helpers
  const isLengthValid = newPassword.length >= 8
  const hasUppercase = /[A-Z]/.test(newPassword)
  const hasLowercase = /[a-z]/.test(newPassword)
  const hasNumber = /[0-9]/.test(newPassword)
  const passwordsMatch = newPassword === confirmPassword && newPassword.length > 0

  const isFormValid = isLengthValid && hasUppercase && hasLowercase && hasNumber && passwordsMatch

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (!isFormValid) {
      setError('Please meet all password requirements')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to change password')
      }

      setSuccess(true)
      
      // Redirect to home after 2 seconds
      setTimeout(() => {
        navigate('/', { replace: true })
      }, 2000)

    } catch (err: any) {
      setError(err.message || 'Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex flex-col items-center mb-8">
            <div className="bg-warning rounded-lg p-3 mb-4">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Change Password Required</h1>
            <p className="text-text-muted mt-2 text-center">
              For security reasons, you must change your password before continuing
            </p>
          </div>

          {success ? (
            <div className="bg-success/10 border border-success text-success px-4 py-3 rounded-md mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              <div>
                <p className="font-medium">Password changed successfully!</p>
                <p className="text-sm">Redirecting to dashboard...</p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="oldPassword" className="block text-sm font-medium text-text-secondary mb-2">
                  Current Password
                </label>
                <input
                  id="oldPassword"
                  type="password"
                  className="input w-full"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="newPassword" className="block text-sm font-medium text-text-secondary mb-2">
                  New Password
                </label>
                <input
                  id="newPassword"
                  type="password"
                  className="input w-full"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  required
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-secondary mb-2">
                  Confirm New Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  className="input w-full"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  required
                  disabled={loading}
                />
              </div>

              {/* Password Requirements */}
              <div className="bg-surface-light p-4 rounded-md space-y-2">
                <p className="text-sm font-medium text-text-secondary mb-2">Password Requirements:</p>
                <div className="space-y-1 text-sm">
                  <div className={`flex items-center gap-2 ${isLengthValid ? 'text-success' : 'text-text-muted'}`}>
                    {isLengthValid ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>At least 8 characters</span>
                  </div>
                  <div className={`flex items-center gap-2 ${hasUppercase ? 'text-success' : 'text-text-muted'}`}>
                    {hasUppercase ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>At least one uppercase letter</span>
                  </div>
                  <div className={`flex items-center gap-2 ${hasLowercase ? 'text-success' : 'text-text-muted'}`}>
                    {hasLowercase ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>At least one lowercase letter</span>
                  </div>
                  <div className={`flex items-center gap-2 ${hasNumber ? 'text-success' : 'text-text-muted'}`}>
                    {hasNumber ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>At least one number</span>
                  </div>
                  <div className={`flex items-center gap-2 ${passwordsMatch ? 'text-success' : 'text-text-muted'}`}>
                    {passwordsMatch ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>Passwords match</span>
                  </div>
                </div>
              </div>

              {error && (
                <div className="bg-error/10 border border-error text-error px-4 py-2 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="btn btn-primary flex-1"
                  disabled={loading || !isFormValid}
                >
                  {loading ? 'Changing Password...' : 'Change Password'}
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn bg-surface-light text-text-secondary hover:bg-surface"
                  disabled={loading}
                >
                  Logout
                </button>
              </div>
            </form>
          )}
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          © 2025 Rhinometric. All rights reserved.
        </p>
      </div>
    </div>
  )
}
