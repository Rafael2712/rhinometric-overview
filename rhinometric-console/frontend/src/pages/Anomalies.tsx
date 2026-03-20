/* eslint-disable */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  AlertTriangle, CheckCircle2, Shield, Zap,
  ChevronDown, ChevronUp, Activity, Eye, Filter, BarChart3,
  RefreshCw, XCircle, Bell, Trash2
} from 'lucide-react'
import { getTelemetryLabel, getTelemetryStatusStyle } from '../utils/signalAvailability'

/* ── Types ────────────────────────────────────────────────────── */
interface AnomalyOccurrence {
  timestamp: string
  current_value: number
  expected_value: number
  deviation_percent: number
  severity: string
  confidence: number | null
  analysis: string | null
}

interface AnomalyGroup {
  fingerprint: string
  entity_type: string
  entity_name: string
  metric_name: string
  source: string
  first_seen: string
  last_seen: string
  occurrence_count: number
  severity_current: string
  status: string
  occurrences: AnomalyOccurrence[]
  environment: string
  service_group: string
  region: string | null
  cluster: string | null
  priority: number
  tags: string[] | null
  metadata: Record<string, unknown> | null
}

/* ── Helpers ──────────────────────────────────────────────────── */
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ${hrs % 24}h ago`
}

function formatTs(iso: string): string {
  return new Date(iso).toLocaleString()
}

/* ── Entity Badge ─────────────────────────────────────────────── */
function EntityBadge({ type }: { type: string }) {
  const map: Record<string, { bg: string; text: string; icon: typeof Shield }> = {
    service:        { bg: 'bg-blue-500/20',   text: 'text-blue-400',   icon: Zap },
    website:        { bg: 'bg-purple-500/20',  text: 'text-purple-400', icon: Activity },
    infrastructure: { bg: 'bg-amber-500/20',  text: 'text-amber-400',  icon: Shield },
  }
  const cfg = map[type] || { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Shield }
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      <Icon size={12} />
      {type}
    </span>
  )
}

/* ── Priority Badge ───────────────────────────────────────────── */
function PriorityBadge({ priority }: { priority: number }) {
  const map: Record<number, { bg: string; text: string; label: string }> = {
    1: { bg: 'bg-red-500/20',    text: 'text-red-400',    label: 'P1 — Critical' },
    2: { bg: 'bg-amber-500/20',  text: 'text-amber-400',  label: 'P2 — High' },
    3: { bg: 'bg-sky-500/20',    text: 'text-sky-400',    label: 'P3 — Medium' },
  }
  const cfg = map[priority] || { bg: 'bg-gray-500/20', text: 'text-gray-400', label: `P${priority}` }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  )
}

/* ── Status Badge ─────────────────────────────────────────────── */
function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; icon: typeof Activity }> = {
    active:          { bg: 'bg-red-500/20',    text: 'text-red-400',    icon: AlertTriangle },
    acknowledged:    { bg: 'bg-blue-500/20',   text: 'text-blue-400',   icon: Eye },
    false_positive:  { bg: 'bg-gray-500/20',   text: 'text-gray-400',  icon: XCircle },
    suppressed:      { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: Bell },
    resolved:        { bg: 'bg-green-500/20',  text: 'text-green-400',  icon: CheckCircle2 },
    alert_created:   { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: Bell },
  }
  const cfg = map[status] || { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: Activity }
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      <Icon size={12} />
      {status.replace('_', ' ')}
    </span>
  )
}

/* ── Severity Badge ───────────────────────────────────────────── */
function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    critical: { bg: 'bg-red-500/20',    text: 'text-red-400' },
    high:     { bg: 'bg-orange-500/20', text: 'text-orange-400' },
    medium:   { bg: 'bg-amber-500/20',  text: 'text-amber-400' },
    low:      { bg: 'bg-sky-500/20',    text: 'text-sky-400' },
  }
  const cfg = map[severity] || { bg: 'bg-gray-500/20', text: 'text-gray-400' }
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {severity}
    </span>
  )
}

/* ── Main Page ────────────────────────────────────────────────── */

/* ── Task 4: Purge Modal ──────────────────────────────────────── */
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
                  ⚠️ This action is irreversible. Are you sure?
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

export function AnomaliesPage() {
  const { token } = useAuthStore()
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }
  const [showPurge, setShowPurge] = useState(false)

  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [expandedFp, setExpandedFp] = useState<string | null>(null)

  // Fetch services for telemetry state lookup
  const { data: servicesData } = useQuery({
    queryKey: ['services-telemetry-state'],
    queryFn: async () => {
      const res = await fetch('/api/external-services', { headers })
      if (!res.ok) return []
      const json = await res.json()
      return json.services || json || []
    },
    staleTime: 30000,
  })

  // Build a map: service_name (lowercase) -> telemetry state
  const svcTelemetryMap: Record<string, { monitoring_mode: string; telemetry_status: string }> = {}
  if (Array.isArray(servicesData)) {
    for (const s of servicesData) {
      svcTelemetryMap[(s.name || '').toLowerCase()] = {
        monitoring_mode: s.monitoring_mode || 'synthetic_only',
        telemetry_status: s.telemetry_status || 'not_configured',
      }
    }
  }

  // Fetch anomaly groups
  const { data, isLoading, error } = useQuery({
    queryKey: ['anomalies', entityTypeFilter, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ page_size: '50' })
      if (entityTypeFilter) params.set('entity_type', entityTypeFilter)
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`/api/anomalies?${params}`, { headers })
      if (!res.ok) throw new Error('Failed to fetch anomalies')
      return res.json() as Promise<{ anomaly_groups: AnomalyGroup[]; total: number }>
    },
    refetchInterval: 30000,
  })

  // Status mutation
  const statusMutation = useMutation({
    mutationFn: async ({ fingerprint, status }: { fingerprint: string; status: string }) => {
      const res = await fetch(`/api/anomalies/${fingerprint}/status`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error('Failed to update status')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] })
    },
  })

  // Correlate mutation
  const correlateMutation = useMutation({
    mutationFn: async (group: AnomalyGroup) => {
      const res = await fetch('/api/correlation/correlate', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: 'anomaly',
          source_id: group.fingerprint,
          entity_type: group.entity_type,
          entity_name: group.entity_name,
          metric_name: group.metric_name,
          timestamp: group.last_seen,
          severity: group.severity_current,
        }),
      })
      if (!res.ok) throw new Error('Correlation failed')
      return res.json()
    },
  })

  const groups = data?.anomaly_groups || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Anomalies</h1>
          <p className="text-sm text-gray-400 mt-1">
            Customer-facing anomaly detection — grouped by entity with lifecycle management
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <Activity size={14} className="text-green-400" />
          <span>{data?.total ?? 0} anomaly groups</span>
          {isAdmin() && (
            <button onClick={() => setShowPurge(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded-lg text-xs transition-colors ml-2">
              <Trash2 size={13} />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      <PurgeModal module="anomalies" isOpen={showPurge} onClose={(purged) => { setShowPurge(false); if (purged) queryClient.invalidateQueries({ queryKey: ['anomalies'] }) }} token={token} />

      {/* Filters */}
      <div className="bg-surface rounded-lg border border-gray-700 p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filters</span>
          </div>

          <div className="flex flex-wrap gap-2 flex-1">
            <select
              value={entityTypeFilter}
              onChange={(e) => setEntityTypeFilter(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All entity types</option>
              <option value="service">Service</option>
              <option value="website">Website</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-primary"
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
              <option value="suppressed">Suppressed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {(error as Error).message}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Empty state — Task 2 customer-facing wording */}
      {!isLoading && !error && groups.length === 0 && (
        <div className="bg-surface rounded-lg border border-gray-700 p-12 text-center">
          <Shield size={48} className="mx-auto text-gray-600 mb-4" />
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No customer anomalies detected</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            No customer-facing service anomalies are currently available.
          </p>
          <p className="text-xs text-gray-600 mt-3 max-w-md mx-auto">
            Synthetic checks or telemetry collectors are required to generate customer anomalies.
          </p>
        </div>
      )}

      {/* Anomaly Groups table — desktop */}
      {!isLoading && groups.length > 0 && (
        <div className="hidden md:block bg-surface rounded-lg border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-800/50 text-left text-xs uppercase tracking-wider text-gray-400">
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Metric</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Occurrences</th>
                  <th className="px-4 py-3">Last Seen</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {groups.map((g) => {
                  const isExpanded = expandedFp === g.fingerprint
                  return (
                    <AnomalyRow
                      key={g.fingerprint}
                      group={g}
                      isExpanded={isExpanded}
                      onToggle={() => setExpandedFp(isExpanded ? null : g.fingerprint)}
                      onStatusChange={(status) => statusMutation.mutate({ fingerprint: g.fingerprint, status })}
                      onCorrelate={() => correlateMutation.mutate(g)}
                      isMutating={statusMutation.isPending}
                      isCorrelating={correlateMutation.isPending}
                      correlationResult={correlateMutation.data}
                      svcTelemetryMap={svcTelemetryMap}
                    />
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Mobile cards */}
      {!isLoading && groups.length > 0 && (
        <div className="md:hidden space-y-3">
          {groups.map((g) => (
            <MobileAnomalyCard
              key={g.fingerprint}
              group={g}
              isExpanded={expandedFp === g.fingerprint}
              onToggle={() => setExpandedFp(expandedFp === g.fingerprint ? null : g.fingerprint)}
              onStatusChange={(status) => statusMutation.mutate({ fingerprint: g.fingerprint, status })}
            />
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Desktop Anomaly Row ──────────────────────────────────────── */
function AnomalyRow({ group, isExpanded, onToggle, onStatusChange, onCorrelate, isMutating, isCorrelating, correlationResult, svcTelemetryMap }: {
  group: AnomalyGroup
  isExpanded: boolean
  onToggle: () => void
  onStatusChange: (s: string) => void
  onCorrelate: () => void
  isMutating: boolean
  isCorrelating: boolean
  correlationResult: Record<string, unknown> | null | undefined
  svcTelemetryMap: Record<string, { monitoring_mode: string; telemetry_status: string }>
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
            <div>
              <div className="text-gray-200 font-medium">{group.entity_name}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <EntityBadge type={group.entity_type} />
                {group.environment !== 'unknown' && (
                  <span className="text-xs text-gray-500">{group.environment}</span>
                )}
              </div>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-gray-300 font-mono text-xs">{group.metric_name}</td>
        <td className="px-4 py-3"><SeverityBadge severity={group.severity_current} /></td>
        <td className="px-4 py-3"><StatusBadge status={group.status} /></td>
        <td className="px-4 py-3"><PriorityBadge priority={group.priority} /></td>
        <td className="px-4 py-3">
          <span className="inline-flex items-center gap-1 text-gray-300">
            <BarChart3 size={12} className="text-gray-500" />{group.occurrence_count}
          </span>
        </td>
        <td className="px-4 py-3 text-gray-400 text-xs" title={formatTs(group.last_seen)}>{timeAgo(group.last_seen)}</td>
        <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-1.5">
            {group.status === 'active' && (
              <button
                onClick={() => onStatusChange('acknowledged')}
                disabled={isMutating}
                className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors disabled:opacity-50"
              >
                Ack
              </button>
            )}
            {(group.status === 'active' || group.status === 'acknowledged') && (
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
            <div className="space-y-4">
              {/* Meta row */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
                <span>Fingerprint: <span className="font-mono text-gray-300">{group.fingerprint}</span></span>
                <span>|</span>
                <span>Source: <span className="text-gray-300">{group.source}</span></span>
                <span>|</span>
                <span>Service group: <span className="text-gray-300">{group.service_group}</span></span>
                <span>|</span>
                <span>First seen: <span className="text-gray-300">{formatTs(group.first_seen)}</span></span>
                {group.tags && group.tags.length > 0 && (
                  <>
                    <span>|</span>
                    <span>Tags: {group.tags.map((t) => (
                      <span key={t} className="inline-block px-1.5 py-0.5 rounded bg-cyan-900/30 text-cyan-400 text-xs mr-1">{t}</span>
                    ))}</span>
                  </>
                )}
              </div>

              {/* Monitoring Mode indicator — reads real telemetry state */}
              {(() => {
                const svcState = svcTelemetryMap[(group.entity_name || '').toLowerCase()]
                if (!svcState || svcState.monitoring_mode === 'synthetic_only') {
                  return (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                      <span className="text-amber-400 text-xs font-medium">📡 Monitoring: Synthetic only</span>
                      <span className="text-gray-500 text-xs">— Telemetry not configured for this service</span>
                    </div>
                  )
                }
                const style = getTelemetryStatusStyle(svcState.telemetry_status)
                const label = getTelemetryLabel(svcState.telemetry_status)
                return (
                  <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${style.bg} border ${style.border}`}>
                    <span className={`text-xs font-medium ${style.color}`}>📡 {label}</span>
                  </div>
                )
              })()}

              {/* Lifecycle actions */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-500 font-medium">Actions:</span>
                {['active', 'acknowledged', 'false_positive', 'suppressed', 'resolved'].map((s) => (
                  <button
                    key={s}
                    disabled={group.status === s || isMutating}
                    onClick={() => onStatusChange(s)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-colors disabled:opacity-30 ${
                      group.status === s
                        ? 'bg-primary/30 text-primary ring-1 ring-primary/50'
                        : 'bg-gray-700/40 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
                    }`}
                  >
                    {s.replace('_', ' ')}
                  </button>
                ))}

                <div className="ml-auto">
                  <button
                    onClick={onCorrelate}
                    disabled={isCorrelating}
                    className="flex items-center gap-1.5 px-3 py-1 rounded text-xs bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 disabled:opacity-50 transition-colors"
                  >
                    <RefreshCw size={12} className={isCorrelating ? 'animate-spin' : ''} />
                    Correlate
                  </button>
                </div>
              </div>

              {/* Correlation result */}
              {correlationResult && (
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3 text-xs text-purple-300">
                  <pre className="whitespace-pre-wrap">{JSON.stringify(correlationResult, null, 2)}</pre>
                </div>
              )}

              {/* Occurrence timeline */}
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Occurrences ({group.occurrence_count})
                </h4>
                <div className="overflow-x-auto rounded-md border border-gray-700/50">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-800/30 text-gray-400 uppercase tracking-wider text-left">
                        <th className="px-3 py-2">Timestamp</th>
                        <th className="px-3 py-2">Value</th>
                        <th className="px-3 py-2">Expected</th>
                        <th className="px-3 py-2">Deviation</th>
                        <th className="px-3 py-2">Severity</th>
                        <th className="px-3 py-2">Confidence</th>
                        <th className="px-3 py-2">Analysis</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700/30">
                      {group.occurrences.map((o, i) => (
                        <tr key={i} className="hover:bg-gray-800/20">
                          <td className="px-3 py-2 text-gray-300" title={formatTs(o.timestamp)}>{timeAgo(o.timestamp)}</td>
                          <td className="px-3 py-2 text-gray-200 font-mono">{o.current_value.toFixed(2)}</td>
                          <td className="px-3 py-2 text-gray-400 font-mono">{o.expected_value.toFixed(2)}</td>
                          <td className="px-3 py-2">
                            <span className={o.deviation_percent > 50 ? 'text-red-400' : o.deviation_percent > 20 ? 'text-amber-400' : 'text-gray-300'}>
                              {o.deviation_percent.toFixed(1)}%
                            </span>
                          </td>
                          <td className="px-3 py-2"><SeverityBadge severity={o.severity} /></td>
                          <td className="px-3 py-2 text-gray-400">{o.confidence != null ? `${(o.confidence * 100).toFixed(0)}%` : '—'}</td>
                          <td className="px-3 py-2 text-gray-400 max-w-xs truncate">{o.analysis || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

/* ── Mobile Card ──────────────────────────────────────────────── */
function MobileAnomalyCard({ group, isExpanded, onToggle, onStatusChange }: {
  group: AnomalyGroup
  isExpanded: boolean
  onToggle: () => void
  onStatusChange: (s: string) => void
}) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 overflow-hidden">
      <div className="p-4 space-y-2 cursor-pointer" onClick={onToggle}>
        <div className="flex items-center justify-between">
          <span className="text-gray-200 font-medium text-sm">{group.entity_name}</span>
          {isExpanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <EntityBadge type={group.entity_type} />
          <SeverityBadge severity={group.severity_current} />
          <StatusBadge status={group.status} />
        </div>
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span className="font-mono">{group.metric_name}</span>
          <span>{group.occurrence_count} occurrences</span>
        </div>
        <div className="text-xs text-gray-500">{timeAgo(group.last_seen)}</div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-700 p-4 space-y-3 bg-gray-800/20">
          <div className="flex gap-2 flex-wrap">
            {group.status === 'active' && (
              <button
                onClick={() => onStatusChange('acknowledged')}
                className="px-3 py-1.5 rounded text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
              >
                Acknowledge
              </button>
            )}
            {(group.status === 'active' || group.status === 'acknowledged') && (
              <button
                onClick={() => onStatusChange('resolved')}
                className="px-3 py-1.5 rounded text-xs bg-green-500/20 text-green-400 hover:bg-green-500/30"
              >
                Resolve
              </button>
            )}
          </div>

          <div className="space-y-2">
            <p className="text-xs text-gray-400 font-medium uppercase">Recent Occurrences</p>
            {group.occurrences.slice(0, 5).map((o, i) => (
              <div key={i} className="bg-gray-800/40 rounded p-3 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-300">{timeAgo(o.timestamp)}</span>
                  <SeverityBadge severity={o.severity} />
                </div>
                <div className="text-xs text-gray-400">
                  Value: <span className="text-gray-200 font-mono">{o.current_value.toFixed(2)}</span>
                  {' '}vs{' '}
                  <span className="text-gray-400 font-mono">{o.expected_value.toFixed(2)}</span>
                  {' '}({o.deviation_percent.toFixed(1)}%)
                </div>
                {o.analysis && <p className="text-xs text-gray-500 truncate">{o.analysis}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
