/* eslint-disable */
import { useState, useEffect, type ReactNode } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Bell, CheckCircle2, Search,
  Filter, ChevronDown, ChevronUp, Clock, Activity,
  Flame, Eye, BarChart3, MessageSquare, Tag, Plus, X, Send,
  Crosshair, Shield, Trash2, Loader2,
  Brain, Lightbulb, BookOpen, RefreshCw, ExternalLink, Zap
} from 'lucide-react'

/* -- Types -- */

interface IncidentSummary {
  id: string
  incident_key: string
  entity_name: string
  entity_type: string
  severity: string
  status: string
  started_at: string | null
  resolved_at: string | null
  duration_seconds: number | null
  alert_count: number
  created_at: string | null
  updated_at: string | null
  tags?: string[]
  // Phase 3 AI fields
  title?: string | null
  summary?: string | null
  investigation_hints?: string[]
  postmortem?: string | null
  anomaly_id?: string | null
  alert_fingerprint?: string | null
  // Phase 5.1 AI Briefing
  ai_briefing?: AiBriefing | null
  // Phase 5.2 AI Decision
  ai_decision?: AiDecision | null
}

interface AiBriefing {
  status_snapshot: string
  executive_summary: string
  likely_cause: string
  probable_cause?: string           // v1 compat
  operational_impact: string
  evidence: string[]
  recommended_actions: string[]
  related_alerts: Array<{ alert_name: string; severity: string; status: string; started_at: string | null; ended_at?: string | null }>
  related_anomalies: Array<{ service: string; score: number | null; severity: string | null; predicted_risk: string | null; timestamp: string | null }>
  confidence_explanation: string
  confidence: 'high' | 'medium' | 'low'
  generated_at: string
  engine: string
  model: string | null
}

interface AiDecision {
  decision: 'ignore' | 'monitor' | 'notify' | 'escalate'
  confidence: 'low' | 'medium' | 'high'
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  summary: string
  reason: string
  evidence: string[]
  recommended_actions: string[]
  noise_assessment: {
    is_likely_noise: boolean
    noise_reason: string
    recurrence_detected: boolean
  }
  customer_impact: 'none' | 'low' | 'medium' | 'high'
  created_at: string
  engine: string
  model: string | null
}

interface IncidentDetail {
  incident: IncidentSummary
  alert_events: AlertEventRow[]
  alert_count: number
}

interface AlertEventRow {
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
}

interface TimelineEvent {
  id: string
  event_type: string
  description: string | null
  created_by: string | null
  created_at: string | null
  metadata: Record<string, unknown> | null
}

interface Comment {
  id: string
  author: string
  comment: string
  created_at: string | null
}

interface RootCauseResult {
  incident_id: string
  likely_root_cause: {
    entity: string | null
    metric: string | null
    confidence: string
    description: string
  }
  score: number
  evidence: Array<{
    type: string
    metric?: string
    detail?: string
    value?: number
    baseline?: number
    factor?: number
    alert_name?: string
    severity?: string
    anomaly_score?: number
    entity?: string
    error_count?: number
    samples?: string[]
  }>
  signal_counts: {
    metric_spikes: number
    alerts: number
    anomalies: number
    log_errors: number
  }
  analyzed_at: string
}


interface IncidentStats {
  total: number
  open: number
  investigating: number
  resolved: number
  avg_resolution_seconds: number | null
}

/* -- Helpers -- */

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '\u2014'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

function timeAgo(iso: string | null): string {
  if (!iso) return '\u2014'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ${hrs % 24}h ago`
}

function formatTs(iso: string | null): string {
  if (!iso) return '\u2014'
  return new Date(iso).toLocaleString()
}

function liveDuration(startedAt: string | null, resolvedAt: string | null): string {
  if (!startedAt) return '\u2014'
  const start = new Date(startedAt).getTime()
  const end = resolvedAt ? new Date(resolvedAt).getTime() : Date.now()
  return formatDuration(Math.floor((end - start) / 1000))
}

/* -- Status Badge -- */

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; icon: typeof Bell }> = {
    open:          { bg: 'bg-red-500/20',    text: 'text-red-400',    icon: Flame },
    investigating: { bg: 'bg-blue-500/20',   text: 'text-blue-400',   icon: Eye },
    resolved:      { bg: 'bg-green-500/20',  text: 'text-green-400',  icon: CheckCircle2 },
  }
  const cfg = map[status] || { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Bell }
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      <Icon size={12} />
      {status}
    </span>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    critical: { bg: 'bg-red-500/20',    text: 'text-red-400' },
    warning:  { bg: 'bg-amber-500/20',  text: 'text-amber-400' },
    info:     { bg: 'bg-sky-500/20',    text: 'text-sky-400' },
  }
  const cfg = map[severity] || { bg: 'bg-gray-500/20', text: 'text-gray-400' }
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {severity}
    </span>
  )
}

function PriorityBadge({ severity }: { severity: string }) {
  const p = severity === 'critical' ? { label: 'P1', bg: 'bg-red-100 dark:bg-red-500/20', text: 'text-red-700 dark:text-red-400', border: 'border-red-300 dark:border-red-500/30' }
    : severity === 'warning' ? { label: 'P2', bg: 'bg-amber-100 dark:bg-amber-500/20', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-300 dark:border-amber-500/30' }
    : { label: 'P3', bg: 'bg-slate-100 dark:bg-gray-500/20', text: 'text-slate-500 dark:text-gray-400', border: 'border-slate-300 dark:border-gray-500/30' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold border ${p.bg} ${p.text} ${p.border}`}>
      {p.label}
    </span>
  )
}

function AlertStatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    firing:       { bg: 'bg-red-500/20',    text: 'text-red-400' },
    resolved:     { bg: 'bg-green-500/20',  text: 'text-green-400' },
    acknowledged: { bg: 'bg-blue-500/20',   text: 'text-blue-400' },
  }
  const cfg = map[status] || { bg: 'bg-gray-500/20', text: 'text-gray-400' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {status}
    </span>
  )
}

/* -- Stat Card -- */

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: typeof Bell; color: string
}) {
  return (
    <div className="bg-white dark:bg-surface rounded-lg border border-slate-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
        </div>
        <div className={`p-2 rounded-lg bg-gray-800/50`}>
          <Icon size={20} className={color} />
        </div>
      </div>
    </div>
  )
}

/* -- Main Page -- */

