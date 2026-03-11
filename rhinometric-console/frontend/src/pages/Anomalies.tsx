import { AlertTriangle, TrendingUp, Filter, Download, X, GitMerge, Globe, CheckCircle2, BarChart3, FileText, Server, Monitor } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'
import { buildDynamicPromQL, buildDynamicLogQL } from '../utils/externalLinks'

interface Anomaly {
  id: string
  timestamp: string
  entity_type: string
  entity_name: string
  source: string
  metric_name: string
  severity: string
  current_value: number
  expected_value: number
  deviation_percent: number
  status: string
  confidence: number | null
  analysis: string | null
  tags: string[] | null
  metadata: Record<string, any> | null
}

// Entity type badge component
function EntityBadge({ entityType, entityName }: { entityType: string; entityName: string }) {
  const config: Record<string, { icon: typeof Globe; color: string; label: string }> = {
    service: { icon: Globe, color: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/30', label: 'Service' },
    infrastructure: { icon: Server, color: 'text-orange-400 bg-orange-400/10 border-orange-400/30', label: 'Infra' },
    website: { icon: Monitor, color: 'text-green-400 bg-green-400/10 border-green-400/30', label: 'Website' },
  }
  const c = config[entityType] || config.infrastructure
  const Icon = c.icon
  return (
    <div className="space-y-0.5">
      <div className="flex items-center gap-1.5">
        <Icon size={12} className={c.color.split(' ')[0]} />
        <span className={`text-xs font-medium ${c.color.split(' ')[0]} truncate max-w-[160px]`} title={entityName}>{entityName}</span>
      </div>
      <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium border ${c.color}`}>
        {c.label}
      </span>
    </div>
  )
}

export function AnomaliesPage() {
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null)
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('')
  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const navigate = useNavigate()

  useEffect(() => {
    document.title = 'Rhinometric - AI Anomaly Detection'
  }, [])

  // Fetch real anomalies from backend
  const { data: anomaliesData, isLoading, error } = useQuery({
    queryKey: ['anomalies', token, entityTypeFilter],
    queryFn: async () => {
      if (!token) throw new Error('No token')

      const params = new URLSearchParams({ page_size: '50' })
      if (entityTypeFilter) params.set('entity_type', entityTypeFilter)

      const response = await fetch(`/api/anomalies?${params.toString()}`, {
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2 sm:mb-6">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">AI Anomaly Detection</h1>
            <span className="inline-flex items-center self-start px-3 py-1 rounded-full text-xs font-medium bg-warning/10 text-warning border border-warning/30" title="This feature uses experimental AI algorithms. Alerting is disabled by default. Enable in Settings if needed.">
              <span className="mr-1.5">&#x26A0;&#xFE0F;</span>
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

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <Filter size={18} className="text-gray-400 flex-shrink-0" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Entity:</span>
            <select
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
              value={entityTypeFilter}
              onChange={(e) => setEntityTypeFilter(e.target.value)}
            >
              <option value="">All Entities</option>
              <option value="service">Services</option>
              <option value="infrastructure">Infrastructure</option>
              <option value="website">Website</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Severity:</span>
            <select className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm">
              <option>All Severities</option>
              <option>Critical</option>
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
            <p className="text-gray-400 text-sm">AI engine is monitoring &mdash; all metrics within expected ranges</p>
          </div>
        ) : (
          <>
            {/* Desktop table view */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Time</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Entity</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Metric</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Severity</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Deviation</th>
                    <th className="text-right px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Current / Expected</th>
                    <th className="text-left px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Source</th>
                    <th className="text-center px-4 py-3 text-sm font-semibold text-gray-400 whitespace-nowrap">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {anomalies.map((anomaly: Anomaly) => (
                    <tr key={anomaly.id} className="border-b border-gray-700/50 hover:bg-surface-light cursor-pointer transition-colors" onClick={() => setSelectedAnomaly(anomaly)}>
                      <td className="px-4 py-3 text-xs text-gray-300 whitespace-nowrap">
                        {new Date(anomaly.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3">
                        <EntityBadge entityType={anomaly.entity_type} entityName={anomaly.entity_name} />
                      </td>
                      <td className="px-4 py-3">
                        <code className="text-xs text-primary bg-primary/10 px-2 py-1 rounded block truncate max-w-[180px]" title={anomaly.metric_name}>
                          {anomaly.metric_name}
                        </code>
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
                        <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-0.5 rounded">
                          {anomaly.source}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${anomaly.timestamp}?entity_type=${encodeURIComponent(anomaly.entity_type)}&entity_name=${encodeURIComponent(anomaly.entity_name)}&metric_name=${encodeURIComponent(anomaly.metric_name)}&source=${encodeURIComponent(anomaly.source)}`) }}
                            className="text-purple-400 hover:bg-purple-500/10 text-xs font-medium px-3 py-1 rounded transition-colors flex items-center gap-1"
                            title="Full correlation analysis with metrics and logs"
                          >
                            <GitMerge size={14} />
                            Correlate
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
              {anomalies.map((anomaly: Anomaly) => (
                <div
                  key={anomaly.id}
                  className="p-3 sm:p-4 hover:bg-surface-light cursor-pointer transition-colors active:bg-surface-light"
                  onClick={() => setSelectedAnomaly(anomaly)}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <EntityBadge entityType={anomaly.entity_type} entityName={anomaly.entity_name} />
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                      anomaly.severity === 'critical' || anomaly.severity === 'high' ? 'bg-error/20 text-error' :
                      anomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {anomaly.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <code className="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded truncate">{anomaly.metric_name}</code>
                    <span className="text-[10px] text-gray-500 bg-gray-700/50 px-1.5 py-0.5 rounded flex-shrink-0">{anomaly.source}</span>
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
                      onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${anomaly.timestamp}?entity_type=${encodeURIComponent(anomaly.entity_type)}&entity_name=${encodeURIComponent(anomaly.entity_name)}&metric_name=${encodeURIComponent(anomaly.metric_name)}&source=${encodeURIComponent(anomaly.source)}`) }}
                      className="text-purple-400 text-xs font-medium flex items-center gap-1"
                    >
                      <GitMerge size={12} />
                      Correlate
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
            {/* Header */}
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-3 sm:p-4 border-b border-gray-700">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-white truncate">Anomaly Details</h2>
                <p className="text-xs text-gray-400 truncate">{selectedAnomaly.id} &middot; {selectedAnomaly.timestamp}</p>
              </div>
              <button
                onClick={() => setSelectedAnomaly(null)}
                className="p-2 bg-error/20 hover:bg-error/30 rounded-lg transition-colors flex-shrink-0"
                title="Close"
              >
                <X className="text-white" size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {/* Entity & Source badge row */}
              <div className="flex items-center gap-3 flex-wrap">
                <EntityBadge entityType={selectedAnomaly.entity_type} entityName={selectedAnomaly.entity_name} />
                <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-1 rounded">Source: {selectedAnomaly.source}</span>
                <span className={`text-xs px-2 py-1 rounded ${selectedAnomaly.status === 'active' ? 'bg-error/20 text-error' : 'bg-green-500/20 text-green-400'}`}>
                  {selectedAnomaly.status.toUpperCase()}
                </span>
              </div>

              {/* Overview grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Metric</p>
                  <code className="text-sm text-primary font-mono break-all">{selectedAnomaly.metric_name}</code>
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
                    {selectedAnomaly.confidence != null ? `${(selectedAnomaly.confidence * 100).toFixed(0)}%` : 'N/A'}
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
                {selectedAnomaly.analysis ? (
                  <p className="text-xs sm:text-sm text-gray-300 mb-3">{selectedAnomaly.analysis}</p>
                ) : (
                  <p className="text-xs sm:text-sm text-gray-300 mb-3">
                    The anomaly detection algorithm identified this deviation based on historical patterns
                    and statistical analysis over the last 24 hours.
                  </p>
                )}
                {selectedAnomaly.tags && selectedAnomaly.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {selectedAnomaly.tags.map((tag, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400">{tag}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Grafana Actions */}
              {isAdmin() && <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Grafana</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    className={`btn flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2${!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown') ? ' opacity-50 cursor-not-allowed' : ''}`}
                    disabled={!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown')}
                    title={selectedAnomaly.metric_name && !selectedAnomaly.metric_name.includes('unknown') ? 'Open metrics in Grafana' : 'No metrics available for this anomaly'}
                    onClick={() => {
                      const prometheusQuery = buildDynamicPromQL({
                        metric_name: selectedAnomaly.metric_name,
                        entity_type: selectedAnomaly.entity_type,
                        entity_name: selectedAnomaly.entity_name,
                        source: selectedAnomaly.source
                      })
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
                    className={`btn flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2${!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown') ? ' opacity-50 cursor-not-allowed' : ''}`}
                    disabled={!selectedAnomaly.metric_name || selectedAnomaly.metric_name.includes('unknown')}
                    title={selectedAnomaly.metric_name && !selectedAnomaly.metric_name.includes('unknown') ? 'Open logs in Grafana (Loki)' : 'No logs available for this anomaly'}
                    onClick={() => {
                      const logQuery = buildDynamicLogQL({
                        metric_name: selectedAnomaly.metric_name,
                        entity_type: selectedAnomaly.entity_type,
                        entity_name: selectedAnomaly.entity_name,
                        source: selectedAnomaly.source
                      })
                      const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                        datasource: 'loki',
                        queries: [{ refId: 'A', expr: logQuery }],
                        range: { from: 'now-6h', to: 'now' }
                      }))}`
                      openGrafanaExplore(exploreUrl)
                    }}
                  >
                    <FileText size={16} />
                    Logs
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
                        `CREATE ALERT FROM ANOMALY\n\n` +
                        `Entity: ${selectedAnomaly.entity_name} (${selectedAnomaly.entity_type})\n` +
                        `Metric: ${selectedAnomaly.metric_name}\n` +
                        `Source: ${selectedAnomaly.source}\n\n` +
                        `Backend: POST /api/alerts/create-from-anomaly\n` +
                        `Frontend: Confirmation modal with YAML rule preview\n\n` +
                        `EXAMPLE RULE:\n` +
                        `- alert: AnomalyDetected_${selectedAnomaly.metric_name}\n` +
                        `  expr: ${selectedAnomaly.metric_name} > ${selectedAnomaly.expected_value.toFixed(2)}\n` +
                        `  for: 5m\n` +
                        `  labels:\n` +
                        `    severity: ${selectedAnomaly.severity}\n` +
                        `    entity_type: ${selectedAnomaly.entity_type}\n` +
                        `    source: ai_anomaly_detection`
                      )
                    }}
                  >
                    Create Alert
                  </button>
                  <button
                    className="btn btn-secondary flex-1 min-h-[44px] text-sm flex items-center justify-center gap-2"
                    onClick={() => {
                      console.log('Marking as false positive:', selectedAnomaly.id)
                      alert(
                        `MARK AS FALSE POSITIVE\n\n` +
                        `Anomaly ID: ${selectedAnomaly.id}\n` +
                        `Entity: ${selectedAnomaly.entity_name} (${selectedAnomaly.entity_type})\n` +
                        `Metric: ${selectedAnomaly.metric_name}\n\n` +
                        `Backend: POST /api/anomalies/${selectedAnomaly.id}/mark-false-positive\n` +
                        `AI Engine: PUT /ml/feedback (update model)\n\n` +
                        `AI IMPACT:\n` +
                        `- Reduces confidence threshold for "${selectedAnomaly.metric_name}"\n` +
                        `- Learns normal patterns vs real outliers\n` +
                        `- Status changes from "active" to "false_positive"`
                      )
                    }}
                  >
                    False Positive
                  </button>
                </div>
              </div>

              {/* Note */}
              <div className="text-xs text-gray-500 text-center">
                Unified Anomaly Model v1.2 &mdash; All anomalies follow a consistent schema
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
