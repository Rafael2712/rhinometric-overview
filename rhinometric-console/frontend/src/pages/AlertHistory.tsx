import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Clock, Filter, Download, Bell, CheckCircle2, XCircle,
  AlertTriangle, Shield, Activity, ChevronDown, ChevronUp,
  Timer, BarChart3
} from 'lucide-react'

/* ── Types ─────────────────────────────────────────────────────── */

interface AlertEvent {
  id: string
  alert_name: string
  entity_type: string
  entity_name: string
  metric_name: string
  severity: string
  status: string
  started_at: string | null
  ended_at: string | null
  duration_seconds: number | null
  fingerprint: string
  summary: string
  source: string
  labels: Record<string, string> | null
  created_at: string | null
}

interface AlertEventResponse {
  alert_events: AlertEvent[]
  total: number
  limit: number
  offset: number
}

interface AlertStats {
  total: number
  firing: number
  resolved: number
  acknowledged: number
  avg_resolution_seconds: number | null
}

/* ── Helpers ───────────────────────────────────────────────────── */

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '—'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ${hrs % 24}h ago`
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

/* ── Status Badge ──────────────────────────────────────────────── */

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string; icon: typeof Bell }> = {
    firing: { bg: 'bg-red-500/20', text: 'text-red-400', icon: AlertTriangle },
    resolved: { bg: 'bg-green-500/20', text: 'text-green-400', icon: CheckCircle2 },
    acknowledged: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: Shield },
    suppressed: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: XCircle },
  }
  const c = config[status] || config.firing
  const Icon = c.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      <Icon size={12} />
      {status.toUpperCase()}
    </span>
  )
}

/* ── Severity Badge ────────────────────────────────────────────── */

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400',
    warning: 'bg-amber-500/20 text-amber-400',
    info: 'bg-blue-500/20 text-blue-400',
    low: 'bg-gray-500/20 text-gray-400',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[severity] || colors.info}`}>
      {severity.toUpperCase()}
    </span>
  )
}

/* ── Stat Card ─────────────────────────────────────────────────── */

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: typeof Bell; color: string
}) {
  return (
    <div className="bg-surface border border-gray-700 rounded-lg p-4 flex items-center gap-3">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
      </div>
    </div>
  )
}

/* ── Main Page ─────────────────────────────────────────────────── */

