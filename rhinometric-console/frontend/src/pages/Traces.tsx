import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Network, Clock, Search, Filter, Download, ExternalLink, AlertCircle } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

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
  const [searchQuery, setSearchQuery] = useState('')
  const [serviceFilter, setServiceFilter] = useState<string>('all')
  const [minDuration, setMinDuration] = useState<string>('')
  const [timeRange, setTimeRange] = useState<string>('15m')  // Changed from 1h to 15min for performance
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null)
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null)

  // Fetch available services from Jaeger
  const { data: servicesData } = useQuery({
    queryKey: ['jaeger-services'],
    queryFn: async () => {
      const response = await fetch('/api/traces/services')
      if (!response.ok) return { services: [] }
      const data = await response.json()
      return data
    },
    staleTime: 30000, // Cache for 30 seconds
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

      const response = await fetch(`/api/traces?${params}`)
      
      if (!response.ok) throw new Error('Failed to fetch traces')
      const data = await response.json()
      return data
    },
    enabled: true, // Temporarily changed from !!token
    staleTime: 0,
  })

  const traces: Trace[] = tracesData?.traces || []
  const services = ['all', ...(servicesData?.services || [])]

  const formatDuration = (microseconds: number): string => {
    if (microseconds < 1000) return `${microseconds.toFixed(0)}µs`
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Distributed Traces</h1>
          <p className="text-text-muted">Analyze request flows and performance with Jaeger</p>
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
          className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download size={16} />
          Export
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card space-y-4">
        {/* Search Bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search by Trace ID or Operation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-light border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button 
            onClick={() => refetch()}
            className="btn flex items-center gap-2"
          >
            <Search size={16} />
            Search
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm text-gray-400">Service:</span>
            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              {services.map(svc => (
                <option key={svc} value={svc}>{svc === 'all' ? 'All Services' : svc}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400" />
            <span className="text-sm text-gray-400">Min Duration:</span>
            <input
              type="number"
              placeholder="ms"
              value={minDuration}
              onChange={(e) => setMinDuration(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm w-24"
            />
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400" />
            <span className="text-sm text-gray-400">Time Range:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              <option value="15m">Last 15 minutes</option>
              <option value="30m">Last 30 minutes</option>
              <option value="1h">Last 1 hour</option>
              <option value="3h">Last 3 hours</option>
            </select>
          </div>

          <div className="ml-auto text-sm text-gray-400">
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
          <div className="text-center py-12">
            <Network className="text-error mx-auto mb-4" size={48} />
            <p className="text-error">Failed to load traces</p>
            <p className="text-sm text-gray-400 mt-2">{(error as Error).message}</p>
            <button onClick={() => refetch()} className="btn btn-secondary mt-4">
              Retry
            </button>
          </div>
        ) : traces.length === 0 ? (
          <div className="text-center py-12">
            <Network className="text-gray-400 mx-auto mb-4" size={48} />
            <p className="text-white text-lg font-semibold">No Traces Found</p>
            <p className="text-gray-400 mt-2">No distributed traces available in the selected time range</p>
            <div className="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-lg max-w-2xl mx-auto text-left">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-primary mt-1 flex-shrink-0" size={20} />
                <div className="text-sm text-gray-300">
                  <p className="font-semibold text-primary mb-2">About Distributed Tracing</p>
                  <p className="mb-2">Jaeger collects traces from instrumented applications. If no traces appear:</p>
                  <ul className="list-disc list-inside space-y-1 text-gray-400">
                    <li>Ensure services are instrumented with OpenTelemetry</li>
                    <li>Verify Jaeger is receiving spans on port 14317 (gRPC) or 14318 (HTTP)</li>
                    <li>Check that services have OTLP exporters configured</li>
                    <li>Try increasing the time range if traces are sparse</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
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
                    className="p-4 bg-surface-light hover:bg-surface-light/80 border border-gray-700 hover:border-primary/50 rounded-lg cursor-pointer transition-all"
                    onClick={() => setSelectedTrace(trace)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${getSpanColor(totalDuration)}`}></div>
                        <span className="text-white font-mono text-sm">{trace.traceID.slice(0, 16)}...</span>
                        <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                          {spanCount} span{spanCount > 1 ? 's' : ''}
                        </span>
                      </div>
                      <span className="text-gray-400 text-sm">
                        {formatDuration(totalDuration)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-300 mb-2">
                      {rootSpan?.operationName || 'Unknown Operation'}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>{rootSpan?.serviceName || 'unknown'}</span>
                      <span>•</span>
                      <span>{new Date(rootSpan?.startTime / 1000).toLocaleString()}</span>
                    </div>
                  </div>
                )
              })}
          </div>
        )}
      </div>

      {/* Trace Detail Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-gray-700 rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-surface z-10">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Trace Details</h2>
                <p className="text-sm text-gray-400 font-mono">{selectedTrace.traceID}</p>
              </div>
              <button 
                onClick={() => setSelectedTrace(null)}
                className="text-gray-400 hover:text-white p-2 hover:bg-error/20 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-6">
                {/* Trace Summary */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="card">
                    <p className="text-sm text-gray-400 mb-1">Total Duration</p>
                    <p className="text-2xl font-bold text-white">
                      {formatDuration(Math.max(...selectedTrace.spans.map(s => s.startTime + s.duration)) - Math.min(...selectedTrace.spans.map(s => s.startTime)))}
                    </p>
                  </div>
                  <div className="card">
                    <p className="text-sm text-gray-400 mb-1">Total Spans</p>
                    <p className="text-2xl font-bold text-white">{selectedTrace.spans.length}</p>
                  </div>
                  <div className="card">
                    <p className="text-sm text-gray-400 mb-1">Services</p>
                    <p className="text-2xl font-bold text-white">
                      {new Set(selectedTrace.spans.map(s => s.serviceName)).size}
                    </p>
                  </div>
                </div>

                {/* Waterfall Chart */}
                <div className="card">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Network size={20} />
                    Span Waterfall
                  </h3>
                  <div className="space-y-2">
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
                              className={`text-sm p-2 rounded hover:bg-white/5 cursor-pointer transition-colors ${selectedSpan?.spanID === span.spanID ? 'bg-white/10 ring-1 ring-primary' : ''}`}
                              onClick={() => setSelectedSpan(span)}
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-gray-400 font-mono text-xs w-8">{index + 1}</span>
                                <span className="text-white flex-1 truncate font-medium">{span.operationName}</span>
                                <span className="text-gray-400 text-xs">{formatDuration(span.duration)}</span>
                              </div>
                              <div className="h-6 bg-surface-light rounded relative ml-10 overflow-hidden">
                                <div 
                                  className={`absolute h-full rounded ${getSpanColor(span.duration)}`}
                                  style={{ 
                                    left: `${startOffset}%`, 
                                    width: `${Math.max(width, 0.5)}%`, // Ensure at least a tiny visible bar
                                    minWidth: '2px'
                                  }}
                                ></div>
                              </div>
                              <div className="text-xs text-gray-500 ml-10 mt-1 flex justify-between">
                                <span>{span.serviceName}</span>
                                <span>{span.spanID.slice(0,8)}</span>
                              </div>
                            </div>
                          )
                        })
                    })()}
                  </div>
                </div>

                {/* Span Details Panel */}
                {selectedSpan && (
                  <div className="card bg-surface-light border-primary/20">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Span Details</h3>
                      <button onClick={() => setSelectedSpan(null)} className="text-gray-400 hover:text-white">
                        Close
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-primary mb-2">Metadata</h4>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Operation:</dt>
                            <dd className="text-white font-mono">{selectedSpan.operationName}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Service:</dt>
                            <dd className="text-white">{selectedSpan.serviceName}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Duration:</dt>
                            <dd className="text-white">{formatDuration(selectedSpan.duration)}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Start Time:</dt>
                            <dd className="text-white">{new Date(selectedSpan.startTime / 1000).toLocaleString()}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Span ID:</dt>
                            <dd className="text-white font-mono">{selectedSpan.spanID}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className="text-gray-400">Trace ID:</dt>
                            <dd className="text-white font-mono">{selectedSpan.traceID}</dd>
                          </div>
                        </dl>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-primary mb-2">Tags & Attributes</h4>
                        {selectedSpan.tags && Object.keys(selectedSpan.tags).length > 0 ? (
                          <div className="bg-black/30 rounded p-3 max-h-48 overflow-y-auto">
                            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                              {JSON.stringify(selectedSpan.tags, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm italic">No tags available</p>
                        )}
                        
                        {selectedSpan.logs && selectedSpan.logs.length > 0 && (
                          <>
                            <h4 className="text-sm font-medium text-primary mb-2 mt-4">Logs</h4>
                            <div className="bg-black/30 rounded p-3 max-h-48 overflow-y-auto">
                              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                                {JSON.stringify(selectedSpan.logs, null, 2)}
                              </pre>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      const jaegerUrl = `http://localhost:3000/explore?orgId=1&left=${encodeURIComponent(JSON.stringify({
                        datasource: 'jaeger',
                        queries: [{ refId: 'A', query: selectedTrace.traceID }],
                        range: { from: 'now-1h', to: 'now' }
                      }))}`
                      window.open(jaegerUrl, '_blank')
                    }}
                    className="btn flex-1 flex items-center justify-center gap-2"
                  >
                    <ExternalLink size={16} />
                    View in Grafana
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
