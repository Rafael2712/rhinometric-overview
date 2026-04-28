import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle2, AlertCircle, AlertTriangle, ArrowRight,
  Flame, Bell, TrendingUp, Activity,
} from 'lucide-react'

// ── Types ──────────────────────────────────────────────────────

interface MonitoredServices {
  total: number; healthy: number; degraded: number; down: number; status: string
}
interface ServiceSummary {
  monitored_services: MonitoredServices
  platform_components: { total: number; healthy: number; down: number; status: string }
}
interface Incident {
  id: string; status: string; severity: string; title: string
  created_at?: string; updated_at?: string; entity_name?: string
}
interface IncidentsResponse { incidents: Incident[]; total: number }
interface Alert {
  id?: string; fingerprint: string; status: string
  labels: { alertname?: string; severity?: string; [k: string]: string | undefined }
  annotations: { summary?: string; [k: string]: string | undefined }
  startsAt: string; severity: string; entity_name?: string
}
interface AlertsResponse { alerts: Alert[]; total: number }
interface AlertHistoryEvent {
  id: string; alert_name: string; status: string; severity: string
  entity_name: string; started_at: string; ended_at?: string; resolved_at?: string
}
interface AlertHistoryResponse {
  alert_events?: AlertHistoryEvent[]; events?: AlertHistoryEvent[]; items?: AlertHistoryEvent[]; total?: number
}

// ── Mini sparkline (SVG, no deps) ──────────────────────────────

function Sparkline({ values, color = '#0284c7', height = 48 }: {
  values: number[]; color?: string; height?: number
}) {
  if (!values || values.length < 2) return <div style={{ height }} />
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  const w = 200; const h = height
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w
    const y = h - ((v - min) / range) * (h * 0.8) - h * 0.1
    return `${x},${y}`
  }).join(' ')
  const areaPoints = `0,${h} ${points} ${w},${h}`

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ height }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon fill="url(#spark-fill)" points={areaPoints} />
      <polyline fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" points={points} />
    </svg>
  )
}

// ── Donut chart (SVG, no deps) ──────────────────────────────────

