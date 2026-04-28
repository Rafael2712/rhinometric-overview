import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Target,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Server,
  Activity,
  Gauge,
  Heart,
  Shield,
} from 'lucide-react'

/* ── helpers ──────────────────────────────────────────────────── */

const API = '/api/slo'

async function fetchWithAuth(url: string, token: string) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/* ── status helpers ───────────────────────────────────────────── */

type SLOStatus = 'healthy' | 'at_risk' | 'breached' | 'no_data'

const STATUS_CONFIG: Record<SLOStatus, { bg: string; text: string; ring: string; icon: React.ReactNode; label: string }> = {
  healthy:  { bg: 'bg-green-50',  text: 'text-green-700',  ring: 'ring-green-300',  icon: <CheckCircle2 className="w-3.5 h-3.5" />, label: 'Meeting SLO' },
  at_risk:  { bg: 'bg-amber-50', text: 'text-amber-700', ring: 'ring-amber-300', icon: <AlertTriangle className="w-3.5 h-3.5" />, label: 'At Risk' },
  breached: { bg: 'bg-red-50',    text: 'text-red-700',    ring: 'ring-red-300',    icon: <XCircle className="w-3.5 h-3.5" />, label: 'Breached' },
  no_data:  { bg: 'bg-slate-100',   text: 'text-slate-500',   ring: 'ring-slate-200',   icon: <Clock className="w-3.5 h-3.5" />, label: 'No Data' },
}

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_CONFIG[(status as SLOStatus)] || STATUS_CONFIG.no_data
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      {s.icon} {s.label}
    </span>
  )
}

function statusColor(status: string): string {
  return STATUS_CONFIG[(status as SLOStatus)]?.text || 'text-gray-500'
}

/* ── SLI Card ─────────────────────────────────────────────────── */

function SLICard({ title, icon, value, unit, targetLabel, budget, status, hint }: {
  title: string
  icon: React.ReactNode
  value: string | number | null
  unit: string
  targetLabel: string
  budget: number | null
  status: string
  hint: string
}) {
  const cfg = STATUS_CONFIG[(status as SLOStatus)] || STATUS_CONFIG.no_data
  const hasData = value !== null && value !== undefined

  return (
    <div className={`relative bg-white border border-slate-200 rounded-xl p-5 ring-1 ${cfg.ring} transition-all hover:bg-slate-50`}>
      {/* Status indicator */}
      <div className={`absolute top-3 right-3 w-2.5 h-2.5 rounded-full ${
        status === 'healthy' ? 'bg-green-400' :
        status === 'at_risk' ? 'bg-yellow-400 animate-pulse' :
        status === 'breached' ? 'bg-red-400 animate-pulse' :
        'bg-gray-300'
      }`} />

      <div className="flex items-center gap-2 mb-3">
        <div className={`p-1.5 rounded-lg ${cfg.bg}`}>{icon}</div>
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>

      {/* Main value */}
      <div className="mb-3">
        <p className={`text-3xl font-bold ${hasData ? cfg.text : 'text-gray-600'}`}>
          {hasData ? value : '—'}
          {hasData && <span className="text-lg font-normal text-slate-400 ml-1">{unit}</span>}
        </p>
        <p className="text-xs text-slate-500 mt-1">{hint}</p>
      </div>

      {/* Target line */}
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-slate-500">Target: <span className="text-slate-800">{targetLabel}</span></span>
        <StatusBadge status={status} />
      </div>

      {/* Error budget bar */}
      {budget !== null && budget !== undefined ? (
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-500">Error budget</span>
            <span className={`font-medium ${budget >= 50 ? 'text-green-400' : budget >= 20 ? 'text-yellow-400' : 'text-red-400'}`}>
              {budget.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                budget >= 50 ? 'bg-green-500' : budget >= 20 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(budget, 100)}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="h-1.5 bg-slate-200 rounded-full" />
      )}
    </div>
  )
}

/* ── Compact stat ─────────────────────────────────────────────── */

function CompactStat({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  )
}

/* ── Type & source badges ─────────────────────────────────────── */

