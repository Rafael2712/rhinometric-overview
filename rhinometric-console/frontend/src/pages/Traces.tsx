import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Network, Clock, Search, Filter, Download, ExternalLink, Inbox } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface Span {
  spanID: string
  traceID: string
  operationName: string
  startTime: number
  duration: number
  serviceName: string
  tags?: Record<string, any>
  logs?: any[]
}

interface Trace {
  traceID: string
  spans: Span[]
  processes: Record<string, any>
  warnings?: string[]
}

export function TracesPage() {
  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const [searchQuery, setSearchQuery] = useState('')
  const [serviceFilter, setServiceFilter] = useState<string>('all')
  const [minDuration, setMinDuration] = useState<string>('')
  const [timeRange, setTimeRange] = useState<string>('15m')
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null)
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null)

  // Fetch available services (backend already filters internal ones)
  const { data: servicesData } = useQuery({
    queryKey: ['jaeger-services'],
    queryFn: async () => {
      const response = await fetch('/api/traces/services', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!response.ok) return { services: [] }
      return response.json()
    },
    staleTime: 30000,
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

  const traces: Trace[] = tracesData?.traces || []
  const services = ['all', ...(servicesData?.services || [])]

  const formatDuration = (microseconds: number): string => {
    if (microseconds < 1000) return `${microseconds.toFixed(0)}us`
    if (microseconds < 1000000) return `${(microseconds / 1000).toFixed(2)}ms`
    return `${(microseconds / 1000000).toFixed(2)}s`
  }

  const getSpanColor = (duration: number): string => {
    if (duration > 1000000) return 'bg-error' // > 1s
    if (duration > 500000) return 'bg-warning' // > 500ms
    if (duration > 100000) return 'bg-primary' // > 100ms
    return 'bg-success' // < 100ms
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Distributed Traces</h1>
          <p className="text-text-muted text-sm sm:text-base">Analyze request flows and service performance</p>
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
              placeholder="Search by Trace ID or Operation..."
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

          <div className="text-xs sm:text-sm text-gray-400 w-full sm:w-auto sm:ml-auto">
            {traces.length} traces found
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
            <p className="text-white text-lg font-semibold">No customer traces connected</p>
            <p className="text-gray-400 mt-2 text-sm">This workspace is not receiving customer distributed traces yet.</p>
            <p className="text-gray-500 mt-1 text-xs">Deploy a collector to ingest traces for your services.</p>
          </div>
        ) : (
          <div className="space-y-2 sm:space-y-3">
            {traces
              .filter(trace =>
                !searchQuery ||
                trace.traceID.toLowerCase().includes(searchQuery.toLowerCase()) ||
                trace.spans.some(s => s.operationName.toLowerCase().includes(searchQuery.toLowerCase()))
              )
              .map((trace) => {
                const rootSpan = trace.spans[0]
                const totalDuration = Math.max(...trace.spans.map(s => s.duration))
                const spanCount = trace.spans.length

                return (
                  <div
                    key={trace.traceID}
                    className="p-3 sm:p-4 bg-surface-light hover:bg-surface-light/80 border border-gray-700 hover:border-primary/50 rounded-lg cursor-pointer transition-all active:bg-surface-light/80"
                    onClick={() => setSelectedTrace(trace)}
                  >
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${getSpanColor(totalDuration)}`}></div>
                        <span className="text-white font-mono text-xs sm:text-sm truncate">{trace.traceID.slice(0, 16)}...</span>
                        <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300 flex-shrink-0">
                          {spanCount} span{spanCount > 1 ? 's' : ''}
                        </span>
                      </div>
                      <span className="text-gray-400 text-xs sm:text-sm flex-shrink-0">
                        {formatDuration(totalDuration)}
                      </span>
                    </div>
                    <div className="text-xs sm:text-sm text-gray-300 mb-2 truncate">
                      {rootSpan?.operationName || 'Unknown Operation'}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="truncate">{rootSpan?.serviceName || 'unknown'}</span>
                      <span>{'\u2022'}</span>
                      <span className="flex-shrink-0">{new Date(rootSpan?.startTime / 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                )
              })}
          </div>
        )}
      </div>

      {/* Trace Detail Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-surface border border-gray-700 rounded-t-xl sm:rounded-lg w-full sm:max-w-6xl max-h-[92vh] sm:max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-3 sm:p-6 border-b border-gray-700 sticky top-0 bg-surface z-10">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-white mb-1">Trace Details</h2>
                <p className="text-xs sm:text-sm text-gray-400 font-mono truncate">{selectedTrace.traceID}</p>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-gray-400 hover:text-white p-2 hover:bg-error/20 rounded-lg transition-colors flex-shrink-0"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-3 sm:p-6">
              <div className="space-y-4 sm:space-y-6">
                {/* Trace Summary */}
                <div className="grid grid-cols-3 gap-2 sm:gap-4">
                  <div className="card p-2 sm:p-4">
                    <p className="text-xs text-gray-400 mb-1">Duration</p>
                    <p className="text-lg sm:text-2xl font-bold text-white">
                      {formatDuration(Math.max(...selectedTrace.spans.map(s => s.startTime + s.duration)) - Math.min(...selectedTrace.spans.map(s => s.startTime)))}
                    </p>
                  </div>
                  <div className="card p-2 sm:p-4">
                    <p className="text-xs text-gray-400 mb-1">Spans</p>
                    <p className="text-lg sm:text-2xl font-bold text-white">{selectedTrace.spans.length}</p>
                  </div>
                  <div className="card p-2 sm:p-4">
                    <p className="text-xs text-gray-400 mb-1">Services</p>
                    <p className="text-lg sm:text-2xl font-bold text-white">
                      {new Set(selectedTrace.spans.map(s => s.serviceName)).size}
                    </p>
                  </div>
                </div>

                {/* Waterfall Chart */}
                <div className="card p-2 sm:p-4">
                  <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4 flex items-center gap-2">
                    <Network size={20} />
                    Span Waterfall
                  </h3>
                  <div className="space-y-2 overflow-x-auto">
                    {(() => {
                      const minStartTime = Math.min(...selectedTrace.spans.map(s => s.startTime))
                      const maxEndTime = Math.max(...selectedTrace.spans.map(s => s.startTime + s.duration))
                      const totalTraceDuration = maxEndTime - minStartTime

                      return selectedTrace.spans
                        .sort((a, b) => a.startTime - b.startTime)
                        .map((span, index) => {
                          const startOffset = ((span.startTime - minStartTime) / totalTraceDuration) * 100
                          const width = (span.duration / totalTraceDuration) * 100

                          return (
                            <div
                              key={span.spanID}
                              className={`text-sm p-1.5 sm:p-2 rounded hover:bg-white/5 cursor-pointer transition-colors ${selectedSpan?.spanID === span.spanID ? 'bg-white/10 ring-1 ring-primary' : ''}`}
                              onClick={() => setSelectedSpan(span)}
                            >
                              <div className="flex items-center gap-1.5 sm:gap-2 mb-1">
                                <span className="text-gray-400 font-mono text-xs w-6 sm:w-8 flex-shrink-0">{index + 1}</span>
                                <span className="text-white flex-1 truncate font-medium text-xs sm:text-sm">{span.operationName}</span>
                                <span className="text-gray-400 text-xs flex-shrink-0">{formatDuration(span.duration)}</span>
                              </div>
                              <div className="h-5 sm:h-6 bg-surface-light rounded relative ml-7 sm:ml-10 overflow-hidden">
                                <div
                                  className={`absolute h-full rounded ${getSpanColor(span.duration)}`}
                                  style={{
                                    left: `${startOffset}%`,
                                    width: `${Math.max(width, 0.5)}%`,
                                    minWidth: '2px'
                                  }}
                                ></div>
                              </div>
                              <div className="text-[10px] sm:text-xs text-gray-500 ml-7 sm:ml-10 mt-1 flex justify-between">
                                <span className="truncate">{span.serviceName}</span>
                                <span className="flex-shrink-0">{span.spanID.slice(0,8)}</span>
                              </div>
                            </div>
                          )
                        })
                    })()}
                  </div>
                </div>

                {/* Span Details Panel */}
                {selectedSpan && (
                  <div className="card bg-surface-light border-primary/20 p-3 sm:p-4">
                    <div className="flex items-center justify-between mb-3 sm:mb-4">
                      <h3 className="text-base sm:text-lg font-semibold text-white">Span Details</h3>
                      <button onClick={() => setSelectedSpan(null)} className="text-gray-400 hover:text-white text-sm">
                        Close
                      </button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-primary mb-2">Metadata</h4>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Operation:</dt>
                            <dd className="text-white font-mono text-right truncate">{selectedSpan.operationName}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Service:</dt>
                            <dd className="text-white text-right truncate">{selectedSpan.serviceName}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Duration:</dt>
                            <dd className="text-white">{formatDuration(selectedSpan.duration)}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Start Time:</dt>
                            <dd className="text-white text-right">{new Date(selectedSpan.startTime / 1000).toLocaleString()}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Span ID:</dt>
                            <dd className="text-white font-mono text-right truncate">{selectedSpan.spanID}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt className="text-gray-400 flex-shrink-0">Trace ID:</dt>
                            <dd className="text-white font-mono text-right truncate">{selectedSpan.traceID}</dd>
                          </div>
                        </dl>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-primary mb-2">Tags & Attributes</h4>
                        {selectedSpan.tags && Object.keys(selectedSpan.tags).length > 0 ? (
                          <div className="bg-black/30 rounded p-2 sm:p-3 max-h-48 overflow-y-auto">
                            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-all">
                              {JSON.stringify(selectedSpan.tags, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm italic">No tags available</p>
                        )}

                        {selectedSpan.logs && selectedSpan.logs.length > 0 && (
                          <>
                            <h4 className="text-sm font-medium text-primary mb-2 mt-4">Logs</h4>
                            <div className="bg-black/30 rounded p-2 sm:p-3 max-h-48 overflow-y-auto">
                              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-all">
                                {JSON.stringify(selectedSpan.logs, null, 2)}
                              </pre>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {isAdmin() && (
                <div className="flex gap-2 sm:gap-3">
                  <button
                    onClick={() => {
                      const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                        datasource: 'jaeger',
                        queries: [{ refId: 'A', query: selectedTrace.traceID }],
                        range: { from: 'now-1h', to: 'now' }
                      }))}`
                      openGrafanaExplore(exploreUrl)
                    }}
                    className="btn flex-1 flex items-center justify-center gap-2 min-h-[44px] text-sm"
                  >
                    <ExternalLink size={16} />
                    View in Grafana
                  </button>
                </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
