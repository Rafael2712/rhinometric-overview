import { useEffect, useState } from 'react'
import { useAuthStore } from '../lib/auth/store'
import {
  Brain, Shield, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Activity, Zap, ChevronDown, ChevronUp,
  Lightbulb, RefreshCw, ArrowRight
} from 'lucide-react'

interface RiskScore {
  score: number
  level: string
  label: string
  factors: string[]
}

interface Trend {
  latency_direction: string
  latency_slope_ms_per_hour?: number
  latency_r_squared?: number
  availability_direction: string
  availability_delta_pct?: number
}

interface ServiceSummary {
  service_id: number
  service_name: string
  service_type?: string
  current_status?: string
  status?: string
  availability_pct?: number
  risk_score: RiskScore | null
  trend?: Trend
  anomaly_count?: number
  failure_pattern?: string
  top_recommendation?: { title: string; severity: string; action: string; category: string } | null
}

interface AISummary {
  summary: {
    total_services: number
    healthy: number
    warning: number
    critical: number
    insufficient_data: number
    avg_risk_score: number
    overall_health: string
    total_recommendations: number
    critical_recommendations: number
    warning_recommendations: number
  }
  services: ServiceSummary[]
  analyzed_at: string
}

interface Latency {
  mean_ms: number
  median_ms: number
  p95_ms: number
  p99_ms: number
  min_ms: number
  max_ms: number
  std_ms: number
  cv_pct: number
  sample_count: number
}

interface Anomaly {
  timestamp: string
  value_ms: number
  z_score: number
  direction: string
  severity: string
}

interface FailurePatterns {
  total_failures: number
  failure_rate_pct?: number
  burst_count?: number
  max_consecutive_failures?: number
  pattern?: string
  currently_failing?: boolean
}

interface Prediction {
  latency_72h_ms?: number
  latency_trend_confidence?: number
  failure_probability_next_hour_pct: number
  availability_forecast_24h_pct?: number
  ssl_monitoring?: boolean
}

interface Recommendation {
  priority: number
  category: string
  severity: string
  title: string
  description: string
  action: string
}

interface ServiceInsight {
  service_id: number
  service_name: string
  service_type: string
  current_status: string
  period_hours: number
  total_checks: number
  availability_pct: number
  latency: Latency
  trend: Trend
  anomalies: { count: number; details: Anomaly[] }
  failure_patterns: FailurePatterns
  predictions: Prediction
  recommendations: Recommendation[]
  risk_score: RiskScore
  analyzed_at: string
}

const RISK_COLORS: Record<string, { bg: string; text: string; ring: string }> = {
  low:      { bg: 'bg-emerald-500/10', text: 'text-emerald-400', ring: 'ring-emerald-500/30' },
  moderate: { bg: 'bg-yellow-500/10',  text: 'text-yellow-400',  ring: 'ring-yellow-500/30' },
  high:     { bg: 'bg-orange-500/10',  text: 'text-orange-400',  ring: 'ring-orange-500/30' },
  critical: { bg: 'bg-red-500/10',     text: 'text-red-400',     ring: 'ring-red-500/30' },
}



function TrendIcon({ direction }: { direction: string }) {
  if (direction === 'increasing' || direction === 'degrading')
    return <TrendingUp size={14} className="text-red-400" />
  if (direction === 'decreasing' || direction === 'improving')
    return <TrendingDown size={14} className="text-emerald-400" />
  return <Minus size={14} className="text-gray-400" />
}

function RiskGauge({ risk }: { risk: RiskScore }) {
  const c = RISK_COLORS[risk.level] || RISK_COLORS.low
  const pct = risk.score
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            risk.level === 'low' ? 'bg-emerald-500' :
            risk.level === 'moderate' ? 'bg-yellow-500' :
            risk.level === 'high' ? 'bg-orange-500' : 'bg-red-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-sm font-bold ${c.text} min-w-[3rem] text-right`}>{pct}/100</span>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const cls =
    severity === 'critical' ? 'bg-red-500/20 text-red-400' :
    severity === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
    'bg-blue-500/20 text-blue-400'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {severity.toUpperCase()}
    </span>
  )
}