/* -- Task 4: Purge Modal -- */
function PurgeModal({ module, isOpen, onClose, token }: {
  module: 'alerts' | 'incidents' | 'anomalies'
  isOpen: boolean
  onClose: (purged: boolean) => void
  token: string | null
}) {
  const [days, setDays] = useState(30)
  const [confirming, setConfirming] = useState(false)
  const [result, setResult] = useState<{ deleted_count: number; message: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handlePurge = async () => {
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`/api/admin/purge/${module}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ confirm: true, older_than_days: days }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Purge failed')
      }
      const data = await res.json()
      setResult(data)
      setConfirming(false)
    } catch (e: any) {
      setError(e.message || 'Purge failed')
      setConfirming(false)
    }
  }

  const labels: Record<string, string> = {
    alerts: 'resolved/suppressed alert events',
    incidents: 'resolved incidents',
    anomalies: 'resolved/suppressed anomaly overrides',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Trash2 size={20} className="text-red-400" />
          Clear {module.charAt(0).toUpperCase() + module.slice(1)} History
        </h3>

        {result ? (
          <div className="space-y-4">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-green-400 text-sm">
              {result.message}
            </div>
            <button onClick={() => onClose(true)}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
              Close
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-300">
              Permanently delete <strong>{labels[module]}</strong> older than:
            </p>
            <div className="flex items-center gap-3">
              <input type="number" min={1} max={365} value={days}
                onChange={(e) => setDays(Math.max(1, Math.min(365, parseInt(e.target.value) || 30)))}
                className="w-24 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white text-sm" />
              <span className="text-sm text-gray-400">days</span>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {!confirming ? (
              <div className="flex gap-3">
                <button onClick={() => onClose(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
                  Cancel
                </button>
                <button onClick={() => setConfirming(true)}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm">
                  Purge
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
                  Warning: This action is irreversible. Are you sure?
                </div>
                <div className="flex gap-3">
                  <button onClick={() => setConfirming(false)}
                    className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
                    Cancel
                  </button>
                  <button onClick={handlePurge}
                    className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg text-sm font-semibold">
                    Confirm Purge
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export 
/* -- Simple Markdown renderer for AI content -- */
function SimpleMarkdown({ text, className = '' }: { text: string; className?: string }) {
  const lines = text.split('\n')
  const elements: React.ReactNode[] = []
  let listItems: string[] = []
  let key = 0

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={key++} className="list-disc list-inside space-y-1 my-2 text-gray-300">
          {listItems.map((item, i) => (
            <li key={i} className="leading-relaxed">{renderInline(item)}</li>
          ))}
        </ul>
      )
      listItems = []
    }
  }

  const renderInline = (line: string): React.ReactNode => {
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-gray-100 font-semibold">{part.slice(2, -2)}</strong>
      }
      return <span key={i}>{part}</span>
    })
  }

  for (const line of lines) {
    const trimmed = line.trim()

    if (!trimmed) {
      flushList()
      continue
    }

    if (trimmed.startsWith('## ')) {
      flushList()
      elements.push(
        <h3 key={key++} className="text-sm font-bold text-gray-200 mt-4 mb-2 first:mt-0">
          {renderInline(trimmed.slice(3))}
        </h3>
      )
      continue
    }

    if (trimmed.startsWith('- ')) {
      listItems.push(trimmed.slice(2))
      continue
    }

    flushList()
    elements.push(
      <p key={key++} className="text-sm text-gray-300 leading-relaxed mb-1">
        {renderInline(trimmed)}
      </p>
    )
  }

  flushList()
  return <div className={className}>{elements}</div>
}

function IncidentsPage() {
  const { token } = useAuthStore()
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }

  const [statusFilter, setStatusFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [entitySearch, setEntitySearch] = useState<string>('')
  const [timeRange, setTimeRange] = useState<string>('7d')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showPurge, setShowPurge] = useState(false)

  // Phase 3: auto-expand from query param (deep-link from Alerts)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const expandParam = params.get('expand')
    if (expandParam) {
      setExpandedId(expandParam)
      // Clean query param without reload
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  // List incidents
  const { data: listData, isLoading: listLoading } = useQuery({
    queryKey: ['incidents', statusFilter, severityFilter, entitySearch, timeRange],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      if (entitySearch) params.set('entity_name', entitySearch)
      if (timeRange) params.set('time_range', timeRange)
      params.set('limit', '100')
      const res = await fetch(`/api/incidents?${params}`, { headers })
      if (!res.ok) throw new Error('Failed to load incidents')
      return res.json() as Promise<{ incidents: IncidentSummary[]; total: number }>
    },
    refetchInterval: 30000,
  })

  // Stats
  const { data: stats } = useQuery({
    queryKey: ['incident-stats'],
    queryFn: async () => {
      const res = await fetch('/api/incidents/stats', { headers })
      if (!res.ok) throw new Error('Failed to load stats')
      return res.json() as Promise<IncidentStats>
    },
    refetchInterval: 30000,
  })

  // Incident detail (when expanded)
  const { data: detailData, isLoading: detailIsLoading } = useQuery({
    queryKey: ['incident-detail', expandedId],
    queryFn: async () => {
      if (!expandedId) return null
      const res = await fetch(`/api/incidents/${expandedId}`, { headers })
      if (!res.ok) throw new Error('Failed to load detail')
      return res.json() as Promise<IncidentDetail>
    },
    enabled: !!expandedId,
  })

  // Status mutation
  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const res = await fetch(`/api/incidents/${id}`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error('Failed to update')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      queryClient.invalidateQueries({ queryKey: ['incident-stats'] })
      queryClient.invalidateQueries({ queryKey: ['incident-detail'] })
    },
  })

  const incidents = listData?.incidents || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Incidents</h1>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">AI-powered incident management -- track, investigate, and resolve with contextual guidance</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-gray-400">
          <Activity size={14} className="text-green-400" />
          <span>{listData?.total ?? 0} incidents</span>
          {isAdmin() && (
            <button onClick={() => setShowPurge(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded-lg text-xs transition-colors ml-2">
              <Trash2 size={13} />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      <PurgeModal module="incidents" isOpen={showPurge} onClose={(purged) => { setShowPurge(false); if (purged) queryClient.invalidateQueries({ queryKey: ['incidents'] }) }} token={token} />

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total" value={stats.total} icon={BarChart3} color="text-slate-700 dark:text-gray-300" />
          <StatCard label="Open" value={stats.open} icon={Flame} color="text-red-400" />
          <StatCard label="Investigating" value={stats.investigating} icon={Eye} color="text-blue-400" />
          <StatCard label="Avg Resolution" value={stats.avg_resolution_seconds != null ? formatDuration(stats.avg_resolution_seconds) : '\u2014'} icon={Clock} color="text-green-400" />
        </div>
      )}

      {/* Filters */}
      <div className="bg-surface rounded-lg border border-gray-700 p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-gray-300">Filters</span>
          </div>

          <div className="flex flex-wrap gap-2 flex-1">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-600 rounded-md px-3 py-1.5 text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="24h">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="">All time</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-600 rounded-md px-3 py-1.5 text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All statuses</option>
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
            </select>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-600 rounded-md px-3 py-1.5 text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>

            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                placeholder="Search entity..."
                className="bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-600 rounded-md pl-8 pr-3 py-1.5 text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-primary w-48"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Incidents table -- desktop */}
      <div className="hidden md:block bg-white dark:bg-surface rounded-lg border border-slate-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 dark:bg-gray-800/50 text-left text-xs uppercase tracking-wider text-slate-500 dark:text-gray-400">
                <th className="px-4 py-3">Pri</th>
                <th className="px-4 py-3">Incident</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Started</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Alerts</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-gray-700/50">
              {listLoading && (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              )}
              {!listLoading && incidents.length === 0 && (
                <tr><td colSpan={9} className="px-4 py-12 text-center">
                  <div className="flex flex-col items-center">
                    <Shield size={40} className="text-gray-600 mb-3" />
                    <p className="text-slate-800 dark:text-gray-300 text-base font-semibold mb-1">No customer incidents</p>
                    <p className="text-slate-500 dark:text-gray-500 text-sm">There are currently no incidents affecting customer services.</p>
                    <p className="text-slate-400 dark:text-gray-600 text-xs mt-2">Create incidents from the Alerts page when anomalies are detected.</p>
                  </div>
                </td></tr>
              )}
              {incidents.map((inc) => {
                const isExpanded = expandedId === inc.id
                return (
                  <IncidentRow
                    key={inc.id}
                    inc={inc}
                    isExpanded={isExpanded}
                    detail={isExpanded ? detailData : null}
                    onToggle={() => setExpandedId(isExpanded ? null : inc.id)}
                    onStatusChange={(status) => statusMutation.mutate({ id: inc.id, status })}
                    isMutating={statusMutation.isPending}
                  />
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incidents cards -- mobile */}
      <div className="md:hidden space-y-3">
        {listLoading && <p className="text-center text-gray-400 py-8">Loading...</p>}
        {!listLoading && incidents.length === 0 && (
          <div className="bg-surface rounded-lg border border-gray-700 p-12 text-center">
            <Shield size={40} className="mx-auto text-gray-600 mb-3" />
            <p className="text-gray-300 text-base font-semibold mb-1">No customer incidents</p>
            <p className="text-gray-500 text-sm">There are currently no incidents affecting customer services.</p>
            <p className="text-slate-500 dark:text-gray-500 text-xs mt-2">Create incidents from the Alerts page when anomalies are detected.</p>
          </div>
        )}
        {incidents.map((inc) => (
          <MobileIncidentCard
            key={inc.id}
            inc={inc}
            isExpanded={expandedId === inc.id}
            detail={expandedId === inc.id ? detailData ?? undefined : undefined}
            onToggle={() => setExpandedId(expandedId === inc.id ? null : inc.id)}
            detailLoading={detailIsLoading}
            onStatusChange={(status) => statusMutation.mutate({ id: inc.id, status })}
          />
        ))}
      </div>
    </div>
  )
}

/* -- Desktop Row -- */

function IncidentRow({ inc, isExpanded, detail, onToggle, onStatusChange, isMutating }: {
  inc: IncidentSummary
  isExpanded: boolean
  detail: IncidentDetail | null | undefined
  onToggle: () => void
  onStatusChange: (s: string) => void
  isMutating: boolean
}) {
  return (
    <>
      <tr
        className="hover:bg-slate-50 dark:hover:bg-gray-800/30 cursor-pointer transition-colors"
        onClick={onToggle}
      >
        <td className="px-4 py-3">
          <PriorityBadge severity={inc.severity} />
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {isExpanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
            <div>
              <span className="text-slate-900 dark:text-gray-200 text-sm font-medium">{inc.title || inc.entity_name}</span>
              <p className="text-slate-500 dark:text-gray-500 font-mono text-xs">{inc.incident_key}</p>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-slate-700 dark:text-gray-300">{inc.entity_name}</td>
        <td className="px-4 py-3"><SeverityBadge severity={inc.severity} /></td>
        <td className="px-4 py-3"><StatusBadge status={inc.status} /></td>
        <td className="px-4 py-3 text-slate-500 dark:text-gray-400 text-xs" title={formatTs(inc.started_at)}>{timeAgo(inc.started_at)}</td>
        <td className="px-4 py-3 text-slate-500 dark:text-gray-400 text-xs">{liveDuration(inc.started_at, inc.resolved_at)}</td>
        <td className="px-4 py-3">
          <span className="inline-flex items-center gap-1 text-slate-700 dark:text-gray-300">
            <Bell size={12} className="text-gray-500" />{inc.alert_count}
          </span>
        </td>
        <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-1.5">
            {inc.status === 'open' && (
              <button
                onClick={() => onStatusChange('investigating')}
                disabled={isMutating}
                className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-50"
              >
                Investigate
              </button>
            )}
            {(inc.status === 'open' || inc.status === 'investigating') && (
              <button
                onClick={() => onStatusChange('resolved')}
                disabled={isMutating}
                className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors disabled:opacity-50"
              >
                Resolve
              </button>
            )}
          </div>
        </td>
      </tr>

      {/* Expanded detail */}
      {isExpanded && (
        <tr>
          <td colSpan={9} className="px-4 py-4 bg-slate-50 dark:bg-gray-800/20 border-t border-slate-200 dark:border-gray-700/50">
            {!detail ? (
              <p className="text-sm text-gray-400">Loading alert events...</p>
            ) : (
              <IncidentDetailPanel detail={detail} />
            )}
          </td>
        </tr>
      )}
    </>
  )
}

/* -- Expanded Detail Panel -- */

function IncidentDetailPanel({ detail }: { detail: IncidentDetail }) {
  const events = detail.alert_events || []
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }
  const incidentId = detail.incident.id
  const inc = detail.incident

  const [activeTab, setActiveTab] = useState<'summary' | 'alerts' | 'timeline' | 'comments' | 'root-cause' | 'briefing' | 'decision'>('summary')
  const [newComment, setNewComment] = useState('')
  const [newTag, setNewTag] = useState('')
  const [regenerating, setRegenerating] = useState(false)

  // Timeline query
  const { data: timelineData } = useQuery({
    queryKey: ['incident-timeline', incidentId],
    queryFn: async () => {
      const res = await fetch(`/api/incidents/${incidentId}/timeline`, { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<{ timeline: TimelineEvent[] }>
    },
    refetchInterval: 15000,
  })

  // Comments query
  const { data: commentsData } = useQuery({
    queryKey: ['incident-comments', incidentId],
    queryFn: async () => {
      const res = await fetch(`/api/incidents/${incidentId}/comments`, { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<{ comments: Comment[] }>
    },
    refetchInterval: 15000,
  })

  // Root Cause query (Phase 2.7)
  const { data: rootCauseData, isLoading: rootCauseLoading, refetch: refetchRootCause } = useQuery({
    queryKey: ['incident-root-cause', incidentId],
    queryFn: async () => {
      const res = await fetch(`/api/incidents/${incidentId}/root-cause`, { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<RootCauseResult>
    },
    enabled: activeTab === 'root-cause',
    staleTime: 30000,
  })

  // AI Decision mutation (Phase 5.2)
  const decisionMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/incidents/${incidentId}/ai-decision`, {
        method: 'POST',
        headers,
      })
      if (!res.ok) throw new Error('Failed to generate decision')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident-detail', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['incident-detail'] })
    },
  })

  // AI Briefing mutation (Phase 5.1)
  const briefingMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/incidents/${incidentId}/ai-briefing`, {
        method: 'POST',
        headers,
      })
      if (!res.ok) throw new Error('Failed to generate briefing')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident-detail', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['incident-detail'] })
    },
  })

  // Add comment mutation
  const commentMutation = useMutation({
    mutationFn: async (comment: string) => {
      const res = await fetch(`/api/incidents/${incidentId}/comments`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment }),
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    onSuccess: () => {
      setNewComment('')
      queryClient.invalidateQueries({ queryKey: ['incident-comments', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['incident-timeline', incidentId] })
    },
  })

  // Tags mutation
  const tagsMutation = useMutation({
    mutationFn: async (tags: string[]) => {
      const res = await fetch(`/api/incidents/${incidentId}/tags`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags }),
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident-detail'] })
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
      queryClient.invalidateQueries({ queryKey: ['incident-timeline', incidentId] })
    },
  })

  // Phase 3: Regenerate AI content
  const handleRegenerate = async () => {
    setRegenerating(true)
    try {
      const res = await fetch(`/api/incidents/${incidentId}/regenerate-ai`, {
        method: 'POST',
        headers,
      })
      if (res.ok) {
        queryClient.invalidateQueries({ queryKey: ['incident-detail'] })
        queryClient.invalidateQueries({ queryKey: ['incident-timeline', incidentId] })
      }
    } catch (e) { /* ignore */ }
    setRegenerating(false)
  }

  const currentTags: string[] = inc.tags || []
  const timeline = timelineData?.timeline || []
  const comments = commentsData?.comments || []
  const hints = inc.investigation_hints || []

  const addTag = () => {
    const tag = newTag.trim().toLowerCase()
    if (tag && !currentTags.includes(tag)) {
      tagsMutation.mutate([...currentTags, tag])
      setNewTag('')
    }
  }

  const removeTag = (tag: string) => {
    tagsMutation.mutate(currentTags.filter((t) => t !== tag))
  }

  const handleCommentSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (newComment.trim()) commentMutation.mutate(newComment.trim())
  }

  const eventTypeIcon: Record<string, { color: string; label: string }> = {
    incident_created:      { color: 'text-red-400',    label: 'Incident created' },
    alert_linked:          { color: 'text-amber-400',  label: 'Alert linked' },
    investigation_started: { color: 'text-blue-400',   label: 'Investigation started' },
    comment_added:         { color: 'text-purple-400', label: 'Comment added' },
    incident_resolved:     { color: 'text-green-400',  label: 'Incident resolved' },
    tag_added:             { color: 'text-cyan-400',   label: 'Tag added' },
    tag_removed:           { color: 'text-gray-400',   label: 'Tag removed' },
    status_changed:        { color: 'text-blue-400',   label: 'Status changed' },
    ai_analysis:           { color: 'text-purple-400', label: 'AI analysis' },
    ai_regenerated:        { color: 'text-purple-400', label: 'AI regenerated' },
    postmortem_generated:  { color: 'text-green-400',  label: 'Postmortem generated' },
  }

  return (
    <div className="space-y-3">
      {/* Header info */}
      <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-gray-400 flex-wrap">
        <span>ID: <span className="font-mono text-slate-700 dark:text-gray-300">{inc.id.slice(0, 8)}</span></span>
        <span>|</span>
        <span>Created: {formatTs(inc.created_at)}</span>
        {inc.resolved_at && (
          <>
            <span>|</span>
            <span>Resolved: {formatTs(inc.resolved_at)}</span>
          </>
        )}
        {/* Deep links */}
        <span>|</span>
        <a href={`/alerts`} className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors">
          <ExternalLink size={10} /> Alerts
        </a>
        <a href={`/ai-anomalies-v2?service=${encodeURIComponent(inc.entity_name)}${inc.anomaly_id ? `&anomaly_id=${encodeURIComponent(inc.anomaly_id)}` : ''}`}
           className="inline-flex items-center gap-1 text-purple-400 hover:text-purple-300 transition-colors">
          <Brain size={10} /> Anomaly Analysis
        </a>
      </div>

      {/* Tags section */}
      <div className="flex items-center gap-2 flex-wrap">
        <Tag size={14} className="text-gray-500" />
        {currentTags.map((tag) => (
          <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-cyan-50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800/50">
            {tag}
            <button onClick={() => removeTag(tag)} className="hover:text-red-400 transition-colors"><X size={10} /></button>
          </span>
        ))}
        <div className="inline-flex items-center gap-1">
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag() } }}
            placeholder="Add tag..."
            className="bg-white dark:bg-gray-800/50 border border-slate-200 dark:border-gray-700 rounded px-2 py-0.5 text-xs text-slate-700 dark:text-gray-300 w-24 focus:outline-none focus:border-cyan-500"
          />
          <button onClick={addTag} className="text-gray-500 hover:text-cyan-400"><Plus size={14} /></button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-200 dark:border-gray-700 overflow-x-auto">
        {([
          { key: 'summary' as const, label: 'AI Summary', icon: Brain },
          { key: 'alerts' as const, label: `Alerts (${events.length})`, icon: Bell },
          { key: 'timeline' as const, label: `Timeline (${timeline.length})`, icon: Clock },
          { key: 'comments' as const, label: `Comments (${comments.length})`, icon: MessageSquare },
          { key: 'root-cause' as const, label: 'Root Cause', icon: Crosshair },
          { key: 'briefing' as const, label: 'AI Briefing', icon: Zap },
          { key: 'decision' as const, label: 'AI Triage', icon: Shield },
        ]).map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === key
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-500 dark:text-gray-500 hover:text-slate-800 dark:hover:text-gray-300'
            }`}
          >
            <TabIcon size={12} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content: AI Summary (Phase 3) */}
      {activeTab === 'summary' && (
        <div className="space-y-4">
          {/* AI Summary */}
          {inc.summary ? (
            <div className="rounded-lg border border-purple-200 dark:border-purple-500/20 bg-purple-50 dark:bg-purple-500/5 p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-purple-700 dark:text-purple-300 flex items-center gap-2">
                  <Brain size={14} className="text-purple-400" />
                  AI Summary
                </h4>
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors disabled:opacity-50"
                  title="Regenerate AI analysis from latest anomaly context"
                >
                  <RefreshCw size={10} className={regenerating ? 'animate-spin' : ''} />
                  {regenerating ? 'Regenerating...' : 'Refresh'}
                </button>
              </div>
              <SimpleMarkdown text={inc.summary} />
            </div>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-gray-700/50 bg-slate-50 dark:bg-gray-800/20 p-4 text-center">
              <Brain size={24} className="mx-auto text-gray-600 mb-2" />
              <p className="text-sm text-slate-500 dark:text-gray-500">No AI summary available</p>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="mt-2 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors disabled:opacity-50"
              >
                <RefreshCw size={10} className={regenerating ? 'animate-spin' : ''} />
                {regenerating ? 'Generating...' : 'Generate AI Summary'}
              </button>
            </div>
          )}

          {/* Investigation Hints */}
          {hints.length > 0 && (
            <div className="rounded-lg border border-amber-200 dark:border-amber-500/20 bg-amber-50 dark:bg-amber-500/5 p-4">
              <h4 className="text-sm font-semibold text-amber-700 dark:text-amber-300 flex items-center gap-2 mb-3">
                <Lightbulb size={14} className="text-amber-400" />
                Investigation Hints
              </h4>
              <ul className="space-y-2">
                {hints.map((hint, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-gray-300">
                    <span className="text-amber-600 dark:text-amber-500 mt-0.5 flex-shrink-0">{i + 1}.</span>
                    <span className="leading-relaxed">{hint}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Postmortem (only when resolved) */}
          {inc.postmortem && (
            <div className="rounded-lg border border-green-200 dark:border-green-500/20 bg-green-50 dark:bg-green-500/5 p-4">
              <h4 className="text-sm font-semibold text-green-700 dark:text-green-300 flex items-center gap-2 mb-3">
                <BookOpen size={14} className="text-green-400" />
                Postmortem
              </h4>
              <SimpleMarkdown text={inc.postmortem} />
            </div>
          )}

          {/* Quick info cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="bg-slate-50 dark:bg-gray-800/40 rounded-lg border border-slate-200 dark:border-gray-700/30 p-3 text-center">
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-1">Severity</p>
              <SeverityBadge severity={inc.severity} />
            </div>
            <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-1">Status</p>
              <StatusBadge status={inc.status} />
            </div>
            <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-1">Alerts</p>
              <p className="text-lg font-bold text-slate-900 dark:text-gray-200">{events.length}</p>
            </div>
            <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-1">Duration</p>
              <p className="text-sm font-medium text-slate-800 dark:text-gray-200">{liveDuration(inc.started_at, inc.resolved_at)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab content: Alerts */}
      {activeTab === 'alerts' && (
        <>
          {events.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No alert events linked yet</p>
          ) : (
            <div className="overflow-x-auto rounded-md border border-gray-700/50">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-50 dark:bg-gray-800/30 text-slate-500 dark:text-gray-400 uppercase tracking-wider text-left">
                    <th className="px-3 py-2">Alert</th>
                    <th className="px-3 py-2">Severity</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Started</th>
                    <th className="px-3 py-2">Ended</th>
                    <th className="px-3 py-2">Duration</th>
                    <th className="px-3 py-2">Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-gray-700/30">
                  {events.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-50 dark:hover:bg-gray-800/20">
                      <td className="px-3 py-2 text-slate-800 dark:text-gray-300 font-medium">{ev.alert_name}</td>
                      <td className="px-3 py-2"><SeverityBadge severity={ev.severity} /></td>
                      <td className="px-3 py-2"><AlertStatusBadge status={ev.status} /></td>
                      <td className="px-3 py-2 text-slate-500 dark:text-gray-400" title={formatTs(ev.started_at)}>{timeAgo(ev.started_at)}</td>
                      <td className="px-3 py-2 text-slate-500 dark:text-gray-400">{ev.ended_at ? timeAgo(ev.ended_at) : '\u2014'}</td>
                      <td className="px-3 py-2 text-slate-500 dark:text-gray-400">{formatDuration(ev.duration_seconds)}</td>
                      <td className="px-3 py-2 text-slate-500 dark:text-gray-400 max-w-xs truncate">{ev.summary || '\u2014'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Tab content: Timeline */}
      {activeTab === 'timeline' && (
        <div className="space-y-0">
          {timeline.length === 0 ? (
            <p className="text-sm text-gray-500 italic py-2">No timeline events</p>
          ) : (
            <div className="relative pl-4">
              <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gray-700" />
              {timeline.map((evt) => {
                const cfg = eventTypeIcon[evt.event_type] || { color: 'text-gray-400', label: evt.event_type }
                const ts = evt.created_at ? new Date(evt.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
                return (
                  <div key={evt.id} className="relative flex items-start gap-3 py-2">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1.5 ${cfg.color.replace('text-', 'bg-')} ring-2 ring-gray-900 z-10`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                        <span className="text-xs text-slate-500 dark:text-gray-500">{ts}</span>
                        {evt.created_by && <span className="text-xs text-slate-500 dark:text-gray-500">by {evt.created_by}</span>}
                      </div>
                      {evt.description && <p className="text-xs text-slate-600 dark:text-gray-400 mt-0.5">{evt.description}</p>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab content: Comments */}
      {activeTab === 'comments' && (
        <div className="space-y-3">
          {comments.length === 0 && (
            <p className="text-sm text-gray-500 italic py-2">No comments yet</p>
          )}
          {comments.map((c) => (
            <div key={c.id} className="bg-slate-50 dark:bg-gray-800/40 rounded-lg p-3 border border-slate-200 dark:border-gray-700/30">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-medium text-blue-600 dark:text-blue-400">{c.author}</span>
                <span className="text-xs text-slate-400 dark:text-gray-600">{c.created_at ? new Date(c.created_at).toLocaleString() : ''}</span>
              </div>
              <p className="text-sm text-slate-700 dark:text-gray-300 whitespace-pre-wrap">{c.comment}</p>
            </div>
          ))}

          <form onSubmit={handleCommentSubmit} className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 bg-white dark:bg-gray-800/50 border border-slate-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={!newComment.trim() || commentMutation.isPending}
              className="px-3 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 disabled:opacity-50 transition-colors"
            >
              <Send size={14} />
            </button>
          </form>
        </div>
      )}

      {/* Tab content: Root Cause */}
      {activeTab === 'root-cause' && (
        <div className="space-y-3">
          {rootCauseLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-400 py-4 justify-center">
              <Loader2 size={14} className="animate-spin" /> Analyzing root cause...
            </div>
          ) : rootCauseData ? (
            <>
              <div className="bg-gradient-to-br from-orange-500/5 to-red-500/5 rounded-lg border border-orange-500/20 p-4">
                <h4 className="text-sm font-semibold text-orange-300 mb-2 flex items-center gap-2">
                  <Crosshair size={14} /> Root Cause Analysis
                </h4>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {rootCauseData.likely_root_cause?.description || 'No root cause determined yet.'}
                </p>
                {rootCauseData.likely_root_cause?.entity && (
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 dark:text-gray-400">
                    <span>Entity: <span className="text-gray-300">{rootCauseData.likely_root_cause.entity}</span></span>
                    {rootCauseData.likely_root_cause.metric && (
                      <span>Metric: <span className="text-gray-300">{rootCauseData.likely_root_cause.metric}</span></span>
                    )}
                    <span>Confidence: <span className="text-gray-300">{rootCauseData.likely_root_cause.confidence}</span></span>
                  </div>
                )}
              </div>

              {rootCauseData.evidence && rootCauseData.evidence.length > 0 && (
                <div>
                  <h5 className="text-xs font-semibold text-gray-400 uppercase mb-2">Evidence ({rootCauseData.evidence.length})</h5>
                  <div className="space-y-2">
                    {rootCauseData.evidence.map((ev, i) => (
                      <div key={i} className="bg-slate-50 dark:bg-gray-800/40 rounded p-2 border border-slate-200 dark:border-gray-700/30 text-sm">
                        <span className="text-xs px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400 mr-2">{ev.type}</span>
                        <span className="text-slate-700 dark:text-gray-300">{ev.detail || ev.metric || 'Signal detected'}</span>
                        {ev.value !== undefined && (
                          <span className="text-xs text-gray-500 ml-2">
                            (value: {ev.value}{ev.baseline !== undefined ? `, baseline: ${ev.baseline}` : ''})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-4 gap-2">
                {Object.entries(rootCauseData.signal_counts || {}).map(([key, val]) => (
                  <div key={key} className="bg-slate-50 dark:bg-gray-800/40 rounded p-2 border border-slate-200 dark:border-gray-700/30 text-center">
                    <p className="text-lg font-bold text-slate-900 dark:text-gray-200">{val as number}</p>
                    <p className="text-xs text-slate-500 dark:text-gray-500">{key.replace(/_/g, ' ')}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-gray-500 pt-2 border-t border-slate-200 dark:border-gray-700/30">
                <span>Score: {rootCauseData.score.toFixed(2)}</span>
                <span>{'\u00b7'}</span>
                <span>Analyzed: {new Date(rootCauseData.analyzed_at).toLocaleString()}</span>
                <button onClick={() => refetchRootCause()} className="ml-auto text-blue-400 hover:text-blue-300">
                  <RefreshCw size={12} />
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <Crosshair size={24} className="mx-auto text-gray-600 mb-2" />
              <p className="text-sm text-gray-500">Root cause analysis unavailable</p>
              <button
                onClick={() => refetchRootCause()}
                className="mt-2 text-xs text-blue-400 hover:text-blue-300"
              >
                Retry Analysis
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab content: AI Triage Decision (Phase 5.2) */}
      {activeTab === 'decision' && (
        <div className="space-y-4">
          {inc.ai_decision ? (
            <AiDecisionPanel
              decision={inc.ai_decision}
              onRegenerate={() => decisionMutation.mutate()}
              isRegenerating={decisionMutation.isPending}
            />
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-gray-700/30 bg-slate-50 dark:bg-gray-800/20 p-6 text-center">
              <Shield size={28} className="mx-auto text-slate-400 mb-3" />
              <p className="text-sm font-medium text-slate-700 dark:text-gray-300 mb-1">AI Triage Decision</p>
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-4">
                Classify this incident: ignore, monitor, notify, or escalate — with evidence and recommended actions.
              </p>
              <button
                onClick={() => decisionMutation.mutate()}
                disabled={decisionMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 dark:bg-gray-700 text-white text-sm font-medium hover:bg-slate-800 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
              >
                {decisionMutation.isPending
                  ? <Loader2 size={14} className="animate-spin" />
                  : <Shield size={14} />}
                {decisionMutation.isPending ? 'Analysing...' : 'Run AI Triage'}
              </button>
              {decisionMutation.isError && (
                <p className="mt-2 text-xs text-red-500">Failed to generate decision. Try again.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab content: AI Briefing (Phase 5.1) */}
      {activeTab === 'briefing' && (
        <div className="space-y-4">
          {inc.ai_briefing && inc.ai_briefing.status_snapshot ? (
            <AiBriefingPanel
              briefing={inc.ai_briefing}
              onRegenerate={() => briefingMutation.mutate()}
              isRegenerating={briefingMutation.isPending}
            />
          ) : (
            <div className="rounded-lg border border-indigo-200 dark:border-indigo-500/20 bg-indigo-50 dark:bg-indigo-500/5 p-6 text-center">
              <Zap size={28} className="mx-auto text-indigo-400 mb-3" />
              <p className="text-sm font-medium text-slate-700 dark:text-gray-300 mb-1">AI Incident Briefing</p>
              <p className="text-xs text-slate-500 dark:text-gray-500 mb-4">
                Generate a structured 10-point operational briefing based on real incident data.
              </p>
              <button
                onClick={() => briefingMutation.mutate()}
                disabled={briefingMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {briefingMutation.isPending
                  ? <Loader2 size={14} className="animate-spin" />
                  : <Zap size={14} />}
                {briefingMutation.isPending ? 'Generating...' : 'Generate AI Briefing'}
              </button>
              {briefingMutation.isError && (
                <p className="mt-2 text-xs text-red-500">Failed to generate briefing. Try again.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* -- AiBriefingPanel component (Phase 5.1 v2) -- */

function AiBriefingPanel({
  briefing,
  onRegenerate,
  isRegenerating,
}: {
  briefing: AiBriefing
  onRegenerate: () => void
  isRegenerating: boolean
}) {
  const confBadge =
    briefing.confidence === 'high'
      ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-500/10 border-green-200 dark:border-green-500/20'
      : briefing.confidence === 'medium'
      ? 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/20'
      : 'text-slate-600 dark:text-gray-400 bg-slate-100 dark:bg-gray-700/30 border-slate-200 dark:border-gray-600/30'

  const sevColor = (sev: string) =>
    sev === 'critical'
      ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400'
      : sev === 'warning'
      ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400'
      : 'bg-slate-100 text-slate-600 dark:bg-gray-700/40 dark:text-gray-400'

  const statusColor = (st: string) =>
    st === 'firing' || st === 'escalated'
      ? 'text-red-600 dark:text-red-400'
      : st === 'resolved'
      ? 'text-green-600 dark:text-green-400'
      : 'text-slate-500 dark:text-gray-500'

  return (
    <div className="space-y-0.5">

      {/* ── Top strip: Status Snapshot ── */}
      <div className="rounded-lg bg-slate-100 dark:bg-gray-800/60 border border-slate-200 dark:border-gray-700/50 px-3 py-2 flex flex-wrap gap-x-4 gap-y-1 items-center">
        {(briefing.status_snapshot || '').split('  ·  ').map((part, i) => (
          <span key={i} className="text-xs font-medium text-slate-600 dark:text-gray-300">{part}</span>
        ))}
        <span className="ml-auto text-xs text-slate-400 dark:text-gray-500">
          {new Date(briefing.generated_at).toLocaleString()}
        </span>
      </div>

      {/* ── Header bar ── */}
      <div className="flex items-center justify-between pt-2 pb-1 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Zap size={13} className="text-indigo-500" />
          <span className="text-sm font-semibold text-slate-900 dark:text-white">AI Incident Briefing</span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${confBadge}`}>
            {briefing.confidence} confidence
          </span>
          <span className="text-xs text-slate-400 dark:text-gray-500">{briefing.engine}</span>
        </div>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 border border-indigo-200 dark:border-indigo-500/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={10} className={isRegenerating ? 'animate-spin' : ''} />
          {isRegenerating ? 'Regenerating...' : 'Regenerate'}
        </button>
      </div>

      {/* ── Sections 1–6 (text) ── */}
      <div className="space-y-2 pt-1">

        {/* § 1 Executive Summary */}
        <BriefingSection index={1} label="Executive Summary">
          <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">{briefing.executive_summary}</p>
        </BriefingSection>

        {/* § 2 Likely Cause */}
        <BriefingSection index={2} label="Likely Cause" accent="amber">
          <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">{briefing.likely_cause || briefing.probable_cause || '—'}</p>
        </BriefingSection>

        {/* § 3 Operational Impact */}
        <BriefingSection index={3} label="Operational Impact" accent="red">
          {(briefing.operational_impact || '').split('\n').map((line, i) => (
            <p key={i} className={`text-sm leading-relaxed ${
              i === 0
                ? 'font-semibold text-slate-800 dark:text-gray-200 mb-0.5'
                : 'text-slate-600 dark:text-gray-400'
            }`}>{line}</p>
          ))}
        </BriefingSection>

        {/* § 4 Evidence */}
        <BriefingSection index={4} label="Evidence Used" accent="blue">
          <ul className="space-y-1">
            {(briefing.evidence || []).map((e, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-gray-300">
                <span className="text-blue-400 dark:text-blue-500 flex-shrink-0 mt-0.5">▸</span>
                <span>{e}</span>
              </li>
            ))}
          </ul>
        </BriefingSection>

        {/* § 5 Recommended Actions */}
        <BriefingSection index={5} label="Recommended Actions" accent="green">
          <ol className="space-y-2">
            {(briefing.recommended_actions || []).map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700 dark:text-gray-300">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-400 text-xs font-bold flex items-center justify-center mt-0.5">{i + 1}</span>
                <span className="leading-relaxed">{a}</span>
              </li>
            ))}
          </ol>
        </BriefingSection>

        {/* § 6 Related Alerts */}
        {(briefing.related_alerts || []).length > 0 && (
          <BriefingSection index={6} label={`Related Alerts (${(briefing.related_alerts || []).length})`}>
            <div className="space-y-1.5">
              {(briefing.related_alerts || []).slice(0, 6).map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className={`px-1.5 py-0.5 rounded font-semibold ${sevColor(a.severity)}`}>{a.severity}</span>
                  <span className="text-slate-700 dark:text-gray-300 font-mono truncate flex-1">{a.alert_name}</span>
                  <span className={`font-medium ${statusColor(a.status)}`}>{a.status}</span>
                </div>
              ))}
            </div>
          </BriefingSection>
        )}

        {/* § 7 Related Anomalies */}
        {(briefing.related_anomalies || []).length > 0 && (
          <BriefingSection index={7} label={`Related Anomalies (${(briefing.related_anomalies || []).length})`} accent="indigo">
            <div className="space-y-1.5">
              {(briefing.related_anomalies || []).map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="text-indigo-600 dark:text-indigo-400 font-medium">{a.service}</span>
                  {a.severity && <span className="text-slate-500 dark:text-gray-500">{a.severity}</span>}
                  {a.predicted_risk && (
                    <span className="text-slate-400 dark:text-gray-500">risk: {a.predicted_risk}</span>
                  )}
                  {a.score != null && (
                    <span className="ml-auto text-slate-400 dark:text-gray-500">score: {a.score}</span>
                  )}
                </div>
              ))}
            </div>
          </BriefingSection>
        )}

        {/* § 8 Confidence Explanation */}
        <BriefingSection index={8} label="Confidence">
          <p className="text-sm text-slate-600 dark:text-gray-400 leading-relaxed">{briefing.confidence_explanation || `Confidence: ${briefing.confidence}`}</p>
        </BriefingSection>

      </div>
    </div>
  )
}

/* -- AiDecisionPanel component (Phase 5.2) -- */

const DECISION_COLORS: Record<string, string> = {
  ignore:   'bg-slate-100 text-slate-600 dark:bg-gray-700/40 dark:text-gray-400 border-slate-200 dark:border-gray-600',
  monitor:  'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 border-blue-200 dark:border-blue-500/30',
  notify:   'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border-amber-200 dark:border-amber-500/30',
  escalate: 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400 border-red-200 dark:border-red-500/30',
}

const RISK_COLORS: Record<string, string> = {
  low:      'text-green-600 dark:text-green-400',
  medium:   'text-amber-600 dark:text-amber-400',
  high:     'text-orange-600 dark:text-orange-400',
  critical: 'text-red-600 dark:text-red-400',
}

const CONFIDENCE_COLORS: Record<string, string> = {
  low:    'text-slate-400 dark:text-gray-500',
  medium: 'text-amber-500 dark:text-amber-400',
  high:   'text-green-500 dark:text-green-400',
}

function AiDecisionPanel({
  decision,
  onRegenerate,
  isRegenerating,
}: {
  decision: AiDecision
  onRegenerate: () => void
  isRegenerating: boolean
}) {
  const decColor = DECISION_COLORS[decision.decision] ?? DECISION_COLORS.monitor
  const riskColor = RISK_COLORS[decision.risk_level] ?? ''
  const confColor = CONFIDENCE_COLORS[decision.confidence] ?? ''

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border ${decColor}`}>
            <Shield size={11} />
            {decision.decision}
          </span>
          <span className={`text-xs font-medium ${riskColor}`}>Risk: {decision.risk_level}</span>
          <span className="text-xs text-slate-300 dark:text-gray-600">·</span>
          <span className={`text-xs font-medium ${confColor}`}>{decision.confidence} confidence</span>
          <span className="text-xs text-slate-300 dark:text-gray-600">·</span>
          <span className="text-xs text-slate-500 dark:text-gray-500">
            Customer impact: <span className="font-medium text-slate-700 dark:text-gray-300">{decision.customer_impact}</span>
          </span>
        </div>
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-gray-700/60 text-slate-500 dark:text-gray-400 text-xs font-medium hover:bg-slate-200 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
        >
          {isRegenerating ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} />}
          Regenerate
        </button>
      </div>

      {/* Summary */}
      <div className="rounded-lg border border-slate-200 dark:border-gray-700/30 bg-slate-50/50 dark:bg-gray-800/20 p-4">
        <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">Summary</p>
        <p className="text-sm text-slate-700 dark:text-gray-300">{decision.summary}</p>
      </div>

      {/* Reason */}
      <div className="flex gap-3">
        <div className="w-0.5 rounded-full flex-shrink-0 mt-1 bg-slate-300 dark:bg-gray-600" style={{ minHeight: '1.5rem' }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">01  Why this decision</p>
          <p className="text-sm text-slate-700 dark:text-gray-300">{decision.reason}</p>
        </div>
      </div>

      {/* Evidence */}
      <div className="flex gap-3">
        <div className="w-0.5 rounded-full flex-shrink-0 mt-1 bg-blue-400 dark:bg-blue-500" style={{ minHeight: '1.5rem' }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">02  Evidence</p>
          <ul className="space-y-1">
            {decision.evidence.map((e, i) => (
              <li key={i} className="flex items-start gap-1.5 text-sm text-slate-700 dark:text-gray-300">
                <span className="mt-1.5 w-1 h-1 rounded-full bg-blue-400 flex-shrink-0" />
                {e}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Recommended actions */}
      <div className="flex gap-3">
        <div className="w-0.5 rounded-full flex-shrink-0 mt-1 bg-green-400 dark:bg-green-500" style={{ minHeight: '1.5rem' }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">03  Recommended actions</p>
          <ul className="space-y-1">
            {decision.recommended_actions.map((a, i) => (
              <li key={i} className="flex items-start gap-1.5 text-sm text-slate-700 dark:text-gray-300">
                <span className="mt-1.5 w-1 h-1 rounded-full bg-green-400 flex-shrink-0" />
                {a}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Noise assessment */}
      <div className="flex gap-3">
        <div className={`w-0.5 rounded-full flex-shrink-0 mt-1 ${decision.noise_assessment.is_likely_noise ? 'bg-slate-300 dark:bg-gray-600' : 'bg-amber-400 dark:bg-amber-500'}`} style={{ minHeight: '1.5rem' }} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">04  Noise assessment</p>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              decision.noise_assessment.is_likely_noise
                ? 'bg-slate-100 text-slate-500 dark:bg-gray-700 dark:text-gray-400'
                : 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
            }`}>
              {decision.noise_assessment.is_likely_noise ? 'Likely noise' : 'Operational signal'}
            </span>
            {decision.noise_assessment.recurrence_detected && (
              <span className="text-xs bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400 px-2 py-0.5 rounded-full">Recurrence detected</span>
            )}
          </div>
          <p className="text-sm text-slate-600 dark:text-gray-400">{decision.noise_assessment.noise_reason}</p>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 dark:border-gray-700/30 pt-3 flex items-center gap-3 text-xs text-slate-400 dark:text-gray-500">
        <span>Engine: {decision.engine}</span>
        {decision.model && <><span>·</span><span>{decision.model}</span></>}
        <span>·</span>
        <span>{new Date(decision.created_at).toLocaleString()}</span>
      </div>
    </div>
  )
}

/* -- BriefingSection helper -- */

function BriefingSection({
  index,
  label,
  accent,
  children,
}: {
  index: number
  label: string
  accent?: 'amber' | 'red' | 'blue' | 'green' | 'indigo'
  children: ReactNode
}) {
  const accentLine =
    accent === 'amber' ? 'bg-amber-400 dark:bg-amber-500'
    : accent === 'red'   ? 'bg-red-400 dark:bg-red-500'
    : accent === 'blue'  ? 'bg-blue-400 dark:bg-blue-500'
    : accent === 'green' ? 'bg-green-400 dark:bg-green-500'
    : accent === 'indigo'? 'bg-indigo-400 dark:bg-indigo-500'
    : 'bg-slate-300 dark:bg-gray-600'

  return (
    <div className="flex gap-3">
      <div className={`w-0.5 rounded-full flex-shrink-0 mt-1 ${accentLine}`} style={{ minHeight: '1.5rem' }} />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-400 dark:text-gray-500 uppercase tracking-wide mb-1">
          {String(index).padStart(2, '0')}  {label}
        </p>
        {children}
      </div>
    </div>
  )
}

/* -- Mobile Incident Card -- */

function MobileIncidentCard({
  inc,
  isExpanded,
  onToggle,
  detail,
  detailLoading,
  onStatusChange,
}: {
  inc: IncidentSummary
  isExpanded: boolean
  onToggle: () => void
  detail?: IncidentDetail
  detailLoading: boolean
  onStatusChange: (id: string, status: string) => void
}) {
  return (
    <div className="bg-white dark:bg-gray-800/30 rounded-lg border border-slate-200 dark:border-gray-700/30 overflow-hidden">
      <div className="p-3 cursor-pointer active:bg-gray-800/50" onClick={onToggle}>
        <div className="flex items-center gap-2 mb-2">
          <SeverityBadge severity={inc.severity} />
          <StatusBadge status={inc.status} />
          <span className="text-xs text-gray-500 ml-auto">{timeAgo(inc.created_at)}</span>
        </div>
        <div className="text-sm font-medium text-slate-900 dark:text-gray-200">{inc.title || inc.entity_name}</div>
        <div className="text-xs text-slate-500 dark:text-gray-500 mt-0.5">{inc.incident_key}</div>
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
          <span>{inc.alert_count} alerts</span>
          <span>{liveDuration(inc.started_at, inc.resolved_at)}</span>
          {inc.status === 'open' && (
            <div className="ml-auto flex gap-1">
              <button onClick={(e) => { e.stopPropagation(); onStatusChange(inc.id, 'investigating') }}
                className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-xs">Investigate</button>
              <button onClick={(e) => { e.stopPropagation(); onStatusChange(inc.id, 'resolved') }}
                className="px-2 py-0.5 rounded bg-green-500/10 text-green-400 text-xs">Resolve</button>
            </div>
          )}
          {inc.status === 'investigating' && (
            <button onClick={(e) => { e.stopPropagation(); onStatusChange(inc.id, 'resolved') }}
              className="ml-auto px-2 py-0.5 rounded bg-green-500/10 text-green-400 text-xs">Resolve</button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-700/30 p-3">
          {detailLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-400 py-4 justify-center">
              <Loader2 size={14} className="animate-spin" /> Loading detail...
            </div>
          ) : detail ? (
            <IncidentDetailPanel detail={detail} />
          ) : null}
        </div>
      )}
    </div>
  )
}

export { IncidentsPage }
export default IncidentsPage