function DonutChart({ segments, total, label }: {
  segments: { label: string; value: number; color: string }[]
  total: number
  label?: string
}) {
  const r = 38; const cx = 50; const cy = 50
  const circumference = 2 * Math.PI * r
  let cumulativePct = 0

  return (
    <div className="flex items-center gap-6">
      <svg viewBox="0 0 100 100" className="w-24 h-24 flex-shrink-0">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--c-border)" strokeWidth="10" />
        {segments.map((seg, i) => {
          if (!seg.value) return null
          const pct = seg.value / (total || 1)
          const dash = pct * circumference
          const offset = circumference - cumulativePct * circumference
          cumulativePct += pct
          return (
            <circle key={i} cx={cx} cy={cy} r={r} fill="none"
              stroke={seg.color} strokeWidth="10"
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={offset}
              style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
            />
          )
        })}
        <text x="50" y="54" textAnchor="middle" fontSize="16" fontWeight="700" fill="var(--c-text-primary)">
          {total}
        </text>
        {label && (
          <text x="50" y="66" textAnchor="middle" fontSize="7" fill="var(--c-text-muted)">{label}</text>
        )}
      </svg>
      <div className="space-y-1.5 flex-1">
        {segments.map((seg, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: seg.color }} />
              <span style={{ color: 'var(--c-text-secondary)' }}>{seg.label}</span>
            </div>
            <span className="font-semibold tabular-nums" style={{ color: 'var(--c-text-primary)' }}>
              {seg.value}
              <span className="font-normal ml-1" style={{ color: 'var(--c-text-muted)' }}>
                ({total ? Math.round(seg.value / total * 100) : 0}%)
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────

export function HomePage() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)

  useEffect(() => { document.title = 'Overview · Rhinometric' }, [])

  // ── Data fetching ──────────────────────────────────────────────

  const { data: summaryData, isLoading: svcLoading } = useQuery<ServiceSummary>({
    queryKey: ['services-summary', token],
    queryFn: async () => {
      const r = await fetch('/api/services/summary', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  const { data: incidentsData, isLoading: incLoading } = useQuery<IncidentsResponse>({
    queryKey: ['incidents-home', token],
    queryFn: async () => {
      const r = await fetch('/api/incidents', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const { data: alertsData, isLoading: alertLoading } = useQuery<AlertsResponse>({
    queryKey: ['alerts-home', token],
    queryFn: async () => {
      const r = await fetch('/api/alerts', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const { data: historyData } = useQuery<AlertHistoryResponse>({
    queryKey: ['alert-history-home', token],
    queryFn: async () => {
      const r = await fetch('/api/alert-history?time_range=24h&limit=50', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  const { data: anomalyData } = useQuery({
    queryKey: ['anomalies-count-home', token],
    queryFn: async () => {
      const r = await fetch('/api/v2/anomalies/active', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return 0
      const d = await r.json()
      return d?.count ?? 0
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  // ── Derived values ─────────────────────────────────────────────

  const allIncidents = incidentsData?.incidents ?? []
  const activeIncidents = allIncidents.filter(i =>
    ['open', 'investigating', 'triggered'].includes(i.status))
  const criticalIncidents = activeIncidents.filter(i => i.severity?.toLowerCase() === 'critical')
  const warningIncidents  = activeIncidents.filter(i => i.severity?.toLowerCase() === 'warning')

  const allAlerts = alertsData?.alerts ?? []
  const firingAlerts = allAlerts.filter(a => a.status === 'firing' || a.status === 'active')
  const criticalAlerts = firingAlerts.filter(a => (a.severity || a.labels?.severity || '').toLowerCase() === 'critical')
  const warningAlerts  = firingAlerts.filter(a => (a.severity || a.labels?.severity || '').toLowerCase() === 'warning')

  const historyEvents = historyData?.alert_events ?? historyData?.events ?? historyData?.items ?? []

  const svc = summaryData?.monitored_services
  const svcDown     = svc?.down ?? 0
  const svcDegraded = svc?.degraded ?? 0
  const svcHealthy  = svc?.healthy ?? 0
  const svcTotal    = svc?.total ?? 0
  const anomalyCount = anomalyData ? Number(anomalyData) : 0

  // Global status — canonical source of truth (mirrors header indicator)
  const globalStatus: 'CRITICAL' | 'DEGRADED' | 'OPERATIONAL' =
    svcDown > 0 || criticalIncidents.length > 0 || criticalAlerts.length > 0 ? 'CRITICAL'
    : svcDegraded > 0 || activeIncidents.length > 0 || firingAlerts.length > 0 || anomalyCount > 0 ? 'DEGRADED'
    : 'OPERATIONAL'

  // Sparkline from 12 × 2h buckets (last 24 h)
  const sparklineValues = useMemo(() => {
    if (!historyEvents.length) return []
    const buckets = Array(12).fill(0)
    const now = Date.now()
    historyEvents.forEach(e => {
      const age = now - new Date(e.started_at).getTime()
      const bucket = Math.floor(age / (2 * 3600000))
      if (bucket >= 0 && bucket < 12) buckets[11 - bucket]++
    })
    return buckets
  }, [historyEvents])

  // Alert severity breakdown (for donut — 24 h history)
  const alertsBySeverity = useMemo(() => {
    const crit = historyEvents.filter(e => (e.severity || '').toLowerCase() === 'critical').length
    const warn = historyEvents.filter(e => (e.severity || '').toLowerCase() === 'warning').length
    const info = Math.max(0, historyEvents.length - crit - warn)
    return { crit, warn, info, total: historyEvents.length }
  }, [historyEvents])

  // Service status breakdown (for donut)
  const svcSegments = [
    { label: 'Operational', value: svcHealthy,  color: 'var(--c-success)' },
    { label: 'Degraded',    value: svcDegraded, color: 'var(--c-warning)'  },
    { label: 'Down',        value: svcDown,     color: 'var(--c-critical)' },
  ]

  // ── Banner colors ──────────────────────────────────────────────

  const bannerBg     = globalStatus === 'OPERATIONAL' ? 'var(--c-success-bg)'
                     : globalStatus === 'CRITICAL' ? 'var(--c-critical-bg)'
                     : 'var(--c-warning-bg)'
  const bannerBorder = globalStatus === 'OPERATIONAL' ? 'var(--c-success-border)'
                     : globalStatus === 'CRITICAL' ? 'var(--c-critical-border)'
                     : 'var(--c-warning-border)'
  const bannerColor  = globalStatus === 'OPERATIONAL' ? 'var(--c-success)'
                     : globalStatus === 'CRITICAL' ? 'var(--c-critical)'
                     : 'var(--c-warning)'

  // ── Render ─────────────────────────────────────────────────────

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">

      {/* ── PAGE HEADER ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--c-text-primary)' }}>Overview</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--c-text-muted)' }}>
            Real-time operational status
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--c-text-muted)' }}>
          <Activity className="w-3.5 h-3.5" />
          <span>Auto-refreshes every 15 s</span>
        </div>
      </div>

      {/* ── GLOBAL STATUS BANNER ───────────────────────────────── */}
      <div
        className="rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        style={{ backgroundColor: bannerBg, border: `1.5px solid ${bannerBorder}` }}
      >
        {/* Left: icon + text */}
        <div className="flex items-center gap-3">
          {globalStatus === 'OPERATIONAL' ? (
            <CheckCircle2 className="w-6 h-6 flex-shrink-0" style={{ color: bannerColor }} />
          ) : globalStatus === 'CRITICAL' ? (
            <AlertCircle className="w-6 h-6 flex-shrink-0 animate-pulse" style={{ color: bannerColor }} />
          ) : (
            <AlertTriangle className="w-6 h-6 flex-shrink-0" style={{ color: bannerColor }} />
          )}
          <div>
            <p className="font-semibold text-sm" style={{ color: bannerColor }}>
              {globalStatus === 'OPERATIONAL'
                ? 'All systems operational'
                : globalStatus === 'CRITICAL'
                  ? `${svcDown} service${svcDown !== 1 ? 's' : ''} down`
                  : 'System degraded — operating with warnings'}
            </p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--c-text-secondary)' }}>
              {globalStatus === 'OPERATIONAL'
                ? 'No active incidents or alerts. All services running correctly.'
                : `${activeIncidents.length} active incident${activeIncidents.length !== 1 ? 's' : ''} · ${firingAlerts.length} firing alert${firingAlerts.length !== 1 ? 's' : ''}`}
            </p>
          </div>
        </div>

        {/* Center: action buttons (only when not healthy) */}
        {globalStatus !== 'OPERATIONAL' && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/incidents')}
              className="btn btn-secondary"
              style={{ fontSize: '0.8125rem' }}
            >
              View incidents
            </button>
            <button
              onClick={() => navigate('/alerts')}
              className="btn btn-secondary"
              style={{ fontSize: '0.8125rem' }}
            >
              View alerts
            </button>
          </div>
        )}

        {/* Right: stability sparkline */}
        <div className="hidden lg:flex flex-col items-end gap-1 min-w-[140px]">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3" style={{ color: 'var(--c-text-muted)' }} />
            <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>24h stability</span>
          </div>
          <div className="w-36">
            <Sparkline values={sparklineValues} color={bannerColor} height={32} />
          </div>
        </div>
      </div>

      {/* ── TWO KPI CARDS ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Card 1: Incidents */}
        <button
          onClick={() => navigate('/incidents')}
          className="card text-left hover:shadow-md transition-shadow cursor-pointer group w-full"
          style={{ padding: '1.25rem 1.5rem' }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3">
                <Flame
                  className="w-4 h-4 flex-shrink-0"
                  style={{ color: activeIncidents.length > 0 ? 'var(--c-critical)' : 'var(--c-text-muted)' }}
                />
                <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--c-text-muted)' }}>
                  Incidents
                </span>
              </div>
              <p
                className="text-4xl font-bold tabular-nums leading-none mb-3"
                style={{ color: activeIncidents.length > 0 ? 'var(--c-critical)' : 'var(--c-text-primary)' }}
              >
                {incLoading ? (
                  <span className="inline-block w-8 h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--c-border)' }} />
                ) : incidentsData ? activeIncidents.length : '—'}
              </p>
              {/* Severity summary */}
              {activeIncidents.length > 0 ? (
                <div className="flex items-center gap-3 text-xs">
                  {criticalIncidents.length > 0 && (
                    <span style={{ color: 'var(--c-critical)' }}>
                      <span className="font-semibold">{criticalIncidents.length}</span> critical
                    </span>
                  )}
                  {warningIncidents.length > 0 && (
                    <span style={{ color: 'var(--c-warning)' }}>
                      <span className="font-semibold">{warningIncidents.length}</span> warning
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>No open incidents</p>
              )}
            </div>
            <div className="flex items-center gap-1 ml-4 mt-1" style={{ color: 'var(--c-primary)' }}>
              <span className="text-xs font-medium group-hover:underline">Open</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </button>

        {/* Card 2: Alerts */}
        <button
          onClick={() => navigate('/alerts')}
          className="card text-left hover:shadow-md transition-shadow cursor-pointer group w-full"
          style={{ padding: '1.25rem 1.5rem' }}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3">
                <Bell
                  className="w-4 h-4 flex-shrink-0"
                  style={{ color: firingAlerts.length > 0 ? 'var(--c-warning)' : 'var(--c-text-muted)' }}
                />
                <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--c-text-muted)' }}>
                  Active alerts
                </span>
              </div>
              <p
                className="text-4xl font-bold tabular-nums leading-none mb-3"
                style={{ color: firingAlerts.length > 0 ? 'var(--c-warning)' : 'var(--c-text-primary)' }}
              >
                {alertLoading ? (
                  <span className="inline-block w-8 h-8 rounded animate-pulse" style={{ backgroundColor: 'var(--c-border)' }} />
                ) : alertsData ? firingAlerts.length : '—'}
              </p>
              {/* Severity summary */}
              {firingAlerts.length > 0 ? (
                <div className="flex items-center gap-3 text-xs">
                  {criticalAlerts.length > 0 && (
                    <span style={{ color: 'var(--c-critical)' }}>
                      <span className="font-semibold">{criticalAlerts.length}</span> critical
                    </span>
                  )}
                  {warningAlerts.length > 0 && (
                    <span style={{ color: 'var(--c-warning)' }}>
                      <span className="font-semibold">{warningAlerts.length}</span> warning
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>No firing alerts</p>
              )}
            </div>
            <div className="flex items-center gap-1 ml-4 mt-1" style={{ color: 'var(--c-primary)' }}>
              <span className="text-xs font-medium group-hover:underline">Open</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </button>
      </div>

      {/* ── OPERATIONAL SUMMARY (full width) ───────────────────── */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-semibold" style={{ color: 'var(--c-text-primary)' }}>
            Operational summary
          </h2>
          <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Last 24 h</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:divide-x" style={{ '--tw-divide-opacity': 1 } as React.CSSProperties}>

          {/* 1. Alerts over time */}
          <div className="md:pr-8">
            <p className="text-xs font-medium mb-3" style={{ color: 'var(--c-text-secondary)' }}>
              Alerts over time
            </p>
            <div className="h-16">
              <Sparkline values={sparklineValues} color="var(--c-primary)" height={64} />
            </div>
            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--c-critical)' }} />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Critical</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--c-warning)' }} />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Warning</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--c-info)' }} />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Info</span>
              </div>
            </div>
          </div>

          {/* 2. Alerts by severity */}
          <div className="md:px-8">
            <p className="text-xs font-medium mb-3" style={{ color: 'var(--c-text-secondary)' }}>
              Alerts by severity
            </p>
            {alertsBySeverity.total > 0 ? (
              <DonutChart
                total={alertsBySeverity.total}
                label="Total"
                segments={[
                  { label: 'Critical', value: alertsBySeverity.crit, color: 'var(--c-critical)' },
                  { label: 'Warning',  value: alertsBySeverity.warn, color: 'var(--c-warning)'  },
                  { label: 'Info',     value: alertsBySeverity.info, color: 'var(--c-info)'     },
                ]}
              />
            ) : (
              <div className="flex items-center justify-center h-24">
                <p className="text-sm" style={{ color: 'var(--c-text-muted)' }}>No data in 24 h</p>
              </div>
            )}
          </div>

          {/* 3. Services by status */}
          <div className="md:pl-8">
            <p className="text-xs font-medium mb-3" style={{ color: 'var(--c-text-secondary)' }}>
              Services by status
            </p>
            {svcLoading ? (
              <div className="flex items-center justify-center h-24">
                <div className="w-20 h-20 rounded-full animate-pulse" style={{ backgroundColor: 'var(--c-border)' }} />
              </div>
            ) : svcTotal > 0 ? (
              <DonutChart
                total={svcTotal}
                label="Total"
                segments={svcSegments.filter(s => s.value > 0)}
              />
            ) : (
              <div className="flex items-center justify-center h-24">
                <button
                  onClick={() => navigate('/services')}
                  className="btn btn-primary text-xs"
                >
                  Add services <ArrowRight className="w-3 h-3 ml-1" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
