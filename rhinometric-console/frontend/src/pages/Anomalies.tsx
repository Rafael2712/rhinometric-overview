import { AlertTriangle, TrendingUp, Filter, Download, X } from 'lucide-react'
import { useEffect, useState } from 'react'

// Mock data for demo purposes
const mockAnomalies = [
  {
    id: 1,
    timestamp: '2024-11-24 14:23:45',
    metric: 'cpu_usage_percent',
    service: 'api-gateway',
    severity: 'high',
    deviation: '+47%',
    baseline: 32.5,
    current: 47.8
  },
  {
    id: 2,
    timestamp: '2024-11-24 14:18:12',
    metric: 'response_time_ms',
    service: 'database',
    severity: 'medium',
    deviation: '+23%',
    baseline: 145,
    current: 178
  },
  {
    id: 3,
    timestamp: '2024-11-24 13:56:33',
    metric: 'memory_usage_bytes',
    service: 'worker-pool',
    severity: 'low',
    deviation: '+12%',
    baseline: 2.1,
    current: 2.35
  }
]

export function AnomaliesPage() {
  const [selectedAnomaly, setSelectedAnomaly] = useState<typeof mockAnomalies[0] | null>(null)

  useEffect(() => {
    document.title = 'Rhinometric - AI Anomaly Detection'
  }, [])

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">AI Anomaly Detection</h1>
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

      {/* Status Notice */}
      <div className="card mb-6 bg-blue-500/10 border-blue-500/30">
        <div className="flex items-start gap-4">
          <AlertTriangle className="text-blue-400 mt-1" size={24} />
          <div className="flex-1">
            <h3 className="text-blue-300 font-semibold mb-2">Backend Integration: In Development</h3>
            <p className="text-blue-200/80 text-sm mb-3">
              This module will display real-time anomalies from the AI Detection Engine (Port 8085). 
              The table below shows sample data to demonstrate the final interface design.
            </p>
            <p className="text-blue-200/80 text-sm">
              <strong>Planned for Phase 2:</strong> Live anomaly stream, detailed drill-down, 
              Grafana dashboard links, and manual feedback loop for model training.
            </p>
          </div>
        </div>
      </div>

      {/* Anomalies Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-light">
              <tr className="border-b border-gray-700">
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-300">Timestamp</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-300">Metric</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-300">Service</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-gray-300">Severity</th>
                <th className="text-right px-6 py-4 text-sm font-semibold text-gray-300">Deviation</th>
                <th className="text-right px-6 py-4 text-sm font-semibold text-gray-300">Baseline</th>
                <th className="text-right px-6 py-4 text-sm font-semibold text-gray-300">Current</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody>
              {mockAnomalies.map((anomaly) => (
                <tr key={anomaly.id} className="border-b border-gray-700/50 hover:bg-surface-light/30 transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-300">{anomaly.timestamp}</td>
                  <td className="px-6 py-4">
                    <code className="text-sm text-primary bg-primary/10 px-2 py-1 rounded">
                      {anomaly.metric}
                    </code>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">{anomaly.service}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      anomaly.severity === 'high' ? 'bg-error/20 text-error' :
                      anomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {anomaly.severity.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1 text-error font-semibold">
                      <TrendingUp size={14} />
                      {anomaly.deviation}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right text-sm text-gray-400">{anomaly.baseline}</td>
                  <td className="px-6 py-4 text-right text-sm text-white font-medium">{anomaly.current}</td>
                  <td className="px-6 py-4 text-center">
                    <button 
                      onClick={() => setSelectedAnomaly(anomaly)}
                      className="text-primary hover:text-primary-dark text-sm font-medium hover:underline"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State (cuando no hay mock data) */}
        {mockAnomalies.length === 0 && (
          <div className="text-center py-16">
            <AlertTriangle className="mx-auto mb-4 text-gray-500" size={48} />
            <p className="text-gray-400">No anomalies detected in the selected time range</p>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-gray-700 rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Anomaly Details</h2>
                <p className="text-sm text-gray-400">{selectedAnomaly.timestamp}</p>
              </div>
              <button 
                onClick={() => setSelectedAnomaly(null)}
                className="p-2 hover:bg-surface-light rounded-lg transition-colors"
              >
                <X className="text-gray-400 hover:text-white" size={24} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Overview */}
              <div className="grid grid-cols-2 gap-4">
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Metric</p>
                  <code className="text-lg text-primary font-mono">{selectedAnomaly.metric}</code>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Service</p>
                  <p className="text-lg text-white font-semibold">{selectedAnomaly.service}</p>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
                    selectedAnomaly.severity === 'high' ? 'bg-error/20 text-error' :
                    selectedAnomaly.severity === 'medium' ? 'bg-warning/20 text-warning' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {selectedAnomaly.severity.toUpperCase()}
                  </span>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Deviation</p>
                  <div className="flex items-center gap-2 text-error text-lg font-bold">
                    <TrendingUp size={20} />
                    {selectedAnomaly.deviation}
                  </div>
                </div>
              </div>

              {/* Metrics Comparison */}
              <div className="card">
                <h3 className="text-lg font-semibold text-white mb-4">Metrics Comparison</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Baseline Value</span>
                    <span className="text-xl font-mono text-gray-300">{selectedAnomaly.baseline}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Current Value</span>
                    <span className="text-xl font-mono text-white font-bold">{selectedAnomaly.current}</span>
                  </div>
                  <div className="flex justify-between items-center pt-3 border-t border-gray-700">
                    <span className="text-gray-400">Absolute Change</span>
                    <span className="text-xl font-mono text-error">
                      +{(selectedAnomaly.current - selectedAnomaly.baseline).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* AI Analysis */}
              <div className="card bg-primary/5 border-primary/20">
                <h3 className="text-lg font-semibold text-primary mb-3">AI Analysis</h3>
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
                <button className="btn flex-1">
                  View in Grafana
                </button>
                <button className="btn btn-secondary flex-1">
                  Create Alert
                </button>
                <button className="btn btn-secondary flex-1">
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
