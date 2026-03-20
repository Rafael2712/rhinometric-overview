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
} from 'lucide-react'

/* ── helpers ────────────────────────────────────────────────── */

const API = '/api/slo'

async function fetchWithAuth(url: string, token: string) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

/* ── tiny components ────────────────────────────────────────── */

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; icon: React.ReactNode; label: string }> = {
    healthy:  { bg: 'bg-green-900/30',  text: 'text-green-400',  icon: <CheckCircle2 className="w-3.5 h-3.5" />, label: 'Healthy' },
    at_risk:  { bg: 'bg-yellow-900/30', text: 'text-yellow-400', icon: <AlertTriangle className="w-3.5 h-3.5" />, label: 'At Risk' },
    breached: { bg: 'bg-red-900/30',    text: 'text-red-400',    icon: <XCircle className="w-3.5 h-3.5" />, label: 'Breached' },
    no_data:  { bg: 'bg-gray-800/50',   text: 'text-gray-500',   icon: <Clock className="w-3.5 h-3.5" />, label: 'No Data' },
  }
  const s = map[status] || map.no_data
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      {s.icon} {s.label}
    </span>
  )
}

function TypeBadge({ type }: { type: string }) {
  const color = type === 'http' ? 'text-blue-400 bg-blue-900/30' : 'text-purple-400 bg-purple-900/30'
  return <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${color}`}>{type}</span>
}

function DataSourceBadge({ monitoringMode }: { source?: string; monitoringMode?: string }) {
  const isTelemetry = monitoringMode === 'telemetry_enabled'
  if (isTelemetry) {
    return <span className="px-2 py-0.5 rounded text-xs font-medium text-green-400 bg-green-900/30">Telemetry + Synthetic</span>
  }
  return <span className="px-2 py-0.5 rounded text-xs font-medium text-amber-400 bg-amber-900/30">Synthetic only</span>
}

function StatCard({ title, value, sub, color }: { title: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-5">
      <p className="text-sm text-gray-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function BudgetBar({ pct }: { pct: number | null }) {
  if (pct === null) return <span className="text-gray-500 text-xs">—</span>
  const color = pct >= 50 ? 'bg-green-500' : pct >= 20 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden max-w-[100px]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-12 text-right">{pct.toFixed(1)}%</span>
    </div>
  )
}

/* ── Detail panel (expandable row) ──────────────────────────── */

function ServiceDetailPanel({ serviceId, token, timeRange }: { serviceId: number; token: string; timeRange: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['slo-detail', serviceId, timeRange],
    queryFn: () => fetchWithAuth(`${API}/services/${serviceId}?time_range=${timeRange}`, token),
    refetchInterval: 60000,
  })

  if (isLoading) return <div className="p-6 text-gray-400">Loading detail…</div>
  if (!data) return null

  const svc = data.service
  const trend = data.availability_trend || []
  const alerts = data.recent_alerts || []
  const incidents = data.recent_incidents || []

  return (
    <div className="p-6 bg-gray-900/50 border-t border-gray-700/50 grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: metrics */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-300 mb-2">SLO Metrics</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500">Availability</p>
            <p className="text-white font-medium">{svc.availability_pct !== null ? `${svc.availability_pct}%` : '—'}</p>
          </div>
          <div>
            <p className="text-gray-500">SLO Target</p>
            <p className="text-white font-medium">{svc.slo_target_pct}%</p>
          </div>
          <div>
            <p className="text-gray-500">Avg Latency</p>
            <p className="text-white font-medium">{svc.avg_latency_ms !== null ? `${svc.avg_latency_ms} ms` : '—'}</p>
          </div>
          <div>
            <p className="text-gray-500">P95 Latency</p>
            <p className="text-white font-medium">{svc.p95_latency_ms !== null ? `${svc.p95_latency_ms} ms` : '—'}</p>
          </div>
          <div>
            <p className="text-gray-500">Error Budget</p>
            <p className="text-white font-medium">{svc.error_budget_remaining_pct !== null ? `${svc.error_budget_remaining_pct}%` : '—'}</p>
          </div>
          <div>
            <p className="text-gray-500">Checks</p>
            <p className="text-white font-medium">{svc.successful_checks}/{svc.total_checks}</p>
          </div>
        </div>
      </div>

      {/* Center: availability trend (simple text table) */}
      <div>
        <h4 className="text-sm font-semibold text-gray-300 mb-2">Availability Trend (hourly)</h4>
        <div className="max-h-48 overflow-y-auto space-y-1 text-xs">
          {trend.length === 0 && <p className="text-gray-500">No trend data</p>}
          {trend.slice(-12).map((b: { time: string; availability_pct: number; avg_latency_ms: number }) => (
            <div key={b.time} className="flex justify-between text-gray-400">
              <span>{b.time.split(' ')[1] || b.time}</span>
              <span className={b.availability_pct >= 99 ? 'text-green-400' : b.availability_pct >= 95 ? 'text-yellow-400' : 'text-red-400'}>
                {b.availability_pct}%
              </span>
              <span>{b.avg_latency_ms} ms</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right: recent alerts + incidents */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Recent Alerts ({alerts.length})</h4>
          {alerts.length === 0 && <p className="text-xs text-gray-500">None in this window</p>}
          {alerts.slice(0, 5).map((a: { id: string; alert_name: string; severity: string; status: string }) => (
            <div key={a.id} className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <span className={`w-2 h-2 rounded-full ${a.status === 'firing' ? 'bg-red-500' : 'bg-green-500'}`} />
              <span className="truncate">{a.alert_name}</span>
              <span className="text-gray-600">{a.severity}</span>
            </div>
          ))}
        </div>
        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Recent Incidents ({incidents.length})</h4>
          {incidents.length === 0 && <p className="text-xs text-gray-500">None in this window</p>}
          {incidents.slice(0, 5).map((inc: { id: string; status: string; severity: string; started_at: string }) => (
            <div key={inc.id} className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <StatusBadge status={inc.status === 'resolved' ? 'healthy' : 'breached'} />
              <span className="text-gray-600">{inc.severity}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── Service row ────────────────────────────────────────────── */

function ServiceRow({ svc, token, timeRange }: { svc: any; token: string; timeRange: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr
        className="border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="px-4 py-3 text-sm">
          <span className="text-gray-400">{expanded ? <ChevronDown className="w-4 h-4 inline" /> : <ChevronRight className="w-4 h-4 inline" />}</span>
        </td>
        <td className="px-4 py-3 text-sm font-medium text-white">{svc.service_name}</td>
        <td className="px-4 py-3 text-sm"><TypeBadge type={svc.service_type} /></td>
        <td className="px-4 py-3 text-sm">
          {svc.availability_pct !== null ? (
            <span className={svc.availability_pct >= 99 ? 'text-green-400' : svc.availability_pct >= 95 ? 'text-yellow-400' : 'text-red-400'}>
              {svc.availability_pct}%
            </span>
          ) : <span className="text-gray-500">—</span>}
        </td>
        <td className="px-4 py-3 text-sm text-gray-300">{svc.avg_latency_ms !== null ? `${svc.avg_latency_ms} ms` : '—'}</td>
        <td className="px-4 py-3 text-sm text-gray-300">{svc.p95_latency_ms !== null ? `${svc.p95_latency_ms} ms` : '—'}</td>
        <td className="px-4 py-3 text-sm text-gray-300">{svc.incident_count}</td>
        <td className="px-4 py-3 text-sm text-gray-300">{svc.alert_count}</td>
        <td className="px-4 py-3 text-sm text-gray-300">{svc.slo_target_pct}%</td>
        <td className="px-4 py-3 text-sm"><BudgetBar pct={svc.error_budget_remaining_pct} /></td>
        <td className="px-4 py-3 text-sm"><DataSourceBadge source={svc.data_source} monitoringMode={svc.monitoring_mode} /></td>
        <td className="px-4 py-3 text-sm"><StatusBadge status={svc.slo_status} /></td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={12} className="p-0">
            <ServiceDetailPanel serviceId={svc.service_id} token={token} timeRange={timeRange} />
          </td>
        </tr>
      )}
    </>
  )
}

/* ── Mobile card ────────────────────────────────────────────── */

function MobileServiceCard({ svc, token, timeRange }: { svc: any; token: string; timeRange: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white font-medium">{svc.service_name}</p>
          <TypeBadge type={svc.service_type} />
        </div>
        <StatusBadge status={svc.slo_status} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-gray-500 text-xs">Availability</p>
          <p className={`font-medium ${svc.availability_pct !== null && svc.availability_pct >= 99 ? 'text-green-400' : 'text-yellow-400'}`}>
            {svc.availability_pct !== null ? `${svc.availability_pct}%` : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">P95 Latency</p>
          <p className="text-gray-300 font-medium">{svc.p95_latency_ms !== null ? `${svc.p95_latency_ms} ms` : '—'}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs">Error Budget</p>
          <BudgetBar pct={svc.error_budget_remaining_pct} />
        </div>
        <div>
          <p className="text-gray-500 text-xs">Incidents / Alerts</p>
          <p className="text-gray-300 font-medium">{svc.incident_count} / {svc.alert_count}</p>
        </div>
      </div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-blue-400 hover:text-blue-300"
      >
        {expanded ? 'Hide detail' : 'Show detail'}
      </button>
      {expanded && <ServiceDetailPanel serviceId={svc.service_id} token={token} timeRange={timeRange} />}
    </div>
  )
}

/* ── Main page ──────────────────────────────────────────────── */

export function SLOPage() {
  const token = useAuthStore((s) => s.token) || ''
  const [timeRange, setTimeRange] = useState('24h')

  const { data, isLoading, error } = useQuery({
    queryKey: ['slo-services', timeRange],
    queryFn: () => fetchWithAuth(`${API}/services?time_range=${timeRange}`, token),
    refetchInterval: 30000,
  })

  const services = data?.services || []
  const summary = data?.summary || { total: 0, healthy: 0, at_risk: 0, breached: 0 }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-7 h-7 text-blue-400" />
            SLO / SLA Tracking
          </h1>
          <p className="text-gray-400 text-sm mt-1">Service-level objectives and error budgets</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Services" value={summary.total} color="text-white" sub="Monitored" />
        <StatCard title="Meeting SLO" value={summary.healthy} color="text-green-400" sub="Healthy" />
        <StatCard title="At Risk" value={summary.at_risk} color="text-yellow-400" sub="Budget low" />
        <StatCard title="Breached" value={summary.breached} color="text-red-400" sub="Below target" />
      </div>

      {/* Loading / error */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      )}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400 text-sm">
          Failed to load SLO data
        </div>
      )}

      {/* Desktop table */}
      {!isLoading && services.length > 0 && (
        <div className="hidden md:block bg-gray-800/30 border border-gray-700/50 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700 text-left text-xs text-gray-400 uppercase tracking-wider">
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Availability</th>
                <th className="px-4 py-3">Avg Latency</th>
                <th className="px-4 py-3">P95 Latency</th>
                <th className="px-4 py-3">Incidents</th>
                <th className="px-4 py-3">Alerts</th>
                <th className="px-4 py-3">SLO Target</th>
                <th className="px-4 py-3">Budget</th>
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
        <div className="text-center py-16">
          <Server className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">No monitored services found</p>
          <p className="text-gray-500 text-sm mt-1">Add external services to start tracking SLOs</p>
        </div>
      )}
    </div>
  )
}
