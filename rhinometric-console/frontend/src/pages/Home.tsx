import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle2, AlertCircle, AlertTriangle, ArrowRight,
  Flame, Bell, Clock, TrendingUp, Activity, ChevronRight,
  Zap,
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
  events?: AlertHistoryEvent[]; items?: AlertHistoryEvent[]; total?: number
}

// ── Helpers ────────────────────────────────────────────────────

function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'ahora'
  if (mins < 60) return `${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} h`
  return `${Math.floor(hrs / 24)} d`
}

function fmtDuration(ms: number): string {
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  if (ms < 3600000) return `${Math.round(ms / 60000)}m`
  return `${(ms / 3600000).toFixed(1)}h`
}

function SeverityDot({ severity }: { severity: string }) {
  const s = (severity || '').toLowerCase()
  return (
    <span className="w-2 h-2 rounded-full flex-shrink-0 inline-block" style={{
      backgroundColor:
        s === 'critical' ? 'var(--c-critical)'
        : s === 'warning' ? 'var(--c-warning)'
        : 'var(--c-info)',
    }} />
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const s = (severity || '').toLowerCase()
  const cls = s === 'critical' ? 'badge-critical' : s === 'warning' ? 'badge-warning' : 'badge-info'
  return <span className={`badge ${cls}`}>{severity || 'info'}</span>
}

function StatusBadge({ status }: { status: string }) {
  const s = (status || '').toLowerCase()
  if (s === 'open' || s === 'investigating' || s === 'triggered') {
    return <span className="badge badge-critical">{status}</span>
  }
  if (s === 'resolved') return <span className="badge badge-success">Resuelto</span>
  if (s === 'acknowledged') return <span className="badge badge-warning">Reconocido</span>
  return <span className="badge badge-neutral">{status}</span>
}

// ── Mini sparkline (SVG, no deps) ─────────────────────────────

function Sparkline({ values, color = '#0ea5e9', height = 40 }: { values: number[]; color?: string; height?: number }) {
  if (!values || values.length < 2) return <div style={{ height }} />
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  const w = 160
  const h = height
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w
    const y = h - ((v - min) / range) * (h * 0.8) - h * 0.1
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ height }} preserveAspectRatio="none">
      <polyline fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" points={points} />
    </svg>
  )
}

// ── Donut chart (SVG, no deps) ────────────────────────────────

