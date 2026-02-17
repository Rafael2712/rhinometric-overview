import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  AlertTriangle,
  Server,
  Calendar,
  ChevronDown,
  ChevronRight,
  Package,
  Clock,
  Building2,
  Info,
  XCircle,
  FileQuestion,
} from 'lucide-react'
import type {
  LicensePayload,
  LicenseStatusResponse,
  LicenseStatus,
  LicenseEdition,
  LicenseModule,
} from '../types/license'

// ================================================================
// ADAPTER: Maps current backend response -> LicenseStatusResponse
// TODO: Remove when backend returns the new schema directly.
// ================================================================

const KNOWN_MODULES: LicenseModule[] = ['core', 'ai_anomalies', 'dashboards', 'veriverde']

function mapBackendResponse(raw: Record<string, unknown>): LicenseStatusResponse {
  let status: LicenseStatus
  const rawStatus = raw.status as string
  const isValid = raw.is_valid as boolean

  if (isValid && rawStatus === 'active') {
    const days = raw.days_remaining as number | null
    status = (days != null && days <= 30) ? 'about_to_expire' : 'valid'
  } else if (rawStatus === 'expired') {
    status = 'expired'
  } else if (['invalid_signature', 'fingerprint_mismatch', 'parse_error'].includes(rawStatus)) {
    status = 'invalid'
  } else if (rawStatus === 'over_limit') {
    status = 'valid'
  } else {
    status = 'error'
  }

  const rawFeatures = raw.features as string[] | null
  const modules: LicenseModule[] =
    Array.isArray(rawFeatures) && rawFeatures.length > 0
      ? (rawFeatures.filter((f) => KNOWN_MODULES.includes(f as LicenseModule)) as LicenseModule[])
      : ['core'] // TODO: fallback until backend sends modules

  const license: LicensePayload = {
    license_id: (raw.tenant_id || raw.license_key || '') as string,
    customer_name: (raw.organization || '') as string,
    customer_contact: raw.organization_email as string | undefined,
    edition: ((raw.tier || 'trial') as LicenseEdition),
    max_hosts: (raw.max_hosts ?? 0) as number,
    modules,
    issued_at: (raw.issued_at || '') as string,
    valid_from: (raw.issued_at || '') as string,     // TODO: use valid_from when available
    valid_until: (raw.expires_at || '') as string,
    install_id: raw.tenant_id as string | undefined,
  }

  return {
    status,
    reason: raw.message as string | undefined,
    license,
    hosts_used: (raw.hosts_used ?? 0) as number,
    hosts_available: (raw.hosts_available ?? 0) as number,
    days_remaining: raw.days_remaining as number | undefined,
    hours_remaining: raw.hours_remaining as number | undefined,
    warning: raw.warning as string | undefined,
    validator: raw.validator as string | undefined,
  }
}

// ================================================================
// HELPERS
// ================================================================

const EDITION_LABELS: Record<string, string> = {
  demo_cloud: 'Demo Cloud',
  trial: 'Trial',
  annual_standard: 'Annual Standard',
  enterprise: 'Enterprise',
}

const MODULE_LABELS: Record<LicenseModule, string> = {
  core: 'Core',
  ai_anomalies: 'AI Anomalies',
  dashboards: 'Dashboards',
  veriverde: 'VeriVerde',
}

function formatDate(iso: string | undefined): string {
  if (!iso) return 'N/A'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    })
  } catch {
    return iso
  }
}

function getHostBarColor(used: number, max: number): string {
  if (max <= 0) return 'bg-primary'
  const ratio = used / max
  if (ratio >= 1) return 'bg-error'
  if (ratio >= 0.8) return 'bg-warning'
  return 'bg-primary'
}

// ================================================================
// STATUS-SPECIFIC UI CONFIGS
// ================================================================

interface StatusConfig {
  icon: React.ReactNode
  title: string
  description: string
  borderClass: string
  bgClass: string
  textClass: string
}

