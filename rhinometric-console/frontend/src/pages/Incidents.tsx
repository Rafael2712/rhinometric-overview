/* eslint-disable */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Bell, CheckCircle2, Search,
  Filter, ChevronDown, ChevronUp, Clock, Activity,
  Flame, Eye, BarChart3, MessageSquare, Tag, Plus, X, Send,
  Crosshair, AlertTriangle, Zap, FileText, TrendingUp, Shield
} from 'lucide-react'

/* ── Types ─────────────────────────────────────────────────────── */

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

function formatTs(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function liveDuration(startedAt: string | null, resolvedAt: string | null): string {
  if (!startedAt) return '—'
  const start = new Date(startedAt).getTime()
  const end = resolvedAt ? new Date(resolvedAt).getTime() : Date.now()
  return formatDuration(Math.floor((end - start) / 1000))
}

/* ── Status Badge ──────────────────────────────────────────────── */

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

/* ── Stat Card ─────────────────────────────────────────────────── */

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: typeof Bell; color: string
}) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 p-4">
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

/* ── Main Page ─────────────────────────────────────────────────── */

export function IncidentsPage() {
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }

  const [statusFilter, setStatusFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [entitySearch, setEntitySearch] = useState<string>('')
  const [timeRange, setTimeRange] = useState<string>('7d')
  const [expandedId, setExpandedId] = useState<string | null>(null)

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
  const { data: detailData } = useQuery({
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
          <h1 className="text-2xl font-bold text-white">Incidents</h1>
          <p className="text-sm text-gray-400 mt-1">Operational incidents grouping related alert events</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Activity size={14} className="text-green-400" />
          <span>{listData?.total ?? 0} incidents</span>
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total" value={stats.total} icon={BarChart3} color="text-gray-300" />
          <StatCard label="Open" value={stats.open} icon={Flame} color="text-red-400" />
          <StatCard label="Investigating" value={stats.investigating} icon={Eye} color="text-blue-400" />
          <StatCard label="Avg Resolution" value={stats.avg_resolution_seconds != null ? formatDuration(stats.avg_resolution_seconds) : '—'} icon={Clock} color="text-green-400" />
        </div>
      )}

      {/* Filters */}
      <div className="bg-surface rounded-lg border border-gray-700 p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filters</span>
          </div>

          <div className="flex flex-wrap gap-2 flex-1">
            {/* Time range */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="24h">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="">All time</option>
            </select>

            {/* Status */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All statuses</option>
              <option value="open">Open</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
            </select>

            {/* Severity */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>

            {/* Entity search */}
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                value={entitySearch}
                onChange={(e) => setEntitySearch(e.target.value)}
                placeholder="Search entity..."
                className="bg-gray-800 border border-gray-600 rounded-md pl-8 pr-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary w-48"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Incidents table — desktop */}
      <div className="hidden md:block bg-surface rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-800/50 text-left text-xs uppercase tracking-wider text-gray-400">
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
            <tbody className="divide-y divide-gray-700/50">
              {listLoading && (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              )}
              {!listLoading && incidents.length === 0 && (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No incidents found</td></tr>
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

      {/* Incidents cards — mobile */}
      <div className="md:hidden space-y-3">
        {listLoading && <p className="text-center text-gray-400 py-8">Loading...</p>}
        {!listLoading && incidents.length === 0 && <p className="text-center text-gray-400 py-8">No incidents found</p>}
        {incidents.map((inc) => (
          <MobileIncidentCard
            key={inc.id}
            inc={inc}
            isExpanded={expandedId === inc.id}
            detail={expandedId === inc.id ? detailData : null}
            onToggle={() => setExpandedId(expandedId === inc.id ? null : inc.id)}
            onStatusChange={(status) => statusMutation.mutate({ id: inc.id, status })}
          />
        ))}
      </div>
    </div>
  )
}

/* ── Desktop Row ───────────────────────────────────────────────── */

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
        className="hover:bg-gray-800/30 cursor-pointer transition-colors"
        onClick={onToggle}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {isExpanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
            <span className="text-gray-300 font-mono text-xs">{inc.incident_key}</span>
          </div>
        </td>
        <td className="px-4 py-3 text-gray-300">{inc.entity_name}</td>
        <td className="px-4 py-3"><SeverityBadge severity={inc.severity} /></td>
        <td className="px-4 py-3"><StatusBadge status={inc.status} /></td>
        <td className="px-4 py-3 text-gray-400 text-xs" title={formatTs(inc.started_at)}>{timeAgo(inc.started_at)}</td>
        <td className="px-4 py-3 text-gray-400 text-xs">{liveDuration(inc.started_at, inc.resolved_at)}</td>
        <td className="px-4 py-3">
          <span className="inline-flex items-center gap-1 text-gray-300">
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
          <td colSpan={8} className="px-4 py-4 bg-gray-800/20 border-t border-gray-700/50">
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

/* ── Expanded Detail Panel ─────────────────────────────────────── */

function IncidentDetailPanel({ detail }: { detail: IncidentDetail }) {
  const events = detail.alert_events || []
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }
  const incidentId = detail.incident.id

  const [activeTab, setActiveTab] = useState<'alerts' | 'timeline' | 'comments' | 'root-cause'>('alerts')
  const [newComment, setNewComment] = useState('')
  const [newTag, setNewTag] = useState('')

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

  const currentTags: string[] = detail.incident.tags || []
  const timeline = timelineData?.timeline || []
  const comments = commentsData?.comments || []

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
  }

  return (
    <div className="space-y-3">
      {/* Header info */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span>Incident ID: <span className="font-mono text-gray-300">{detail.incident.id.slice(0, 8)}</span></span>
        <span>|</span>
        <span>Created: {formatTs(detail.incident.created_at)}</span>
        {detail.incident.resolved_at && (
          <>
            <span>|</span>
            <span>Resolved: {formatTs(detail.incident.resolved_at)}</span>
          </>
        )}
      </div>

      {/* Tags section */}
      <div className="flex items-center gap-2 flex-wrap">
        <Tag size={14} className="text-gray-500" />
        {currentTags.map((tag) => (
          <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-cyan-900/30 text-cyan-400 border border-cyan-800/50">
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
            className="bg-gray-800/50 border border-gray-700 rounded px-2 py-0.5 text-xs text-gray-300 w-24 focus:outline-none focus:border-cyan-500"
          />
          <button onClick={addTag} className="text-gray-500 hover:text-cyan-400"><Plus size={14} /></button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-700">
        {([
          { key: 'alerts' as const, label: `Alerts (${events.length})`, icon: Bell },
          { key: 'timeline' as const, label: `Timeline (${timeline.length})`, icon: Clock },
          { key: 'comments' as const, label: `Comments (${comments.length})`, icon: MessageSquare },
          { key: 'root-cause' as const, label: 'Root Cause', icon: Crosshair },
        ]).map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === key
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            <TabIcon size={12} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content: Alerts */}
      {activeTab === 'alerts' && (
        <>
          {events.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No alert events linked yet</p>
          ) : (
            <div className="overflow-x-auto rounded-md border border-gray-700/50">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-800/30 text-gray-400 uppercase tracking-wider text-left">
                    <th className="px-3 py-2">Alert</th>
                    <th className="px-3 py-2">Severity</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Started</th>
                    <th className="px-3 py-2">Ended</th>
                    <th className="px-3 py-2">Duration</th>
                    <th className="px-3 py-2">Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700/30">
                  {events.map((ev) => (
                    <tr key={ev.id} className="hover:bg-gray-800/20">
                      <td className="px-3 py-2 text-gray-300 font-medium">{ev.alert_name}</td>
                      <td className="px-3 py-2"><SeverityBadge severity={ev.severity} /></td>
                      <td className="px-3 py-2"><AlertStatusBadge status={ev.status} /></td>
                      <td className="px-3 py-2 text-gray-400" title={formatTs(ev.started_at)}>{timeAgo(ev.started_at)}</td>
                      <td className="px-3 py-2 text-gray-400">{ev.ended_at ? timeAgo(ev.ended_at) : '\u2014'}</td>
                      <td className="px-3 py-2 text-gray-400">{formatDuration(ev.duration_seconds)}</td>
                      <td className="px-3 py-2 text-gray-400 max-w-xs truncate">{ev.summary || '\u2014'}</td>
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
                        <span className="text-xs text-gray-600">{ts}</span>
                        {evt.created_by && <span className="text-xs text-gray-500">by {evt.created_by}</span>}
                      </div>
                      {evt.description && <p className="text-xs text-gray-400 mt-0.5">{evt.description}</p>}
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
            <div key={c.id} className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/30">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-xs font-medium text-blue-400">{c.author}</span>
                <span className="text-xs text-gray-600">{c.created_at ? new Date(c.created_at).toLocaleString() : ''}</span>
              </div>
              <p className="text-sm text-gray-300 whitespace-pre-wrap">{c.comment}</p>
            </div>
          ))}

          {/* Add comment form */}
          <form onSubmit={handleCommentSubmit} className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 bg-gray-800/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
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

      {/* Tab content: Root Cause (Phase 2.7) */}
      {activeTab === 'root-cause' && (
        <div className="space-y-4">
          {rootCauseLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400"></div>
              <span className="ml-3 text-sm text-gray-400">Analyzing root cause...</span>
            </div>
          ) : !rootCauseData ? (
            <div className="text-center py-8">
              <Crosshair size={24} className="mx-auto text-gray-600 mb-2" />
              <p className="text-sm text-gray-500">No analysis data available</p>
            </div>
          ) : (
            <>
              {/* Likely Root Cause Card */}
              <div className={`rounded-lg border p-4 ${
                rootCauseData.likely_root_cause.confidence === 'high'
                  ? 'bg-red-500/10 border-red-500/30'
                  : rootCauseData.likely_root_cause.confidence === 'medium'
                  ? 'bg-yellow-500/10 border-yellow-500/30'
                  : rootCauseData.likely_root_cause.confidence === 'low'
                  ? 'bg-blue-500/10 border-blue-500/30'
                  : 'bg-gray-800/40 border-gray-700/30'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  <Crosshair size={16} className={
                    rootCauseData.likely_root_cause.confidence === 'high' ? 'text-red-400'
                    : rootCauseData.likely_root_cause.confidence === 'medium' ? 'text-yellow-400'
                    : rootCauseData.likely_root_cause.confidence === 'low' ? 'text-blue-400'
                    : 'text-gray-500'
                  } />
                  <h3 className="text-sm font-semibold text-gray-200">Likely Root Cause</h3>
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${
                    rootCauseData.likely_root_cause.confidence === 'high'
                      ? 'bg-red-500/20 text-red-400'
                      : rootCauseData.likely_root_cause.confidence === 'medium'
                      ? 'bg-yellow-500/20 text-yellow-400'
                      : rootCauseData.likely_root_cause.confidence === 'low'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-700 text-gray-400'
                  }`}>
                    {rootCauseData.likely_root_cause.confidence.toUpperCase()} confidence
                  </span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {rootCauseData.likely_root_cause.description}
                </p>
                {rootCauseData.likely_root_cause.entity && (
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Shield size={10} /> Entity: <span className="text-gray-200 font-mono">{rootCauseData.likely_root_cause.entity}</span>
                    </span>
                    {rootCauseData.likely_root_cause.metric && (
                      <span className="flex items-center gap-1">
                        <TrendingUp size={10} /> Metric: <span className="text-gray-200 font-mono">{rootCauseData.likely_root_cause.metric}</span>
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <BarChart3 size={10} /> Score: <span className="text-gray-200 font-mono">{rootCauseData.score}</span>
                    </span>
                  </div>
                )}
              </div>

              {/* Signal Counts Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
                  <TrendingUp size={14} className="mx-auto text-orange-400 mb-1" />
                  <p className="text-lg font-bold text-gray-200">{rootCauseData.signal_counts.metric_spikes}</p>
                  <p className="text-xs text-gray-500">Metric Spikes</p>
                </div>
                <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
                  <Bell size={14} className="mx-auto text-red-400 mb-1" />
                  <p className="text-lg font-bold text-gray-200">{rootCauseData.signal_counts.alerts}</p>
                  <p className="text-xs text-gray-500">Alerts</p>
                </div>
                <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
                  <Zap size={14} className="mx-auto text-purple-400 mb-1" />
                  <p className="text-lg font-bold text-gray-200">{rootCauseData.signal_counts.anomalies}</p>
                  <p className="text-xs text-gray-500">Anomalies</p>
                </div>
                <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-3 text-center">
                  <FileText size={14} className="mx-auto text-yellow-400 mb-1" />
                  <p className="text-lg font-bold text-gray-200">{rootCauseData.signal_counts.log_errors}</p>
                  <p className="text-xs text-gray-500">Log Errors</p>
                </div>
              </div>

              {/* Evidence List */}
              {rootCauseData.evidence.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Evidence</h4>
                  <div className="space-y-2">
                    {rootCauseData.evidence.map((ev, i) => (
                      <div key={i} className="bg-gray-800/30 rounded-lg border border-gray-700/20 p-3">
                        <div className="flex items-center gap-2 mb-1">
                          {ev.type === 'metric_spike' && <TrendingUp size={12} className="text-orange-400" />}
                          {ev.type === 'alert' && <AlertTriangle size={12} className="text-red-400" />}
                          {ev.type === 'anomaly' && <Zap size={12} className="text-purple-400" />}
                          {ev.type === 'log_errors' && <FileText size={12} className="text-yellow-400" />}
                          <span className="text-xs font-medium text-gray-300 capitalize">
                            {ev.type === 'metric_spike' ? 'Metric Spike' : ev.type === 'log_errors' ? 'Log Errors' : ev.type}
                          </span>
                          {ev.metric && (
                            <span className="text-xs text-gray-500 font-mono ml-1">{ev.metric}</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 space-y-0.5">
                          {ev.type === 'metric_spike' && (
                            <>
                              <p>Value: <span className="text-gray-200">{typeof ev.value === 'number' ? ev.value.toFixed(2) : ev.value}</span>
                                {typeof ev.baseline === 'number' && (
                                  <> vs baseline <span className="text-gray-200">{ev.baseline.toFixed(2)}</span></>
                                )}
                              </p>
                              {typeof ev.factor === 'number' && (
                                <p>Factor: <span className="text-orange-300 font-semibold">{ev.factor.toFixed(1)}x</span> increase</p>
                              )}
                            </>
                          )}
                          {ev.type === 'alert' && (
                            <>
                              {ev.alert_name && <p>Alert: <span className="text-gray-200">{ev.alert_name}</span></p>}
                              {ev.severity && <p>Severity: <span className="text-gray-200">{ev.severity}</span></p>}
                            </>
                          )}
                          {ev.type === 'anomaly' && (
                            <>
                              {ev.entity && <p>Entity: <span className="text-gray-200">{ev.entity}</span></p>}
                              {typeof ev.anomaly_score === 'number' && (
                                <p>Anomaly score: <span className="text-purple-300 font-semibold">{ev.anomaly_score.toFixed(2)}</span></p>
                              )}
                            </>
                          )}
                          {ev.type === 'log_errors' && (
                            <>
                              <p>Error count: <span className="text-yellow-300 font-semibold">{ev.error_count}</span></p>
                              {ev.samples && ev.samples.length > 0 && (
                                <div className="mt-1 space-y-1">
                                  {ev.samples.map((s: string, j: number) => (
                                    <p key={j} className="text-xs text-gray-500 font-mono truncate bg-gray-900/50 rounded px-2 py-0.5">{s}</p>
                                  ))}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Analysis metadata */}
              <div className="flex items-center justify-between text-xs text-gray-600 pt-2 border-t border-gray-700/30">
                <span>Analyzed: {rootCauseData.analyzed_at ? new Date(rootCauseData.analyzed_at).toLocaleString() : 'N/A'}</span>
                <button
                  onClick={() => refetchRootCause()}
                  className="flex items-center gap-1 text-gray-500 hover:text-cyan-400 transition-colors"
                >
                  <Activity size={10} />
                  Re-analyze
                </button>
              </div>
            </>
          )}
        </div>
      )}

    </div>
  )
}

/* ── Mobile Card ───────────────────────────────────────────────── */

function MobileIncidentCard({ inc, isExpanded, detail, onToggle, onStatusChange }: {
  inc: IncidentSummary
  isExpanded: boolean
  detail: IncidentDetail | null | undefined
  onToggle: () => void
  onStatusChange: (s: string) => void
}) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 overflow-hidden">
      <div className="p-4 space-y-3 cursor-pointer" onClick={onToggle}>
        <div className="flex items-center justify-between">
          <span className="font-mono text-xs text-gray-300">{inc.incident_key}</span>
          {isExpanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <SeverityBadge severity={inc.severity} />
          <StatusBadge status={inc.status} />
          <span className="text-xs text-gray-400 flex items-center gap-1"><Bell size={10} />{inc.alert_count} alerts</span>
        </div>
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>{timeAgo(inc.started_at)}</span>
          <span>{liveDuration(inc.started_at, inc.resolved_at)}</span>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-700 p-4 space-y-3 bg-gray-800/20">
          {/* Action buttons */}
          <div className="flex gap-2">
            {inc.status === 'open' && (
              <button
                onClick={() => onStatusChange('investigating')}
                className="px-3 py-1.5 rounded text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
              >
                Investigate
              </button>
            )}
            {(inc.status === 'open' || inc.status === 'investigating') && (
              <button
                onClick={() => onStatusChange('resolved')}
                className="px-3 py-1.5 rounded text-xs bg-green-500/20 text-green-400 hover:bg-green-500/30"
              >
                Resolve
              </button>
            )}
          </div>

          {!detail ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-gray-400 font-medium uppercase">Alert Events ({detail.alert_events.length})</p>
              {detail.alert_events.map((ev) => (
                <div key={ev.id} className="bg-gray-800/40 rounded p-3 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-300 font-medium">{ev.alert_name}</span>
                    <AlertStatusBadge status={ev.status} />
                  </div>
                  <div className="text-xs text-gray-400">
                    <SeverityBadge severity={ev.severity} />
                    <span className="ml-2">{timeAgo(ev.started_at)}</span>
                    {ev.ended_at && <span> → {timeAgo(ev.ended_at)}</span>}
                  </div>
                  {ev.summary && <p className="text-xs text-gray-500 truncate">{ev.summary}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
