import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { FileText, AlertTriangle, XCircle, Info, Bug, ChevronDown, ChevronUp } from 'lucide-react'
import { useState, useMemo } from 'react'

interface LogEntry {
  timestamp: string
  message: string
  level: string
  source_type: string
  service_type: string
  fields: Record<string, any>
  stream: Record<string, string>
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

function usToNs(us: number): string {
  return String(Math.floor(us) * 1000)
}

function formatNsTimestamp(ns: string): string {
  const ms = Number(ns) / 1_000_000
  try {
    const d = new Date(ms)
    return d.toLocaleTimeString(undefined, {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      fractionalSecondDigits: 3,
    } as Intl.DateTimeFormatOptions)
  } catch { return ns }
}

/** Detect if a log message is generic collector noise */
function isCollectorNoise(msg: string): boolean {
  const noisePatterns = [
    /^collector.*cycle/i,
    /^sending\s+(metrics|logs)/i,
    /^cycle\s+completed/i,
    /^starting\s+collection/i,
  ]
  return noisePatterns.some(p => p.test(msg))
}

export function RelatedLogs({ serviceKey, traceStartUs, traceDurationUs }: Props) {
  const token = useAuthStore((s) => s.token)
  const [expanded, setExpanded] = useState(false)
  const [limit, setLimit] = useState(25)

  const PAD = 30_000_000
  const startNs = usToNs(traceStartUs - PAD)
  const endNs   = usToNs(traceStartUs + traceDurationUs + PAD)

  const { data, isLoading, error } = useQuery({
    queryKey: ['related-logs', serviceKey, traceStartUs, limit],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({
        query: `{job="${serviceKey}"}`,
        limit: String(limit),
        start: startNs,
        end: endNs,
        direction: 'forward',
        service: serviceKey,
      })
      const res = await fetch(`/api/logs/enriched?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`Logs API error: ${res.status}`)
      const json = await res.json()
      return (json.data?.entries || []) as LogEntry[]
    },
    enabled: !!token && !!serviceKey,
    staleTime: 120_000,
    retry: 1,
  })

  const logs = data || []

  // Sort by severity: errors first, then warns, then info/debug
  const sortedLogs = useMemo(() => {
    return [...logs].sort((a, b) => {
      const pa = LEVEL_PRIORITY[a.level] ?? 4
      const pb = LEVEL_PRIORITY[b.level] ?? 4
      if (pa !== pb) return pa - pb
      return 0 // preserve original order within same level
    })
  }, [logs])

  const errorLogs = logs.filter(l => l.level === 'error')
  const warnLogs  = logs.filter(l => l.level === 'warn')
  const allNoise = logs.length > 0 && logs.every(l => isCollectorNoise(l.message))
  const visibleLogs = expanded ? sortedLogs : sortedLogs.slice(0, 8)

  // Summary sentence
  const summaryParts: string[] = []
  if (logs.length > 0) {
    summaryParts.push(`${logs.length} log${logs.length > 1 ? 's' : ''} found in \u00B130s window`)
    if (errorLogs.length > 0) summaryParts.push(`${errorLogs.length} error${errorLogs.length > 1 ? 's' : ''}`)
    if (warnLogs.length > 0) summaryParts.push(`${warnLogs.length} warning${warnLogs.length > 1 ? 's' : ''}`)
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
          {errorLogs.length > 0 && (
            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">
              {errorLogs.length} error{errorLogs.length > 1 ? 's' : ''}
            </span>
          )}
          {warnLogs.length > 0 && (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full">
              {warnLogs.length} warn
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

        {/* Empty state */}
        {!isLoading && !error && logs.length === 0 && (
          <p className="text-gray-500 text-sm">No related logs found in the {'\u00B1'}30s window around this trace.</p>
        )}

        {/* Summary sentence */}
        {logs.length > 0 && (
          <p className="text-xs text-gray-400 mb-3">
            {summaryParts.join(' \u2014 ')}
            {allNoise && (
              <span className="ml-1 text-gray-500 italic"> &mdash; all entries appear to be internal collector logs.</span>
            )}
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
                  {formatNsTimestamp(log.timestamp)}
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
        {logs.length >= limit && (
          <button
            onClick={() => setLimit(l => l + 50)}
            className="text-xs text-gray-400 hover:text-white mt-1 ml-5"
          >
            Load more...
          </button>
        )}
      </div>
    </div>
  )
}
