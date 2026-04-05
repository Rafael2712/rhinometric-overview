import { X, Tag, Clock, Server, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { JaegerSpan, JaegerProcess } from '../utils/traceAnalysis'
import { formatDuration, getServiceName, isErrorSpan, getTagValue } from '../utils/traceAnalysis'

interface Props {
  span: JaegerSpan
  processes: Record<string, JaegerProcess>
  onClose: () => void
}

export function SpanDetailPanel({ span, processes, onClose }: Props) {
  const [showRawJSON, setShowRawJSON] = useState(false)
  const serviceName = getServiceName(span, processes)
  const hasError = isErrorSpan(span)

  // Separate system tags from user attributes
  const systemKeys = new Set([
    'otel.scope.name', 'otel.scope.version', 'otel.status_code',
    'span.kind', 'internal.span.format',
  ])
  const systemTags = span.tags.filter(t => systemKeys.has(t.key))
  const userTags = span.tags.filter(t => !systemKeys.has(t.key))

  return (
    <div className="card bg-surface-light border-primary/20 p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            Span Details
            {hasError && <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400">ERROR</span>}
          </h3>
          <p className="text-xs text-gray-400 font-mono truncate mt-0.5">{span.spanID}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white p-1 hover:bg-gray-700 rounded transition-colors">
          <X size={18} />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Metadata */}
        <div>
          <h4 className="text-sm font-semibold text-primary mb-3 flex items-center gap-1.5">
            <Server size={14} /> Metadata
          </h4>
          <dl className="space-y-2.5 text-sm">
            <MetaRow label="Operation" value={span.operationName} mono />
            <MetaRow label="Service" value={serviceName} />
            <MetaRow label="Duration" value={formatDuration(span.duration)} />
            <MetaRow label="Start Time" value={new Date(span.startTime / 1000).toLocaleString()} />
            <MetaRow label="Status" value={String(getTagValue(span.tags, 'otel.status_code') || 'UNSET')}
              className={hasError ? 'text-red-400 font-medium' : ''} />
            <MetaRow label="Span Kind" value={String(getTagValue(span.tags, 'span.kind') || 'â€”')} />
            <MetaRow label="Span ID" value={span.spanID} mono />
            <MetaRow label="Trace ID" value={span.traceID} mono />
            {span.references.length > 0 && (
              <MetaRow label="Parent" value={span.references[0].spanID} mono />
            )}
          </dl>
        </div>

        {/* Tags / Attributes */}
        <div>
          <h4 className="text-sm font-semibold text-primary mb-3 flex items-center gap-1.5">
            <Tag size={14} /> Attributes
          </h4>
          {userTags.length > 0 ? (
            <div className="overflow-y-auto max-h-60">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left text-gray-400 pb-1.5 pr-2 font-medium">Key</th>
                    <th className="text-left text-gray-400 pb-1.5 font-medium">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {userTags.map((tag, i) => (
                    <tr key={i} className="border-b border-gray-700/30">
                      <td className="py-1.5 pr-2 text-gray-300 font-mono whitespace-nowrap">{tag.key}</td>
                      <td className="py-1.5 text-white font-mono break-all">{String(tag.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-sm italic">No custom attributes</p>
          )}

          {/* System tags (collapsed) */}
          {systemTags.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-700/30">
              <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1.5">Instrumentation</p>
              <div className="space-y-1">
                {systemTags.map((tag, i) => (
                  <div key={i} className="flex gap-2 text-[11px]">
                    <span className="text-gray-500">{tag.key}:</span>
                    <span className="text-gray-400">{String(tag.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Span Logs */}
          {span.logs && span.logs.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-700/30">
              <h4 className="text-sm font-semibold text-primary mb-2 flex items-center gap-1.5">
                <Clock size={14} /> Span Events ({span.logs.length})
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {span.logs.map((log, i) => (
                  <div key={i} className="bg-black/20 rounded p-2 text-xs">
                    <div className="text-gray-500 mb-1">{new Date(log.timestamp / 1000).toLocaleTimeString()}</div>
                    {log.fields.map((f: any, j: number) => (
                      <div key={j} className="text-gray-300">
                        <span className="text-gray-500">{f.key}: </span>{String(f.value)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Raw JSON toggle */}
      <div className="mt-4 pt-3 border-t border-gray-700/30">
        <button
          onClick={() => setShowRawJSON(!showRawJSON)}
          className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1 transition-colors"
        >
          {showRawJSON ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {showRawJSON ? 'Hide' : 'Show'} Raw JSON
        </button>
        {showRawJSON && (
          <div className="mt-2 bg-black/30 rounded p-3 max-h-48 overflow-y-auto">
            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-all">
              {JSON.stringify(span, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}

function MetaRow({ label, value, mono, className }: { label: string; value: string; mono?: boolean; className?: string }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-gray-400 flex-shrink-0">{label}:</dt>
      <dd className={`text-right truncate ${mono ? 'font-mono' : ''} ${className || 'text-white'}`}>{value}</dd>
    </div>
  )
}