function getStatusConfig(status: LicenseStatus, reason?: string): StatusConfig {
  switch (status) {
    case 'valid':
      return {
        icon: <ShieldCheck className="w-6 h-6 text-success" />,
        title: 'Active license',
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
        title: 'Expired license',
        description: reason || 'License has expired. System operates in degraded mode.',
        borderClass: 'border-error/30',
        bgClass: 'bg-error/10',
        textClass: 'text-error',
      }
    case 'invalid':
      return {
        icon: <XCircle className="w-6 h-6 text-error" />,
        title: 'Invalid license',
        description: reason || 'Incorrect signature or unrecognized format.',
        borderClass: 'border-error/30',
        bgClass: 'bg-error/10',
        textClass: 'text-error',
      }
    case 'missing':
      return {
        icon: <FileQuestion className="w-6 h-6 text-warning" />,
        title: 'License not found',
        description: reason || 'No valid license found installed.',
        borderClass: 'border-warning/30',
        bgClass: 'bg-warning/10',
        textClass: 'text-warning',
      }
    case 'error':
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

// ================================================================
// COMPONENT
// ================================================================

export function LicensePage() {
  useEffect(() => {
    document.title = 'Rhinometric - License Management'
  }, [])

  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const [techOpen, setTechOpen] = useState(false)

  const {
    data: rawData,
    isLoading,
    error,
  } = useQuery({
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
              <p className="text-text-muted">Checking license…</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !rawData) {
    const cfg = getStatusConfig('error')
    return (
      <div className="space-y-6">
        <PageHeader />
        <StatusCard config={cfg}>
          <ul className="list-disc list-inside text-warning/80 space-y-1 mb-4 text-sm">
            <li>The license validator (port 8091) is not responding</li>
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

  const data = mapBackendResponse(rawData as Record<string, unknown>)
  const { license } = data

  if (data.status === 'invalid') {
    const cfg = getStatusConfig('invalid', data.reason)
    return (
      <div className="space-y-6">
        <PageHeader />
        <StatusCard config={cfg}>
          <p className="text-error/80 text-sm mb-4">
            The cryptographic signature does not match or the license file has an unrecognized format.
            Verify that the <code className="bg-surface-light px-1 rounded">license.key</code> no
            haya sido modificado manualmente.
          </p>
          <ContactSupportButton
            subject="Invalid license"
            body={`Reason: ${data.reason || 'Signature or unrecognized format'}`}
          />
        </StatusCard>
      </div>
    )
  }

  if (data.status === 'expired') {
    const cfg = getStatusConfig('expired', data.reason)
    return (
      <div className="space-y-6">
        <PageHeader />
        <StatusCard config={cfg}>
          {license && (
            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <p className="text-text-muted">Customer</p>
                <p className="text-white font-medium">{license.customer_name || "—"}</p>
              </div>
              <div>
                <p className="text-text-muted">Edition</p>
                <p className="text-white font-medium">
                  {EDITION_LABELS[license.edition] || license.edition}
                </p>
              </div>
              <div>
                <p className="text-text-muted">Expired on</p>
                <p className="text-error font-medium">{formatDate(license.valid_until)}</p>
              </div>
              <div>
                <p className="text-text-muted">Max Hosts</p>
                <p className="text-white font-medium">{license.max_hosts}</p>
              </div>
            </div>
          )}
          <p className="text-error/80 text-sm mb-4">
            System operates in degraded mode. Contact support to renew your license.
          </p>
          <div className="flex flex-col sm:flex-row gap-2">
            <ContactSupportButton
              subject="Expired license renewal"
              body={`License: ${license?.license_id || 'N/A'}\nExpired: ${formatDate(license?.valid_until)}`}
            />
          </div>
        </StatusCard>
        {isAdmin() && license && (
          <TechnicalDetails license={license} data={data} rawData={rawData} techOpen={techOpen} setTechOpen={setTechOpen} />
        )}
      </div>
    )
  }

  const cfg = getStatusConfig(data.status, data.reason)

  return (
    <div className="space-y-4 sm:space-y-6">
      <PageHeader />

      {data.warning && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <AlertTriangle className="text-warning flex-shrink-0" size={24} />
            <p className="text-warning font-medium text-sm sm:text-base">{data.warning}</p>
          </div>
        </div>
      )}

      {data.status === 'about_to_expire' && !data.warning && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <Clock className="text-warning flex-shrink-0" size={24} />
            <p className="text-warning font-medium text-sm sm:text-base">
              License expires in {data.days_remaining} days. Contact sales to renew.
            </p>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-6 gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              {cfg.icon}
              <h2 className="text-xl sm:text-2xl font-bold text-white">
                {EDITION_LABELS[license?.edition ?? ''] || license?.edition || 'License'}{' '}
                <span className="text-base font-normal text-text-muted">License</span>
              </h2>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bgClass} ${cfg.textClass}`}
              >
                {cfg.title}
              </span>
              {data.validator && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-surface-light text-text-muted">
                  {data.validator === 'rust' ? 'Ed25519' : 'Legacy'}
                </span>
              )}
            </div>
            {license?.customer_name && (
              <div className="flex items-center gap-1.5 mt-2 text-sm text-text-muted">
                <Building2 className="w-4 h-4 flex-shrink-0" />
                <span>{license.customer_name}</span>
                {license.customer_contact && (
                  <span className="text-text-muted/70">({license.customer_contact})</span>
                )}
              </div>
            )}
          </div>
          <div className="p-3 bg-primary/10 rounded-lg self-start flex-shrink-0">
            <ShieldCheck className="w-7 h-7 sm:w-8 sm:h-8 text-primary" />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          <div className="space-y-2">
            <div className="flex items-center text-text-muted text-sm mb-2">
              <Server className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>Host Usage</span>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl sm:text-3xl font-bold text-white">{data.hosts_used}</span>
              <span className="text-text-muted">/ {license?.max_hosts ?? 0}</span>
            </div>
            <div className="w-full bg-surface-light rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${getHostBarColor(data.hosts_used, license?.max_hosts ?? 0)}`}
                style={{
                  width: `${Math.min(((data.hosts_used / (license?.max_hosts || 1)) * 100), 100)}%`,
                }}
              />
            </div>
            <p className="text-xs text-text-muted">{data.hosts_available} hosts available</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center text-text-muted text-sm mb-2">
              <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>Expiration Date</span>
            </div>
            <p className="text-lg sm:text-xl font-semibold text-white">
              {formatDate(license?.valid_until)}
            </p>
            {license?.edition === 'demo_cloud' && data.hours_remaining != null ? (
              <p className={`text-sm ${(data.hours_remaining ?? 0) > 2 ? 'text-success' : 'text-error'}`}>
                {data.hours_remaining} hours remaining
              </p>
            ) : (
              data.days_remaining != null && (
                <p
                  className={`text-sm ${(data.days_remaining ?? 0) > 30 ? 'text-success' : (data.days_remaining ?? 0) > 7 ? 'text-warning' : 'text-error'}`}
                >
                  {data.days_remaining} days remaining
                </p>
              )
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center text-text-muted text-sm mb-2">
              <Package className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>Enabled Modules</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {(license?.modules ?? ['core']).map((mod) => (
                <span
                  key={mod}
                  className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary border border-primary/20"
                >
                  {MODULE_LABELS[mod] || mod}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-base sm:text-lg font-semibold text-white mb-4">
          License Information
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 text-sm">
          <div>
            <p className="text-text-muted">Edition</p>
            <p className="text-white font-medium">
              {EDITION_LABELS[license?.edition ?? ''] || license?.edition || '—'}
            </p>
          </div>
          <div>
            <p className="text-text-muted">Status</p>
            <p className={`font-medium ${cfg.textClass}`}>{cfg.title}</p>
          </div>
          <div>
            <p className="text-text-muted">Issue Date</p>
            <p className="text-white">{formatDate(license?.issued_at)}</p>
          </div>
          <div>
            <p className="text-text-muted">Max Hosts</p>
            <p className="text-white font-medium">{license?.max_hosts ?? "—"}</p>
          </div>
        </div>
      </div>

      <div className="card bg-primary/5 border-primary/20">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          {license?.customer_name && (
            <p className="text-sm text-text-muted">
              <span className="font-semibold text-primary">Licensed to:</span>{" "}
              {license.customer_name}
              {license.customer_contact && (
                <span className="text-text-muted/70 ml-1">({license.customer_contact})</span>
              )}
            </p>
          )}

        </div>
      </div>

      {isAdmin() && license && (
        <TechnicalDetails license={license} data={data} rawData={rawData} techOpen={techOpen} setTechOpen={setTechOpen} />
      )}
    </div>
  )
}

// ================================================================
// SUB-COMPONENTS
// ================================================================

function PageHeader() {
  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
        License Management
      </h1>
      <p className="text-text-muted text-sm sm:text-base">
        View and manage your Rhinometric instance license
      </p>
    </div>
  )
}

function StatusCard({
  config,
  children,
}: {
  config: StatusConfig
  children?: React.ReactNode
}) {
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

function TechnicalDetails({
  license,
  data,
  rawData,
  techOpen,
  setTechOpen,
}: {
  license: LicensePayload
  data: LicenseStatusResponse
  rawData: unknown
  techOpen: boolean
  setTechOpen: (v: boolean) => void
}) {
  return (
    <div className="card">
      <button
        type="button"
        className="flex items-center gap-2 w-full text-left"
        onClick={() => setTechOpen(!techOpen)}
      >
        {techOpen ? (
          <ChevronDown className="w-4 h-4 text-text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-text-muted" />
        )}
        <Info className="w-4 h-4 text-text-muted" />
        <span className="text-sm font-medium text-text-muted">
          Technical Details
        </span>
        <span className="text-xs text-text-muted/50 ml-auto">Only visible to Admin / Owner</span>
      </button>

      {techOpen && (
        <div className="mt-4 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-text-muted">License ID</p>
              <code className="block bg-surface-light px-3 py-1.5 rounded text-xs text-primary font-mono break-all mt-1">
                {license.license_id || "—"}
              </code>
            </div>
            <div>
              <p className="text-text-muted">Install ID</p>
              <code className="block bg-surface-light px-3 py-1.5 rounded text-xs text-primary font-mono break-all mt-1">
                {license.install_id || "—"}
              </code>
            </div>
            <div>
              <p className="text-text-muted">Validator</p>
              <p className="text-white font-medium">
                {data.validator === 'rust' ? 'Rust Ed25519 (rhino-lic)' : 'Legacy Server v2'}
              </p>
            </div>
            <div>
              <p className="text-text-muted">Status normalizado</p>
              <p className="text-white font-medium">{data.status}</p>
            </div>
          </div>

          <div>
            <p className="text-text-muted text-sm mb-2">Raw backend response</p>
            <pre className="bg-surface-light rounded p-3 text-xs text-text-muted font-mono overflow-x-auto max-h-60 overflow-y-auto">
              {JSON.stringify(rawData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}



function ContactSupportButton({
  subject,
  body,
}: {
  subject: string
  body: string
}) {
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

