import { FileText, Search, Download, RefreshCw, Filter, Clock, Inbox, ExternalLink, X } from 'lucide-react'
import { useEffect, useState, useMemo, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface LogEntry {
  timestamp: string
  /** Loki nanosecond timestamp — kept for identity/comparison */
  rawTimestamp: string
  level: string
  message: string
  labels: Record<string, string>
  stream: Record<string, string>
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function detectLogLevel(message: string): string {
  const msg = message.toLowerCase()
  if (msg.includes('error') || msg.includes('fatal')) return 'error'
  if (msg.includes('warn')) return 'warning'
  if (msg.includes('info')) return 'info'
  if (msg.includes('debug')) return 'debug'
  return 'info'
}

function getLevelColor(level: string) {
  switch (level) {
    case 'error': return 'text-error bg-error/10 border-error/30'
    case 'warning': return 'text-warning bg-warning/10 border-warning/30'
    case 'info': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
    case 'debug': return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    default: return 'text-gray-300 bg-gray-500/10 border-gray-500/30'
  }
}

function getLevelBadgeColor(level: string) {
  switch (level) {
    case 'error': return 'text-error bg-error/15 border-error/40'
    case 'warning': return 'text-warning bg-warning/15 border-warning/40'
    case 'info': return 'text-blue-400 bg-blue-500/15 border-blue-500/40'
    case 'debug': return 'text-gray-400 bg-gray-500/15 border-gray-500/40'
    default: return 'text-gray-300 bg-gray-500/15 border-gray-500/40'
  }
}

/** Unique identity key for a log entry */
function logKey(log: LogEntry): string {
  return `${log.rawTimestamp}|${log.message}|${log.stream.job || ''}`
}

/* ------------------------------------------------------------------ */
/* Priority labels (split for the detail panel)                        */
/* ------------------------------------------------------------------ */

const PRIORITY_LABEL_KEYS = new Set([
  'service_key', 'service_name', 'job', 'level', 'environment', 'source',
  'trace_id', 'span_id',
])

/* ------------------------------------------------------------------ */
/* Selected-log Grafana deep link                                      */
/* ------------------------------------------------------------------ */

function buildSelectedLogGrafanaPath(log: LogEntry): string {
  const s = log.stream

  // Build the most specific Loki selector available
  let selector = ''
  if (s.service_key)       selector = `service_key="${s.service_key}"`
  else if (s.service_name) selector = `service_name="${s.service_name}"`
  else if (s.job)          selector = `job="${s.job}"`

  // Prefix with job if selector is not already job and job exists
  if (selector && !selector.startsWith('job=') && s.job) {
    selector = `job="${s.job}", ${selector}`
  }

  // Fallback if nothing found at all
  if (!selector) selector = 'job=~".+"'

  let expr = `{${selector}}`

  // Add a safe message substring as a line filter for precision
  if (log.message) {
    // Take first 80 chars, strip quotes/backslashes to keep LogQL safe
    const safe = log.message.slice(0, 80).replace(/[\\"`]/g, '')
    if (safe.length > 5) {
      expr += ` |= "${safe}"`
    }
  }

  // Time window: 5 min around the event
  const tsMs = new Date(log.timestamp).getTime()
  let from: string, to: string
  if (!isNaN(tsMs) && tsMs > 0) {
    from = String(tsMs - 5 * 60 * 1000)
    to   = String(tsMs + 5 * 60 * 1000)
  } else {
    from = 'now-15m'
    to   = 'now'
  }

  const left = JSON.stringify({
    datasource: 'loki',
    queries: [{ refId: 'A', expr }],
    range: { from, to },
  })

  return `?orgId=1&left=${encodeURIComponent(left)}`
}

/* ================================================================== */
/*  Component                                                          */
/* ================================================================== */

export function LogsPage() {
  useEffect(() => { document.title = 'Rhinometric - Logs' }, [])

  const token   = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)

  const [searchQuery, setSearchQuery]   = useState('')
  const [levelFilter, setLevelFilter]   = useState<string>('all')
  const [timeRange, setTimeRange]       = useState<string>('15m')
  const [autoRefresh, setAutoRefresh]   = useState(false)
  const [selectedKey, setSelectedKey]   = useState<string | null>(null)

  /* ---- Data fetching ---- */

  const parseTimeRange = useCallback((range: string): number => {
    const value = parseInt(range.slice(0, -1))
    const unit = range.slice(-1)
    const multipliers: Record<string, number> = { 'h': 3600000, 'm': 60000, 'd': 86400000 }
    return value * (multipliers[unit] || 3600000)
  }, [])

  const { data: logsData, isLoading, error, refetch } = useQuery({
    queryKey: ['logs', token, searchQuery, levelFilter, timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token available')

      let logql = '{job=~".+"}'
      if (levelFilter !== 'all') {
        logql = `{job=~".+"} |= "${levelFilter}"`
      }
      if (searchQuery) {
        logql += ` |= "${searchQuery}"`
      }

      const params = new URLSearchParams({
        query: logql,
        limit: '50',
        start: `${Date.now() - parseTimeRange(timeRange)}000000`,
        end: `${Date.now()}000000`,
        direction: 'backward'
      })

      const response = await fetch(`/api/logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) throw new Error('Failed to fetch logs')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: autoRefresh ? 5000 : false,
    refetchOnMount: true,
    staleTime: 0,
  })

  /* ---- Parsed log entries ---- */

  const logs: LogEntry[] = useMemo(() =>
    logsData?.data?.result?.flatMap((stream: any) =>
      stream.values?.map(([timestamp, message]: [string, string]) => ({
        timestamp: new Date(parseInt(timestamp) / 1000000).toISOString(),
        rawTimestamp: timestamp,
        message,
        level: detectLogLevel(message),
        labels: stream.stream || {},
        stream: stream.stream || {},
      })) || []
    ) || []
  , [logsData])

  /* ---- Selection management ---- */

  // Clear stale selection after data refresh
  useEffect(() => {
    if (selectedKey && logs.length > 0) {
      const stillExists = logs.some(l => logKey(l) === selectedKey)
      if (!stillExists) setSelectedKey(null)
    }
  }, [logs, selectedKey])

  const selectedLog = useMemo(
    () => (selectedKey ? logs.find(l => logKey(l) === selectedKey) ?? null : null),
    [logs, selectedKey],
  )

  const handleRowClick = useCallback((log: LogEntry) => {
    const key = logKey(log)
    setSelectedKey(prev => (prev === key ? null : key))
  }, [])

  /* ================================================================ */
  /*  Render                                                           */
  /* ================================================================ */

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Log Explorer</h1>
          <p className="text-text-muted text-sm sm:text-base">Query and analyze service logs</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn btn-secondary flex items-center gap-2 text-sm ${autoRefresh ? 'bg-primary/20 text-primary' : ''}`}
          >
            <RefreshCw size={16} className={autoRefresh ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Auto-refresh</span>
            <span className="sm:hidden">Auto</span>
          </button>
          <button
            onClick={() => {
              const dataStr = JSON.stringify(logs, null, 2)
              const dataBlob = new Blob([dataStr], { type: 'application/json' })
              const url = URL.createObjectURL(dataBlob)
              const link = document.createElement('a')
              link.href = url
              link.download = `logs-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`
              link.click()
              URL.revokeObjectURL(url)
            }}
            disabled={logs.length === 0}
            className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <Download size={16} />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card space-y-3 sm:space-y-4">
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search logs... (press Enter)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && refetch()}
              className="w-full bg-surface-light border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-primary text-sm"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => refetch()}
              className="btn flex items-center gap-2 flex-1 sm:flex-none min-h-[44px] text-sm justify-center"
            >
              <Search size={16} />
              Search
            </button>
            {isAdmin() && (
            <button
              onClick={() => {
                let logql = '{job=~".+"}'
                if (levelFilter !== 'all') {
                  logql = `{job=~".+"} |= "${levelFilter}"`
                }
                if (searchQuery) {
                  logql += ` |= "${searchQuery}"`
                }
                const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                  datasource: 'loki',
                  queries: [{ refId: 'A', expr: logql }],
                  range: { from: `now-${timeRange}`, to: 'now' }
                }))}`
                openGrafanaExplore(exploreUrl)
              }}
              className="btn btn-secondary flex items-center gap-2 flex-1 sm:flex-none min-h-[44px] text-sm justify-center"
            >
              <Download size={16} />
              <span className="hidden sm:inline">View in Grafana</span>
              <span className="sm:hidden">Grafana</span>
            </button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Level:</span>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Time:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="30m">Last 30 minutes</option>
              <option value="1h">Last 1 hour</option>
            </select>
          </div>

          <div className="text-xs sm:text-sm text-gray-400">
            {logs.length} entries (max 50)
          </div>
        </div>
      </div>

      {/* ======== Selected Log Detail Panel ======== */}
      {selectedLog && (
        <SelectedLogPanel
          log={selectedLog}
          isAdmin={isAdmin()}
          onClose={() => setSelectedKey(null)}
        />
      )}

      {/* Logs Display */}
      <div className="card p-0 sm:p-0">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading logs...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 px-4">
            <FileText className="text-error mx-auto mb-4" size={48} />
            <p className="text-error">Failed to load logs</p>
            <p className="text-sm text-gray-400 mt-2">{(error as Error).message}</p>
            <button onClick={() => refetch()} className="btn btn-secondary mt-4">
              Retry
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 px-4">
            <Inbox className="text-gray-500 mx-auto mb-4" size={56} />
            <p className="text-white text-lg font-semibold">No customer logs connected</p>
            <p className="text-gray-400 mt-2 text-sm">This workspace is not receiving customer service logs yet.</p>
            <p className="text-gray-500 mt-1 text-xs">Deploy a collector to ingest logs for your services.</p>
          </div>
        ) : (
          <div className="space-y-0 max-h-[600px] overflow-y-auto divide-y divide-gray-700/30">
            {logs.map((log, index) => {
              const key = logKey(log)
              const isSelected = selectedKey === key
              return (
                <div
                  key={index}
                  onClick={() => handleRowClick(log)}
                  className={`p-2 sm:p-3 transition-colors cursor-pointer border-l-2 ${
                    isSelected
                      ? 'bg-primary/10 border-primary'
                      : 'hover:bg-surface-light border-transparent hover:border-primary/40'
                  }`}
                >
                  {/* Desktop: single row */}
                  <div className="hidden sm:flex items-start gap-3">
                    <div className="text-xs text-gray-500 font-mono whitespace-nowrap pt-1">
                      {new Date(log.timestamp).toLocaleTimeString('en-US', {
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </div>
                    <div className={`text-xs font-medium px-2 py-0.5 rounded border whitespace-nowrap ${getLevelColor(log.level)}`}>
                      {log.level.toUpperCase()}
                    </div>
                    {log.stream.job && (
                      <code className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded whitespace-nowrap">
                        {log.stream.job}
                      </code>
                    )}
                    <div className="flex-1 text-sm text-gray-300 font-mono break-all">
                      {log.message}
                    </div>
                  </div>

                  {/* Mobile: stacked layout */}
                  <div className="sm:hidden">
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${getLevelColor(log.level)}`}>
                        {log.level.toUpperCase()}
                      </div>
                      {log.stream.job && (
                        <code className="text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded truncate">
                          {log.stream.job}
                        </code>
                      )}
                      <span className="text-[10px] text-gray-500 font-mono ml-auto flex-shrink-0">
                        {new Date(log.timestamp).toLocaleTimeString('en-US', {
                          hour12: false,
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })}
                      </span>
                    </div>
                    <div className="text-xs text-gray-300 font-mono break-all line-clamp-3">
                      {log.message}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

/* ================================================================== */
/*  Selected Log Detail Panel                                          */
/* ================================================================== */

function SelectedLogPanel({
  log,
  isAdmin,
  onClose,
}: {
  log: LogEntry
  isAdmin: boolean
  onClose: () => void
}) {
  const s = log.stream

  // Collect priority labels
  const priorityLabels: { key: string; value: string }[] = []
  const otherLabels: { key: string; value: string }[] = []

  for (const [k, v] of Object.entries(s)) {
    if (!v) continue
    if (PRIORITY_LABEL_KEYS.has(k)) {
      priorityLabels.push({ key: k, value: v })
    } else {
      otherLabels.push({ key: k, value: v })
    }
  }

  // Sort priority labels in a meaningful order
  const PRIORITY_ORDER = ['service_key', 'service_name', 'job', 'level', 'environment', 'source', 'trace_id', 'span_id']
  priorityLabels.sort((a, b) => {
    const ai = PRIORITY_ORDER.indexOf(a.key)
    const bi = PRIORITY_ORDER.indexOf(b.key)
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
  })

  return (
    <div className="card border border-primary/30 bg-surface/80">
      {/* Panel header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Selected Log</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors p-1 rounded hover:bg-surface-light"
          title="Dismiss"
        >
          <X size={16} />
        </button>
      </div>

      {/* Main fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-2 mb-3">
        <DetailField label="Timestamp" value={
          new Date(log.timestamp).toLocaleString('en-US', {
            hour12: false, year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', second: '2-digit',
          })
        } />
        <DetailField label="Level">
          <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded border ${getLevelBadgeColor(log.level)}`}>
            {log.level.toUpperCase()}
          </span>
        </DetailField>
        <DetailField label="Service Key" value={s.service_key || 'N/A'} mono />
        <DetailField label="Job" value={s.job || 'N/A'} mono />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-2 mb-3">
        <DetailField label="Service Name" value={s.service_name || s.service || 'N/A'} mono />
        <DetailField label="Environment" value={s.environment || 'N/A'} />
        <DetailField label="Trace ID" value={s.trace_id || 'N/A'} mono />
        <DetailField label="Span ID" value={s.span_id || 'N/A'} mono />
      </div>

      {/* Message */}
      <div className="mb-3">
        <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">Message</span>
        <div className="mt-1 text-sm text-gray-200 font-mono bg-surface-light rounded p-2.5 max-h-32 overflow-y-auto break-all whitespace-pre-wrap border border-gray-700/50">
          {log.message}
        </div>
      </div>

      {/* Labels */}
      {priorityLabels.length > 0 && (
        <div className="mb-3">
          <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">Labels</span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {priorityLabels.map(({ key, value }) => (
              <span key={key} className="inline-flex items-center gap-1 text-xs bg-surface-light border border-gray-700/50 rounded px-2 py-0.5 text-gray-300">
                <span className="text-gray-500">{key}:</span>
                <span className="text-gray-200 font-mono">{value}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {otherLabels.length > 0 && (
        <div className="mb-3">
          <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">Other Labels</span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {otherLabels.map(({ key, value }) => (
              <span key={key} className="inline-flex items-center gap-1 text-xs bg-surface-light/60 border border-gray-700/30 rounded px-2 py-0.5 text-gray-400">
                <span className="text-gray-500">{key}:</span>
                <span className="font-mono">{value}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action */}
      {isAdmin && (
        <div className="pt-2 border-t border-gray-700/40">
          <button
            onClick={() => openGrafanaExplore(buildSelectedLogGrafanaPath(log))}
            className="btn btn-secondary flex items-center gap-2 text-sm"
          >
            <ExternalLink size={14} />
            Open Selected in Grafana
          </button>
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Tiny sub-component                                                 */
/* ------------------------------------------------------------------ */

function DetailField({
  label,
  value,
  mono,
  children,
}: {
  label: string
  value?: string
  mono?: boolean
  children?: React.ReactNode
}) {
  return (
    <div className="min-w-0">
      <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">{label}</span>
      <div className={`text-sm mt-0.5 truncate ${mono ? 'font-mono text-gray-200' : 'text-gray-300'}`}>
        {children ?? value ?? 'N/A'}
      </div>
    </div>
  )
}