export function AlertHistoryPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Alert History'
  }, [])

  const token = useAuthStore((s) => s.token)
  const [timeRange, setTimeRange] = useState('24h')
  const [statusFilter, setStatusFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  // Fetch alert events
  const { data, isLoading, error } = useQuery<AlertEventResponse>({
    queryKey: ['alert-history', token, timeRange, statusFilter, severityFilter],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({ time_range: timeRange, limit: '200' })
      if (statusFilter !== 'all') params.set('status', statusFilter)
      if (severityFilter !== 'all') params.set('severity', severityFilter)
      const res = await fetch(`/api/alert-history?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch alert history')
      return res.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  // Fetch stats
  const { data: stats } = useQuery<AlertStats>({
    queryKey: ['alert-history-stats', token, timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const res = await fetch(`/api/alert-history/stats?time_range=${timeRange}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Failed to fetch stats')
      return res.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  const events = data?.alert_events || []

  // Export CSV
  const exportCSV = () => {
    const headers = ['Alert', 'Entity', 'Severity', 'Status', 'Started', 'Ended', 'Duration']
    const rows = events.map(e => [
      e.alert_name, e.entity_name, e.severity, e.status,
      e.started_at || '', e.ended_at || '',
      e.duration_seconds ? formatDuration(e.duration_seconds) : ''
    ])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `alert-history-${timeRange}.csv`; a.click()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-3">
            <Clock className="text-primary" size={28} />
            Alert History
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Complete alert lifecycle history — firing, resolved, acknowledged
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={exportCSV}
            className="flex items-center gap-2 px-3 py-2 bg-surface border border-gray-700 rounded-lg text-sm text-gray-300 hover:bg-surface-light transition-colors">
            <Download size={16} /> Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Events" value={stats.total} icon={BarChart3} color="bg-blue-500/20 text-blue-400" />
          <StatCard label="Firing" value={stats.firing} icon={AlertTriangle} color="bg-red-500/20 text-red-400" />
          <StatCard label="Resolved" value={stats.resolved} icon={CheckCircle2} color="bg-green-500/20 text-green-400" />
          <StatCard label="Avg Resolution" value={stats.avg_resolution_seconds ? formatDuration(stats.avg_resolution_seconds) : '—'} icon={Timer} color="bg-purple-500/20 text-purple-400" />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <span className="text-sm text-gray-400">Filters:</span>
        </div>

        <select value={timeRange} onChange={e => setTimeRange(e.target.value)}
          className="bg-surface border border-gray-700 text-white text-sm rounded-lg px-3 py-2">
          <option value="1h">Last 1h</option>
          <option value="6h">Last 6h</option>
          <option value="24h">Last 24h</option>
          <option value="7d">Last 7d</option>
          <option value="30d">Last 30d</option>
        </select>

        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="bg-surface border border-gray-700 text-white text-sm rounded-lg px-3 py-2">
          <option value="all">All Status</option>
          <option value="firing">Firing</option>
          <option value="resolved">Resolved</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="suppressed">Suppressed</option>
        </select>

        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}
          className="bg-surface border border-gray-700 text-white text-sm rounded-lg px-3 py-2">
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>

        <span className="text-xs text-gray-500 ml-auto">
          {data?.total ?? 0} event{(data?.total ?? 0) !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Loading / Error / Empty States */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          <span className="ml-3 text-gray-400">Loading alert history...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
          <XCircle className="mx-auto text-red-400 mb-2" size={32} />
          <p className="text-red-400 font-medium">Failed to load alert history</p>
          <p className="text-sm text-gray-400 mt-1">{String(error)}</p>
        </div>
      )}

      {!isLoading && !error && events.length === 0 && (
        <div className="bg-surface border border-gray-700 rounded-lg p-12 text-center">
          <Clock className="mx-auto text-gray-500 mb-3" size={48} />
          <h3 className="text-lg font-semibold text-gray-300">No Alert Events</h3>
          <p className="text-sm text-gray-500 mt-1">
            No alert events recorded in the selected time range.
          </p>
        </div>
      )}

      {/* Desktop Table */}
      {!isLoading && !error && events.length > 0 && (
        <div className="hidden md:block bg-surface border border-gray-700 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-surface-light border-b border-gray-700">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Alert</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Entity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Severity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Started</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Ended</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Duration</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-400 uppercase w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {events.map((ev) => (
                  <>
                    <tr key={ev.id}
                      className="hover:bg-surface-light/50 transition-colors cursor-pointer"
                      onClick={() => setExpandedRow(expandedRow === ev.id ? null : ev.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">{ev.alert_name}</div>
                        {ev.metric_name && (
                          <div className="text-xs text-gray-500 mt-0.5">{ev.metric_name}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-gray-300">{ev.entity_name || '—'}</div>
                        <div className="text-xs text-gray-500">{ev.entity_type}</div>
                      </td>
                      <td className="px-4 py-3">
                        <SeverityBadge severity={ev.severity} />
                      </td>
                      <td className="px-4 py-3 text-gray-300 whitespace-nowrap">
                        <div>{formatTimestamp(ev.started_at)}</div>
                        <div className="text-xs text-gray-500">{timeAgo(ev.started_at)}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-300 whitespace-nowrap">
                        {ev.ended_at ? (
                          <>
                            <div>{formatTimestamp(ev.ended_at)}</div>
                            <div className="text-xs text-gray-500">{timeAgo(ev.ended_at)}</div>
                          </>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`font-mono text-sm ${
                          ev.status === 'firing' ? 'text-red-400' :
                          ev.duration_seconds && ev.duration_seconds > 3600 ? 'text-amber-400' : 'text-gray-300'
                        }`}>
                          {ev.status === 'firing' ? (
                            <span className="flex items-center gap-1">
                              <Activity size={14} className="animate-pulse" />
                              {timeAgo(ev.started_at)}
                            </span>
                          ) : formatDuration(ev.duration_seconds)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={ev.status} />
                      </td>
                      <td className="px-4 py-3 text-center">
                        {expandedRow === ev.id ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                      </td>
                    </tr>
                    {expandedRow === ev.id && (
                      <tr key={`${ev.id}-detail`} className="bg-surface-light/30">
                        <td colSpan={8} className="px-6 py-4">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500 block text-xs">Fingerprint</span>
                              <span className="text-gray-300 font-mono text-xs">{ev.fingerprint}</span>
                            </div>
                            <div>
                              <span className="text-gray-500 block text-xs">Source</span>
                              <span className="text-gray-300">{ev.source || 'alertmanager'}</span>
                            </div>
                            <div>
                              <span className="text-gray-500 block text-xs">Created At</span>
                              <span className="text-gray-300">{formatTimestamp(ev.created_at)}</span>
                            </div>
                            <div>
                              <span className="text-gray-500 block text-xs">Entity Type</span>
                              <span className="text-gray-300">{ev.entity_type}</span>
                            </div>
                          </div>
                          {ev.summary && (
                            <div className="mt-3 p-3 bg-surface rounded border border-gray-700">
                              <span className="text-gray-500 text-xs block mb-1">Summary</span>
                              <span className="text-gray-300 text-sm">{ev.summary}</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Mobile Cards */}
      {!isLoading && !error && events.length > 0 && (
        <div className="md:hidden space-y-3">
          {events.map((ev) => (
            <div key={ev.id}
              className="bg-surface border border-gray-700 rounded-lg p-4 space-y-3"
              onClick={() => setExpandedRow(expandedRow === ev.id ? null : ev.id)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-white text-sm">{ev.alert_name}</h3>
                  <p className="text-xs text-gray-500">{ev.entity_name} · {ev.entity_type}</p>
                </div>
                <StatusBadge status={ev.status} />
              </div>
              <div className="flex items-center justify-between text-xs">
                <SeverityBadge severity={ev.severity} />
                <span className="text-gray-400">{timeAgo(ev.started_at)}</span>
                <span className="font-mono text-gray-300">
                  {ev.status === 'firing' ? 'ongoing' : formatDuration(ev.duration_seconds)}
                </span>
              </div>
              {expandedRow === ev.id && ev.summary && (
                <div className="pt-2 border-t border-gray-700 text-xs text-gray-400">
                  {ev.summary}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
