import { AlertTriangle, Zap, Info, XCircle, Link2 } from 'lucide-react'
import type { TraceAnalysis, ServiceBreakdown } from '../utils/traceAnalysis'
import { formatDuration } from '../utils/traceAnalysis'

interface Props {
  analysis: TraceAnalysis
  correlationContext?: {
    serviceKey: string | null
    serviceName: string | null
    logsAvailable: boolean
    metricsAvailable: boolean
  }
}

export function TraceInsights({ analysis, correlationContext }: Props) {
  const hasErrors = analysis.errorCount > 0
  const isSlow = analysis.bottleneckPct >= 50
  const ctx = correlationContext

  return (
    <div className="space-y-4">
      {/* Insight Banner */}
      <div className={`rounded-lg border p-4 ${
        hasErrors ? 'bg-red-500/10 border-red-500/30' :
        isSlow ? 'bg-yellow-500/10 border-yellow-500/30' :
        'bg-blue-500/10 border-blue-500/30'
      }`}>
        <div className="flex items-start gap-3">
          {hasErrors ? (
            <XCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
          ) : isSlow ? (
            <AlertTriangle size={20} className="text-yellow-400 flex-shrink-0 mt-0.5" />
          ) : (
            <Info size={20} className="text-blue-400 flex-shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            {analysis.insights.map((insight, i) => (
              <p key={i} className={`text-sm ${
                hasErrors ? 'text-red-200' : isSlow ? 'text-yellow-200' : 'text-blue-200'
              }`}>
                {insight}
              </p>
            ))}
            {/* Correlation context line */}
            {ctx && ctx.serviceKey && (
              <p className="text-sm text-gray-300 flex items-center gap-1.5 mt-1">
                <Link2 size={14} className="text-gray-400" />
                Service: <span className="font-mono text-primary">{ctx.serviceKey}</span>
                {ctx.logsAvailable && <span className="text-xs bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">logs ✓</span>}
                {ctx.metricsAvailable && <span className="text-xs bg-green-500/20 text-green-300 px-1.5 py-0.5 rounded">metrics ✓</span>}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard label="Duration" value={formatDuration(analysis.totalDuration)} />
        <SummaryCard label="Spans" value={String(analysis.spanCount)} />
        <SummaryCard label="Services" value={String(analysis.serviceCount)} />
        <SummaryCard
          label="Errors"
          value={String(analysis.errorCount)}
          variant={analysis.errorCount > 0 ? 'error' : 'default'}
        />
      </div>

      {/* Service Breakdown */}
      {analysis.serviceBreakdown.length > 0 && (
        <div className="card p-4">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Zap size={16} className="text-primary" />
            Service Breakdown
          </h4>
          <div className="space-y-2">
            {analysis.serviceBreakdown.map((svc) => (
              <ServiceBar key={svc.serviceName} svc={svc} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, variant = 'default' }: { label: string; value: string; variant?: 'default' | 'error' }) {
  return (
    <div className="card p-3">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-xl font-bold ${variant === 'error' ? 'text-red-400' : 'text-white'}`}>
        {value}
      </p>
    </div>
  )
}

function ServiceBar({ svc }: { svc: ServiceBreakdown }) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-gray-300 truncate mr-2 flex items-center gap-1.5">
          {svc.serviceName}
          {svc.hasErrors && <XCircle size={12} className="text-red-400" />}
        </span>
        <span className="text-gray-400 flex-shrink-0">
          {svc.spanCount} span{svc.spanCount > 1 ? 's' : ''} · {formatDuration(svc.totalDuration)} · {svc.pctOfTrace.toFixed(0)}%
        </span>
      </div>
      <div className="h-2 bg-surface-light rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${svc.hasErrors ? 'bg-red-500' : 'bg-primary'}`}
          style={{ width: `${Math.max(svc.pctOfTrace, 1)}%` }}
        />
      </div>
    </div>
  )
}
