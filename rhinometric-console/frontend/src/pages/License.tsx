import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  AlertTriangle,
  Globe,
  ChevronDown,
  ChevronRight,
  Package,
  Clock,
  Building2,
  Info,
  XCircle,
  Users,
  Crown,
  Shield,
  Wrench,
  Eye,
  Zap,
  TrendingUp,
  DollarSign,
} from 'lucide-react'
import type { LicenseStatusResponse } from '../types/license'

// ==================================================================
// HELPERS
// ==================================================================

function formatDate(iso: string | null | undefined): string {
  if (!iso) return 'N/A'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    })
  } catch {
    return iso
  }
}

function getBarColor(used: number, max: number): string {
  if (max <= 0) return 'bg-primary'
  const ratio = used / max
  if (ratio >= 1) return 'bg-error'
  if (ratio >= 0.8) return 'bg-warning'
  return 'bg-primary'
}

function getBarPercent(used: number, max: number): number {
  if (max <= 0) return 0
  return Math.min((used / max) * 100, 100)
}

function getStatusColor(used: number, limit: number): string {
  if (limit <= 0) return 'text-text-muted'
  const ratio = used / limit
  if (ratio >= 1) return 'text-error'
  if (ratio >= 0.8) return 'text-warning'
  return 'text-success'
}

function getPlanLabel(data: LicenseStatusResponse): string {
  if (data.edition === 'community_trial') {
    return `${data.plan_display} (Trial)`
  }
  return data.plan_display
}

function getUsageBadge(status: string): { label: string; cls: string } {
  switch (status) {
    case 'exceeded':
      return { label: 'Limit exceeded', cls: 'bg-error/15 text-error border-error/30' }
    case 'warning':
      return { label: 'Approaching limit', cls: 'bg-warning/15 text-warning border-warning/30' }
    default:
      return { label: 'Within plan', cls: 'bg-success/15 text-success border-success/30' }
  }
}

// ==================================================================
// STATUS CONFIG
// ==================================================================

interface StatusConfig {
  icon: React.ReactNode
  title: string
  description: string
  borderClass: string
  bgClass: string
  textClass: string
}

function getStatusConfig(status: string, reason?: string): StatusConfig {
  switch (status) {
    case 'active':
    case 'valid':
      return {
        icon: <ShieldCheck className="w-6 h-6 text-success" />,
        title: 'Active License',
        description: reason || 'License is valid and operational.',
        borderClass: 'border-success/30',
        bgClass: 'bg-success/10',
        textClass: 'text-success',
      }
    case 'about_to_expire':
      return {
        icon: <ShieldAlert className="w-6 h-6 text-warning" />,
        title: 'About to expire',
        description: reason || 'License is valid but expires soon.',
        borderClass: 'border-warning/30',
        bgClass: 'bg-warning/10',
        textClass: 'text-warning',
      }
    case 'expired':
      return {
        icon: <ShieldX className="w-6 h-6 text-error" />,
        title: 'Expired License',
        description: reason || 'License has expired.',
        borderClass: 'border-error/30',
        bgClass: 'bg-error/10',
        textClass: 'text-error',
      }
    case 'invalid':
      return {
        icon: <XCircle className="w-6 h-6 text-error" />,
        title: 'Invalid License',
        description: reason || 'Incorrect signature or unrecognized format.',
        borderClass: 'border-error/30',
        bgClass: 'bg-error/10',
        textClass: 'text-error',
      }
    default:
      return {
        icon: <AlertTriangle className="w-6 h-6 text-warning" />,
        title: 'License service unavailable',
        description: reason || 'Could not contact the license service.',
        borderClass: 'border-warning/30',
        bgClass: 'bg-warning/10',
        textClass: 'text-warning',
      }
  }
}

// ==================================================================
// MAIN COMPONENT
// ==================================================================