export function AIInsightsPage() {
  const token = useAuthStore(s => s.token)
  const [summary, setSummary] = useState<AISummary | null>(null)
  const [detail, setDetail] = useState<ServiceInsight | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [hours, setHours] = useState(24)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => { document.title = 'Rhinometric - AI Insights' }, [])

  const fetchSummary = async () => {
    if (!token) return
    setLoading(true)
    try {
      const res = await fetch(`/api/external-services/ai/summary?hours=${hours}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) setSummary(await res.json())
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const fetchDetail = async (serviceId: number) => {
    if (!token) return
    if (expandedId === serviceId) { setExpandedId(null); setDetail(null); return }
    setExpandedId(serviceId)
    setDetailLoading(true)
    try {
      const res = await fetch(`/api/external-services/${serviceId}/ai-insights?hours=${hours}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) setDetail(await res.json())
    } catch (e) { console.error(e) }
    setDetailLoading(false)
  }

  const refresh = async () => { setRefreshing(true); await fetchSummary(); setRefreshing(false) }

  useEffect(() => { fetchSummary() }, [token, hours])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4" />
        <p className="text-gray-400">Analyzing services with AI...</p>
      </div>
    )
  }

  if (!summary || !summary.summary) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <Brain className="text-gray-600 mb-4" size={48} />
        <p className="text-white text-lg font-semibold mb-1">No Services to Analyze</p>
        <p className="text-gray-400 text-sm">Add external services to get AI-powered insights</p>
      </div>
    )
  }

  const s = summary.summary

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">AI Insights</h1>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30">
              <Brain size={12} className="mr-1.5" /> Powered by Statistical AI
            </span>
          </div>
          <p className="text-text-muted text-sm">Intelligent analysis of external service health, trends, and predictions</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={hours}
            onChange={e => setHours(Number(e.target.value))}
            className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
          >
            <option value={6}>Last 6h</option>
            <option value={24}>Last 24h</option>
            <option value={72}>Last 3d</option>
            <option value={168}>Last 7d</option>
            <option value={720}>Last 30d</option>
          </select>
          <button onClick={refresh} className="btn flex items-center gap-2 text-sm">
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="card p-4 text-center">
          <div className="text-3xl font-bold text-white">{s.total_services}</div>
          <div className="text-xs text-gray-400 mt-1">Services Monitored</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-3xl font-bold text-emerald-400">{s.healthy}</div>
          <div className="text-xs text-gray-400 mt-1">Healthy</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-3xl font-bold text-yellow-400">{s.warning}</div>
          <div className="text-xs text-gray-400 mt-1">Warning</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-3xl font-bold text-red-400">{s.critical}</div>
          <div className="text-xs text-gray-400 mt-1">Critical</div>
        </div>
        <div className="card p-4 text-center">
          <div className={`text-3xl font-bold ${
            s.avg_risk_score <= 20 ? 'text-emerald-400' :
            s.avg_risk_score <= 45 ? 'text-yellow-400' :
            s.avg_risk_score <= 70 ? 'text-orange-400' : 'text-red-400'
          }`}>{s.avg_risk_score}</div>
          <div className="text-xs text-gray-400 mt-1">Avg Risk Score</div>
        </div>
      </div>

      {/* Overall Health + Recommendations Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className={`card p-4 border-l-4 ${
          s.overall_health === 'healthy' ? 'border-emerald-500' :
          s.overall_health === 'warning' ? 'border-yellow-500' : 'border-red-500'
        }`}>
          <div className="flex items-center gap-3 mb-2">
            <Shield size={20} className={
              s.overall_health === 'healthy' ? 'text-emerald-400' :
              s.overall_health === 'warning' ? 'text-yellow-400' : 'text-red-400'
            } />
            <span className="text-white font-semibold">Overall Health</span>
          </div>
          <p className={`text-2xl font-bold capitalize ${
            s.overall_health === 'healthy' ? 'text-emerald-400' :
            s.overall_health === 'warning' ? 'text-yellow-400' : 'text-red-400'
          }`}>{s.overall_health}</p>
          <p className="text-xs text-gray-400 mt-1">Based on analysis of {s.total_services} services over {hours}h</p>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3 mb-2">
            <Lightbulb size={20} className="text-purple-400" />
            <span className="text-white font-semibold">AI Recommendations</span>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{s.critical_recommendations}</div>
              <div className="text-xs text-gray-400">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{s.warning_recommendations}</div>
              <div className="text-xs text-gray-400">Warning</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{s.total_recommendations}</div>
              <div className="text-xs text-gray-400">Total</div>
            </div>
          </div>
        </div>
      </div>

      {/* Services List */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Activity size={18} /> Service Analysis
        </h2>

        {summary.services.map(svc => (
          <div key={svc.service_id} className="card overflow-hidden">
            {/* Service Row */}
            <button
              onClick={() => fetchDetail(svc.service_id)}
              className="w-full p-4 flex items-center gap-4 hover:bg-surface-light transition-colors text-left"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    svc.current_status === 'up' ? 'bg-emerald-400' :
                    svc.current_status === 'down' ? 'bg-red-400' :
                    svc.current_status === 'degraded' ? 'bg-yellow-400' : 'bg-gray-400'
                  }`} />
                  <span className="text-white font-medium truncate">{svc.service_name}</span>
                  {svc.service_type && (
                    <span className="text-xs text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">{svc.service_type}</span>
                  )}
                </div>
                {svc.status === 'insufficient_data' ? (
                  <span className="text-xs text-gray-500">Insufficient data for analysis</span>
                ) : (
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    <span>Avail: <span className="text-white">{svc.availability_pct?.toFixed(1)}%</span></span>
                    {svc.trend && (
                      <span className="flex items-center gap-1">
                        Latency: <TrendIcon direction={svc.trend.latency_direction} />
                        <span className="text-white capitalize">{svc.trend.latency_direction}</span>
                      </span>
                    )}
                    {(svc.anomaly_count ?? 0) > 0 && (
                      <span className="text-yellow-400">{svc.anomaly_count} anomalies</span>
                    )}
                  </div>
                )}
              </div>

              {/* Risk Score Badge */}
              {svc.risk_score && (
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${RISK_COLORS[svc.risk_score.level]?.bg || 'bg-gray-700'}`}>
                  <span className={`text-sm font-bold ${RISK_COLORS[svc.risk_score.level]?.text || 'text-gray-400'}`}>
                    {svc.risk_score.score}
                  </span>
                  <span className={`text-xs ${RISK_COLORS[svc.risk_score.level]?.text || 'text-gray-400'}`}>
                    {svc.risk_score.label}
                  </span>
                </div>
              )}

              {expandedId === svc.service_id ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
            </button>

            {/* Expanded Detail */}
            {expandedId === svc.service_id && (
              <div className="border-t border-gray-700 p-4">
                {detailLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                  </div>
                ) : detail ? (
                  <div className="space-y-4">
                    {/* Risk Gauge */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Risk Score</span>
                        <span className={`text-sm font-semibold ${RISK_COLORS[detail.risk_score.level]?.text}`}>{detail.risk_score.label}</span>
                      </div>
                      <RiskGauge risk={detail.risk_score} />
                      {detail.risk_score.factors.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {detail.risk_score.factors.map((f, i) => (
                            <span key={i} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">{f}</span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      <div className="bg-surface-light rounded-lg p-3">
                        <div className="text-xs text-gray-400 mb-1">Availability</div>
                        <div className="text-xl font-bold text-white">{detail.availability_pct.toFixed(1)}%</div>
                        <div className="text-xs text-gray-500 mt-1">{detail.total_checks} checks</div>
                      </div>
                      <div className="bg-surface-light rounded-lg p-3">
                        <div className="text-xs text-gray-400 mb-1">Avg Latency</div>
                        <div className="text-xl font-bold text-white">{detail.latency?.mean_ms?.toFixed(0) || '-'}ms</div>
                        <div className="text-xs text-gray-500 mt-1">P95: {detail.latency?.p95_ms?.toFixed(0) || '-'}ms</div>
                      </div>
                      <div className="bg-surface-light rounded-lg p-3">
                        <div className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                          Latency Trend <TrendIcon direction={detail.trend.latency_direction} />
                        </div>
                        <div className="text-xl font-bold text-white capitalize">{detail.trend.latency_direction}</div>
                        {detail.trend.latency_slope_ms_per_hour !== undefined && (
                          <div className="text-xs text-gray-500 mt-1">{detail.trend.latency_slope_ms_per_hour > 0 ? '+' : ''}{detail.trend.latency_slope_ms_per_hour.toFixed(2)} ms/h</div>
                        )}
                      </div>
                      <div className="bg-surface-light rounded-lg p-3">
                        <div className="text-xs text-gray-400 mb-1">Failure Pattern</div>
                        <div className="text-xl font-bold text-white capitalize">{(detail.failure_patterns.pattern || 'none').replace(/_/g, ' ')}</div>
                        <div className="text-xs text-gray-500 mt-1">{detail.failure_patterns.total_failures} failures</div>
                      </div>
                    </div>

                    {/* Predictions */}
                    {detail.predictions && (
                      <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-4">
                        <h4 className="text-sm font-semibold text-purple-400 flex items-center gap-2 mb-3">
                          <Zap size={14} /> AI Predictions
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                          <div>
                            <span className="text-gray-400">Failure probability (1h):</span>
                            <span className={`ml-2 font-semibold ${
                              detail.predictions.failure_probability_next_hour_pct > 50 ? 'text-red-400' :
                              detail.predictions.failure_probability_next_hour_pct > 20 ? 'text-yellow-400' : 'text-emerald-400'
                            }`}>
                              {detail.predictions.failure_probability_next_hour_pct}%
                            </span>
                          </div>
                          {detail.predictions.latency_72h_ms !== undefined && (
                            <div>
                              <span className="text-gray-400">Latency in 72h:</span>
                              <span className="ml-2 font-semibold text-white">{detail.predictions.latency_72h_ms.toFixed(0)}ms</span>
                              {detail.predictions.latency_trend_confidence !== undefined && (
                                <span className="text-xs text-gray-500 ml-1">({(detail.predictions.latency_trend_confidence * 100).toFixed(0)}% conf)</span>
                              )}
                            </div>
                          )}
                          {detail.predictions.availability_forecast_24h_pct !== undefined && (
                            <div>
                              <span className="text-gray-400">Availability forecast:</span>
                              <span className="ml-2 font-semibold text-white">{detail.predictions.availability_forecast_24h_pct.toFixed(1)}%</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Anomalies */}
                    {detail.anomalies.count > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-white flex items-center gap-2 mb-2">
                          <AlertTriangle size={14} className="text-yellow-400" />
                          Latency Anomalies ({detail.anomalies.count})
                        </h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-700">
                                <th className="text-left px-3 py-2 text-xs text-gray-400">Time</th>
                                <th className="text-right px-3 py-2 text-xs text-gray-400">Value</th>
                                <th className="text-right px-3 py-2 text-xs text-gray-400">Z-Score</th>
                                <th className="text-center px-3 py-2 text-xs text-gray-400">Severity</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail.anomalies.details.map((a, i) => (
                                <tr key={i} className="border-b border-gray-700/50">
                                  <td className="px-3 py-2 text-xs text-gray-300">{new Date(a.timestamp).toLocaleString()}</td>
                                  <td className="px-3 py-2 text-right text-white">{a.value_ms.toFixed(0)}ms</td>
                                  <td className="px-3 py-2 text-right text-yellow-400">{a.z_score.toFixed(1)}</td>
                                  <td className="px-3 py-2 text-center"><SeverityBadge severity={a.severity} /></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {detail.recommendations.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-white flex items-center gap-2 mb-2">
                          <Lightbulb size={14} className="text-purple-400" /> Recommendations
                        </h4>
                        <div className="space-y-2">
                          {detail.recommendations.map((r, i) => (
                            <div key={i} className={`rounded-lg p-3 border ${
                              r.severity === 'critical' ? 'bg-red-500/5 border-red-500/20' :
                              r.severity === 'warning' ? 'bg-yellow-500/5 border-yellow-500/20' :
                              'bg-blue-500/5 border-blue-500/20'
                            }`}>
                              <div className="flex items-center gap-2 mb-1">
                                <SeverityBadge severity={r.severity} />
                                <span className="text-sm font-medium text-white">{r.title}</span>
                              </div>
                              <p className="text-xs text-gray-400 mb-1">{r.description}</p>
                              <p className="text-xs text-gray-300 flex items-center gap-1">
                                <ArrowRight size={10} /> {r.action}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 text-center">
        Last analyzed: {new Date(summary.analyzed_at).toLocaleString()} | Analysis period: {hours}h | No external AI service required
      </div>
    </div>
  )
}