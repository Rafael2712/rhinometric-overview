import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { ArrowLeft, ExternalLink, Network, Loader2 } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'
import { analyzeTrace } from '../utils/traceAnalysis'
import type { JaegerTrace, JaegerSpan } from '../utils/traceAnalysis'
import { TraceInsights } from '../components/TraceInsights'
import { TraceWaterfall } from '../components/TraceWaterfall'
import { SpanDetailPanel } from '../components/SpanDetailPanel'

export function TraceDetailPage() {
  const { traceId } = useParams<{ traceId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const [selectedSpan, setSelectedSpan] = useState<JaegerSpan | null>(null)

  // Try to get trace data from router state (passed from list page)
  const stateTrace = (location.state as any)?.trace as JaegerTrace | undefined

  const { data, isLoading, error } = useQuery({
    queryKey: ['trace-detail', traceId],
    queryFn: async () => {
      if (!token || !traceId) throw new Error('Missing token or trace ID')
      // Try multiple lookback windows to find the trace
      for (const lookback of ['3h', '12h', '24h']) {
        const response = await fetch(`/api/traces?limit=200&lookback=${lookback}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!response.ok) continue
        const result = await response.json()
        const traces: JaegerTrace[] = result.traces || []
        const found = traces.find(t => t.traceID === traceId)
        if (found) return found
      }
      throw new Error(`Trace ${traceId} not found (checked 3h, 12h, 24h lookbacks)`)
    },
    enabled: !!token && !!traceId && !stateTrace,
    staleTime: 120000,
    retry: 1,
  })

  const traceData = stateTrace || data

  if (!stateTrace && isLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="animate-spin text-primary" size={32} />
        <span className="text-gray-400 ml-3">Loading trace...</span>
      </div>
    )
  }

  if (error && !traceData) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/traces')} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
          <ArrowLeft size={18} /> Back to Traces
        </button>
        <div className="card p-8 text-center">
          <Network className="text-error mx-auto mb-4" size={48} />
          <p className="text-error text-lg">Trace not found</p>
          <p className="text-gray-400 mt-2 text-sm">{(error as Error)?.message || 'Could not load trace data'}</p>
          <p className="text-gray-500 mt-1 text-xs">The trace may have expired or is outside the 24h retention window.</p>
        </div>
      </div>
    )
  }

  if (!traceData) return null

  const analysis = analyzeTrace(traceData)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="min-w-0">
          <button
            onClick={() => navigate('/traces')}
            className="flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors text-sm mb-2"
          >
            <ArrowLeft size={16} /> Back to Traces
          </button>
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-1">Trace Detail</h1>
          <p className="text-xs sm:text-sm text-gray-400 font-mono truncate">{traceId}</p>
          {analysis.rootSpan && (
            <p className="text-sm text-gray-300 mt-1">{analysis.rootSpan.operationName}</p>
          )}
        </div>
        {isAdmin() && (
          <button
            onClick={() => {
              const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                datasource: 'jaeger',
                queries: [{ refId: 'A', query: traceId }],
                range: { from: 'now-1h', to: 'now' }
              }))}`
              openGrafanaExplore(exploreUrl)
            }}
            className="btn btn-secondary flex items-center gap-2 text-sm self-start"
          >
            <ExternalLink size={16} /> View in Grafana
          </button>
        )}
      </div>

      {/* Insights */}
      <TraceInsights analysis={analysis} />

      {/* Waterfall */}
      <TraceWaterfall
        flatTree={analysis.flatTree}
        trace={traceData}
        selectedSpanID={selectedSpan?.spanID || null}
        onSelectSpan={setSelectedSpan}
      />

      {/* Selected span detail */}
      {selectedSpan && (
        <SpanDetailPanel
          span={selectedSpan}
          processes={traceData.processes}
          onClose={() => setSelectedSpan(null)}
        />
      )}
    </div>
  )
}