function DonutChart({ segments, total, label }: {
  segments: { label: string; value: number; color: string }[]
  total: number
  label?: string
}) {
  const r = 38
  const cx = 50; const cy = 50
  const circumference = 2 * Math.PI * r
  let cumulativePct = 0

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 100 100" className="w-24 h-24">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--c-border)" strokeWidth="10" />
        {segments.map((seg, i) => {
          if (!seg.value) return null
          const pct = seg.value / (total || 1)
          const dash = pct * circumference
          const offset = circumference - cumulativePct * circumference
          cumulativePct += pct
          return (
            <circle
              key={i}
              cx={cx} cy={cy} r={r}
              fill="none"
              stroke={seg.color}
              strokeWidth="10"
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
      <div className="mt-2 space-y-1 w-full">
        {segments.map((seg, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: seg.color }} />
              <span style={{ color: 'var(--c-text-secondary)' }}>{seg.label}</span>
            </div>
            <span className="font-medium tabular-nums" style={{ color: 'var(--c-text-primary)' }}>
              {seg.value} <span style={{ color: 'var(--c-text-muted)' }}>({total ? Math.round(seg.value / total * 100) : 0}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────

export function HomePage() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)

  useEffect(() => { document.title = 'Overview · Rhinometric' }, [])

  // ── Data fetching ──────────────────────────────────────────

  const { data: summaryData } = useQuery<ServiceSummary>({
    queryKey: ['services-summary', token],
    queryFn: async () => {
      const r = await fetch('/api/services/summary', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  const { data: incidentsData } = useQuery<IncidentsResponse>({
    queryKey: ['incidents-home', token],
    queryFn: async () => {
      const r = await fetch('/api/incidents', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const { data: alertsData } = useQuery<AlertsResponse>({
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

  // ── Derived values ─────────────────────────────────────────

  const allIncidents = incidentsData?.incidents ?? []
  const activeIncidents = allIncidents.filter(i =>
    ['open', 'investigating', 'triggered'].includes(i.status))
  const criticalIncidents = activeIncidents.filter(i => i.severity?.toLowerCase() === 'critical')

  const allAlerts = alertsData?.alerts ?? []
  const firingAlerts = allAlerts.filter(a => a.status === 'firing')
  const criticalAlerts = firingAlerts.filter(a => (a.severity || a.labels?.severity || '').toLowerCase() === 'critical')
  const warningAlerts = firingAlerts.filter(a => (a.severity || a.labels?.severity || '').toLowerCase() === 'warning')

  const historyEvents = historyData?.events ?? historyData?.items ?? []
  const resolvedToday = historyEvents.filter(e => e.status === 'resolved').length

  // Avg resolution time (from resolved events that have both started_at and ended_at)
  const resolvedWithTimes = historyEvents.filter(e =>
    e.status === 'resolved' && e.started_at && (e.ended_at || e.resolved_at))
  const avgResolutionMs = resolvedWithTimes.length > 0
    ? resolvedWithTimes.reduce((sum, e) => {
        const end = new Date(e.ended_at ?? e.resolved_at!).getTime()
        const start = new Date(e.started_at).getTime()
        return sum + (end - start)
      }, 0) / resolvedWithTimes.length
    : null


  const svc = summaryData?.monitored_services
  const svcDown = svc?.down ?? 0
  const svcDegraded = svc?.degraded ?? 0
  const svcHealthy = svc?.healthy ?? 0
  const svcTotal = svc?.total ?? 0

  // Global status
  const globalStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY' =
    svcDown > 0 || criticalIncidents.length > 0 ? 'CRITICAL'
    : svcDegraded > 0 || activeIncidents.length > 0 || criticalAlerts.length > 0 ? 'WARNING'
    : 'HEALTHY'

  // Sparkline from hourly alert buckets (derived from history events)
  const sparklineValues = useMemo(() => {
    if (!historyEvents.length) return Array(12).fill(0)
    const buckets = Array(12).fill(0) // last 12 x 2h buckets = 24h
    const now = Date.now()
    historyEvents.forEach(e => {
      const age = now - new Date(e.started_at).getTime()
      const bucket = Math.floor(age / (2 * 3600000))
      if (bucket >= 0 && bucket < 12) buckets[11 - bucket]++
    })
    return buckets
  }, [historyEvents])

  // Alert severity breakdown (for donut)
  const alertsBySeverity = useMemo(() => {
    const all = historyEvents
    const crit = all.filter(e => (e.severity || '').toLowerCase() === 'critical').length
    const warn = all.filter(e => (e.severity || '').toLowerCase() === 'warning').length
    const info = Math.max(0, all.length - crit - warn)
    return { crit, warn, info, total: all.length }
  }, [historyEvents])

  // Service status breakdown (for donut)
  const svcSegments = [
    { label: 'Operativos', value: svcHealthy, color: 'var(--c-success)' },
    { label: 'Degradados', value: svcDegraded, color: 'var(--c-warning)' },
    { label: 'Caídos', value: svcDown, color: 'var(--c-critical)' },
  ]

  // ── Render ─────────────────────────────────────────────────

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">

      {/* ── HEADER ROW ────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--c-text-primary)' }}>Overview</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--c-text-muted)' }}>
            Visión general de la operación en tiempo real
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--c-text-muted)' }}>
          <Activity className="w-4 h-4" />
          <span>Últimos 15 minutos</span>
        </div>
      </div>

      {/* ── GLOBAL STATUS BANNER ──────────────────────────── */}
      <div
        className="rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
        style={{
          backgroundColor: globalStatus === 'HEALTHY'
            ? 'var(--c-success-bg)'
            : globalStatus === 'CRITICAL'
              ? 'var(--c-critical-bg)'
              : 'var(--c-warning-bg)',
          border: `1px solid ${
            globalStatus === 'HEALTHY' ? 'var(--c-success-border)'
            : globalStatus === 'CRITICAL' ? 'var(--c-critical-border)'
            : 'var(--c-warning-border)'
          }`,
        }}
      >
        <div className="flex items-center gap-3">
          {globalStatus === 'HEALTHY' ? (
            <CheckCircle2 className="w-6 h-6 flex-shrink-0" style={{ color: 'var(--c-success)' }} />
          ) : globalStatus === 'CRITICAL' ? (
            <AlertCircle className="w-6 h-6 flex-shrink-0 animate-pulse" style={{ color: 'var(--c-critical)' }} />
          ) : (
            <AlertTriangle className="w-6 h-6 flex-shrink-0" style={{ color: 'var(--c-warning)' }} />
          )}
          <div>
            <p className="font-semibold" style={{ color: globalStatus === 'HEALTHY' ? 'var(--c-success)' : globalStatus === 'CRITICAL' ? 'var(--c-critical)' : 'var(--c-warning)' }}>
              {globalStatus === 'HEALTHY'
                ? 'Todos los sistemas operativos'
                : globalStatus === 'CRITICAL'
                  ? `${svcDown} servicio${svcDown !== 1 ? 's' : ''} caído${svcDown !== 1 ? 's' : ''}`
                  : 'Operación con advertencias'}
            </p>
            <p className="text-sm mt-0.5" style={{ color: 'var(--c-text-secondary)' }}>
              {globalStatus === 'HEALTHY'
                ? 'No hay incidentes activos. Todos los servicios funcionan correctamente.'
                : `${activeIncidents.length} incidente${activeIncidents.length !== 1 ? 's' : ''} activo${activeIncidents.length !== 1 ? 's' : ''} · ${firingAlerts.length} alerta${firingAlerts.length !== 1 ? 's' : ''} activa${firingAlerts.length !== 1 ? 's' : ''}`}
            </p>
          </div>
        </div>
        {globalStatus !== 'HEALTHY' && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/incidents')}
              className="btn btn-secondary text-sm"
              style={{ fontSize: '0.8125rem' }}
            >
              Ver incidentes
            </button>
            <button
              onClick={() => navigate('/alerts')}
              className="btn btn-secondary text-sm"
              style={{ fontSize: '0.8125rem' }}
            >
              Ver alertas
            </button>
          </div>
        )}
        {/* Stability sparkline */}
        <div className="hidden lg:flex flex-col items-end gap-1">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" style={{ color: 'var(--c-text-muted)' }} />
            <span className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>Estabilidad 24h</span>
          </div>
          <div className="w-32">
            <Sparkline
              values={sparklineValues}
              color={globalStatus === 'HEALTHY' ? 'var(--c-success)' : globalStatus === 'CRITICAL' ? 'var(--c-critical)' : 'var(--c-warning)'}
              height={32}
            />
          </div>
        </div>
      </div>

      {/* ── KPI SUMMARY CARDS ────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

        {/* Incidentes activos */}
        <button
          className="card-sm text-left hover:shadow-md transition-shadow cursor-pointer group"
          onClick={() => navigate('/incidents')}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>Incidentes</span>
            <Flame className="w-4 h-4" style={{ color: activeIncidents.length > 0 ? 'var(--c-critical)' : 'var(--c-text-muted)' }} />
          </div>
          <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: activeIncidents.length > 0 ? 'var(--c-critical)' : 'var(--c-text-primary)' }}>
            {incidentsData ? activeIncidents.length : '—'}
          </p>
          <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
            {criticalIncidents.length > 0
              ? <span style={{ color: 'var(--c-critical)' }}>▲ {criticalIncidents.length} crítico{criticalIncidents.length !== 1 ? 's' : ''}</span>
              : 'Activos'}
          </p>
        </button>

        {/* Atención requerida */}
        <button
          className="card-sm text-left hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => navigate('/alerts')}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>Atención requerida</span>
            <Bell className="w-4 h-4" style={{ color: firingAlerts.length > 0 ? 'var(--c-warning)' : 'var(--c-text-muted)' }} />
          </div>
          <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: firingAlerts.length > 0 ? 'var(--c-warning)' : 'var(--c-text-primary)' }}>
            {alertsData ? firingAlerts.length : '—'}
          </p>
          <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
            {warningAlerts.length > 0
              ? <span style={{ color: 'var(--c-warning)' }}>▲ {warningAlerts.length} advertencia{warningAlerts.length !== 1 ? 's' : ''}</span>
              : 'Alertas activas'}
          </p>
        </button>

        {/* Resueltos hoy */}
        <button
          className="card-sm text-left hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => navigate('/alert-history')}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>Resueltos hoy</span>
            <CheckCircle2 className="w-4 h-4" style={{ color: resolvedToday > 0 ? 'var(--c-success)' : 'var(--c-text-muted)' }} />
          </div>
          <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: resolvedToday > 0 ? 'var(--c-success)' : 'var(--c-text-primary)' }}>
            {historyData ? resolvedToday : '—'}
          </p>
          <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
            Alertas + incidentes
          </p>
        </button>

        {/* Tiempo medio de resolución */}
        <div className="card-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium" style={{ color: 'var(--c-text-muted)' }}>Tiempo medio resolución</span>
            <Clock className="w-4 h-4" style={{ color: 'var(--c-text-muted)' }} />
          </div>
          <p className="text-3xl font-bold tabular-nums mb-1" style={{ color: 'var(--c-text-primary)' }}>
            {avgResolutionMs != null ? fmtDuration(avgResolutionMs) : '—'}
          </p>
          <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Últimas 24h</p>
        </div>
      </div>

      {/* ── MAIN OPERATIONAL BLOCKS ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Incidentes activos */}
        <div className="card p-0 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--c-border)' }}>
            <div className="flex items-center gap-2">
              <Flame className="w-4 h-4" style={{ color: activeIncidents.length > 0 ? 'var(--c-critical)' : 'var(--c-text-muted)' }} />
              <h2 className="text-sm font-semibold" style={{ color: 'var(--c-text-primary)' }}>Incidentes activos</h2>
            </div>
            <button
              onClick={() => navigate('/incidents')}
              className="text-xs flex items-center gap-1 transition-colors"
              style={{ color: 'var(--c-primary)' }}
            >
              Ver todos <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="flex-1 divide-y overflow-auto" style={{ maxHeight: '340px' }}>
            {!incidentsData ? (
              <div className="px-5 py-8 text-center text-sm" style={{ color: 'var(--c-text-muted)' }}>Cargando…</div>
            ) : activeIncidents.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--c-success)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--c-text-primary)' }}>Sin incidentes activos</p>
                <p className="text-xs mt-1" style={{ color: 'var(--c-text-muted)' }}>¡Excelente! Todo en orden.</p>
              </div>
            ) : (
              activeIncidents.slice(0, 8).map(inc => (
                <div key={inc.id} className="px-5 py-3.5 flex items-start gap-3" style={{ borderBottomColor: 'var(--c-border)' }}>
                  <div
                    className="mt-0.5 w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                    style={{ backgroundColor: inc.severity?.toLowerCase() === 'critical' ? 'var(--c-critical)' : 'var(--c-warning)' }}
                  >
                    P{inc.severity?.toLowerCase() === 'critical' ? '1' : '2'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--c-text-primary)' }}>
                      {inc.title || inc.entity_name || inc.id}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
                        Iniciado {inc.created_at ? timeAgo(inc.created_at) : '—'}
                      </span>
                      <StatusBadge status={inc.status} />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Alertas recientes */}
        <div className="card p-0 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--c-border)' }}>
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4" style={{ color: firingAlerts.length > 0 ? 'var(--c-warning)' : 'var(--c-text-muted)' }} />
              <h2 className="text-sm font-semibold" style={{ color: 'var(--c-text-primary)' }}>Alertas recientes</h2>
            </div>
            <button
              onClick={() => navigate('/alerts')}
              className="text-xs flex items-center gap-1"
              style={{ color: 'var(--c-primary)' }}
            >
              Ver todas <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="flex-1 divide-y overflow-auto" style={{ maxHeight: '340px' }}>
            {!alertsData ? (
              <div className="px-5 py-8 text-center text-sm" style={{ color: 'var(--c-text-muted)' }}>Cargando…</div>
            ) : firingAlerts.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--c-success)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--c-text-primary)' }}>Sin alertas activas</p>
              </div>
            ) : (
              firingAlerts.slice(0, 8).map(alert => {
                const name = alert.labels?.alertname || alert.annotations?.summary || 'Alerta'
                const sev = alert.severity || alert.labels?.severity || 'warning'
                return (
                  <div key={alert.fingerprint} className="px-5 py-3.5 flex items-start gap-3" style={{ borderBottomColor: 'var(--c-border)' }}>
                    <SeverityDot severity={sev} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: 'var(--c-text-primary)' }}>{name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs truncate max-w-[100px]" style={{ color: 'var(--c-text-muted)' }}>
                          {alert.entity_name || alert.labels?.instance || ''}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
                          {timeAgo(alert.startsAt)}
                        </span>
                        <SeverityBadge severity={sev} />
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Actividad reciente */}
        <div className="card p-0 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--c-border)' }}>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" style={{ color: 'var(--c-primary)' }} />
              <h2 className="text-sm font-semibold" style={{ color: 'var(--c-text-primary)' }}>Actividad reciente</h2>
            </div>
            <button
              onClick={() => navigate('/alert-history')}
              className="text-xs flex items-center gap-1"
              style={{ color: 'var(--c-primary)' }}
            >
              Ver todo <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="flex-1 divide-y overflow-auto" style={{ maxHeight: '340px' }}>
            {!historyData ? (
              <div className="px-5 py-8 text-center text-sm" style={{ color: 'var(--c-text-muted)' }}>Cargando…</div>
            ) : historyEvents.length === 0 ? (
              <div className="px-5 py-8 text-center">
                <p className="text-sm" style={{ color: 'var(--c-text-muted)' }}>Sin actividad reciente</p>
              </div>
            ) : (
              historyEvents.slice(0, 10).map(ev => (
                <div key={ev.id} className="px-5 py-3 flex items-start gap-3" style={{ borderBottomColor: 'var(--c-border)' }}>
                  <div className="mt-0.5 flex-shrink-0">
                    {ev.status === 'resolved' ? (
                      <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--c-success)' }} />
                    ) : ev.severity?.toLowerCase() === 'critical' ? (
                      <AlertCircle className="w-4 h-4" style={{ color: 'var(--c-critical)' }} />
                    ) : (
                      <AlertTriangle className="w-4 h-4" style={{ color: 'var(--c-warning)' }} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--c-text-primary)' }}>
                      {ev.alert_name?.replace(/^policy:SERVICE_DOWN:/, '') || ev.entity_name || ev.alert_name}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>{timeAgo(ev.started_at)}</span>
                      <span className="badge badge-neutral text-xs" style={{ fontSize: '0.6875rem' }}>{ev.status}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ── OPERATIONAL SUMMARY ──────────────────────────── */}
      <div className="card">
        <h2 className="text-sm font-semibold mb-5" style={{ color: 'var(--c-text-primary)' }}>Resumen de operación</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

          {/* Alertas en el tiempo */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium" style={{ color: 'var(--c-text-secondary)' }}>Alertas en el tiempo</span>
              <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Últimas 24h ↓</span>
            </div>
            <div className="h-24 flex items-end">
              <Sparkline values={sparklineValues} color="var(--c-primary)" height={80} />
            </div>
            <div className="flex items-center gap-4 mt-2">
              <div className="flex items-center gap-1.5">
                <span className="dot-critical" />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Críticas</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="dot-warning" />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Advertencias</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="dot-info" />
                <span className="text-xs" style={{ color: 'var(--c-text-muted)' }}>Info</span>
              </div>
            </div>
          </div>

          {/* Alertas por severidad */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium" style={{ color: 'var(--c-text-secondary)' }}>Alertas por severidad</span>
            </div>
            {alertsBySeverity.total > 0 ? (
              <DonutChart
                total={alertsBySeverity.total}
                label="Total"
                segments={[
                  { label: 'Críticas', value: alertsBySeverity.crit, color: 'var(--c-critical)' },
                  { label: 'Advertencias', value: alertsBySeverity.warn, color: 'var(--c-warning)' },
                  { label: 'Info', value: alertsBySeverity.info, color: 'var(--c-info)' },
                ]}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-24">
                <p className="text-sm" style={{ color: 'var(--c-text-muted)' }}>Sin datos en 24h</p>
              </div>
            )}
          </div>

          {/* Servicios por estado */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium" style={{ color: 'var(--c-text-secondary)' }}>Servicios por estado</span>
            </div>
            {svcTotal > 0 ? (
              <DonutChart
                total={svcTotal}
                label="Total"
                segments={svcSegments.filter(s => s.value > 0)}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-24">
                <button
                  onClick={() => navigate('/services')}
                  className="btn btn-primary text-xs"
                >
                  Agregar servicios <ArrowRight className="w-3 h-3 ml-1" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
