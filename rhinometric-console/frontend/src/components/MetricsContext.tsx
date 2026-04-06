import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { Activity, TrendingUp, TrendingDown, CheckCircle, XCircle, Shield, Clock } from 'lucide-react'

interface ServiceStatus {
  id: number
  name: string
  service_key?: string
  status: string
  latency_ms: number
  health_score: number
  last_check?: string
  consecutive_failures: number
  ssl_expiry_days?: number
}

interface Props {
  serviceName: string
  serviceKey: string
  traceStartUs: number
  traceDurationUs: number
}

export function MetricsContext({ serviceName, serviceKey }: Props) {
  const token = useAuthStore((s) => s.token)

  // Fetch ONCE from /api/external-services
  const { data, isLoading, error } = useQuery({
    queryKey: ['svc-metrics', serviceKey],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const res = await fetch('/api/external-services', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const services: ServiceStatus[] = await res.json()
      // Match by service_name OR serviceKey
      return services.find(s =>
        s.name === serviceName ||
        s.service_key === serviceKey ||
        s.name === serviceKey
      ) || null
    },
    enabled: !!token && !!serviceName,
    staleTime: 60_000,
    retry: 1,
  })

  const svc = data

  if (isLoading) {
    return (
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-white">Service Metrics</h3>
        </div>
        <p className="text-gray-400 text-sm animate-pulse">Loading metrics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-white">Service Metrics</h3>
        </div>
        <p className="text-gray-500 text-sm">Metrics context unavailable for this service.</p>
      </div>
    )
  }

  // No match state
  if (!svc) {
    return (
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-white">Service Metrics</h3>
        </div>
        <p className="text-gray-500 text-sm">No metrics available for this service</p>
      </div>
    )
  }

  const isUp = svc.status === 'healthy' || svc.status === 'up'
  const healthPct = typeof svc.health_score === 'number' ? svc.health_score : null
  const latency = typeof svc.latency_ms === 'number' ? svc.latency_ms : null
  const failures = svc.consecutive_failures || 0

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-white">Service Metrics</h3>
          <span className="text-xs text-gray-500 font-mono">({serviceName})</span>
        </div>
        <div className="flex items-center gap-1.5">
          {isUp ? (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <CheckCircle size={14} /> Healthy
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <XCircle size={14} /> {svc.status || 'Down'}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4">
        {/* Latency */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Clock size={12} /> Latency
          </div>
          <p className={'text-lg font-bold ' + (latency !== null && latency > 1000 ? 'text-yellow-400' : 'text-white')}>
            {latency !== null ? `${latency.toFixed(0)}ms` : '\u2014'}
          </p>
        </div>

        {/* Health Score */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Shield size={12} /> Health
          </div>
          <p className={'text-lg font-bold ' + (
            healthPct !== null && healthPct >= 90 ? 'text-green-400' :
            healthPct !== null && healthPct >= 70 ? 'text-yellow-400' :
            healthPct !== null ? 'text-red-400' : 'text-white'
          )}>
            {healthPct !== null ? `${healthPct.toFixed(0)}%` : '\u2014'}
          </p>
        </div>

        {/* Consecutive Failures */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            {failures > 0 ? <TrendingDown size={12} className="text-red-400" /> : <TrendingUp size={12} />}
            Failures
          </div>
          <p className={'text-lg font-bold ' + (failures > 0 ? 'text-red-400' : 'text-green-400')}>
            {failures}
          </p>
        </div>

        {/* SSL Expiry — only if data exists */}
        {svc.ssl_expiry_days !== undefined && svc.ssl_expiry_days !== null && (
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Shield size={12} /> SSL Expiry
            </div>
            <p className={'text-lg font-bold ' + (
              svc.ssl_expiry_days < 14 ? 'text-red-400' :
              svc.ssl_expiry_days < 30 ? 'text-yellow-400' : 'text-green-400'
            )}>
              {svc.ssl_expiry_days}d
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
