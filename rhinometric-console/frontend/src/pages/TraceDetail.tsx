import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState, useMemo } from 'react'
import { ArrowLeft, Network, Loader2 } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { analyzeTrace, getTagValue } from '../utils/traceAnalysis'
import type { JaegerTrace, JaegerSpan } from '../utils/traceAnalysis'
import { TraceInsights } from '../components/TraceInsights'
import { TraceWaterfall } from '../components/TraceWaterfall'
import { SpanDetailPanel } from '../components/SpanDetailPanel'
import { RelatedLogs } from '../components/RelatedLogs'
import { MetricsContext } from '../components/MetricsContext'
import { TraceActionLinks } from '../components/TraceActionLinks'

/** Extract service_key from trace span tags or process tags */
function extractServiceKey(trace: JaegerTrace): string | null {
  // 1. Check root span tags for rhinometric.service_key or service_key
  for (const span of trace.spans) {
    const sk = getTagValue(span.tags, 'rhinometric.service_key')
      || getTagValue(span.tags, 'service_key')
    if (sk && typeof sk === 'string') return sk
  }
  // 2. Fall back to process tags
  for (const pid of Object.keys(trace.processes)) {
    const proc = trace.processes[pid]
    const sk = getTagValue(proc.tags, 'rhinometric.service_key')
      || getTagValue(proc.tags, 'service_key')
    if (sk && typeof sk === 'string') return sk
  }
  return null
}

/** Derive a human-friendly service_name from service_key by stripping env suffix */
function deriveServiceName(serviceKey: string): string {
  // "rhinometric-web-produccion" -> "rhinometric-web"
  const envSuffixes = ['-produccion', '-production', '-staging', '-dev', '-test', '-qa']
  let name = serviceKey
  for (const suffix of envSuffixes) {
    if (name.endsWith(suffix)) {
      name = name.slice(0, -suffix.length)
      break
    }
  }
  return name
}

export function TraceDetailPage() {
  const { traceId } = useParams<{ traceId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((state) => state.token)
  const [selectedSpan, setSelectedSpan] = useState<JaegerSpan | null>(null)

  const stateTrace = (location.state as any)?.trace as JaegerTrace | undefined

  const { data, isLoading, error } = useQuery({
    queryKey: ['trace-detail', traceId],
    queryFn: async () => {
      if (!token || !traceId) throw new Error('Missing token or trace ID')
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

  // Compute correlation context
  const correlationCtx = useMemo(() => {
    if (!traceData) return null
    const serviceKey = extractServiceKey(traceData)
    const serviceName = serviceKey ? deriveServiceName(serviceKey) : null
    return {
      serviceKey,
      serviceName,
      logsAvailable: !!serviceKey,
      metricsAvailable: !!serviceName,
    }
  }, [traceData])

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
  const sKey = correlationCtx?.serviceKey
  const sName = correlationCtx?.serviceName

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
      </div>

      {/* Action Links */}
      {sKey && sName && traceId && (
        <TraceActionLinks
          serviceKey={sKey}
          serviceName={sName}
          traceId={traceId}
          traceStartUs={analysis.rootSpan?.startTime || traceData.spans[0]?.startTime || 0}
          traceDurationUs={analysis.totalDuration}
        />
      )}

      {/* Insights with correlation context */}
      <TraceInsights
        analysis={analysis}
        correlationContext={correlationCtx || undefined}
      />

      {/* Metrics Context */}
      {sKey && sName && (
        <MetricsContext
          serviceName={sName}
          serviceKey={sKey}
          traceStartUs={analysis.rootSpan?.startTime || traceData.spans[0]?.startTime || 0}
          traceDurationUs={analysis.totalDuration}
        />
      )}

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

      {/* Related Logs */}
      {sKey && (
        <RelatedLogs
          serviceKey={sKey}
          traceStartUs={analysis.rootSpan?.startTime || traceData.spans[0]?.startTime || 0}
          traceDurationUs={analysis.totalDuration}
        />
      )}
    </div>
  )
}
