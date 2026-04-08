import { useState, useMemo, useCallback, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  AlertTriangle, Activity, Brain, ArrowUpDown, Eye,
  BarChart3, Zap, TrendingUp, ChevronDown, ChevronUp,
  History, Radio, Sparkles, Loader2
} from 'lucide-react'

// ─── Types ───

interface CategoryScores {
  latency: number
  availability: number
  error: number
  trace: number
  ssl: number
}

interface AnomalyV2 {
  id: string
  service_id: number
  service_name: string
  service_type: string | null
  group_name: string | null
  environment: string | null
  anomaly_score: number
  severity: string
  confidence: number
  confidence_label: string
  category_scores: CategoryScores
  reason_codes: Array<{ code: string; detail: Record<string, number> }>
  evidence_summary: string
  status: string
  fingerprint: string
  first_seen_at: string
  last_seen_at: string
  occurrence_count: number
  baseline_deviation_pct: number | null
  triggered_categories_count: number | null
  is_anomalous: boolean | null
  evaluation_duration_ms: number | null
  latency_trend_slope: number | null
  latency_trend_r2: number | null
  log_error_burst_ratio: number | null
  trace_p95_latency_ms: number | null
  trace_error_rate: number | null
  trace_bottleneck_score: number | null
  trace_slow_operations: number | null
  predicted_risk_score: number | null
  predicted_risk_level: string | null
  predicted_horizon_minutes: number | null
  prediction_confidence: string | null
  prediction_reason_codes: Array<{ code: string; detail: Record<string, number> }> | null
  prediction_summary: string | null
}

interface LlmExplanation {
  summary: string
  current_state: string
  prediction_outlook: string
  key_signals: string[]
  risk_interpretation: string
  confidence_note: string
}

interface ExplanationApiResponse {
  anomaly_id: string
  service_name: string
  explanation: LlmExplanation
  model: string
  cached: boolean
}

interface AnomalySummary {
  total_active: number
  severity_counts: Record<string, number>
  max_score: number
}

interface AnomalyListResponse {
  anomalies: AnomalyV2[]
  count: number
  summary: AnomalySummary
}

interface ValidationSummary {
  total_evaluated: number
  total_active: number
  total_anomalous: number
  avg_score: number
  max_score: number
  avg_confidence: number
  avg_baseline_deviation_pct: number
  avg_triggered_categories: number
  avg_evaluation_duration_ms: number
  avg_latency_trend_slope: number
  avg_log_error_burst_ratio: number
  pct_positive_trend: number
  pct_burst_detected: number
  avg_trace_bottleneck_score: number
  avg_trace_error_rate: number
  avg_trace_p95_latency: number
  total_slow_operations: number
  avg_predicted_risk_score: number
  predicted_high_count: number
  predicted_critical_count: number
  predicted_with_horizon_count: number
  severity_distribution: Array<{ severity: string; count: number }>
  score_histogram: Array<{ range: string; count: number }>
}

interface ServiceComparison {
  service_name: string
  rust_score: number
  rust_severity: string
  rust_confidence: number
  python_anomaly_score: number
  python_severity: string
  python_confidence: number
  python_deviation_percent: number
  agreement: string
}

interface CompareResponse {
  rust_v2_count: number
  python_v1_count: number
  matched_services: ServiceComparison[]
  rust_only: string[]
  python_only: string[]
}

// ─── Constants ───

const V2_BASE = '/api/v2/anomalies'
const PAGE_LIMIT = 50

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string; ring: string }> = {
  normal:    { bg: 'bg-green-500/10',  text: 'text-green-400',  border: 'border-green-500/20', ring: 'ring-green-500/30' },
  watch:     { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20', ring: 'ring-yellow-500/30' },
  degraded:  { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', ring: 'ring-orange-500/30' },
  critical:  { bg: 'bg-red-500/10',    text: 'text-red-400',    border: 'border-red-500/20', ring: 'ring-red-500/30' },
  emergency: { bg: 'bg-red-700/20',    text: 'text-red-300',    border: 'border-red-700/30', ring: 'ring-red-700/40' },
}

const SEVERITY_ORDER: Record<string, number> = {
  emergency: 5, critical: 4, degraded: 3, watch: 2, normal: 1,
}

// ─── Fetch hook ───

function useV2Fetch<T>(key: string, endpoint: string, enabled = true) {
  const { token } = useAuthStore()
  return useQuery<T>({
    queryKey: [key],
    queryFn: async () => {
      const res = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    refetchInterval: 30_000,
    staleTime: 15_000,
    retry: 2,
    enabled,
  })
}

// ─── Utility: how fresh is last_seen ───

function freshness(lastSeen: string): 'live' | 'recent' | 'stale' {
  const age = Date.now() - new Date(lastSeen).getTime()
  if (age < 3 * 60_000) return 'live'   // < 3 min
  if (age < 15 * 60_000) return 'recent' // < 15 min
  return 'stale'
}

function timeAgo(iso: string): string {
  const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (sec < 60) return `${sec}s ago`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
  return `${Math.floor(sec / 86400)}d ago`
}

// ─── Components ───

function StatCard({ label, value, sub, icon: Icon, color = 'text-primary' }: {
  label: string; value: string | number; sub?: string; icon: typeof Activity; color?: string
}) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700/60 p-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] text-gray-500 uppercase tracking-wider font-medium">{label}</span>
        <Icon className={`w-3.5 h-3.5 ${color} opacity-60`} />
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-500 mt-0.5">{sub}</div>}
    </div>
  )
}

