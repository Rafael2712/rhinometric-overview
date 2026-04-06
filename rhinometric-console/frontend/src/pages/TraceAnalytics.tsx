/* eslint-disable */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { RefreshCw, AlertTriangle, Inbox, Flame, Zap, BarChart3 } from 'lucide-react'
import { summarizeTrace, formatDuration } from '../utils/traceAnalysis'
import type { JaegerTrace } from '../utils/traceAnalysis'

/* ================================================================
   TYPES
   ================================================================ */

interface OperationStats {
  operation: string
  rootService: string
  count: number
  avgLatency: number   // µs
  p95Latency: number   // µs
  maxLatency: number   // µs
  errorRate: number    // 0..1
  errorCount: number
  serviceCount: number // max unique services across traces
}

/* ================================================================
   AGGREGATION ENGINE
   ================================================================ */

function aggregateOperations(traces: JaegerTrace[]): OperationStats[] {
  const groups = new Map<string, {
    operation: string
    rootService: string
    durations: number[]
    errorTraces: number
    maxServiceCount: number
  }>()

  for (const trace of traces) {
    const summary = summarizeTrace(trace)
    if (!summary.rootOperation || summary.rootOperation === 'Unknown') continue

    const key = summary.rootOperation
    let g = groups.get(key)
    if (!g) {
      g = {
        operation: summary.rootOperation,
        rootService: summary.rootService,
        durations: [],
        errorTraces: 0,
        maxServiceCount: 0,
      }
      groups.set(key, g)
    }

    g.durations.push(summary.totalDuration)
    if (summary.errorCount > 0) g.errorTraces++
    if (summary.serviceCount > g.maxServiceCount) g.maxServiceCount = summary.serviceCount
  }

  const result: OperationStats[] = []
  for (const g of groups.values()) {
    const sorted = [...g.durations].sort((a, b) => a - b)
    const count = sorted.length
    const sum = sorted.reduce((a, b) => a + b, 0)
    const p95Idx = Math.min(Math.floor(count * 0.95), count - 1)

    result.push({
      operation: g.operation,
      rootService: g.rootService,
      count,
      avgLatency: Math.round(sum / count),
      p95Latency: sorted[p95Idx],
      maxLatency: sorted[count - 1],
      errorRate: count > 0 ? g.errorTraces / count : 0,
      errorCount: g.errorTraces,
      serviceCount: g.maxServiceCount,
    })
  }

  return result
}

/* ================================================================
   FORMATTING HELPERS
   ================================================================ */

function latencyColor(us: number): string {
  if (us > 1_000_000) return 'text-red-400'
  if (us > 500_000) return 'text-amber-400'
  if (us > 100_000) return 'text-blue-400'
  return 'text-emerald-400'
}

function barWidth(value: number, max: number): string {
  if (max <= 0) return '0%'
  return `${Math.max(4, Math.round((value / max) * 100))}%`
}

function barColor(us: number): string {
  if (us > 1_000_000) return 'bg-red-500'
  if (us > 500_000) return 'bg-amber-500'
  if (us > 100_000) return 'bg-blue-500'
  return 'bg-emerald-500'
}

function errorBadgeClass(rate: number): string {
  if (rate > 0.1) return 'bg-red-500/20 text-red-400 border-red-500/40'
  if (rate > 0) return 'bg-amber-500/20 text-amber-400 border-amber-500/40'
  return 'bg-gray-700/30 text-gray-500 border-gray-600/30'
}

/* ================================================================
   SECTION COMPONENT
   ================================================================ */

