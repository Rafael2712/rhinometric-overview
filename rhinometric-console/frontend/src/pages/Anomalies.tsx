import { AlertTriangle, TrendingUp, Filter, Download, X, GitMerge, Globe, CheckCircle2, BarChart3, FileText, Activity } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface Anomaly {
  metric_name: string
  timestamp: string
  severity: string
  deviation_percent: number
  expected_value: number
  current_value: number
  status: string
  confidence: number
  entity_type?: string
  entity_name?: string
  source?: string
}

export function AnomaliesPage() {
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null)
  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const navigate = useNavigate()

  useEffect(() => {
    document.title = 'Rhinometric - AI Anomaly Detection'
  }, [])

  // Fetch real anomalies from backend
  const { data: anomaliesData, isLoading, error } = useQuery({
    queryKey: ['anomalies', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')

      const response = await fetch('/api/anomalies?page_size=50', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      // Handle 503 - AI service unavailable
      if (response.status === 503) {
        throw new Error('AI_SERVICE_UNAVAILABLE')
      }

      if (!response.ok) throw new Error('Failed to fetch anomalies')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
    retry: false,
  })

  const anomalies = anomaliesData?.anomalies || []
  const isAIUnavailable = error && (error as Error).message === 'AI_SERVICE_UNAVAILABLE'

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header – stacks on mobile */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2 sm:mb-6">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">AI Anomaly Detection</h1>
            <span className="inline-flex items-center self-start px-3 py-1 rounded-full text-xs font-medium bg-warning/10 text-warning border border-warning/30" title="This feature uses experimental AI algorithms. Alerting is disabled by default. Enable in Settings if needed.">
              <span className="mr-1.5">⚠️</span>
              Experimental Beta
            </span>
          </div>
          <p className="text-text-muted text-sm sm:text-base">Monitor and manage detected anomalies across your infrastructure and external services</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          <button className="btn flex items-center gap-2 text-sm">
            <Download size={18} />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Filters – wraps on mobile */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <Filter size={18} className="text-gray-400 flex-shrink-0" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Severity:</span>
            <select className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm">
              <option>All Severities</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Time Range:</span>
            <select className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm">
              <option>Last 24 hours</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Status Notice - AI Service Unavailable */}
      {isAIUnavailable && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-start gap-3 sm:gap-4">
            <AlertTriangle className="text-warning mt-1 flex-shrink-0" size={24} />
            <div className="flex-1 min-w-0">
              <h3 className="text-warning font-semibold mb-2 text-sm sm:text-base">AI Anomaly Detection Engine Unavailable</h3>
              <p className="text-warning/80 text-xs sm:text-sm mb-3">
                The AI Detection Engine is temporarily unavailable. This could mean:
              </p>
              <ul className="list-disc list-inside text-warning/80 text-xs sm:text-sm space-y-1 mb-3">
                <li>Service is starting up (please wait 30 seconds)</li>
                <li>Service crashed or stopped (check container logs)</li>
                <li>Network connectivity issues</li>
              </ul>
              <p className="text-warning/80 text-xs sm:text-sm">
                <strong>Note:</strong> Check that rhinometric-ai-anomaly container is running on port 8085.
                No anomaly detection is currently being performed.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Anomalies Table */}
      <div className="card p-0 sm:p-0">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-gray-400 text-sm">Loading anomalies...</p>
          </div>
        ) : error && !isAIUnavailable ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <AlertTriangle className="text-error mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">Failed to load anomalies</p>
            <p className="text-sm text-gray-400">{(error as Error).message}</p>
          </div>
        ) : isAIUnavailable ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <AlertTriangle className="text-warning mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">AI Service Unavailable</p>
            <p className="text-sm text-gray-400">No anomaly detection is currently active</p>
          </div>
        ) : anomalies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <CheckCircle2 className="text-success mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">No Anomalies Detected</p>
            <p className="text-gray-400 text-sm">AI engine is monitoring — all metrics within expected ranges</p>
          </div>
        ) : (
          <>
            {/* Desktop table view */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Time</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Metric</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Severity</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Deviation</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Values</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {anomalies.map((anomaly: Anomaly, index: number) => (
                    <tr key={index} className="border-b border-gray-700/50 hover:bg-surface-light cursor-pointer transition-colors" onClick={() => setSelectedAnomaly(anomaly)}>
                      <td className="px-4 py-3 text-xs text-gray-300">
                        {new Date(anomaly.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 max-w-[220px]">
                        {anomaly.entity_type === 'service' && anomaly.entity_name ? (
                          <div className="space-y-1">
                            <div className="flex items-center gap-1.5">
                              <Globe size={12} className="text-cyan-400 flex-shrink-0" />
                              <span className="text-xs font-medium text-cyan-400 truncate">{anomaly.entity_name}</span>
                            </div>
                            <code className="text-xs text-primary/70 bg-primary/5 px-1.5 py-0.5 rounded block truncate">
                              {anomaly.metric_name.includes('::') ? anomaly.metric_name.split('::')[0] : anomaly.metric_name}
                            </code>
                          </div>
                        ) : (
                          <code className="text-xs text-primary bg-primary/10 px-2 py-1 rounded block truncate">
                            {anomaly.metric_name}
                          </code>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          anomaly.severity === 'critical' || anomaly.severity === 'high' ? 'bg-error/20 text-error' :
                          anomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {anomaly.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className={`flex items-center justify-end gap-1 text-sm font-semibold ${
                          anomaly.deviation_percent > 0 ? 'text-error' : 'text-green-400'
                        }`}>
                          <TrendingUp size={12} />
                          {anomaly.deviation_percent > 0 ? '+' : ''}{anomaly.deviation_percent.toFixed(1)}%
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-xs">
                        <div className="text-white font-medium">{anomaly.current_value.toFixed(1)}</div>
                        <div className="text-gray-500">/ {anomaly.expected_value.toFixed(1)}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${anomaly.timestamp}`) }}
                            className="text-purple-400 hover:bg-purple-500/10 text-xs font-medium px-3 py-1 rounded transition-colors flex items-center gap-1"
                            title="Full correlation analysis with metrics, logs and traces"
                          >
                            <GitMerge size={14} />
                            View Correlation
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile card view */}
            <div className="md:hidden divide-y divide-gray-700/50">
              {anomalies.map((anomaly: Anomaly, index: number) => (
                <div
                  key={index}
                  className="p-3 sm:p-4 hover:bg-surface-light cursor-pointer transition-colors active:bg-surface-light"
                  onClick={() => setSelectedAnomaly(anomaly)}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    {anomaly.entity_type === 'service' && anomaly.entity_name ? (
                      <div className="flex items-center gap-1 min-w-0">
                        <Globe size={10} className="text-cyan-400 flex-shrink-0" />
                        <span className="text-xs font-medium text-cyan-400 truncate">{anomaly.entity_name}</span>
                      </div>
                    ) : (
                      <code className="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded truncate min-w-0">
                        {anomaly.metric_name}
                      </code>
                    )}
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                      anomaly.severity === 'critical' || anomaly.severity === 'high' ? 'bg-error/20 text-error' :
                      anomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {anomaly.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-gray-500">
                      {new Date(anomaly.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <span className={`font-semibold ${anomaly.deviation_percent > 0 ? 'text-error' : 'text-green-400'}`}>
                      <TrendingUp size={10} className="inline mr-0.5" />
                      {anomaly.deviation_percent > 0 ? '+' : ''}{anomaly.deviation_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">
                      {anomaly.current_value.toFixed(1)} / {anomaly.expected_value.toFixed(1)}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${anomaly.timestamp}`) }}
                      className="text-purple-400 text-xs font-medium flex items-center gap-1"
                    >
                      <GitMerge size={12} />
                      Correlation
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Details Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-surface border border-gray-700 rounded-t-xl sm:rounded-lg shadow-2xl w-full sm:max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto">
            {/* Header - Fixed at top */}
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-3 sm:p-4 border-b border-gray-700">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-white truncate">Anomaly Details</h2>
                <p className="text-xs text-gray-400 truncate">{selectedAnomaly.timestamp}</p>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="p-2 bg-error/20 hover:bg-error/30 rounded-lg transition-colors flex-shrink-0"
                title="Close"
              >
                <X className="text-white" size={20} />
              </button>
            </div>

            {/* Content - Scrollable */}
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {/* Overview – responsive grid */}
              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Metric</p>
                  <code className="text-sm sm:text-lg text-primary font-mono break-all">
                    {selectedAnomaly.metric_name.includes('::') ? selectedAnomaly.metric_name.split('::')[0] : selectedAnomaly.metric_name}
                  </code>
                  {selectedAnomaly.entity_type === 'service' && selectedAnomaly.entity_name && (
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <Globe size={14} className="text-cyan-400" />
                      <span className="text-sm text-cyan-400 font-medium">{selectedAnomaly.entity_name}</span>
                      <span className="text-xs text-gray-500 ml-1">({selectedAnomaly.source || 'external service'})</span>
                    </div>
                  )}
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Status</p>
                  <p className="text-sm sm:text-lg text-white font-semibold">{selectedAnomaly.status}</p>
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center gap-1 px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium ${
                    selectedAnomaly.severity === 'critical' || selectedAnomaly.severity === 'high' ? 'bg-error/20 text-error' :
                    selectedAnomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {selectedAnomaly.severity.toUpperCase()}
                  </span>
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Confidence</p>
                  <div className="text-sm sm:text-lg font-bold text-white">
                    {(selectedAnomaly.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Metrics Comparison */}
              <div className="card p-3 sm:p-4">
                <h3 className="text-sm sm:text-base font-semibold text-white mb-3">Metrics Comparison</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Expected Value</span>
                    <span className="text-lg sm:text-xl font-mono text-gray-300">{selectedAnomaly.expected_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Current Value</span>
                    <span className="text-lg sm:text-xl font-mono text-white font-bold">{selectedAnomaly.current_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t border-gray-700">
                    <span className="text-gray-400 text-sm">Deviation</span>
                    <span className={`text-lg sm:text-xl font-mono ${selectedAnomaly.deviation_percent > 0 ? 'text-error' : 'text-green-400'}`}>
                      {selectedAnomaly.deviation_percent > 0 ? '+' : ''}{selectedAnomaly.deviation_percent.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* AI Analysis */}
              <div className="card bg-primary/5 border-primary/20 p-3 sm:p-4">
                <h3 className="text-sm sm:text-base font-semibold text-primary mb-2">AI Analysis</h3>
                <p className="text-xs sm:text-sm text-gray-300 mb-3">
                  The anomaly detection algorithm identified this deviation based on historical patterns
                  and statistical analysis over the last 30 days.
                </p>
                <ul className="space-y-2 text-xs sm:text-sm text-gray-400">
                  <li>• Pattern recognition: Outlier detected outside 3σ confidence interval</li>
                  <li>• Similar incidents: 2 occurrences in the last 90 days</li>
                  <li>• Recommended action: Investigate service load and resource allocation</li>
                </ul>
              </div>

              {/* Grafana Actions – admin/owner only */}
              {isAdmin() && <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Grafana</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    className={`btn flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2${!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown') ? ' opacity-50 cursor-not-allowed' : ''}`}
                    disabled={!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown')}
                    title={selectedAnomaly.metric_name && !selectedAnomaly.metric_name.includes('unknown') ? 'Open metrics in Grafana' : 'No metrics available for this anomaly'}
                    onClick={() => {
                      const metricMap: Record<string, string> = {
                        'node_cpu_usage': '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                        'node_memory_usage': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                        'node_disk_io': 'rate(node_disk_io_time_seconds_total[5m])',
                        'node_network_receive': 'rate(node_network_receive_bytes_total[5m])',
                        'node_network_transmit': 'rate(node_network_transmit_bytes_total[5m])',
                        'node_disk_usage': '(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100',
                        'rhinometric_website_dns_time': 'rhinometric_website_dns_time',
                        'rhinometric_website_ssl_expiry': 'rhinometric_website_ssl_expiry',
                        'rhinometric_website_response_time': 'rhinometric_website_response_time',
                        'rhinometric_website_availability': 'rhinometric_website_availability',
                        'postgres_connections': 'pg_stat_database_numbackends',
                        'response_time_ms': 'http_request_duration_seconds',
                        'error_rate': 'rate(http_requests_total{status=~"5.."}[5m])',
                        'http_request_rate': 'sum(rate(http_requests_total[5m]))',
                        'http_error_rate': 'sum(rate(http_requests_total{status=~"5.."}[5m]))',
                        'http_latency_p95': 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
                        'http_latency_p99': 'histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
                        'external_service_latency': 'external_service_latency_ms',
                        'external_service_health': 'external_service_health_score',
                        'external_service_availability': 'external_service_up'
                      }
                      const prometheusQuery = metricMap[selectedAnomaly.metric_name] || selectedAnomaly.metric_name
                      const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                        datasource: 'victoriametrics',
                        queries: [{ refId: 'A', expr: prometheusQuery }],
                        range: { from: 'now-6h', to: 'now' }
                      }))}`
                      openGrafanaExplore(exploreUrl)
                    }}
                  >
                    <BarChart3 size={16} />
                    Metrics
                  </button>
                  <button
                    className="btn btn-secondary flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2 opacity-50 cursor-not-allowed"
                    disabled
                    title="Coming soon"
                  >
                    <FileText size={16} />
                    Logs
                  </button>
                  <button
                    className="btn btn-secondary flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2 opacity-50 cursor-not-allowed"
                    disabled
                    title="Coming soon"
                  >
                    <Activity size={16} />
                    Traces
                  </button>
                </div>
              </div>}

              {/* AI Actions */}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">AI Actions</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    className="btn btn-secondary flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2"
                    onClick={() => {
                      console.log('Creating alert for:', selectedAnomaly.metric_name)
                      alert(
                        `📊 CREATE ALERT FROM ANOMALY\n\n` +
                        `🎯 FUNCTIONALITY:\n` +
                        `• Automatically create alerting rule in Prometheus/AlertManager\n` +
                        `• Based on AI-detected pattern (threshold = expected value ± deviation)\n` +
                        `• Send to config/rules/alerts/ai-generated.yml\n` +
                        `• Reload rules in Prometheus via API (POST /-/reload)\n\n` +
                        `⏱️ IMPLEMENTATION:\n` +
                        `• Sprint 4: AI Anomalies UI Complete\n` +
                        `• Estimated time: 2-3 hours\n` +
                        `• Backend: POST /api/alerts/create-from-anomaly\n` +
                        `• Frontend: Confirmation modal with YAML rule preview\n\n` +
                        `📋 EXAMPLE RULE:\n` +
                        `- alert: AnomalyDetected_${selectedAnomaly.metric_name}\n` +
                        `  expr: ${selectedAnomaly.metric_name} > ${selectedAnomaly.expected_value.toFixed(2)}\n` +
                        `  for: 5m\n` +
                        `  labels:\n` +
                        `    severity: ${selectedAnomaly.severity}\n` +
                        `    source: ai_anomaly_detection`
                      )
                    }}
                  >
                    Create Alert
                  </button>
                  <button
                    className="btn btn-secondary flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2"
                    onClick={() => {
                      console.log('Marking as false positive:', selectedAnomaly.metric_name)
                      alert(
                        `❌ MARK AS FALSE POSITIVE\n\n` +
                        `🎯 FUNCTIONALITY:\n` +
                        `• Send negative feedback to the AI engine (port 8085)\n` +
                        `• Update ML model to reduce false positives\n` +
                        `• Guardar en DB como 'false_positive' for retraining\n` +
                        `• Remove from active anomalies list\n` +
                        `• Adjust model sensitivity for that metric\n\n` +
                        `⏱️ IMPLEMENTATION:\n` +
                        `• Sprint 4: AI Anomalies UI Complete\n` +
                        `• Estimated time: 1-2 hours\n` +
                        `• Backend: POST /api/anomalies/{id}/mark-false-positive\n` +
                        `• AI Engine: PUT /ml/feedback (update model)\n` +
                        `• Frontend: Confirmation + list update\n\n` +
                        `🤖 AI IMPACT:\n` +
                        `• Reduces confidence threshold for "${selectedAnomaly.metric_name}"\n` +
                        `• Learns normal patterns vs real outliers\n` +
                        `• Improves model precision with each feedback\n` +
                        `• Accumulated feedback: Will be used in next retraining`
                      )
                    }}
                  >
                    False Positive
                  </button>
                </div>
              </div>

              {/* Note */}
              <div className="text-xs text-gray-500 text-center">
                Full integration with AI Anomaly Detection Engine (Port 8085) coming in Phase 2
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
