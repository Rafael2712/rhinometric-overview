import { CreditCard, Calendar, Server, CheckCircle, AlertTriangle } from 'lucide-react'
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'

export function LicensePage() {
  useEffect(() => {
    document.title = 'Rhinometric - License Management'
  }, [])

  const token = useAuthStore((state) => state.token)

  // Fetch real license data from backend
  const { data: license, isLoading, error } = useQuery({
    queryKey: ['license', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      
      const response = await fetch('/api/license/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        if (response.status === 503) {
          throw new Error('License service unavailable')
        }
        throw new Error('Failed to fetch license')
      }
      return response.json()
    },
    enabled: !!token,
    retry: 1,
  })

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">License Management</h1>
          <p className="text-text-muted">View and manage your Rhinometric license</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-muted">Loading license information...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error state - License service unavailable
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">License Management</h1>
          <p className="text-text-muted">View and manage your Rhinometric license</p>
        </div>
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-start gap-4">
            <AlertTriangle className="text-warning mt-1" size={32} />
            <div className="flex-1">
              <h3 className="text-warning font-semibold mb-2 text-lg">License Service Unavailable</h3>
              <p className="text-warning/80 mb-3">
                The License Validator service is not configured or currently unavailable. 
                This could mean:
              </p>
              <ul className="list-disc list-inside text-warning/80 space-y-1 mb-4">
                <li>License Validator is not running (port 8091)</li>
                <li>AWS License Validator is not connected</li>
                <li>Network connectivity issues</li>
              </ul>
              <p className="text-warning/80 text-sm">
                <strong>Note:</strong> Please contact your system administrator or Rhinometric support 
                to configure the licensing module.
              </p>
              <div className="mt-4">
                <a 
                  href="mailto:support@rhinometric.com?subject=License%20Configuration%20Required&body=Hello%2C%0A%0AI%20need%20help%20configuring%20the%20License%20Validator%20service.%0A%0AError%3A%20{error.message}%0A%0AThank%20you!"
                  className="btn btn-warning"
                >
                  Contact Support
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Success state - Show real license data
  const getTierDisplayName = (tier: string) => {
    const tierNames: Record<string, string> = {
      'demo_cloud': 'Demo Cloud',
      'trial': 'Trial',
      'annual_standard': 'Annual Standard',
      'enterprise': 'Enterprise'
    }
    return tierNames[tier] || tier
  }

  const getStatusColor = (status: string) => {
    if (status === 'active') return 'text-success'
    if (status === 'expired') return 'text-error'
    if (status === 'not_activated') return 'text-warning'
    if (status === 'over_limit') return 'text-error'
    return 'text-text-muted'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'active') return <CheckCircle className="w-5 h-5 text-success" />
    return <AlertTriangle className="w-5 h-5 text-warning" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">License Management</h1>
        <p className="text-text-muted">View and manage your Rhinometric license</p>
      </div>

      {/* Warning Banner */}
      {license.warning && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-warning" size={24} />
            <p className="text-warning font-medium">{license.warning}</p>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">{getTierDisplayName(license.tier)} License</h2>
            <div className="flex items-center space-x-2">
              {getStatusIcon(license.status)}
              <span className={`font-medium capitalize ${getStatusColor(license.status)}`}>
                {license.status.replace('_', ' ')}
              </span>
            </div>
            <p className="text-text-muted text-sm mt-1">{license.message}</p>
          </div>
          <div className="p-3 bg-primary/10 rounded-lg">
            <CreditCard className="w-8 h-8 text-primary" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="flex items-center text-text-muted text-sm mb-2">
              <Server className="w-4 h-4 mr-2" />
              <span>Hosts Usage</span>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-bold text-white">{license.hosts_used}</span>
              <span className="text-text-muted">/ {license.max_hosts}</span>
            </div>
            <div className="w-full bg-surface-light rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  license.hosts_used >= license.max_hosts ? 'bg-error' : 
                  license.hosts_used >= license.max_hosts * 0.8 ? 'bg-warning' : 'bg-primary'
                }`} 
                style={{ width: `${Math.min((license.hosts_used / license.max_hosts) * 100, 100)}%` }} 
              />
            </div>
            <p className="text-xs text-text-muted">{license.hosts_available} hosts available</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center text-text-muted text-sm mb-2">
              <Calendar className="w-4 h-4 mr-2" />
              <span>Expiration Date</span>
            </div>
            <p className="text-xl font-semibold text-white">
              {license.expires_at ? new Date(license.expires_at).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              }) : 'N/A'}
            </p>
            {license.tier === 'demo_cloud' && license.hours_remaining !== null ? (
              <p className={`text-sm ${license.hours_remaining > 2 ? 'text-success' : 'text-error'}`}>
                {license.hours_remaining} hours remaining
              </p>
            ) : (
              <p className={`text-sm ${
                license.days_remaining > 30 ? 'text-success' : 
                license.days_remaining > 7 ? 'text-warning' : 'text-error'
              }`}>
                {license.days_remaining} days remaining
              </p>
            )}
          </div>

          <div className="space-y-3">
            <div className="text-sm text-text-muted">
              <p><strong>License Key:</strong></p>
              <code className="block bg-surface-light px-3 py-2 rounded mt-1 text-xs text-primary font-mono">
                {license.license_key}
              </code>
            </div>
            {license.activated_at && (
              <p className="text-xs text-text-muted">
                Activated: {new Date(license.activated_at).toLocaleDateString('en-US', { 
                  year: 'numeric', 
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            )}
            <a 
              href={`mailto:sales@rhinometric.com?subject=License%20Upgrade%20Request&body=Hello%2C%0A%0AI%20would%20like%20to%20upgrade%20my%20Rhinometric%20license.%0A%0ACurrent%20Tier%3A%20${getTierDisplayName(license.tier)}%0AOrganization%3A%20${license.organization || 'N/A'}%0AHosts%3A%20${license.hosts_used}%2F${license.max_hosts}%0A%0AThank%20you!`}
              className="btn btn-primary w-full block text-center"
            >
              Upgrade License
            </a>
            <a 
              href="mailto:sales@rhinometric.com?subject=Sales%20Inquiry&body=Hello%2C%0A%0AI%20would%20like%20to%20discuss%20Rhinometric%20licensing%20options.%0A%0AThank%20you!"
              className="btn btn-secondary w-full block text-center"
            >
              Contact Sales
            </a>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">License Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-text-muted">Tier</p>
            <p className="text-white font-medium">{getTierDisplayName(license.tier)}</p>
          </div>
          <div>
            <p className="text-text-muted">Status</p>
            <p className={`font-medium capitalize ${getStatusColor(license.status)}`}>
              {license.status.replace('_', ' ')}
            </p>
          </div>
          <div>
            <p className="text-text-muted">Issued Date</p>
            <p className="text-white">
              {new Date(license.issued_at).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
          <div>
            <p className="text-text-muted">Max Hosts</p>
            <p className="text-white font-medium">{license.max_hosts}</p>
          </div>
        </div>
      </div>

      {license.organization && (
        <div className="card bg-primary/5 border-primary/20">
          <p className="text-sm text-text-muted">
            <span className="font-semibold text-primary">Licensed to:</span> {license.organization}
            {license.organization_email && (
              <span className="text-text-muted ml-2">({license.organization_email})</span>
            )}
          </p>
        </div>
      )}
    </div>
  )
}