function OperationSection({
  title,
  icon,
  iconColor,
  ops,
  navigate,
  maxLatency,
}: {
  title: string
  icon: React.ReactNode
  iconColor: string
  ops: OperationStats[]
  navigate: (path: string, opts?: any) => void
  maxLatency: number
}) {
  if (ops.length === 0) return null

  return (
    <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <span className={iconColor}>{icon}</span>
        <h3 className="text-sm font-bold text-gray-200">{title}</h3>
        <span className="text-xs text-gray-500 ml-1">({ops.length})</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-800/40 text-gray-400 uppercase tracking-wider text-[10px]">
              <th className="px-4 py-2.5 text-left font-semibold w-8">#</th>
              <th className="px-4 py-2.5 text-left font-semibold">Operation</th>
              <th className="px-4 py-2.5 text-right font-semibold">Calls</th>
              <th className="px-4 py-2.5 text-right font-semibold">Avg</th>
              <th className="px-4 py-2.5 text-right font-semibold">p95</th>
              <th className="px-4 py-2.5 text-right font-semibold">Max</th>
              <th className="px-4 py-2.5 text-left font-semibold pl-6" style={{ minWidth: 140 }}>Latency</th>
              <th className="px-4 py-2.5 text-right font-semibold">Errors</th>
              <th className="px-4 py-2.5 text-right font-semibold">Svcs</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {ops.map((op, i) => (
              <tr
                key={op.operation}
                className="hover:bg-gray-800/30 cursor-pointer transition-colors"
                onClick={() => navigate('/traces', { state: { prefillOperation: op.operation } })}
              >
                <td className="px-4 py-2.5 text-gray-500 font-mono">{i + 1}</td>
                <td className="px-4 py-2.5">
                  <div className="text-gray-200 font-medium truncate max-w-[280px]" title={op.operation}>
                    {op.operation}
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5">{op.rootService}</div>
                </td>
                <td className="px-4 py-2.5 text-right text-gray-200 font-mono">{op.count}</td>
                <td className={`px-4 py-2.5 text-right font-mono ${latencyColor(op.avgLatency)}`}>
                  {formatDuration(op.avgLatency)}
                </td>
                <td className={`px-4 py-2.5 text-right font-mono font-medium ${latencyColor(op.p95Latency)}`}>
                  {formatDuration(op.p95Latency)}
                </td>
                <td className={`px-4 py-2.5 text-right font-mono ${latencyColor(op.maxLatency)}`}>
                  {formatDuration(op.maxLatency)}
                </td>
                <td className="px-4 py-2.5 pl-6">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${barColor(op.p95Latency)}`}
                        style={{ width: barWidth(op.p95Latency, maxLatency) }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border ${errorBadgeClass(op.errorRate)}`}>
                    {(op.errorRate * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right text-gray-400 font-mono">{op.serviceCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ================================================================
   MAIN PAGE
   ================================================================ */

export function TraceAnalyticsPage() {
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const { data: tracesData, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['trace-analytics'],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({ limit: '100', lookback: '15m' })
      const res = await fetch(`/api/traces?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch traces')
      return res.json()
    },
    enabled: !!token,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })

  const traces: JaegerTrace[] = tracesData?.traces || []

  const ops = useMemo(() => aggregateOperations(traces), [traces])

  const topSlow = useMemo(() =>
    [...ops].sort((a, b) => b.p95Latency - a.p95Latency).slice(0, 10),
    [ops]
  )
  const topFailing = useMemo(() =>
    [...ops].filter(o => o.errorRate > 0).sort((a, b) => b.errorRate - a.errorRate).slice(0, 10),
    [ops]
  )
  const topFrequent = useMemo(() =>
    [...ops].sort((a, b) => b.count - a.count).slice(0, 10),
    [ops]
  )

  const globalMaxLatency = useMemo(() =>
    Math.max(1, ...ops.map(o => o.p95Latency)),
    [ops]
  )

  const summaryStats = useMemo(() => ({
    operations: ops.length,
    totalTraces: traces.length,
    avgLatency: ops.length > 0
      ? Math.round(ops.reduce((s, o) => s + o.avgLatency, 0) / ops.length)
      : 0,
    errorOps: ops.filter(o => o.errorRate > 0).length,
  }), [ops, traces])

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Trace Analytics</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Operational insights &mdash; aggregated from {traces.length} traces
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs
            transition-colors disabled:opacity-50 border border-gray-700"
        >
          <RefreshCw size={12} className={isFetching ? 'animate-spin' : ''} />
          {isFetching ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: 'Operations', value: summaryStats.operations, color: 'text-cyan-400' },
          { label: 'Traces', value: summaryStats.totalTraces, color: 'text-gray-200' },
          { label: 'Avg Latency', value: formatDuration(summaryStats.avgLatency), color: 'text-amber-400' },
          { label: 'Error Ops', value: summaryStats.errorOps,
            color: summaryStats.errorOps > 0 ? 'text-red-400' : 'text-emerald-400' },
        ].map(s => (
          <div key={s.label} className="bg-surface rounded-lg border border-gray-700/50 p-2 sm:p-3 text-center">
            <p className={`text-lg sm:text-xl font-bold font-mono ${s.color}`}>{s.value}</p>
            <p className="text-[10px] sm:text-xs text-gray-500 font-medium uppercase tracking-wide">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle size={16} />
          Failed to load traces: {(error as Error).message}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16 gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
          <span className="text-gray-400 text-sm">Analyzing traces&hellip;</span>
        </div>
      ) : ops.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <Inbox size={56} className="mb-4 opacity-20" />
          <p className="text-lg font-semibold text-gray-400">No trace operations available</p>
          <p className="text-sm mt-1 text-gray-600">
            No traces found in the last 15 minutes.
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs
              transition-colors border border-gray-700 flex items-center gap-1.5"
          >
            <RefreshCw size={12} />
            Try again
          </button>
        </div>
      ) : (
        /* Sections */
        <div className="space-y-4 sm:space-y-6">
          <OperationSection
            title="Top Slow Operations"
            icon={<Zap size={14} />}
            iconColor="text-amber-400"
            ops={topSlow}
            navigate={navigate}
            maxLatency={globalMaxLatency}
          />
          {topFailing.length > 0 && (
            <OperationSection
              title="Most Failing Operations"
              icon={<Flame size={14} />}
              iconColor="text-red-400"
              ops={topFailing}
              navigate={navigate}
              maxLatency={globalMaxLatency}
            />
          )}
          <OperationSection
            title="Most Frequent Operations"
            icon={<BarChart3 size={14} />}
            iconColor="text-cyan-400"
            ops={topFrequent}
            navigate={navigate}
            maxLatency={globalMaxLatency}
          />
        </div>
      )}
    </div>
  )
}
