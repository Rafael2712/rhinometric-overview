import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { useNavigate } from 'react-router-dom'
import { FileText, AlertTriangle, XCircle, Info, Bug, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import { useState, useMemo } from 'react'

interface LogEntry {
  timestamp: string
  message: string
  level: string
  source_type?: string
  service_type?: string
  fields?: Record<string, any>
  stream?: Record<string, string>
}

interface Props {
  serviceKey: string
  traceStartUs: number
  traceDurationUs: number
}

const LEVEL_ICON: Record<string, React.ReactNode> = {
  error: <XCircle size={14} className="text-red-400" />,
  warn:  <AlertTriangle size={14} className="text-yellow-400" />,
  info:  <Info size={14} className="text-blue-400" />,
  debug: <Bug size={14} className="text-gray-400" />,
}

const LEVEL_COLOR: Record<string, string> = {
  error: 'text-red-300',
  warn:  'text-yellow-300',
  info:  'text-gray-300',
  debug: 'text-gray-500',
}

const LEVEL_PRIORITY: Record<string, number> = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
}

/** Convert Jaeger microseconds to milliseconds */
function usToMs(us: number): number {
  return Math.floor(us / 1000)
}

/** Convert milliseconds to nanoseconds (string to avoid precision loss) */
function msToNs(ms: number): string {
  return String(ms * 1_000_000)
}

function formatTimestamp(ts: string): string {
  let ms: number
  if (/^\d{16,}$/.test(ts)) {
    ms = Number(ts) / 1_000_000
  } else if (/^\d{13}$/.test(ts)) {
    ms = Number(ts)
  } else {
    ms = new Date(ts).getTime()
  }
  try {
    const d = new Date(ms)
    return d.toLocaleTimeString(undefined, {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      fractionalSecondDigits: 3,
    } as Intl.DateTimeFormatOptions)
  } catch { return ts }
}

export function RelatedLogs({ serviceKey, traceStartUs, traceDurationUs }: Props) {
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)

  // Step 2: Compute time window in milliseconds with ±30s padding
  const fromMs = usToMs(traceStartUs) - 30_000
  const toMs   = usToMs(traceStartUs + traceDurationUs) + 30_000

  // Step 3: Convert to nanoseconds for API
  const fromNs = msToNs(fromMs)
  const toNs   = msToNs(toMs)

  // Step 4: Fetch logs ONCE on mount / when trace changes
  const { data, isLoading, error } = useQuery({
    queryKey: ['related-logs', serviceKey, traceStartUs, traceDurationUs],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({
        query: '{job="' + serviceKey + '"}',
        service: serviceKey,
        start: fromNs,
        end: toNs,
      })
      const res = await fetch(`/api/logs/enriched?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`Logs API error: ${res.status}`)
      const json = await res.json()
      return (json.data?.entries || json.entries || json.data || []) as LogEntry[]
    },
    enabled: !!token && !!serviceKey,
    staleTime: 120_000,
    retry: 1,
  })

  const logs = data || []

  // Sort by severity: ERROR → WARN → INFO → DEBUG
  const sortedLogs = useMemo(() => {
    return [...logs].sort((a, b) => {
      const pa = LEVEL_PRIORITY[a.level] ?? 4
      const pb = LEVEL_PRIORITY[b.level] ?? 4
      return pa - pb
    })
  }, [logs])

  const errorCount = logs.filter(l => l.level === 'error').length
  const warnCount  = logs.filter(l => l.level === 'warn').length
  const visibleLogs = expanded ? sortedLogs : sortedLogs.slice(0, 8)

  // Summary: "X logs found — Y errors, Z warnings"
  const summaryParts: string[] = []
  if (logs.length > 0) {
    summaryParts.push(`${logs.length} log${logs.length !== 1 ? 's' : ''} found`)
    if (errorCount > 0) summaryParts.push(`${errorCount} error${errorCount !== 1 ? 's' : ''}`)
    if (warnCount > 0) summaryParts.push(`${warnCount} warning${warnCount !== 1 ? 's' : ''}`)
  }

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-primary" />
          <h3 className="text-sm font-semibold text-white">Related Logs</h3>
          <span className="text-xs text-gray-500 font-mono">({serviceKey})</span>
        </div>
        <div className="flex items-center gap-2">
          {errorCount > 0 && (
            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">
              {errorCount} error{errorCount !== 1 ? 's' : ''}
            </span>
          )}
          {warnCount > 0 && (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
              {warnCount} warn
            </span>
          )}
          <span className="text-xs text-gray-500">{logs.length} entries</span>
        </div>
      </div>

      <div className="p-4">
        {isLoading && (
          <p className="text-gray-400 text-sm animate-pulse">Loading logs...</p>
        )}
        {error && (
          <p className="text-red-400 text-sm">Failed to load logs</p>
        )}

        {/* Empty state: no logs in window */}
        {!isLoading && !error && logs.length === 0 && (
          <p className="text-gray-500 text-sm">No logs found in this time window</p>
        )}

        {/* Summary */}
        {logs.length > 0 && (
          <p className="text-xs text-gray-400 mb-3">
            {summaryParts.join(' \u2014 ')}
          </p>
        )}

        {visibleLogs.length > 0 && (
          <div className="space-y-1 font-mono text-xs">
            {visibleLogs.map((log, i) => (
              <div
                key={i}
                className={'flex items-start gap-2 py-1 px-2 rounded hover:bg-white/5 ' +
                  (log.level === 'error' ? 'bg-red-500/5' : log.level === 'warn' ? 'bg-yellow-500/5' : '')}
              >
                <span className="flex-shrink-0 mt-0.5">{LEVEL_ICON[log.level] || LEVEL_ICON.info}</span>
                <span className="text-gray-500 flex-shrink-0 w-20">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={LEVEL_COLOR[log.level] || 'text-gray-300'}>
                  {log.message.length > 200 ? log.message.slice(0, 200) + '...' : log.message}
                </span>
              </div>
            ))}
          </div>
        )}

        {logs.length > 8 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 mt-2"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? 'Show less' : `Show all ${logs.length} entries`}
          </button>
        )}

        {/* View All Logs — navigate internally */}
        {serviceKey && (
          <button
            onClick={() => navigate('/logs', {
              state: {
                query: '{job=" ' + serviceKey + '}',
 service: serviceKey,
                from: fromMs,
                to: toMs,
              },
            })}
            className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 mt-3 pt-3 border-t border-white/5"
          >
            <ExternalLink size={14} />
            View All Logs
          </button>
        )}
      </div>
    </div>
  )
}
