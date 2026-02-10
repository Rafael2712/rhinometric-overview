import { Bell, Filter, Download, Clock, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface Alert {
  fingerprint: string
  status: string // Backend returns string directly: 'active', 'suppressed', 'resolved'
  labels: {
    alertname: string
    severity: string
    instance?: string
    job?: string
    [key: string]: string | undefined
  }
  annotations: {
    summary?: string
    description?: string
    [key: string]: string | undefined
  }
  startsAt: string
  endsAt?: string
  generatorURL?: string
  severity: string
}

interface AlertsResponse {
  alerts: Alert[]
}

export function AlertsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Alerts'
  }, [])

  const token = useAuthStore((state) => state.token)
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)

  const { data: alertsData, isLoading, error } = useQuery({
    queryKey: ['alerts', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      
      const response = await fetch('/api/alerts', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) throw new Error('Failed to fetch alerts')
      return response.json() as Promise<AlertsResponse>
    },
    enabled: !!token,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Filter alerts
  const filteredAlerts = alertsData?.alerts?.filter(alert => {
    const severityMatch = severityFilter === 'all' || alert.severity === severityFilter
    const statusMatch = statusFilter === 'all' || alert.status === statusFilter
    return severityMatch && statusMatch
  }) || []

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-error/20 text-error'
      case 'warning': return 'bg-warning/20 text-warning'
      case 'info': return 'bg-blue-500/20 text-blue-400'
      default: return 'bg-gray-500/20 text-gray-400'
    }
  }

  const getStatusIcon = (state: string) => {
    const s = state?.toLowerCase() || ''
    if (s.includes('active') || s.includes('firing')) {
      return <AlertTriangle className="text-error" size={20} />
    } else if (s.includes('suppress') || s.includes('silence')) {
      return <XCircle className="text-warning" size={20} />
    } else if (s.includes('resolve')) {
      return <CheckCircle2 className="text-success" size={20} />
    }
    return <Bell className="text-gray-400" size={20} />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Alert Management</h1>
          <p className="text-text-muted">Monitor and manage system alerts from AlertManager</p>
        </div>
        <button className="btn btn-secondary flex items-center gap-2">
          <Download size={20} />
          Export
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <Filter size={20} className="text-gray-400" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All States</option>
              <option value="firing">Firing</option>
              <option value="active">Active</option>
              <option value="suppressed">Suppressed</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading alerts...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertTriangle className="text-error mx-auto mb-4" size={48} />
            <p className="text-error">Failed to load alerts</p>
            <p className="text-sm text-gray-400 mt-2">{(error as Error).message}</p>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle2 className="text-success mx-auto mb-4" size={48} />
            <p className="text-white text-lg font-semibold">No Alerts</p>
            <p className="text-gray-400 mt-2">All systems operational</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Alert</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Severity</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Instance</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Started</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((alert) => (
                  <tr 
                    key={alert.fingerprint}
                    className="border-b border-gray-700/50 hover:bg-surface-light cursor-pointer transition-colors"
                    onClick={() => setSelectedAlert(alert)}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(alert.status)}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-white font-medium">{alert.labels.alertname}</p>
                        <p className="text-sm text-gray-400 truncate max-w-md">
                          {alert.annotations.summary || alert.annotations.description || 'No description'}
                        </p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <code className="text-sm text-blue-400">{alert.labels.instance || alert.labels.job || '-'}</code>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1 text-sm text-gray-400">
                        <Clock size={14} />
                        {new Date(alert.startsAt).toLocaleString()}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <button className="text-primary hover:text-primary-light text-sm font-medium">
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Alert Details Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-gray-700 rounded-lg shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            {/* Modal Header - Fixed */}
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-4 border-b border-gray-700">
              <div>
                <h2 className="text-xl font-bold text-white">{selectedAlert.labels.alertname}</h2>
                <p className="text-xs text-gray-400">Started: {new Date(selectedAlert.startsAt).toLocaleTimeString()}</p>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="p-2 bg-error/20 hover:bg-error/30 rounded-lg transition-colors flex-shrink-0"
                title="Close"
              >
                <XCircle className="text-white" size={20} />
              </button>
            </div>

            {/* Modal Content - Scrollable */}
            <div className="p-4 space-y-4">
              {/* Status & Severity */}
              <div className="grid grid-cols-2 gap-3">
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedAlert.status)}
                    <span className="text-lg text-white font-semibold capitalize">{selectedAlert.status}</span>
                  </div>
                </div>
                <div className="card bg-surface-light">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                    {selectedAlert.severity.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Description */}
              {selectedAlert.annotations.description && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-white mb-2">Description</h3>
                  <p className="text-gray-300">{selectedAlert.annotations.description}</p>
                </div>
              )}

              {/* Labels */}
              <div className="card">
                <h3 className="text-lg font-semibold text-white mb-3">Labels</h3>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(selectedAlert.labels).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2">
                      <span className="text-gray-400 text-sm">{key}:</span>
                      <code className="text-blue-400 text-sm flex-1">{value}</code>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button 
                  className="btn flex-1"
                  onClick={() => {
                    // Extraer job e instance de los labels para construir query específica
                    const job = selectedAlert.labels.job || ''
                    const instance = selectedAlert.labels.instance || ''
                    
                    // Construir query basada en el job y la instancia específica
                    let prometheusQuery = 'up'
                    
                    if (job && instance) {
                      prometheusQuery = `up{job="${job}", instance="${instance}"}`
                    } else if (job) {
                      prometheusQuery = `up{job="${job}"}`
                    } else if (instance) {
                      prometheusQuery = `up{instance="${instance}"}`
                    }
                    
                    // Open Grafana Explore directly (v2.5.1 - direct links strategy)
                    const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                      datasource: 'prometheus',
                      queries: [{ refId: 'A', expr: prometheusQuery }],
                      range: { from: 'now-1h', to: 'now' }
                    }))}`
                    openGrafanaExplore(exploreUrl)
                  }}
                >
                  View in Grafana
                </button>
                <button 
                  className="btn btn-secondary flex-1"
                  onClick={() => {
                    alert('🔕 SILENCE ALERT\n\n' +
                      'Esta funcionalidad creará una regla de silencio en AlertManager.\n\n' +
                      'Lo que hará:\n' +
                      '• Enviar petición POST /api/v2/silences a AlertManager\n' +
                      '• Silenciar esta alerta por 1h, 4h, 24h o custom\n' +
                      '• Dejar de enviar notificaciones (Slack, Email)\n' +
                      '• La alerta seguirá activa pero no molestará\n\n' +
                      '📅 CUANDO: Sprint 5 - Settings & Notifications\n' +
                      '⏱️ Estimado: 2-3 horas de desarrollo')
                  }}
                  title="Silenciar esta alerta temporalmente (Sprint 5)"
                >
                  Silence Alert
                </button>
                <button 
                  className="btn btn-secondary flex-1"
                  onClick={() => {
                    if (confirm(`Mark alert "${selectedAlert.labels.alertname}" as acknowledged?`)) {
                      alert('✅ ACKNOWLEDGE ALERT\n\n' +
                        'Esta funcionalidad marcará la alerta como reconocida.\n\n' +
                        'Lo que hará:\n' +
                        '• Guardar en BD que "admin" vio esta alerta\n' +
                        '• Timestamp de acknowledgement\n' +
                        '• Evitar re-notificaciones duplicadas\n' +
                        '• Mostrar badge "ACK" en la tabla\n' +
                        '• Tracking de quién y cuándo fue acknowledged\n\n' +
                        '📅 CUANDO: Sprint 3 - Home Dashboard (Activity Feed)\n' +
                        '⏱️ Estimado: 1-2 horas de desarrollo')
                      setSelectedAlert(null)
                    }
                  }}
                  title="Marcar como reconocida (Sprint 3)"
                >
                  Acknowledge
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