function SeverityBadge({ severity, size = 'sm' }: { severity: string; size?: 'sm' | 'xs' }) {
  const c = SEVERITY_COLORS[severity] || SEVERITY_COLORS.normal
  const cls = size === 'xs'
    ? `px-1.5 py-0 text-[10px]`
    : `px-2 py-0.5 text-xs`
  return (
    <span className={`inline-flex items-center rounded font-semibold uppercase ${c.bg} ${c.text} border ${c.border} ${cls}`}>
      {severity}
    </span>
  )
}

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100)
  const color = score > 60 ? 'bg-red-500' : score > 35 ? 'bg-orange-500' : score > 15 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-700/60 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono w-7 text-right text-gray-300">{score}</span>
    </div>
  )
}

function CategoryBreakdown({ scores }: { scores: CategoryScores }) {
  const cats = [
    { key: 'latency', label: 'LAT', score: scores.latency },
    { key: 'availability', label: 'AVL', score: scores.availability },
    { key: 'error', label: 'ERR', score: scores.error },
    { key: 'ssl', label: 'SSL', score: scores.ssl },
  ]
  return (
    <div className="grid grid-cols-4 gap-3">
      {cats.map(c => (
        <div key={c.key}>
          <div className="text-[10px] text-gray-500 mb-1 font-medium">{c.label}</div>
          <ScoreBar score={c.score} />
        </div>
      ))}
    </div>
  )
}

function FreshnessDot({ lastSeen }: { lastSeen: string }) {
  const f = freshness(lastSeen)
  const colors = { live: 'bg-green-400', recent: 'bg-yellow-400', stale: 'bg-gray-500' }
  const labels = { live: 'Live', recent: 'Recent', stale: 'Stale' }
  return (
    <span className="inline-flex items-center gap-1" title={`Last seen: ${new Date(lastSeen).toLocaleString()}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${colors[f]}`} />
      <span className="text-[10px] text-gray-500">{labels[f]}</span>
    </span>
  )
}

// ─── Anomaly Card ───

