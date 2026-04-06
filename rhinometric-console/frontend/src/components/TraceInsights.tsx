import { AlertTriangle, Zap, Info, XCircle, Link2, Tag, AlertCircle } from 'lucide-react'
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

const CLASSIFICATION_STYLE: Record<string, { bg: string; text: string }> = {
  collector: { bg: 'bg-gray-500/20', text: 'text-gray-300' },
  platform: { bg: 'bg-purple-500/20', text: 'text-purple-300' },
  customer: { bg: 'bg-emerald-500/20', text: 'text-emerald-300' },
}

export function TraceInsights({ analysis, correlationContext }: Props) {
  const hasErrors = analysis.errorCount > 0
  const isSlow = analysis.bottleneckPct >= 50
  const ctx = correlationContext
  const cls = analysis.classification

  // Consistency check: detect naming mismatch between trace service and correlation keys
  const hasMismatch = ctx?.serviceKey && ctx?.serviceName &&
    ctx.serviceKey !== ctx.serviceName &&
    !ctx.serviceKey.startsWith(ctx.serviceName)

  return (
    <div className="space-y-4">
      {/* Classification note for non-customer traces */}
      {cls && cls.type !== 'customer' && (
        <div className="flex items-start gap-2.5 p-3 rounded-lg bg-surface-light/50 border border-gray-700/50">
          <Tag size={16} className="text-gray-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded ${CLASSIFICATION_STYLE[cls.type]?.bg || ''} ${CLASSIFICATION_STYLE[cls.type]?.text || ''}`}>
              {cls.label}
            </span>
            <p className="text-xs text-gray-400 mt-1">{cls.description}</p>
          </div>
        </div>
      )}

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
                {ctx.logsAvailable && <span className="text-xs bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">logs {'\u2713'}</span>}
                {ctx.metricsAvailable && <span className="text-xs bg-green-500/20 text-green-300 px-1.5 py-0.5 rounded">metrics {'\u2713'}</span>}
              </p>
            )}
            {/* No serviceKey — logs unavailable */}
            {ctx && !ctx.serviceKey && (
              <p className="text-sm text-gray-400 flex items-center gap-1.5 mt-1">
                <Link2 size={14} className="text-gray-500" />
                Logs unavailable for this trace
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Consistency mismatch warning */}
      {hasMismatch && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
          <AlertCircle size={16} className="text-yellow-400 flex-shrink-0" />
          <p className="text-xs text-yellow-300">Correlation limited due to naming mismatch</p>
        </div>
      )}

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
          {analysis.serviceBreakdown.length === 1 ? (
            <SingleServiceSummary svc={analysis.serviceBreakdown[0]} />
          ) : (
            <div className="space-y-2">
              {analysis.serviceBreakdown.map((svc) => (
                <ServiceBar key={svc.serviceName} svc={svc} maxDuration={analysis.serviceBreakdown[0].totalDuration} />
              ))}
            </div>
          )}
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

function SingleServiceSummary({ svc }: { svc: ServiceBreakdown }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-300 flex items-center gap-1.5">
        {svc.serviceName}
        {svc.hasErrors && <XCircle size={12} className="text-red-400" />}
      </span>
      <span className="text-gray-400">
        {svc.spanCount} span{svc.spanCount > 1 ? 's' : ''} &middot; {formatDuration(svc.totalDuration)}
      </span>
    </div>
  )
}

function ServiceBar({ svc, maxDuration }: { svc: ServiceBreakdown; maxDuration: number }) {
  const barPct = maxDuration > 0 ? (svc.totalDuration / maxDuration) * 100 : 0
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-gray-300 truncate mr-2 flex items-center gap-1.5">
          {svc.serviceName}
          {svc.hasErrors && <XCircle size={12} className="text-red-400" />}
        </span>
        <span className="text-gray-400 flex-shrink-0">
          {svc.spanCount} span{svc.spanCount > 1 ? 's' : ''} &middot; {formatDuration(svc.totalDuration)}
        </span>
      </div>
      <div className="h-2 bg-surface-light rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${svc.hasErrors ? 'bg-red-500' : 'bg-primary'}`}
          style={{ width: `${Math.max(barPct, 2)}%` }}
        />
      </div>
    </div>
  )
}