function TypeBadge({ type }: { type: string }) {
  const color = type === 'http' ? 'text-blue-700 bg-blue-50 border border-blue-200' : 'text-purple-700 bg-purple-50 border border-purple-200'
  return <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${color}`}>{type}</span>
}

function DataSourceBadge({ monitoringMode, telemetryStatus }: { monitoringMode?: string; telemetryStatus?: string }) {
  if (monitoringMode !== 'telemetry_enabled') {
    return <span className="px-2 py-0.5 rounded text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200">Synthetic</span>
  }
  const isActive = telemetryStatus === 'receiving_data' || telemetryStatus === 'connected'
  if (isActive) {
    return <span className="px-2 py-0.5 rounded text-xs font-medium text-green-700 bg-green-50 border border-green-200">Telemetry + Synthetic</span>
  }
  return <span className="px-2 py-0.5 rounded text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200">Telemetry (pending)</span>
}

/* ── Budget bar ───────────────────────────────────────────────── */

function BudgetBar({ pct }: { pct: number | null }) {
  if (pct === null || pct === undefined) return <span className="text-gray-500 text-xs">—</span>
  const color = pct >= 50 ? 'bg-green-500' : pct >= 20 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden max-w-[100px]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className="text-xs text-slate-600 w-12 text-right">{pct.toFixed(1)}%</span>
    </div>
  )
}

/* ── Detail panel (expandable row) ────────────────────────────── */

function ServiceDetailPanel({ serviceId, token, timeRange }: { serviceId: number; token: string; timeRange: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['slo-detail', serviceId, timeRange],
    queryFn: () => fetchWithAuth(`${API}/services/${serviceId}?time_range=${timeRange}`, token),
    refetchInterval: 60000,
  })

  if (isLoading) return <div className="p-6 text-gray-500">Loading detail…</div>
  if (!data) return null

  const svc = data.service
  const trend = data.availability_trend || []
  const alerts = data.recent_alerts || []
  const incidents = data.recent_incidents || []

  return (
    <div className="p-6 bg-slate-50 border-t border-slate-200 space-y-6">
      {/* SLI cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SLICard
          title="Availability"
          icon={<Activity className="w-4 h-4 text-green-400" />}
          value={svc.availability_pct}
          unit="%"
          targetLabel={`≥ ${svc.targets?.availability ?? 99}%`}
          budget={svc.error_budget_availability}
          status={svc.slo_status_availability}
          hint={`${svc.successful_checks}/${svc.total_checks} checks passed`}
        />
        <SLICard
          title="Latency (P95)"
          icon={<Gauge className="w-4 h-4 text-blue-400" />}
          value={svc.p95_latency_ms}
          unit="ms"
          targetLabel={`≤ ${svc.targets?.latency ?? 1000} ms`}
          budget={svc.error_budget_latency}
          status={svc.slo_status_latency}
          hint={`Avg: ${svc.avg_latency_ms ?? '—'} ms`}
        />
        <SLICard
          title="Health Score"
          icon={<Heart className="w-4 h-4 text-purple-400" />}
          value={svc.health_score}
          unit="/100"
          targetLabel={`≥ ${svc.targets?.health_score ?? 70}`}
          budget={svc.error_budget_health}
          status={svc.slo_status_health}
          hint="AI anomaly detection score"
        />
      </div>

      {/* Trend + alerts + incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Availability trend */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2">Availability Trend (hourly)</h4>
          <div className="max-h-48 overflow-y-auto space-y-1 text-xs">
            {trend.length === 0 && <p className="text-slate-500">No trend data</p>}
            {trend.slice(-12).map((b: { time: string; availability_pct: number; avg_latency_ms: number }) => (
              <div key={b.time} className="flex justify-between text-slate-600">
                <span>{b.time.split(' ')[1] || b.time}</span>
                <span className={b.availability_pct >= 99 ? 'text-green-400' : b.availability_pct >= 95 ? 'text-yellow-400' : 'text-red-400'}>
                  {b.availability_pct}%
                </span>
                <span>{b.avg_latency_ms} ms</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent alerts */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2">Recent Alerts ({alerts.length})</h4>
          {alerts.length === 0 && <p className="text-xs text-slate-500">None in this window</p>}
          {alerts.slice(0, 5).map((a: { id: string; alert_name: string; severity: string; status: string }) => (
            <div key={a.id} className="flex items-center gap-2 text-xs text-slate-600 mb-1">
              <span className={`w-2 h-2 rounded-full ${a.status === 'firing' ? 'bg-red-500' : 'bg-green-500'}`} />
              <span className="truncate">{a.alert_name}</span>
              <span className="text-slate-500">{a.severity}</span>
            </div>
          ))}
        </div>

        {/* Recent incidents */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2">Recent Incidents ({incidents.length})</h4>
          {incidents.length === 0 && <p className="text-xs text-gray-500">None in this window</p>}
          {incidents.slice(0, 5).map((inc: { id: string; status: string; severity: string; started_at: string }) => (
            <div key={inc.id} className="flex items-center gap-2 text-xs text-slate-600 mb-1">
              <StatusBadge status={inc.status === 'resolved' ? 'healthy' : 'breached'} />
              <span className="text-slate-500">{inc.severity}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── Service row (desktop) ────────────────────────────────────── */

function ServiceRow({ svc, token, timeRange }: { svc: any; token: string; timeRange: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr
        className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3 text-sm">
          <span className="text-gray-500">{expanded ? <ChevronDown className="w-4 h-4 inline" /> : <ChevronRight className="w-4 h-4 inline" />}</span>
        </td>
        <td className="px-4 py-3 text-sm font-medium text-slate-900">{svc.service_name}</td>
        <td className="px-4 py-3 text-sm"><TypeBadge type={svc.service_type} /></td>
        <td className="px-4 py-3 text-sm">
          {svc.availability_pct !== null ? (
            <span className={statusColor(svc.slo_status_availability)}>{svc.availability_pct}%</span>
          ) : <span className="text-gray-500">—</span>}
        </td>
        <td className="px-4 py-3 text-sm">
          {svc.p95_latency_ms !== null && svc.p95_latency_ms > 0 ? (
            <span className={statusColor(svc.slo_status_latency)}>{svc.p95_latency_ms} ms</span>
          ) : <span className="text-gray-500">—</span>}
        </td>
        <td className="px-4 py-3 text-sm">
          {svc.health_score !== null ? (
            <span className={statusColor(svc.slo_status_health)}>{svc.health_score}</span>
          ) : <span className="text-gray-500">—</span>}
        </td>
        <td className="px-4 py-3 text-sm"><BudgetBar pct={svc.error_budget_remaining_pct} /></td>
        <td className="px-4 py-3 text-sm"><DataSourceBadge monitoringMode={svc.monitoring_mode} telemetryStatus={svc.telemetry_status} /></td>
        <td className="px-4 py-3 text-sm"><StatusBadge status={svc.slo_status} /></td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={9} className="p-0">
            <ServiceDetailPanel serviceId={svc.service_id} token={token} timeRange={timeRange} />
          </td>
        </tr>
      )}
    </>
  )
}

/* ── Mobile card ──────────────────────────────────────────────── */

function MobileServiceCard({ svc, token, timeRange }: { svc: any; token: string; timeRange: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-900 font-medium">{svc.service_name}</p>
          <TypeBadge type={svc.service_type} />
        </div>
        <StatusBadge status={svc.slo_status} />
      </div>

      {/* 3 SLIs in a row */}
      <div className="grid grid-cols-3 gap-2 text-sm">
        <div>
          <p className="text-gray-500 text-[10px] uppercase">Availability</p>
          <p className={`font-medium ${statusColor(svc.slo_status_availability)}`}>
            {svc.availability_pct !== null ? `${svc.availability_pct}%` : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-500 text-[10px] uppercase">P95 Latency</p>
          <p className={`font-medium ${statusColor(svc.slo_status_latency)}`}>
            {svc.p95_latency_ms !== null && svc.p95_latency_ms > 0 ? `${svc.p95_latency_ms} ms` : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-500 text-[10px] uppercase">Health</p>
          <p className={`font-medium ${statusColor(svc.slo_status_health)}`}>
            {svc.health_score !== null ? svc.health_score : '—'}
          </p>
        </div>
      </div>

      {/* Error budget */}
      <div>
        <p className="text-gray-500 text-xs mb-1">Error Budget</p>
        <BudgetBar pct={svc.error_budget_remaining_pct} />
      </div>

      <button onClick={() => setExpanded(!expanded)} className="text-xs text-blue-600 hover:text-blue-700">
        {expanded ? 'Hide detail' : 'Show detail'}
      </button>
      {expanded && <ServiceDetailPanel serviceId={svc.service_id} token={token} timeRange={timeRange} />}
    </div>
  )
}

/* ── Main SLO page ────────────────────────────────────────────── */

export function SLOPage() {
  const token = useAuthStore((s) => s.token) || ''
  const [timeRange, setTimeRange] = useState('24h')

  // Fetch summary (global aggregates)
  const { data: summaryData } = useQuery({
    queryKey: ['slo-summary', timeRange],
    queryFn: () => fetchWithAuth(`${API}/summary?time_range=${timeRange}`, token),
    refetchInterval: 30000,
  })

  // Fetch per-service list
  const { data, isLoading, error } = useQuery({
    queryKey: ['slo-services', timeRange],
    queryFn: () => fetchWithAuth(`${API}/services?time_range=${timeRange}`, token),
    refetchInterval: 30000,
  })

  const services = data?.services || []
  const summary = data?.summary || { total: 0, healthy: 0, at_risk: 0, breached: 0 }
  const s = summaryData || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Target className="w-7 h-7 text-blue-400" />
            Service Level Objectives
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Track availability, performance and health against your targets
          </p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      {/* Global SLI overview cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SLICard
          title="Platform Availability"
          icon={<Activity className="w-4 h-4 text-green-400" />}
          value={s.availability_pct ?? null}
          unit="%"
          targetLabel={`≥ ${s.defaults?.availability ?? 99}%`}
          budget={s.error_budget_availability ?? null}
          status={s.status_availability || 'no_data'}
          hint={`${summary.total} service${summary.total !== 1 ? 's' : ''} monitored`}
        />
        <SLICard
          title="Worst P95 Latency"
          icon={<Gauge className="w-4 h-4 text-blue-400" />}
          value={s.latency_p95_ms ?? null}
          unit="ms"
          targetLabel={`≤ ${s.defaults?.latency ?? 1000} ms`}
          budget={s.error_budget_latency ?? null}
          status={s.status_latency || 'no_data'}
          hint="Slowest service across your fleet"
        />
        <SLICard
          title="Health Score"
          icon={<Heart className="w-4 h-4 text-purple-400" />}
          value={s.health_score_avg ?? null}
          unit="/100"
          targetLabel={`≥ ${s.defaults?.health_score ?? 70}`}
          budget={s.error_budget_health ?? null}
          status={s.status_health || 'no_data'}
          hint="AI-powered anomaly assessment"
        />
      </div>

      {/* Service count stats */}
      <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl px-6 py-4">
        <div className="flex items-center gap-6">
          <CompactStat label="Services" value={summary.total} color="text-slate-900" />
          <div className="w-px h-8 bg-slate-200" />
          <CompactStat label="Meeting SLO" value={summary.healthy} color="text-green-400" />
          <CompactStat label="At Risk" value={summary.at_risk} color="text-yellow-400" />
          <CompactStat label="Breached" value={summary.breached} color="text-red-400" />
        </div>
        <div className="hidden sm:flex items-center gap-2">
          {s.overall_status && s.overall_status !== 'no_data' && <StatusBadge status={s.overall_status} />}
        </div>
      </div>

      {/* Loading / error */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Failed to load SLO data
        </div>
      )}

      {/* Desktop table */}
      {!isLoading && services.length > 0 && (
        <div className="hidden md:block bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500 uppercase tracking-wider">
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Availability</th>
                <th className="px-4 py-3">P95 Latency</th>
                <th className="px-4 py-3">Health</th>
                <th className="px-4 py-3">Error Budget</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc: any) => (
                <ServiceRow key={svc.service_id} svc={svc} token={token} timeRange={timeRange} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Mobile cards */}
      {!isLoading && services.length > 0 && (
        <div className="md:hidden space-y-4">
          {services.map((svc: any) => (
            <MobileServiceCard key={svc.service_id} svc={svc} token={token} timeRange={timeRange} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && services.length === 0 && (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-xl">
          <Shield className="w-14 h-14 text-gray-600 mx-auto mb-4" />
          <p className="text-slate-800 text-lg font-medium">No services monitored yet</p>
          <p className="text-gray-500 text-sm mt-2 max-w-md mx-auto">
            Add external services (HTTP endpoints or databases) to start tracking
            availability, latency, and health against your SLO targets.
          </p>
          <a
            href="/services"
            className="inline-flex items-center gap-2 mt-5 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Server className="w-4 h-4" /> Add a Service
          </a>
        </div>
      )}
    </div>
  )
}