function AiExplanationSection({ anomalyId }: { anomalyId: string }) {
  const [open, setOpen] = useState(false)
  const token = useAuthStore(s => s.token)
  const { data, isLoading, error, refetch } = useQuery<ExplanationApiResponse>({
    queryKey: ['v2-explanation', anomalyId],
    queryFn: async () => {
      const r = await fetch(`/api/v2/anomalies/${anomalyId}/explanation`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
      return r.json()
    },
    enabled: open,
    staleTime: 5 * 60_000,
    retry: 1,
  })

  const ex = data?.explanation

  return (
    <div className="border border-indigo-500/20 rounded bg-indigo-500/5">
      <button
        className="w-full text-left px-2.5 py-2 flex items-center gap-2 hover:bg-indigo-500/10 transition-colors"
        onClick={() => { setOpen(!open); if (!open && !data && !isLoading) refetch() }}
      >
        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
        <span className="text-[10px] text-indigo-400/80 uppercase tracking-wider font-medium flex-1">
          AI Explanation
        </span>
        {data?.cached && <span className="text-[9px] text-gray-600 font-mono">cached</span>}
        {open ? <ChevronUp className="w-3 h-3 text-gray-600" /> : <ChevronDown className="w-3 h-3 text-gray-600" />}
      </button>

      {open && (
        <div className="px-2.5 pb-2.5 space-y-2.5">
          {isLoading && (
            <div className="flex items-center gap-2 py-3 justify-center">
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
              <span className="text-xs text-gray-500">Generating explanation…</span>
            </div>
          )}
          {error && (
            <div className="text-xs text-red-400 py-2">
              Failed to generate explanation: {(error as Error).message}
            </div>
          )}
          {ex && (
            <>
              {/* Summary */}
              <p className="text-xs text-indigo-200 leading-relaxed font-medium">{ex.summary}</p>

              {/* Anomaly Explanation */}
              <div>
                <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider font-medium">Current State</div>
                <p className="text-xs text-gray-300 leading-relaxed">{ex.current_state}</p>
              </div>

              {/* Prediction Explanation */}
              <div>
                <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider font-medium">Prediction Outlook</div>
                <p className="text-xs text-gray-300 leading-relaxed">{ex.prediction_outlook}</p>
              </div>

              {/* Key Signals */}
              {ex.key_signals.length > 0 && (
                <div>
                  <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider font-medium">Key Signals</div>
                  <ul className="space-y-0.5">
                    {ex.key_signals.map((s, i) => (
                      <li key={i} className="text-[11px] text-gray-400 flex items-start gap-1.5">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risk + Confidence row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div>
                  <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider font-medium">Risk interpretation</div>
                  <p className="text-[11px] text-gray-400">{ex.risk_interpretation}</p>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider font-medium">Confidence note</div>
                  <p className="text-[11px] text-gray-400">{ex.confidence_note}</p>
                </div>
              </div>

              {/* Model tag */}
              <div className="text-[9px] text-gray-600 font-mono text-right">
                model: {data?.model}{data?.cached ? ' (cached)' : ''}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function AnomalyCard({ anomaly, validationMode, isHistory = false }: {
  anomaly: AnomalyV2; validationMode: boolean; isHistory?: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const c = SEVERITY_COLORS[anomaly.severity] || SEVERITY_COLORS.normal

  return (
    <div className={`rounded-lg border ${isHistory ? 'border-gray-700/40 opacity-75' : c.border} overflow-hidden bg-surface`}>
      {/* Compact header */}
      <button
        className={`w-full text-left p-3 sm:p-4 hover:bg-surface-light/30 transition-colors focus:outline-none ${!isHistory ? c.bg : ''}`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          {/* Severity color strip (left accent) */}
          <div className={`w-1 self-stretch rounded-full ${c.text.replace('text-', 'bg-')} opacity-60 shrink-0`} />

          {/* Service info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white text-sm truncate">{anomaly.service_name}</span>
              {!isHistory && <FreshnessDot lastSeen={anomaly.last_seen_at} />}
              {isHistory && <span className="text-[10px] text-gray-500 bg-gray-700/50 px-1.5 rounded">resolved</span>}
            </div>
            <div className="text-[11px] text-gray-500 mt-0.5 truncate">
              {[anomaly.group_name, anomaly.environment, anomaly.service_type].filter(Boolean).join(' · ')}
            </div>
          </div>

          {/* Score + severity (right side) */}
          <div className="flex items-center gap-2.5 shrink-0">
            <SeverityBadge severity={anomaly.severity} />
            {anomaly.predicted_risk_level && anomaly.predicted_risk_level !== 'none' && (
              <div className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${
                anomaly.predicted_risk_level === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                anomaly.predicted_risk_level === 'high' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                anomaly.predicted_risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                'bg-blue-500/20 text-blue-400 border border-blue-500/30'
              }`}>
                {anomaly.predicted_risk_level === 'critical' ? '⚠ ' : ''}{anomaly.predicted_risk_level}
                {anomaly.predicted_horizon_minutes && <span className="ml-1 opacity-70">{anomaly.predicted_horizon_minutes}m</span>}
              </div>
            )}
            <div className="text-right">
              <div className="text-lg font-bold font-mono text-white leading-tight">{anomaly.anomaly_score}</div>
              <div className="text-[10px] text-gray-500">{anomaly.confidence_label}</div>
            </div>
            {expanded
              ? <ChevronUp className="w-4 h-4 text-gray-600" />
              : <ChevronDown className="w-4 h-4 text-gray-600" />}
          </div>
        </div>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-700/40 space-y-3">
          {/* Category breakdown */}
          <div>
            <div className="text-[10px] text-gray-500 mb-1.5 uppercase tracking-wider font-medium">Category Scores</div>
            <CategoryBreakdown scores={anomaly.category_scores} />
          </div>

          {/* Evidence */}
          <div>
            <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider font-medium">Evidence</div>
            <p className="text-xs text-gray-300 leading-relaxed">{anomaly.evidence_summary}</p>
          </div>

          {/* Reason codes */}
          {anomaly.reason_codes.length > 0 && (
            <div>
              <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider font-medium">Reason Codes</div>
              <div className="flex flex-wrap gap-1">
                {anomaly.reason_codes.map((rc, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-gray-700/50 rounded text-[11px] text-gray-400 font-mono">
                    {rc.code}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Prediction details */}
          {anomaly.predicted_risk_score != null && anomaly.predicted_risk_score > 0 && (
            <div className="p-2.5 bg-amber-500/5 border border-amber-500/20 rounded">
              <div className="text-[10px] text-amber-400/80 mb-1.5 uppercase tracking-wider font-medium">Predictive Risk</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                <div>
                  <span className="text-gray-500">Risk Score</span>
                  <div className="text-white font-mono">{anomaly.predicted_risk_score}/100</div>
                </div>
                <div>
                  <span className="text-gray-500">Risk Level</span>
                  <div className={`font-medium ${
                    anomaly.predicted_risk_level === 'critical' ? 'text-red-400' :
                    anomaly.predicted_risk_level === 'high' ? 'text-orange-400' :
                    anomaly.predicted_risk_level === 'medium' ? 'text-yellow-400' :
                    'text-gray-300'
                  }`}>{anomaly.predicted_risk_level?.toUpperCase() ?? '—'}</div>
                </div>
                <div>
                  <span className="text-gray-500">Horizon</span>
                  <div className="text-white font-mono">{anomaly.predicted_horizon_minutes ? `${anomaly.predicted_horizon_minutes}m` : '—'}</div>
                </div>
                <div>
                  <span className="text-gray-500">Confidence</span>
                  <div className="text-white font-mono">{anomaly.prediction_confidence ?? '—'}</div>
                </div>
              </div>
              {anomaly.prediction_summary && anomaly.prediction_summary !== 'No elevated predicted risk' && (
                <p className="text-xs text-amber-300/80 mt-1.5">{anomaly.prediction_summary}</p>
              )}
              {anomaly.prediction_reason_codes && anomaly.prediction_reason_codes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {anomaly.prediction_reason_codes.map((rc, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-amber-700/30 rounded text-[10px] text-amber-400 font-mono">
                      {rc.code}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AI Explanation (V1.6) */}
          <AiExplanationSection anomalyId={anomaly.id} />

          {/* Metadata row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
            <div>
              <span className="text-gray-500">Occurrences</span>
              <div className="text-white font-mono">{anomaly.occurrence_count}</div>
            </div>
            <div>
              <span className="text-gray-500">First Seen</span>
              <div className="text-gray-300">{timeAgo(anomaly.first_seen_at)}</div>
            </div>
            <div>
              <span className="text-gray-500">Last Seen</span>
              <div className="text-gray-300">{timeAgo(anomaly.last_seen_at)}</div>
            </div>
            <div>
              <span className="text-gray-500">Confidence</span>
              <div className="text-white font-mono">{(anomaly.confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Validation data (only when validation mode is active) */}
          {validationMode && (
            <div className="p-2.5 bg-purple-500/5 border border-purple-500/20 rounded">
              <div className="text-[10px] text-purple-400/80 mb-1.5 uppercase tracking-wider font-medium flex items-center gap-1">
                <Eye className="w-3 h-3" /> Validation
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                <div>
                  <span className="text-gray-500">Baseline Dev</span>
                  <div className="text-white font-mono">
                    {anomaly.baseline_deviation_pct !== null ? `${anomaly.baseline_deviation_pct.toFixed(1)}%` : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Triggered Cats</span>
                  <div className="text-white font-mono">{anomaly.triggered_categories_count ?? '—'}</div>
                </div>
                <div>
                  <span className="text-gray-500">Anomalous</span>
                  <div className={anomaly.is_anomalous ? 'text-red-400 font-medium' : 'text-green-400'}>
                    {anomaly.is_anomalous !== null ? (anomaly.is_anomalous ? 'YES' : 'NO') : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Eval Time</span>
                  <div className="text-white font-mono">{anomaly.evaluation_duration_ms ?? 0}ms</div>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] mt-2 pt-2 border-t border-purple-500/10">
                <div>
                  <span className="text-gray-500">Trend</span>
                  <div className="text-white font-mono">
                    {anomaly.latency_trend_slope != null
                      ? `${anomaly.latency_trend_slope > 0 ? '↑' : anomaly.latency_trend_slope < 0 ? '↓' : '→'} ${anomaly.latency_trend_slope > 0 ? '+' : ''}${anomaly.latency_trend_slope.toFixed(3)}`
                      : '—'}
                    {anomaly.latency_trend_r2 != null && anomaly.latency_trend_r2 > 0
                      ? <span className="text-gray-500 ml-1">(r²: {anomaly.latency_trend_r2.toFixed(2)})</span>
                      : null}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Burst Ratio</span>
                  <div className={`font-mono ${(anomaly.log_error_burst_ratio ?? 0) > 3 ? 'text-red-400' : 'text-white'}`}>
                    {anomaly.log_error_burst_ratio != null ? `${anomaly.log_error_burst_ratio.toFixed(1)}x` : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Fingerprint</span>
                  <div className="text-gray-400 font-mono truncate">{anomaly.fingerprint.substring(0, 12)}</div>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] mt-2 pt-2 border-t border-purple-500/10">
                <div>
                  <span className="text-gray-500">Trace P95</span>
                  <div className="text-white font-mono">
                    {anomaly.trace_p95_latency_ms != null && anomaly.trace_p95_latency_ms > 0 ? `${anomaly.trace_p95_latency_ms.toFixed(0)}ms` : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Trace Err</span>
                  <div className={`font-mono ${(anomaly.trace_error_rate ?? 0) > 0.05 ? 'text-red-400' : 'text-white'}`}>
                    {anomaly.trace_error_rate != null && anomaly.trace_error_rate > 0 ? `${(anomaly.trace_error_rate * 100).toFixed(1)}%` : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Bottleneck</span>
                  <div className={`font-mono ${(anomaly.trace_bottleneck_score ?? 0) > 0.5 ? 'text-orange-400' : 'text-white'}`}>
                    {anomaly.trace_bottleneck_score != null && anomaly.trace_bottleneck_score > 0 ? `${(anomaly.trace_bottleneck_score * 100).toFixed(0)}%` : '—'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">Slow Ops</span>
                  <div className={`font-mono ${(anomaly.trace_slow_operations ?? 0) >= 2 ? 'text-yellow-400' : 'text-white'}`}>
                    {anomaly.trace_slow_operations != null && anomaly.trace_slow_operations > 0 ? anomaly.trace_slow_operations : '—'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Validation Summary Panel (collapsible) ───

function ValidationSummaryPanel({ data }: { data: ValidationSummary }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-surface rounded-lg border border-purple-500/20">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-light/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Validation Summary</span>
          <span className="text-[10px] text-gray-500 ml-1">
            {data.total_evaluated} evaluated · {data.total_anomalous} anomalous
          </span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 text-center text-xs">
            <div><div className="text-lg font-bold text-white">{data.total_evaluated}</div><div className="text-gray-500">Evaluated</div></div>
            <div><div className="text-lg font-bold text-yellow-400">{data.total_active}</div><div className="text-gray-500">Active</div></div>
            <div><div className="text-lg font-bold text-red-400">{data.total_anomalous}</div><div className="text-gray-500">Anomalous</div></div>
            <div><div className="text-lg font-bold text-primary">{data.avg_score.toFixed(1)}</div><div className="text-gray-500">Avg Score</div></div>
            <div><div className="text-lg font-bold text-orange-400">{data.max_score}</div><div className="text-gray-500">Max Score</div></div>
          </div>

          {data.score_histogram.length > 0 && (
            <div>
              <div className="text-[10px] text-gray-500 mb-1.5 uppercase tracking-wider">Score Distribution</div>
              <div className="flex items-end gap-1 h-12">
                {data.score_histogram.map(b => {
                  const maxC = Math.max(...data.score_histogram.map(x => x.count), 1)
                  const h = Math.max((b.count / maxC) * 100, 4)
                  return (
                    <div key={b.range} className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-purple-500/40 rounded-t" style={{ height: `${h}%` }} title={`${b.range}: ${b.count}`} />
                      <div className="text-[9px] text-gray-600 mt-0.5">{b.range}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          <div className="grid grid-cols-3 gap-3 text-[11px] text-gray-500">
            <div>Avg Confidence: <span className="text-gray-300">{(data.avg_confidence * 100).toFixed(0)}%</span></div>
            <div>Avg Baseline Dev: <span className="text-gray-300">{data.avg_baseline_deviation_pct.toFixed(1)}%</span></div>
            <div>Avg Eval Time: <span className="text-gray-300">{data.avg_evaluation_duration_ms.toFixed(0)}ms</span></div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-gray-500">
            <div>Avg Trend Slope: <span className="text-gray-300">{data.avg_latency_trend_slope.toFixed(4)}</span></div>
            <div>Avg Burst Ratio: <span className="text-gray-300">{data.avg_log_error_burst_ratio.toFixed(2)}x</span></div>
            <div>Degrading Trend: <span className="text-yellow-400">{data.pct_positive_trend.toFixed(1)}%</span></div>
            <div>Burst Detected: <span className="text-red-400">{data.pct_burst_detected.toFixed(1)}%</span></div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-gray-500">
            <div>Avg Bottleneck: <span className={`${data.avg_trace_bottleneck_score > 0.3 ? 'text-orange-400' : 'text-gray-300'}`}>{(data.avg_trace_bottleneck_score * 100).toFixed(0)}%</span></div>
            <div>Avg Trace Err: <span className={`${data.avg_trace_error_rate > 0.05 ? 'text-red-400' : 'text-gray-300'}`}>{(data.avg_trace_error_rate * 100).toFixed(1)}%</span></div>
            <div>Avg Trace P95: <span className="text-gray-300">{data.avg_trace_p95_latency.toFixed(0)}ms</span></div>
            <div>Total Slow Ops: <span className={`${data.total_slow_operations > 0 ? 'text-yellow-400' : 'text-gray-300'}`}>{data.total_slow_operations}</span></div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-gray-500">
            <div>Avg Risk Score: <span className={`${data.avg_predicted_risk_score > 20 ? 'text-orange-400' : 'text-gray-300'}`}>{data.avg_predicted_risk_score.toFixed(1)}</span></div>
            <div>Predicted High: <span className={`${data.predicted_high_count > 0 ? 'text-orange-400' : 'text-gray-300'}`}>{data.predicted_high_count}</span></div>
            <div>Predicted Critical: <span className={`${data.predicted_critical_count > 0 ? 'text-red-400' : 'text-gray-300'}`}>{data.predicted_critical_count}</span></div>
            <div>With Horizon: <span className={`${data.predicted_with_horizon_count > 0 ? 'text-yellow-400' : 'text-gray-300'}`}>{data.predicted_with_horizon_count}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Compare Panel (collapsible) ───

function ComparePanel({ data }: { data: CompareResponse }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-surface rounded-lg border border-purple-500/20">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-light/20 transition-colors"
      >
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">V1 ↔ V2 Comparison</span>
          <span className="text-[10px] text-gray-500 ml-1">
            {data.matched_services.length} matched · {data.rust_only.length + data.python_only.length} unmatched
          </span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <div className="grid grid-cols-4 gap-3 text-center text-xs">
            <div><div className="text-lg font-bold text-primary">{data.rust_v2_count}</div><div className="text-gray-500">V2 Active</div></div>
            <div><div className="text-lg font-bold text-yellow-400">{data.python_v1_count}</div><div className="text-gray-500">V1 Active</div></div>
            <div><div className="text-lg font-bold text-green-400">{data.matched_services.length}</div><div className="text-gray-500">Matched</div></div>
            <div><div className="text-lg font-bold text-gray-400">{data.rust_only.length + data.python_only.length}</div><div className="text-gray-500">Unmatched</div></div>
          </div>

          {data.matched_services.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[10px] text-gray-500 uppercase border-b border-gray-700/50">
                    <th className="text-left py-1.5 pr-2">Service</th>
                    <th className="text-right py-1.5 px-2">V2</th>
                    <th className="text-right py-1.5 px-2">V1</th>
                    <th className="text-center py-1.5 pl-2">Agreement</th>
                  </tr>
                </thead>
                <tbody>
                  {data.matched_services.map(s => (
                    <tr key={s.service_name} className="border-b border-gray-800/40">
                      <td className="py-1.5 pr-2 text-gray-300">{s.service_name}</td>
                      <td className="py-1.5 px-2 text-right font-mono text-white">
                        {s.rust_score} <SeverityBadge severity={s.rust_severity} size="xs" />
                      </td>
                      <td className="py-1.5 px-2 text-right font-mono text-gray-300">
                        {s.python_anomaly_score.toFixed(1)} <SeverityBadge severity={s.python_severity} size="xs" />
                      </td>
                      <td className="py-1.5 pl-2 text-center">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          s.agreement === 'both_flagged' ? 'bg-red-500/15 text-red-400' :
                          s.agreement === 'both_normal' ? 'bg-green-500/15 text-green-400' :
                          'bg-yellow-500/15 text-yellow-400'
                        }`}>{s.agreement.replace('_', ' ')}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(data.rust_only.length > 0 || data.python_only.length > 0) && (
            <div className="grid grid-cols-2 gap-3 text-[11px]">
              {data.rust_only.length > 0 && (
                <div><span className="text-gray-500">V2 only: </span><span className="text-primary">{data.rust_only.join(', ')}</span></div>
              )}
              {data.python_only.length > 0 && (
                <div><span className="text-gray-500">V1 only: </span><span className="text-yellow-400">{data.python_only.join(', ')}</span></div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Filter types ───

type FilterSeverity = 'all' | 'normal' | 'watch' | 'degraded' | 'critical' | 'emergency'
type SortBy = 'score' | 'service' | 'severity' | 'last_seen'
type ViewTab = 'active' | 'history'

// ─── Page ───

export function AiAnomaliesV2Page() {
  useEffect(() => { document.title = 'Rhinometric - Anomaly Analysis' }, [])
  const [validationMode] = useState(false)
  const [filterSeverity, setFilterSeverity] = useState<FilterSeverity>('all')
  const [sortBy, setSortBy] = useState<SortBy>('score')
  const [sortDesc, setSortDesc] = useState(true)
  const [tab, setTab] = useState<ViewTab>('active')

  // --- Data fetching ---
  const { data: activeData, isLoading: loadingActive, error: activeError } =
    useV2Fetch<AnomalyListResponse>('v2-active', `${V2_BASE}/active?limit=${PAGE_LIMIT}`)

  const { data: historyData, isLoading: loadingHistory } =
    useV2Fetch<AnomalyListResponse>('v2-resolved', `${V2_BASE}/resolved?limit=${PAGE_LIMIT}`)

  const { data: validationData } =
    useV2Fetch<ValidationSummary>('v2-validation-summary', `${V2_BASE}/validation-summary`, validationMode)

  const { data: compareData } =
    useV2Fetch<CompareResponse>('v2-compare-python', `${V2_BASE}/compare-python`, validationMode)

  // --- Derived: which list to show ---
  const sourceList = tab === 'active' ? activeData?.anomalies : historyData?.anomalies

  // --- Client-side summary from displayed data (Task 3) ---
  const displaySummary = useMemo(() => {
    const list = activeData?.anomalies ?? []
    const counts: Record<string, number> = { normal: 0, watch: 0, degraded: 0, critical: 0, emergency: 0 }
    let maxScore = 0
    for (const a of list) {
      const sev = a.severity in counts ? a.severity : 'normal'
      counts[sev]++
      if (a.anomaly_score > maxScore) maxScore = a.anomaly_score
    }
    return { total: list.length, counts, maxScore }
  }, [activeData])

  // --- Filter + sort ---
  const displayedAnomalies = useMemo(() => {
    if (!sourceList) return []
    let list = [...sourceList]

    // Severity filter
    if (filterSeverity !== 'all') {
      list = list.filter(a => a.severity === filterSeverity)
    }

    // Sort
    list.sort((a, b) => {
      let cmp = 0
      switch (sortBy) {
        case 'score': cmp = a.anomaly_score - b.anomaly_score; break
        case 'service': cmp = a.service_name.localeCompare(b.service_name); break
        case 'severity': cmp = (SEVERITY_ORDER[a.severity] ?? 0) - (SEVERITY_ORDER[b.severity] ?? 0); break
        case 'last_seen': cmp = new Date(a.last_seen_at).getTime() - new Date(b.last_seen_at).getTime(); break
      }
      return sortDesc ? -cmp : cmp
    })

    return list.slice(0, PAGE_LIMIT)
  }, [sourceList, filterSeverity, sortBy, sortDesc])

  // --- Handlers ---
  const toggleSort = useCallback(() => setSortDesc(d => !d), [])

  // --- Loading / error states ---
  const isLoading = tab === 'active' ? loadingActive : loadingHistory
  const error = tab === 'active' ? activeError : null

  if (isLoading && !sourceList) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <p className="text-red-400 text-sm">Failed to load anomalies</p>
        <p className="text-[11px] text-gray-500 mt-1">{String(error)}</p>
      </div>
    )
  }

  const activeCount = activeData?.count ?? 0
  const historyCount = historyData?.count ?? 0

  return (
    <div className="space-y-5">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            Anomaly Analysis
          </h1>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Detect, inspect and understand anomalous service behavior — scores, evidence & predictions
          </p>
        </div>
        {/* Validation toggle removed ? AI Cutover: single engine */}
      </div>

      {/* ── Summary cards (always from active data) ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label="Detected"
          value={displaySummary.total}
          sub={displaySummary.total === 0 ? 'No anomalies detected' : undefined}
          icon={Zap}
          color={displaySummary.total > 0 ? 'text-red-400' : 'text-green-400'}
        />
        <StatCard
          label="Peak Score"
          value={displaySummary.maxScore}
          icon={TrendingUp}
          color={displaySummary.maxScore > 60 ? 'text-red-400' : displaySummary.maxScore > 15 ? 'text-orange-400' : 'text-green-400'}
        />
        <StatCard
          label="Critical+"
          value={(displaySummary.counts.critical ?? 0) + (displaySummary.counts.emergency ?? 0)}
          sub={`${displaySummary.counts.degraded ?? 0} degraded, ${displaySummary.counts.watch ?? 0} watch`}
          icon={AlertTriangle}
          color="text-red-400"
        />
        <StatCard label="Resolved" value={historyCount} sub="Recently resolved anomalies" icon={History} color="text-gray-400" />
      </div>

      {/* ── Validation panels (only when enabled, collapsible) ── */}
      {validationMode && (
        <div className="space-y-2">
          {validationData && <ValidationSummaryPanel data={validationData} />}
          {compareData && <ComparePanel data={compareData} />}
        </div>
      )}

      {/* ── Tab bar ── */}
      <div className="flex items-center gap-4 border-b border-gray-700/50">
        <button
          onClick={() => setTab('active')}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            tab === 'active'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          Detected
          {activeCount > 0 && (
            <span className="ml-1 px-1.5 py-0 text-[10px] rounded-full bg-red-500/20 text-red-400 font-bold">{activeCount}</span>
          )}
        </button>
        <button
          onClick={() => setTab('history')}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            tab === 'history'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Resolved
          {historyCount > 0 && (
            <span className="ml-1 px-1.5 py-0 text-[10px] rounded-full bg-gray-600 text-gray-300 font-medium">{historyCount}</span>
          )}
        </button>
      </div>

      {/* ── Filters + sort (below tab bar) ── */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-[11px] text-gray-500 font-medium">Severity:</span>
        {(['all', 'normal', 'watch', 'degraded', 'critical', 'emergency'] as FilterSeverity[]).map(s => {
          const isActive = filterSeverity === s
          return (
            <button
              key={s}
              onClick={() => setFilterSeverity(s)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                isActive
                  ? 'bg-primary/15 text-primary border border-primary/30'
                  : 'text-gray-500 hover:text-gray-300 border border-transparent'
              }`}
            >
              {s}
            </button>
          )
        })}

        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-[11px] text-gray-500">Sort:</span>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortBy)}
            className="bg-surface border border-gray-700 rounded px-2 py-0.5 text-[11px] text-gray-300 focus:outline-none"
          >
            <option value="score">Score</option>
            <option value="severity">Severity</option>
            <option value="service">Service</option>
            <option value="last_seen">Last Seen</option>
          </select>
          <button onClick={toggleSort} className="p-0.5 rounded hover:bg-surface-light text-gray-500 hover:text-white" title="Toggle order">
            <ArrowUpDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Anomaly list ── */}
      <div className="space-y-2">
        {displayedAnomalies.length === 0 ? (
          <div className="bg-surface rounded-lg border border-gray-700/40 p-10 text-center">
            <Activity className="w-8 h-8 text-gray-700 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">
              {tab === 'active' ? 'No anomalies detected — all services within normal baselines' : 'No resolved anomalies in the analysis window'}
            </p>
          </div>
        ) : (
          displayedAnomalies.map(a => (
            <AnomalyCard key={a.id} anomaly={a} validationMode={validationMode} isHistory={tab === 'history'} />
          ))
        )}
      </div>

      {/* ── Footer ── */}
      <div className="text-center text-[11px] text-gray-600 pb-2">
        Showing {displayedAnomalies.length} of {(tab === 'active' ? activeCount : historyCount)} · Auto-refresh 30s
      </div>
    </div>
  )
}
