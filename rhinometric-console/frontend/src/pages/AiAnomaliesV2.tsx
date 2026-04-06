import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  AlertTriangle, Activity, Brain, ArrowUpDown, Eye, EyeOff,
  BarChart3, Zap, Shield, Clock, TrendingUp, ChevronDown, ChevronUp
} from 'lucide-react'

// ─── Types ───

interface CategoryScores {
  latency: number
  availability: number
  error: number
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

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  normal:    { bg: 'bg-green-500/10',  text: 'text-green-400',  border: 'border-green-500/30' },
  watch:     { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  degraded:  { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  critical:  { bg: 'bg-red-500/10',    text: 'text-red-400',    border: 'border-red-500/30' },
  emergency: { bg: 'bg-red-700/20',    text: 'text-red-300',    border: 'border-red-700/40' },
}

// ─── Fetch helpers ───

function useV2Fetch<T>(key: string, endpoint: string) {
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
  })
}

// ─── Components ───

function StatCard({ label, value, icon: Icon, color = 'text-primary' }: {
  label: string; value: string | number; icon: typeof Activity; color?: string
}) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const c = SEVERITY_COLORS[severity] || SEVERITY_COLORS.normal
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text} border ${c.border}`}>
      {severity}
    </span>
  )
}

function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100)
  const color = score > 60 ? 'bg-red-500' : score > 35 ? 'bg-orange-500' : score > 15 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono w-8 text-right">{score}</span>
    </div>
  )
}

function CategoryBreakdown({ scores }: { scores: CategoryScores }) {
  const categories = [
    { key: 'latency', label: 'Latency', score: scores.latency },
    { key: 'availability', label: 'Availability', score: scores.availability },
    { key: 'error', label: 'Error', score: scores.error },
    { key: 'ssl', label: 'SSL', score: scores.ssl },
  ]
  return (
    <div className="grid grid-cols-4 gap-2">
      {categories.map(c => (
        <div key={c.key} className="text-center">
          <div className="text-xs text-gray-400 mb-1">{c.label}</div>
          <ScoreBar score={c.score} />
        </div>
      ))}
    </div>
  )
}

function AnomalyCard({ anomaly, validationMode }: { anomaly: AnomalyV2; validationMode: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const c = SEVERITY_COLORS[anomaly.severity] || SEVERITY_COLORS.normal

  return (
    <div className={`bg-surface rounded-lg border ${c.border} overflow-hidden`}>
      {/* Header */}
      <div
        className={`p-4 cursor-pointer hover:bg-surface-light/50 transition-colors ${c.bg}`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className={`w-5 h-5 ${c.text}`} />
            <div>
              <div className="font-semibold text-white">{anomaly.service_name}</div>
              <div className="text-xs text-gray-400">
                {anomaly.service_type} · {anomaly.group_name} · {anomaly.environment}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <SeverityBadge severity={anomaly.severity} />
            <div className="text-right">
              <div className="text-lg font-bold font-mono text-white">{anomaly.anomaly_score}</div>
              <div className="text-xs text-gray-400">{anomaly.confidence_label} conf</div>
            </div>
            {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
          </div>
        </div>

        {/* Score bar */}
        <div className="mt-3">
          <ScoreBar score={anomaly.anomaly_score} />
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="p-4 border-t border-gray-700 space-y-4">
          {/* Category breakdown */}
          <div>
            <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider">Category Breakdown</div>
            <CategoryBreakdown scores={anomaly.category_scores} />
          </div>

          {/* Evidence */}
          <div>
            <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Evidence</div>
            <p className="text-sm text-gray-300">{anomaly.evidence_summary}</p>
          </div>

          {/* Reason codes */}
          {anomaly.reason_codes.length > 0 && (
            <div>
              <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider">Reason Codes</div>
              <div className="flex flex-wrap gap-1.5">
                {anomaly.reason_codes.map((rc, i) => (
                  <span key={i} className="px-2 py-0.5 bg-surface-light rounded text-xs text-gray-300 font-mono">
                    {rc.code}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-gray-400">Status</span>
              <div className={anomaly.status === 'active' ? 'text-red-400' : 'text-green-400'}>{anomaly.status}</div>
            </div>
            <div>
              <span className="text-gray-400">Occurrences</span>
              <div className="text-white">{anomaly.occurrence_count}</div>
            </div>
            <div>
              <span className="text-gray-400">First Seen</span>
              <div className="text-white">{new Date(anomaly.first_seen_at).toLocaleString()}</div>
            </div>
            <div>
              <span className="text-gray-400">Last Seen</span>
              <div className="text-white">{new Date(anomaly.last_seen_at).toLocaleString()}</div>
            </div>
          </div>

          {/* Validation fields */}
          {validationMode && (
            <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
              <div className="text-xs text-purple-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5" /> Validation Data
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-gray-400">Baseline Dev %</span>
                  <div className="text-white font-mono">
                    {anomaly.baseline_deviation_pct !== null ? `${anomaly.baseline_deviation_pct.toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-400">Triggered Cats</span>
                  <div className="text-white font-mono">{anomaly.triggered_categories_count ?? 'N/A'}</div>
                </div>
                <div>
                  <span className="text-gray-400">Is Anomalous</span>
                  <div className={anomaly.is_anomalous ? 'text-red-400' : 'text-green-400'}>
                    {anomaly.is_anomalous !== null ? (anomaly.is_anomalous ? 'YES' : 'NO') : 'N/A'}
                  </div>
                </div>
                <div>
                  <span className="text-gray-400">Eval Duration</span>
                  <div className="text-white font-mono">{anomaly.evaluation_duration_ms ?? 0}ms</div>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-500 font-mono">
                Fingerprint: {anomaly.fingerprint.substring(0, 16)}...
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ValidationSummaryPanel({ data }: { data: ValidationSummary }) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-semibold text-white">Validation Summary</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{data.total_evaluated}</div>
          <div className="text-xs text-gray-400">Evaluated</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">{data.total_active}</div>
          <div className="text-xs text-gray-400">Active</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-400">{data.total_anomalous}</div>
          <div className="text-xs text-gray-400">Anomalous</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-primary">{data.avg_score.toFixed(1)}</div>
          <div className="text-xs text-gray-400">Avg Score</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-400">{data.max_score}</div>
          <div className="text-xs text-gray-400">Max Score</div>
        </div>
      </div>

      {/* Score histogram */}
      {data.score_histogram.length > 0 && (
        <div>
          <div className="text-xs text-gray-400 mb-2 uppercase tracking-wider">Score Distribution</div>
          <div className="flex items-end gap-1 h-16">
            {data.score_histogram.map(b => {
              const maxCount = Math.max(...data.score_histogram.map(x => x.count), 1)
              const height = Math.max((b.count / maxCount) * 100, 4)
              return (
                <div key={b.range} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-primary/60 rounded-t"
                    style={{ height: `${height}%` }}
                    title={`${b.range}: ${b.count}`}
                  />
                  <div className="text-[10px] text-gray-500 mt-1">{b.range}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-gray-400">
        <div>Avg Confidence: <span className="text-white">{(data.avg_confidence * 100).toFixed(0)}%</span></div>
        <div>Avg Baseline Dev: <span className="text-white">{data.avg_baseline_deviation_pct.toFixed(1)}%</span></div>
        <div>Avg Eval Duration: <span className="text-white">{data.avg_evaluation_duration_ms.toFixed(0)}ms</span></div>
      </div>
    </div>
  )
}

function ComparePanel({ data }: { data: CompareResponse }) {
  return (
    <div className="bg-surface rounded-lg border border-gray-700 p-5">
      <div className="flex items-center gap-2 mb-4">
        <ArrowUpDown className="w-5 h-5 text-purple-400" />
        <h3 className="text-lg font-semibold text-white">V1 ↔ V2 Comparison</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 text-center">
        <div>
          <div className="text-xl font-bold text-primary">{data.rust_v2_count}</div>
          <div className="text-xs text-gray-400">Rust V2 Active</div>
        </div>
        <div>
          <div className="text-xl font-bold text-yellow-400">{data.python_v1_count}</div>
          <div className="text-xs text-gray-400">Python V1 Active</div>
        </div>
        <div>
          <div className="text-xl font-bold text-green-400">{data.matched_services.length}</div>
          <div className="text-xs text-gray-400">Matched</div>
        </div>
        <div>
          <div className="text-xl font-bold text-gray-400">
            {data.rust_only.length + data.python_only.length}
          </div>
          <div className="text-xs text-gray-400">Unmatched</div>
        </div>
      </div>

      {/* Matched services table */}
      {data.matched_services.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase border-b border-gray-700">
                <th className="text-left py-2 pr-3">Service</th>
                <th className="text-right py-2 px-2">V2 Score</th>
                <th className="text-right py-2 px-2">V1 Score</th>
                <th className="text-center py-2 px-2">Agreement</th>
              </tr>
            </thead>
            <tbody>
              {data.matched_services.map(s => (
                <tr key={s.service_name} className="border-b border-gray-800">
                  <td className="py-2 pr-3 text-white">{s.service_name}</td>
                  <td className="py-2 px-2 text-right font-mono">
                    {s.rust_score}
                    <SeverityBadge severity={s.rust_severity} />
                  </td>
                  <td className="py-2 px-2 text-right font-mono">
                    {s.python_anomaly_score.toFixed(2)}
                    <SeverityBadge severity={s.python_severity} />
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      s.agreement === 'both_flagged' ? 'bg-red-500/20 text-red-400' :
                      s.agreement === 'both_normal' ? 'bg-green-500/20 text-green-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {s.agreement.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Unmatched */}
      {(data.rust_only.length > 0 || data.python_only.length > 0) && (
        <div className="mt-3 grid grid-cols-2 gap-4 text-xs">
          {data.rust_only.length > 0 && (
            <div>
              <span className="text-gray-400">V2 only: </span>
              <span className="text-primary">{data.rust_only.join(', ')}</span>
            </div>
          )}
          {data.python_only.length > 0 && (
            <div>
              <span className="text-gray-400">V1 only: </span>
              <span className="text-yellow-400">{data.python_only.join(', ')}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Filters ───

type FilterSeverity = 'all' | 'normal' | 'watch' | 'degraded' | 'critical' | 'emergency'
type FilterStatus = 'all' | 'active' | 'resolved'
type SortBy = 'score' | 'service' | 'severity' | 'last_seen'

// ─── Page ───

export function AiAnomaliesV2Page() {
  const [validationMode, setValidationMode] = useState(true)
  const [filterSeverity, setFilterSeverity] = useState<FilterSeverity>('all')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [sortBy, setSortBy] = useState<SortBy>('score')
  const [sortDesc, setSortDesc] = useState(true)

  const { data: anomalyData, isLoading: loadingAnomalies, error: anomalyError } =
    useV2Fetch<AnomalyListResponse>('v2-anomalies', `${V2_BASE}?limit=200`)

  const { data: validationData, isLoading: loadingValidation } =
    useV2Fetch<ValidationSummary>('v2-validation-summary', `${V2_BASE}/validation-summary`)

  const { data: compareData, isLoading: loadingCompare } =
    useV2Fetch<CompareResponse>('v2-compare-python', `${V2_BASE}/compare-python`)

  // Filtered + sorted anomalies
  const filteredAnomalies = useMemo(() => {
    if (!anomalyData?.anomalies) return []
    let list = [...anomalyData.anomalies]

    if (filterSeverity !== 'all') {
      list = list.filter(a => a.severity === filterSeverity)
    }
    if (filterStatus !== 'all') {
      list = list.filter(a => a.status === filterStatus)
    }

    list.sort((a, b) => {
      let cmp = 0
      switch (sortBy) {
        case 'score': cmp = a.anomaly_score - b.anomaly_score; break
        case 'service': cmp = a.service_name.localeCompare(b.service_name); break
        case 'severity': cmp = a.anomaly_score - b.anomaly_score; break
        case 'last_seen': cmp = new Date(a.last_seen_at).getTime() - new Date(b.last_seen_at).getTime(); break
      }
      return sortDesc ? -cmp : cmp
    })

    return list
  }, [anomalyData, filterSeverity, filterStatus, sortBy, sortDesc])

  if (loadingAnomalies && !anomalyData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (anomalyError) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <p className="text-red-400">Failed to load anomalies from V2 engine</p>
        <p className="text-xs text-gray-400 mt-1">{String(anomalyError)}</p>
      </div>
    )
  }

  const summary = anomalyData?.summary

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-7 h-7 text-primary" />
            AI Anomalies V2
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Rust-native multi-signal scoring engine · Validation mode
          </p>
        </div>

        {/* Validation mode toggle */}
        <button
          onClick={() => setValidationMode(!validationMode)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
            validationMode
              ? 'bg-purple-500/20 border-purple-500/40 text-purple-300'
              : 'bg-surface border-gray-600 text-gray-400 hover:text-white'
          }`}
        >
          {validationMode ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          Validation Mode {validationMode ? 'ON' : 'OFF'}
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total Active" value={summary.total_active} icon={Zap} color="text-red-400" />
          <StatCard label="Max Score" value={summary.max_score} icon={TrendingUp} color="text-orange-400" />
          <StatCard label="Services" value={anomalyData?.count ?? 0} icon={Shield} color="text-primary" />
          <StatCard label="Refresh" value="30s" icon={Clock} color="text-gray-400" />
        </div>
      )}

      {/* Validation panels */}
      {validationMode && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {validationData && <ValidationSummaryPanel data={validationData} />}
          {loadingValidation && (
            <div className="bg-surface rounded-lg border border-gray-700 p-5 flex items-center justify-center">
              <div className="animate-pulse text-gray-400 text-sm">Loading validation data...</div>
            </div>
          )}
          {compareData && <ComparePanel data={compareData} />}
          {loadingCompare && (
            <div className="bg-surface rounded-lg border border-gray-700 p-5 flex items-center justify-center">
              <div className="animate-pulse text-gray-400 text-sm">Loading comparison data...</div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Severity filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-400">Severity:</span>
          {(['all', 'normal', 'watch', 'degraded', 'critical', 'emergency'] as FilterSeverity[]).map(s => (
            <button
              key={s}
              onClick={() => setFilterSeverity(s)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterSeverity === s
                  ? 'bg-primary/20 text-primary border border-primary/40'
                  : 'bg-surface text-gray-400 hover:text-white border border-gray-700'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Status filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-400">Status:</span>
          {(['all', 'active', 'resolved'] as FilterStatus[]).map(s => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filterStatus === s
                  ? 'bg-primary/20 text-primary border border-primary/40'
                  : 'bg-surface text-gray-400 hover:text-white border border-gray-700'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-xs text-gray-400">Sort:</span>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortBy)}
            className="bg-surface border border-gray-700 rounded px-2 py-1 text-xs text-white"
          >
            <option value="score">Score</option>
            <option value="service">Service</option>
            <option value="last_seen">Last Seen</option>
          </select>
          <button
            onClick={() => setSortDesc(!sortDesc)}
            className="p-1 rounded hover:bg-surface-light text-gray-400 hover:text-white"
          >
            <ArrowUpDown className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Anomaly list */}
      <div className="space-y-3">
        {filteredAnomalies.length === 0 ? (
          <div className="bg-surface rounded-lg border border-gray-700 p-8 text-center">
            <Activity className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No anomalies match current filters</p>
          </div>
        ) : (
          filteredAnomalies.map(a => (
            <AnomalyCard key={a.id} anomaly={a} validationMode={validationMode} />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-500">
        Rust Anomaly Engine V2 · Polling every 30s · {anomalyData?.count ?? 0} results
      </div>
    </div>
  )
}
