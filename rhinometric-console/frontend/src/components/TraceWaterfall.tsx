import { ChevronRight, Star, XCircle } from 'lucide-react'
import type { SpanNode, JaegerSpan, JaegerTrace } from '../utils/traceAnalysis'
import { formatDuration } from '../utils/traceAnalysis'

interface Props {
  flatTree: SpanNode[]
  trace: JaegerTrace
  selectedSpanID: string | null
  onSelectSpan: (span: JaegerSpan) => void
}

export function TraceWaterfall({ flatTree, trace, selectedSpanID, onSelectSpan }: Props) {
  if (flatTree.length === 0) return null

  const allSpans = trace.spans
  const minStart = Math.min(...allSpans.map(s => s.startTime))
  const maxEnd = Math.max(...allSpans.map(s => s.startTime + s.duration))
  const totalDuration = maxEnd - minStart

  // Time ruler ticks
  const tickCount = 5
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => ({
    pct: (i / tickCount) * 100,
    label: formatDuration((i / tickCount) * totalDuration),
  }))

  return (
    <div className="card p-3 sm:p-4">
      <h3 className="text-base sm:text-lg font-semibold text-white mb-3 flex items-center gap-2">
        Span Waterfall
        <span className="text-xs font-normal text-gray-400">({flatTree.length} spans)</span>
      </h3>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mb-3 text-xs text-gray-400">
        <span className="flex items-center gap-1"><Star size={12} className="text-yellow-400" /> Bottleneck</span>
        <span className="flex items-center gap-1"><XCircle size={12} className="text-red-400" /> Error</span>
        <span className="flex items-center gap-1"><span className="w-3 h-1.5 rounded bg-yellow-500/40 inline-block" /> Critical path</span>
      </div>

      {/* Time ruler */}
      <div className="relative h-5 ml-[200px] sm:ml-[260px] mb-1 border-b border-gray-700/50">
        {ticks.map((tick, i) => (
          <div
            key={i}
            className="absolute top-0 text-[10px] text-gray-500 -translate-x-1/2"
            style={{ left: `${tick.pct}%` }}
          >
            {tick.label}
            <div className="w-px h-1.5 bg-gray-600 mx-auto mt-0.5" />
          </div>
        ))}
      </div>

      {/* Span rows */}
      <div className="space-y-0.5">
        {flatTree.map((node) => {
          const { span } = node
          const startOffset = totalDuration > 0 ? ((span.startTime - minStart) / totalDuration) * 100 : 0
          const width = totalDuration > 0 ? (span.duration / totalDuration) * 100 : 0
          const isSelected = selectedSpanID === span.spanID

          return (
            <div
              key={span.spanID}
              className={`flex items-stretch cursor-pointer rounded transition-colors group ${
                isSelected ? 'bg-white/10 ring-1 ring-primary' :
                node.isCriticalPath ? 'bg-yellow-500/5 hover:bg-yellow-500/10' :
                'hover:bg-white/5'
              }`}
              onClick={() => onSelectSpan(span)}
            >
              {/* Left: operation info */}
              <div
                className="flex items-center gap-1 py-1.5 px-2 flex-shrink-0 min-w-0"
                style={{ width: '200px', paddingLeft: `${8 + node.depth * 16}px` }}
              >
                {node.children.length > 0 && (
                  <ChevronRight size={12} className="text-gray-500 flex-shrink-0" />
                )}
                {node.isBottleneck && <Star size={12} className="text-yellow-400 flex-shrink-0" />}
                {node.isError && <XCircle size={12} className="text-red-400 flex-shrink-0" />}
                <span className={`text-xs truncate ${node.isError ? 'text-red-300' : 'text-gray-200'}`}>
                  {span.operationName}
                </span>
              </div>

              {/* Center: service tag */}
              <div className="hidden sm:flex items-center w-[60px] flex-shrink-0 px-1">
                <span className="text-[10px] text-gray-500 truncate">{node.serviceName}</span>
              </div>

              {/* Right: waterfall bar */}
              <div className="flex-1 flex items-center py-1.5 pr-2 min-w-0">
                <div className="flex-1 h-5 bg-surface-light/50 rounded relative overflow-hidden">
                  <div
                    className={`absolute h-full rounded transition-all ${
                      node.isError ? 'bg-red-500/80' :
                      node.isBottleneck ? 'bg-yellow-500/80' :
                      node.isCriticalPath ? 'bg-yellow-500/40' :
                      span.duration > 1000000 ? 'bg-red-500/60' :
                      span.duration > 500000 ? 'bg-yellow-500/60' :
                      span.duration > 100000 ? 'bg-blue-500/60' :
                      'bg-green-500/60'
                    }`}
                    style={{
                      left: `${startOffset}%`,
                      width: `${Math.max(width, 0.3)}%`,
                      minWidth: '2px',
                    }}
                  />
                </div>
                <span className="text-xs text-gray-400 ml-2 flex-shrink-0 w-16 text-right">
                  {formatDuration(span.duration)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
