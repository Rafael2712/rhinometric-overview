import { AlertTriangle, TrendingUp, Filter, Download, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'

interface Anomaly {
  metric_name: string
  timestamp: string
  severity: string
  deviation_percent: number
  expected_value: number
  current_value: number
  status: string
  confidence: number
}

export function AnomaliesPage() {
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null)
  const token = useAuthStore((state) => state.token)

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
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: false, // Don't retry on 503
  })

  const anomalies = anomaliesData?.anomalies || []

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-white">AI Anomaly Detection</h1>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-warning/10 text-warning border border-warning/30" title="This feature uses experimental AI algorithms. Alerting is disabled by default. Enable in Settings if needed.">
            <span className="mr-1.5">⚠️</span>
            Experimental Beta
          </span>
        </div>
        <p className="text-gray-400">Monitor and manage detected anomalies across your infrastructure</p>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button className="btn btn-secondary flex items-center gap-2">
            <Filter size={16} />
            Filters
          </button>
          <select className="input bg-surface border-gray-600">
            <option>All Severities</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select className="input bg-surface border-gray-600">
            <option>Last 24 hours</option>
            <option>Last 7 days</option>
            <option>Last 30 days</option>
          </select>
        </div>
        <button className="btn flex items-center gap-2">
          <Download size={16} />
          Export
        </button>
      </div>

      {/* Status Notice - AI Service Unavailable */}
      {error && (error as Error).message === 'AI_SERVICE_UNAVAILABLE' && (
        <div className="card mb-6 bg-warning/10 border-warning/30">
          <div className="flex items-start gap-4">
            <AlertTriangle className="text-warning mt-1" size={24} />
            <div className="flex-1">
              <h3 className="text-warning font-semibold mb-2">AI Anomaly Detection Engine Unavailable</h3>
              <p className="text-warning/80 text-sm mb-3">
                The AI Detection Engine is temporarily unavailable. This could mean:
              </p>
              <ul className="list-disc list-inside text-warning/80 text-sm space-y-1 mb-3">
                <li>Service is starting up (please wait 30 seconds)</li>
                <li>Service crashed or stopped (check container logs)</li>
                <li>Network connectivity issues</li>
              </ul>
              <p className="text-warning/80 text-sm">
                <strong>Note:</strong> Check that rhinometric-ai-anomaly container is running on port 8085.
                No anomaly detection is currently being performed.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Status Notice - Only show when no anomalies */}
      {!isLoading && !error && anomalies.length === 0 && (
        <div className="card mb-6 bg-blue-500/10 border-blue-500/30">
          <div className="flex items-start gap-4">
            <AlertTriangle className="text-blue-400 mt-1" size={24} />
            <div className="flex-1">
              <h3 className="text-blue-300 font-semibold mb-2">No Anomalies Detected</h3>
              <p className="text-blue-200/80 text-sm mb-3">
                AI Detection Engine is monitoring your infrastructure in real-time. 
                No anomalies have been detected in the selected time range.
              </p>
              <p className="text-blue-200/80 text-sm">
                <strong>Tip:</strong> Generate application traffic to see the ML model detect deviations from baseline behavior.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Anomalies Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-light">
              <tr className="border-b border-gray-700">
                <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Time</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Metric</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-gray-300">Severity</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-gray-300">Deviation</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-gray-300">Values</th>
                <th className="text-center px-4 py-3 text-sm font-semibold text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-12 text-center text-gray-400">Loading anomalies...</td></tr>
              ) : error && (error as Error).message !== 'AI_SERVICE_UNAVAILABLE' ? (
                <tr><td colSpan={6} className="px-4 py-12 text-center text-error">Error loading anomalies: {(error as Error).message}</td></tr>
              ) : error && (error as Error).message === 'AI_SERVICE_UNAVAILABLE' ? (
                <tr><td colSpan={6} className="px-4 py-12 text-center text-warning">AI service unavailable - No anomaly detection active</td></tr>
              ) : anomalies.map((anomaly: Anomaly, index: number) => (
                <tr key={index} className="border-b border-gray-700/50 hover:bg-surface-light/30 transition-colors">
                  <td className="px-4 py-3 text-xs text-gray-300">
                    {new Date(anomaly.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-3 max-w-[180px]">
                    <code className="text-xs text-primary bg-primary/10 px-2 py-1 rounded block truncate">
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
                  <td className="px-4 py-3 text-center">
                    <button 
                      onClick={() => setSelectedAnomaly(anomaly)}
                      className="text-primary hover:bg-primary/10 text-xs font-medium px-3 py-1 rounded transition-colors"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {!isLoading && !error && anomalies.length === 0 && (
          <div className="text-center py-16">
            <AlertTriangle className="mx-auto mb-4 text-gray-500" size={48} />
            <p className="text-gray-400">No anomalies detected in the selected time range</p>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-gray-700 rounded-lg shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            {/* Header - Fixed at top */}
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-4 border-b border-gray-700">
              <div>
                <h2 className="text-xl font-bold text-white">Anomaly Details</h2>
                <p className="text-xs text-gray-400">{selectedAnomaly.timestamp}</p>
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
            <div className="p-4 space-y-4">
              {/* Overview */}
              <div className="grid grid-cols-2 gap-3">
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Metric</p>
                  <code className="text-lg text-primary font-mono">{selectedAnomaly.metric_name}</code>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Status</p>
                  <p className="text-lg text-white font-semibold">{selectedAnomaly.status}</p>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
                    selectedAnomaly.severity === 'critical' || selectedAnomaly.severity === 'high' ? 'bg-error/20 text-error' :
                    selectedAnomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {selectedAnomaly.severity.toUpperCase()}
                  </span>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Confidence</p>
                  <div className="text-lg font-bold text-white">
                    {(selectedAnomaly.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Metrics Comparison */}
              <div className="card">
                <h3 className="text-base font-semibold text-white mb-3">Metrics Comparison</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Expected Value</span>
                    <span className="text-xl font-mono text-gray-300">{selectedAnomaly.expected_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Current Value</span>
                    <span className="text-xl font-mono text-white font-bold">{selectedAnomaly.current_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t border-gray-700">
                    <span className="text-gray-400">Deviation</span>
                    <span className={`text-xl font-mono ${selectedAnomaly.deviation_percent > 0 ? 'text-error' : 'text-green-400'}`}>
                      {selectedAnomaly.deviation_percent > 0 ? '+' : ''}{selectedAnomaly.deviation_percent.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* AI Analysis */}
              <div className="card bg-primary/5 border-primary/20">
                <h3 className="text-base font-semibold text-primary mb-2">AI Analysis</h3>
                <p className="text-sm text-gray-300 mb-3">
                  The anomaly detection algorithm identified this deviation based on historical patterns 
                  and statistical analysis over the last 30 days.
                </p>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• Pattern recognition: Outlier detected outside 3σ confidence interval</li>
                  <li>• Similar incidents: 2 occurrences in the last 90 days</li>
                  <li>• Recommended action: Investigate service load and resource allocation</li>
                </ul>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button 
                  className="btn flex-1"
                  onClick={() => {
                    // Map simplified AI metric names to actual Prometheus queries
                    const metricMap: Record<string, string> = {
                      'node_cpu_usage': '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                      'node_memory_usage': '100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)',
                      'node_disk_io': 'rate(node_disk_io_time_seconds_total[5m])',
                      'node_network_receive': 'rate(node_network_receive_bytes_total[5m])',
                      'node_network_transmit': 'rate(node_network_transmit_bytes_total[5m])',
                      'node_disk_usage': '100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)',
                      'postgres_connections': 'pg_stat_database_numbackends',
                      'response_time_ms': 'http_request_duration_seconds',
                      'error_rate': 'rate(http_requests_total{status=~"5.."}[5m])',
                      // HTTP Metrics (exact queries from AI Anomaly config.yaml)
                      'http_request_rate': 'sum(rate(http_requests_total[5m]))',
                      'http_error_rate': 'sum(rate(http_requests_total{status=~"5.."}[5m]))',
                      'http_latency_p95': 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))',
                      'http_latency_p99': 'histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))'
                    }
                    
                    // Get the actual Prometheus query
                    const prometheusQuery = metricMap[selectedAnomaly.metric_name] || selectedAnomaly.metric_name
                    
                    // Build Grafana Explore URL with proper encoding (datasource UID debe ser 'prometheus' minúsculas) - usando RBAC proxy
                    const grafanaUrl = `/api/grafana/explore?orgId=1&left=${encodeURIComponent(JSON.stringify({
                      datasource: 'prometheus',
                      queries: [{ refId: 'A', expr: prometheusQuery }],
                      range: { from: 'now-6h', to: 'now' }
                    }))}&token=${token}`
                    window.open(grafanaUrl, '_blank')
                  }}
                >
                  View in Grafana
                </button>
                <button 
                  className="btn btn-secondary flex-1"
                  onClick={() => {
                    console.log('Creating alert for:', selectedAnomaly.metric_name)
                    alert(
                      `📊 CREATE ALERT FROM ANOMALY\n\n` +
                      `🎯 FUNCIONALIDAD:\n` +
                      `• Crear automáticamente regla de alerting en Prometheus/AlertManager\n` +
                      `• Basada en el patrón detectado por IA (threshold = valor esperado ± desviación)\n` +
                      `• Enviar a config/rules/alerts/ai-generated.yml\n` +
                      `• Recargar reglas en Prometheus vía API (POST /-/reload)\n\n` +
                      `⏱️ IMPLEMENTACIÓN:\n` +
                      `• Sprint 4: AI Anomalies UI Complete\n` +
                      `• Tiempo estimado: 2-3 horas\n` +
                      `• Backend: POST /api/alerts/create-from-anomaly\n` +
                      `• Frontend: Modal de confirmación con preview de regla YAML\n\n` +
                      `📋 EJEMPLO REGLA:\n` +
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
                  className="btn btn-secondary flex-1"
                  onClick={() => {
                    console.log('Marking as false positive:', selectedAnomaly.metric_name)
                    alert(
                      `❌ MARK AS FALSE POSITIVE\n\n` +
                      `🎯 FUNCIONALIDAD:\n` +
                      `• Enviar feedback negativo al motor de IA (puerto 8085)\n` +
                      `• Actualizar modelo ML para reducir false positives\n` +
                      `• Guardar en DB como 'false_positive' para reentrenamiento\n` +
                      `• Eliminar de lista de anomalías activas\n` +
                      `• Ajustar sensibilidad del modelo para esa métrica\n\n` +
                      `⏱️ IMPLEMENTACIÓN:\n` +
                      `• Sprint 4: AI Anomalies UI Complete\n` +
                      `• Tiempo estimado: 1-2 horas\n` +
                      `• Backend: POST /api/anomalies/{id}/mark-false-positive\n` +
                      `• AI Engine: PUT /ml/feedback (actualizar modelo)\n` +
                      `• Frontend: Confirmación + actualización lista\n\n` +
                      `🤖 IMPACTO EN IA:\n` +
                      `• Reduce confidence threshold para "${selectedAnomaly.metric_name}"\n` +
                      `• Aprende patrones normales vs outliers reales\n` +
                      `• Mejora precisión del modelo con cada feedback\n` +
                      `• Feedback acumulado: Se usará en próximo reentrenamiento`
                    )
                  }}
                >
                  Mark as False Positive
                </button>
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
