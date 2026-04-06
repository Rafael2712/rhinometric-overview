import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Clock, ArrowUpDown, Network, XCircle, Download, Inbox } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { summarizeTrace, formatDuration } from '../utils/traceAnalysis'
import type { JaegerTrace, TraceClassificationType } from '../utils/traceAnalysis'

type SortKey = 'recent' | 'duration' | 'errors' | 'spans'

const CLS_BADGE: Record<TraceClassificationType, { bg: string; text: string; label: string }> = {
  collector: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'Collector' },
  platform:  { bg: 'bg-purple-500/20', text: 'text-purple-300', label: 'Platform' },
  customer:  { bg: 'bg-emerald-500/20', text: 'text-emerald-300', label: 'Customer' },
}

export function TracesPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((state) => state.token)

  // Read navigation state from Service Map (node click / edge click)
  const navState = (location.state || {}) as Record<string, string | undefined>
  const prefillSvc = navState.prefillService || navState.sourceService || ''
  const prefillOp = navState.prefillOperation || ''

  const [searchQuery, setSearchQuery] = useState(prefillOp)
  const [serviceFilter, setServiceFilter] = useState(prefillSvc || 'all')
  const [minDuration, setMinDuration] = useState('')
  const [timeRange, setTimeRange] = useState('1h')
  const [sortBy, setSortBy] = useState<SortKey>('recent')

  // Fetch available services
  const { data: servicesData } = useQuery({
    queryKey: ['trace-services', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const res = await fetch('/api/traces/services', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch services')
      return res.json()
    },
    enabled: !!token,
    staleTime: 60_000,
  })

  const { data: tracesData, isLoading, error, refetch } = useQuery({
    queryKey: ['traces', token, serviceFilter, minDuration, timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token available')

      const params = new URLSearchParams({
        limit: '100',
        lookback: timeRange
      })

      if (serviceFilter !== 'all') {
        params.append('service', serviceFilter)
      }
      if (minDuration) {
        params.append('minDuration', `${minDuration}ms`)
      }

      const response = await fetch(`/api/traces?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (!response.ok) throw new Error('Failed to fetch traces')
      return response.json()
    },
    enabled: !!token,
    staleTime: 0,
  })

  const traces: JaegerTrace[] = tracesData?.traces || []
  const services = ['all', ...(servicesData?.services || [])]

  // Compute summaries for all traces
  const traceSummaries = traces.map(trace => ({
    trace,
    summary: summarizeTrace(trace),
  }))

  // Filter
  const filtered = traceSummaries.filter(({ trace, summary }) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      trace.traceID.toLowerCase().includes(q) ||
      summary.rootOperation.toLowerCase().includes(q) ||
      summary.rootService.toLowerCase().includes(q)
    )
  })

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    switch (sortBy) {
      case 'duration': return b.summary.totalDuration - a.summary.totalDuration
      case 'errors': return b.summary.errorCount - a.summary.errorCount
      case 'spans': return b.summary.spanCount - a.summary.spanCount
      case 'recent':
      default: return b.summary.startTime - a.summary.startTime
    }
  })

  const getDurationColor = (us: number): string => {
    if (us > 1000000) return 'bg-red-500'
    if (us > 500000) return 'bg-yellow-500'
    if (us > 100000) return 'bg-blue-500'
    return 'bg-green-500'
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Distributed Traces</h1>
          <p className="text-text-muted text-sm sm:text-base">Analyze request flows and identify bottlenecks</p>
        </div>
        <button
          onClick={() => {
            const dataStr = JSON.stringify(traces, null, 2)
            const dataBlob = new Blob([dataStr], { type: 'application/json' })
            const url = URL.createObjectURL(dataBlob)
            const link = document.createElement('a')
            link.href = url
            link.download = `traces-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`
            link.click()
            URL.revokeObjectURL(url)
          }}
          disabled={traces.length === 0}
          className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm self-start sm:self-auto"
        >
          <Download size={16} />
          Export
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card space-y-3 sm:space-y-4">
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search by Trace ID, Operation, or Service..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-light border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            />
          </div>
          <button
            onClick={() => refetch()}
            className="btn flex items-center gap-2 min-h-[44px] text-sm justify-center"
          >
            <Search size={16} />
            Search
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Service:</span>
            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm max-w-[160px]"
            >
              {services.map(svc => (
                <option key={svc} value={svc}>{svc === 'all' ? 'All Services' : svc}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Min Duration:</span>
            <input
              type="number"
              placeholder="ms"
              value={minDuration}
              onChange={(e) => setMinDuration(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm w-20"
            />
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Time Range:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="15m">Last 15 min</option>
              <option value="30m">Last 30 min</option>
              <option value="1h">Last 1 hour</option>
              <option value="3h">Last 3 hours</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <ArrowUpDown size={16} className="text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400 hidden sm:inline">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="recent">Most Recent</option>
              <option value="duration">Slowest First</option>
              <option value="errors">Most Errors</option>
              <option value="spans">Most Spans</option>
            </select>
          </div>

          <div className="text-xs sm:text-sm text-gray-400 w-full sm:w-auto sm:ml-auto">
            {sorted.length} trace{sorted.length !== 1 ? 's' : ''} found
          </div>
        </div>
      </div>

      {/* Traces Display */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading traces...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 px-4">
            <Network className="text-error mx-auto mb-4" size={48} />
            <p className="text-error">Failed to load traces</p>
            <p className="text-sm text-gray-400 mt-2">{(error as Error).message}</p>
            <button onClick={() => refetch()} className="btn btn-secondary mt-4">
              Retry
            </button>
          </div>
        ) : traces.length === 0 ? (
          <div className="text-center py-16 px-4">
            <Inbox className="text-gray-500 mx-auto mb-4" size={56} />
            <p className="text-white text-lg font-semibold">No traces found</p>
            <p className="text-gray-400 mt-2 text-sm">No distributed traces available in the selected time range.</p>
            <p className="text-gray-500 mt-1 text-xs">Try expanding the time range or check that trace ingestion is active.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sorted.map(({ trace, summary }) => {
              const clsBadge = CLS_BADGE[summary.classificationType] || CLS_BADGE.collector
              const isSlow = summary.totalDuration > 1000000
              return (
                <div
                  key={trace.traceID}
                  className={`p-3 sm:p-4 bg-surface-light hover:bg-surface-light/80 border rounded-lg cursor-pointer transition-all ${
                    summary.errorCount > 0
                      ? 'border-red-500/30 hover:border-red-500/50'
                      : isSlow
                      ? 'border-yellow-500/20 hover:border-yellow-500/40'
                      : 'border-gray-700 hover:border-primary/50'
                  }`}
                  onClick={() => navigate(`/traces/${trace.traceID}`, { state: { trace } })}
                >
                  {/* Row 1: ID + badges + duration */}
                  <div className="flex items-center justify-between mb-1.5 gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${getDurationColor(summary.totalDuration)}`} />
                      <span className="text-white font-mono text-xs sm:text-sm truncate">
                        {trace.traceID.slice(0, 16)}...
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${clsBadge.bg} ${clsBadge.text}`}>
                        {clsBadge.label}
                      </span>
                      <span className="text-[10px] sm:text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-300 flex-shrink-0">
                        {summary.spanCount} span{summary.spanCount > 1 ? 's' : ''}
                      </span>
                      {summary.serviceCount > 1 && (
                        <span className="text-[10px] sm:text-xs px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400 flex-shrink-0">
                          {summary.serviceCount} svc{summary.serviceCount > 1 ? 's' : ''}
                        </span>
                      )}
                      {summary.errorCount > 0 && (
                        <span className="text-[10px] sm:text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 flex-shrink-0 flex items-center gap-0.5">
                          <XCircle size={10} /> {summary.errorCount}
                        </span>
                      )}
                    </div>
                    <span className={`font-mono text-xs sm:text-sm flex-shrink-0 font-medium ${
                      summary.totalDuration > 1000000 ? 'text-red-400' :
                      summary.totalDuration > 500000 ? 'text-yellow-400' :
                      'text-gray-300'
                    }`}>
                      {formatDuration(summary.totalDuration)}
                    </span>
                  </div>

                  {/* Row 2: operation */}
                  <div className="text-xs sm:text-sm text-gray-200 mb-1.5 truncate font-medium">
                    {summary.rootOperation}
                  </div>

                  {/* Row 3: service + timestamp */}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="truncate">{summary.rootService}</span>
                    <span>{'\u2022'}</span>
                    <span className="flex-shrink-0">
                      {new Date(summary.startTime / 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
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