export function LicensePage() {
  useEffect(() => {
    document.title = 'Rhinometric - License Management'
  }, [])

  const token = useAuthStore((s) => s.token)
  const isAdmin = useAuthStore((s) => s.isAdmin)
  const [techOpen, setTechOpen] = useState(false)

  const { data, isLoading, error } = useQuery<LicenseStatusResponse>({
    queryKey: ['license', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      const response = await fetch('/api/license/status', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        if (response.status === 503) throw new Error('LICENSE_SERVICE_UNAVAILABLE')
        throw new Error('LICENSE_FETCH_FAILED')
      }
      return response.json()
    },
    enabled: !!token,
    retry: 1,
  })

  // Loading
  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
              <p className="text-text-muted">Checking license...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error
  if (error || !data) {
    const cfg = getStatusConfig('error')
    return (
      <div className="space-y-6">
        <PageHeader />
        <StatusCard config={cfg}>
          <ul className="list-disc list-inside text-warning/80 space-y-1 mb-4 text-sm">
            <li>The license validator is not responding</li>
            <li>Network connectivity issues</li>
          </ul>
          <ContactSupportButton
            subject="License service unavailable"
            body={`Error: ${error?.message || 'unknown'}`}
          />
        </StatusCard>
      </div>
    )
  }

  // Expired
  if (data.status === 'expired') {
    const cfg = getStatusConfig('expired', data.message)
    return (
      <div className="space-y-6">
        <PageHeader />
        <StatusCard config={cfg}>
          <div className="grid grid-cols-2 gap-3 text-sm mb-4">
            <div>
              <p className="text-text-muted">Organization</p>
              <p className="text-gray-900 font-medium">{data.organization || '\u2014'}</p>
            </div>
            <div>
              <p className="text-text-muted">Plan</p>
              <p className="text-gray-900 font-medium">{getPlanLabel(data)}</p>
            </div>
            <div>
              <p className="text-text-muted">Expired on</p>
              <p className="text-error font-medium">{formatDate(data.expires_at)}</p>
            </div>
          </div>
          <p className="text-error/80 text-sm mb-4">
            System operates in degraded mode. Contact support to renew your license.
          </p>
          <ContactSupportButton
            subject="Expired license renewal"
            body={`Tenant: ${data.tenant_id || 'N/A'}\nExpired: ${formatDate(data.expires_at)}`}
          />
        </StatusCard>
      </div>
    )
  }

  // Normalize status for display
  const displayStatus = data.days_remaining != null && data.days_remaining <= 30 && data.is_valid
    ? 'about_to_expire'
    : (data.is_valid ? 'active' : data.status)
  const cfg = getStatusConfig(displayStatus, data.message)
  const usageBadge = getUsageBadge(data.usage_status)

  return (
    <div className="space-y-4 sm:space-y-6">
      <PageHeader />

      {/* Warnings / Breaches */}
      {data.breaches && data.breaches.length > 0 && (
        <div className="card bg-error/10 border-error/30">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-error flex-shrink-0 mt-0.5" size={20} />
            <div>
              <p className="text-error font-semibold text-sm mb-1">Limit Exceeded</p>
              {data.breaches.map((b: string, i: number) => (
                <p key={i} className="text-error/80 text-sm">{b}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {data.warning && !data.breaches && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-warning flex-shrink-0" size={20} />
            <p className="text-warning font-medium text-sm">{data.warning}</p>
          </div>
        </div>
      )}

      {displayStatus === 'about_to_expire' && !data.warning && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <Clock className="text-warning flex-shrink-0" size={20} />
            <p className="text-warning font-medium text-sm">
              License expires in {data.days_remaining} days. Contact sales to renew.
            </p>
          </div>
        </div>
      )}

      {/* CARD 1: Plan Info */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-6 gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              {cfg.icon}
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                {getPlanLabel(data)}{' '}
                <span className="text-base font-normal text-text-muted">Plan</span>
              </h2>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bgClass} ${cfg.textClass}`}>
                {cfg.title}
              </span>
              {data.validator && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-text-muted">
                  {data.validator === 'rust' ? 'Ed25519' : 'Legacy'}
                </span>
              )}
            </div>
            {data.organization && (
              <div className="flex items-center gap-1.5 mt-2 text-sm text-text-muted">
                <Building2 className="w-4 h-4 flex-shrink-0" />
                <span>{data.organization}</span>
              </div>
            )}
          </div>
          <div className="p-3 bg-primary/10 rounded-lg self-start flex-shrink-0">
            <ShieldCheck className="w-7 h-7 sm:w-8 sm:h-8 text-primary" />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 sm:gap-6">
          <div className="space-y-1">
            <p className="text-text-muted text-sm">Plan</p>
            <p className="text-gray-900 text-lg font-semibold">{getPlanLabel(data)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-text-muted text-sm">Monthly price</p>
            <p className="text-gray-900 text-lg font-semibold">
              {data.plan_price_monthly}{data.currency === 'EUR' ? '\u20AC' : ` ${data.currency}`}/month
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-text-muted text-sm">Expiration</p>
            <p className="text-gray-900 text-lg font-semibold">{formatDate(data.expires_at)}</p>
            {data.days_remaining != null && (
              <p className={`text-xs ${(data.days_remaining ?? 0) > 30 ? 'text-success' : (data.days_remaining ?? 0) > 7 ? 'text-warning' : 'text-error'}`}>
                {data.days_remaining} days remaining
              </p>
            )}
          </div>
          <div className="space-y-1">
            <p className="text-text-muted text-sm">Edition</p>
            <p className="text-gray-900 text-lg font-semibold">{data.edition}</p>
          </div>
        </div>
      </div>

      {/* CARD 2: Endpoint Usage */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Endpoint Usage</h3>
          </div>
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${usageBadge.cls}`}>
            {usageBadge.label}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-text-muted text-xs mb-1">Used</p>
            <p className="text-2xl font-bold text-gray-900">{data.services_used}</p>
          </div>
          <div>
            <p className="text-text-muted text-xs mb-1">Included</p>
            <p className="text-2xl font-bold text-gray-900">{data.max_services}</p>
          </div>
          <div>
            <p className="text-text-muted text-xs mb-1">Remaining</p>
            <p className={`text-2xl font-bold ${data.remaining_services > 0 ? 'text-success' : 'text-error'}`}>
              {data.remaining_services}
            </p>
          </div>
          <div>
            <p className="text-text-muted text-xs mb-1">Extra in use</p>
            <p className={`text-2xl font-bold ${data.extra_services_used > 0 ? 'text-warning' : 'text-text-muted'}`}>
              {data.extra_services_used}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-50 rounded-full h-2.5 mb-2">
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${getBarColor(data.services_used, data.max_services)}`}
            style={{ width: `${getBarPercent(data.services_used, data.max_services)}%` }}
          />
        </div>
        <p className="text-sm text-text-muted mb-3">
          {data.services_used} / {data.max_services} endpoints used
        </p>

        {/* Pricing info */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 text-sm border-t border-border/30 pt-3">
          <div className="flex items-center gap-1.5 text-text-muted">
            <DollarSign className="w-4 h-4 flex-shrink-0" />
            <span>Extra endpoints: <span className="text-gray-900 font-medium">{data.price_per_extra_service}{data.currency === 'EUR' ? '\u20AC' : ` ${data.currency}`} / endpoint</span></span>
          </div>
          {data.extra_services_used > 0 && (
            <div className="flex items-center gap-1.5 text-warning">
              <TrendingUp className="w-4 h-4 flex-shrink-0" />
              <span className="font-medium">
                Estimated extra cost: {data.estimated_extra_cost}{data.currency === 'EUR' ? '\u20AC' : ` ${data.currency}`}/month
              </span>
            </div>
          )}
        </div>

        {/* Upgrade hint */}
        {(data.usage_status === 'warning' || data.usage_status === 'exceeded') && (
          <p className="text-xs text-text-muted mt-3 italic">
            Consider upgrading your plan to avoid additional costs.
          </p>
        )}
      </div>

      {/* CARD 3: Users */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-primary" />
          <h3 className="text-base sm:text-lg font-semibold text-gray-900">User Limits</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <UserRoleCard icon={<Crown className="w-4 h-4 text-amber-400" />} label="Owner" used={data.users.owner} limit={data.users.owner_limit} />
          <UserRoleCard icon={<Shield className="w-4 h-4 text-blue-400" />} label="Admins" used={data.users.admins_used} limit={data.users.admins_limit} />
          <UserRoleCard icon={<Wrench className="w-4 h-4 text-green-400" />} label="Operators" used={data.users.operators_used} limit={data.users.operators_limit} />
          <UserRoleCard icon={<Eye className="w-4 h-4 text-gray-500" />} label="Viewers" used={data.users.viewers_used} limit={data.users.viewers_limit} />
        </div>
      </div>

      {/* CARD 4: Features */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Package className="w-5 h-5 text-primary" />
          <h3 className="text-base sm:text-lg font-semibold text-gray-900">Enabled Modules</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {(data.features ?? []).map((mod) => (
            <span
              key={mod}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-primary/10 text-primary border border-primary/20"
            >
              <Zap className="w-3 h-3" />
              {mod}
            </span>
          ))}
        </div>
      </div>

      {/* Licensed to */}
      {data.organization && (
        <div className="card bg-primary/5 border-primary/20">
          <p className="text-sm text-text-muted">
            <span className="font-semibold text-primary">Licensed to:</span>{' '}
            {data.organization}
          </p>
        </div>
      )}

      {/* Technical details (admin only) */}
      {isAdmin() && (
        <div className="card">
          <button
            type="button"
            className="flex items-center gap-2 w-full text-left"
            onClick={() => setTechOpen(!techOpen)}
          >
            {techOpen ? <ChevronDown className="w-4 h-4 text-text-muted" /> : <ChevronRight className="w-4 h-4 text-text-muted" />}
            <Info className="w-4 h-4 text-text-muted" />
            <span className="text-sm font-medium text-text-muted">Technical Details</span>
            <span className="text-xs text-text-muted/50 ml-auto">Only visible to Admin / Owner</span>
          </button>
          {techOpen && (
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <p className="text-text-muted">Tenant ID</p>
                  <code className="block bg-gray-50 px-3 py-1.5 rounded text-xs text-primary font-mono break-all mt-1">
                    {data.tenant_id || '\u2014'}
                  </code>
                </div>
                <div>
                  <p className="text-text-muted">Validator</p>
                  <p className="text-gray-900 font-medium">
                    {data.validator === 'rust' ? 'Rust Ed25519 (rhino-lic)' : 'Legacy Server v2'}
                  </p>
                </div>
                <div>
                  <p className="text-text-muted">Status</p>
                  <p className="text-gray-900 font-medium">{data.status}</p>
                </div>
              </div>
              <div>
                <p className="text-text-muted text-sm mb-2">Raw backend response</p>
                <pre className="bg-gray-50 rounded p-3 text-xs text-text-muted font-mono overflow-x-auto max-h-60 overflow-y-auto">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ==================================================================
// SUB-COMPONENTS
// ==================================================================

function PageHeader() {
  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
        License Management
      </h1>
      <p className="text-text-muted text-sm sm:text-base">
        View and manage your Rhinometric instance license
      </p>
    </div>
  )
}

function StatusCard({ config, children }: { config: StatusConfig; children?: React.ReactNode }) {
  return (
    <div className={`card ${config.bgClass} ${config.borderClass}`}>
      <div className="flex items-start gap-3 sm:gap-4">
        <div className="mt-1 flex-shrink-0">{config.icon}</div>
        <div className="flex-1 min-w-0">
          <h3 className={`${config.textClass} font-semibold mb-2 text-base sm:text-lg`}>
            {config.title}
          </h3>
          <p className={`${config.textClass}/80 mb-3 text-sm`}>{config.description}</p>
          {children}
        </div>
      </div>
    </div>
  )
}

function UserRoleCard({
  icon, label, used, limit,
}: {
  icon: React.ReactNode; label: string; used: number; limit: number
}) {
  return (
    <div className="bg-gray-50/50 rounded-lg p-3">
      <div className="flex items-center gap-1.5 mb-2">
        {icon}
        <span className="text-text-muted text-xs">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className={`text-xl font-bold ${getStatusColor(used, limit)}`}>{used}</span>
        <span className="text-text-muted text-sm">/ {limit}</span>
      </div>
      <div className="w-full bg-gray-50 rounded-full h-1.5 mt-2">
        <div
          className={`h-1.5 rounded-full transition-all duration-300 ${getBarColor(used, limit)}`}
          style={{ width: `${getBarPercent(used, limit)}%` }}
        />
      </div>
    </div>
  )
}

function ContactSupportButton({ subject, body }: { subject: string; body: string }) {
  const s = encodeURIComponent(subject)
  const b = encodeURIComponent(`Hello,\n\n${body}\n\nThank you.`)
  return (
    <a
      href={`mailto:support@rhinometric.com?subject=${s}&body=${b}`}
      className="btn btn-secondary text-center"
    >
      Contact Support
    </a>
  )
}
