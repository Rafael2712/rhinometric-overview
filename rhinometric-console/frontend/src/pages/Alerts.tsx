import { Bell, Filter, Download, Clock, AlertTriangle, CheckCircle2, XCircle, VolumeX, UserCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface Alert {
  fingerprint: string
  status: string
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

interface AckInfo {
  fingerprint: string
  acknowledged: boolean
  ack_by?: string
  ack_at?: string
  status?: string
  note?: string
}

export function AlertsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Alerts'
  }, [])

  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const queryClient = useQueryClient()
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [silenceDuration, setSilenceDuration] = useState<string>('1h')
  const [silenceLoading, setSilenceLoading] = useState(false)
  const [ackLoading, setAckLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Fetch alerts
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
    refetchInterval: 30000,
  })

  // Fetch ack status for all alerts
  const fingerprints = alertsData?.alerts?.map(a => a.fingerprint).join(',') || ''
  const { data: ackData } = useQuery({
    queryKey: ['ack-status', fingerprints],
    queryFn: async () => {
      if (!token || !fingerprints) return {}
      const response = await fetch(`/api/alerts/ack-status?fingerprints=${encodeURIComponent(fingerprints)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) return {}
      return response.json() as Promise<Record<string, AckInfo>>
    },
    enabled: !!token && !!fingerprints,
    refetchInterval: 30000,
  })

  // Fetch active silences
  const { data: silencesData } = useQuery({
    queryKey: ['silences'],
    queryFn: async () => {
      if (!token) return { silences: [], total: 0 }
      const response = await fetch('/api/alerts/silences', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) return { silences: [], total: 0 }
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  // Silence mutation
  const handleSilence = async (fingerprint: string) => {
    if (!token) return
    setSilenceLoading(true)
    setActionMessage(null)
    try {
      const response = await fetch(`/api/alerts/${fingerprint}/silence`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ duration: silenceDuration })
      })
      const data = await response.json()
      if (response.ok) {
        setActionMessage({ type: 'success', text: `Alert silenced for ${silenceDuration}` })
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
        queryClient.invalidateQueries({ queryKey: ['silences'] })
      } else {
        setActionMessage({ type: 'error', text: data.detail || 'Failed to silence alert' })
      }
    } catch (e) {
      setActionMessage({ type: 'error', text: 'Failed to silence alert' })
    } finally {
      setSilenceLoading(false)
    }
  }

  // Acknowledge mutation
  const handleAcknowledge = async (fingerprint: string) => {
    if (!token) return
    setAckLoading(true)
    setActionMessage(null)
    try {
      const response = await fetch(`/api/alerts/${fingerprint}/ack`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
      const data = await response.json()
      if (response.ok) {
        setActionMessage({ type: 'success', text: `Alert acknowledged by ${data.ack_by}` })
        queryClient.invalidateQueries({ queryKey: ['ack-status'] })
      } else {
        setActionMessage({ type: 'error', text: data.detail || 'Failed to acknowledge alert' })
      }
    } catch (e) {
      setActionMessage({ type: 'error', text: 'Failed to acknowledge alert' })
    } finally {
      setAckLoading(false)
    }
  }

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
    <div className="space-y-4 sm:space-y-6">
      {/* Header - stacks on mobile */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2 sm:mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Alert Management</h1>
          <p className="text-text-muted text-sm sm:text-base">Monitor and manage system alerts from AlertManager</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          {silencesData?.total > 0 && (
            <span className="text-xs px-2 sm:px-3 py-1 rounded-full bg-warning/20 text-warning border border-warning/30">
              <VolumeX size={12} className="inline mr-1" />
              {silencesData.total} silence{silencesData.total > 1 ? 's' : ''}
            </span>
          )}
          <button className="btn btn-secondary flex items-center gap-2 text-sm">
            <Download size={18} />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Filters - wraps on mobile */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <Filter size={18} className="text-gray-400 flex-shrink-0" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 hidden sm:inline">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
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
      <div className="card p-0 sm:p-0">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-gray-400 text-sm">Loading alerts...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <AlertTriangle className="text-error mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">Failed to load alerts</p>
            <p className="text-sm text-gray-400">{(error as Error).message}</p>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <CheckCircle2 className="text-success mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">No Alerts</p>
            <p className="text-gray-400 text-sm">All systems operational</p>
          </div>
        ) : (
          <>
            {/* Desktop table view */}
            <div className="hidden md:block overflow-x-auto">
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
                  {filteredAlerts.map((alert) => {
                    const ackInfo = ackData?.[alert.fingerprint]
                    return (
                      <tr
                        key={alert.fingerprint}
                        className="border-b border-gray-700/50 hover:bg-surface-light cursor-pointer transition-colors"
                        onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(alert.status)}
                            {ackInfo?.acknowledged && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30" title={`Acknowledged by ${ackInfo.ack_by}`}>
                                <UserCheck size={10} className="inline mr-0.5" />
                                ACK
                              </span>
                            )}
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
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile card view */}
            <div className="md:hidden divide-y divide-gray-700/50">
              {filteredAlerts.map((alert) => {
                const ackInfo = ackData?.[alert.fingerprint]
                return (
                  <div
                    key={alert.fingerprint}
                    className="p-3 sm:p-4 hover:bg-surface-light cursor-pointer transition-colors active:bg-surface-light"
                    onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        {getStatusIcon(alert.status)}
                        <span className="text-white font-medium text-sm truncate">{alert.labels.alertname}</span>
                      </div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-2 mb-2 ml-7">
                      {alert.annotations.summary || alert.annotations.description || 'No description'}
                    </p>
                    <div className="flex items-center justify-between ml-7">
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock size={12} />
                        {new Date(alert.startsAt).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div className="flex items-center gap-2">
                        {ackInfo?.acknowledged && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">ACK</span>
                        )}
                        <span className="text-primary text-xs font-medium">Details &rarr;</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>

      {/* Alert Details Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-surface border border-gray-700 rounded-t-xl sm:rounded-lg shadow-2xl w-full sm:max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-3 sm:p-4 border-b border-gray-700">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-white truncate">{selectedAlert.labels.alertname}</h2>
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
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {actionMessage && (
                <div className={`p-3 rounded-lg border text-sm ${actionMessage.type === 'success' ? 'bg-success/10 border-success/30 text-success' : 'bg-error/10 border-error/30 text-error'}`}>
                  {actionMessage.text}
                </div>
              )}
              {ackData?.[selectedAlert.fingerprint]?.acknowledged && (
                <div className="p-3 rounded-lg border bg-blue-500/10 border-blue-500/30 text-sm text-blue-400 flex items-center gap-2 flex-wrap">
                  <UserCheck size={16} className="flex-shrink-0" />
                  <span>Acknowledged by <strong>{ackData[selectedAlert.fingerprint].ack_by}</strong> at {new Date(ackData[selectedAlert.fingerprint].ack_at!).toLocaleString()}</span>
                  {ackData[selectedAlert.fingerprint].note && (
                    <span className="text-gray-400 break-words">{ackData[selectedAlert.fingerprint].note}</span>
                  )}
                </div>
              )}
              {/* Status / Severity grid */}
              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                <div className="card bg-surface-light p-3">
                  <p className="text-xs text-gray-400 mb-1">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedAlert.status)}
                    <span className="text-base sm:text-lg text-white font-semibold capitalize">{selectedAlert.status}</span>
                  </div>
                </div>
                <div className="card bg-surface-light p-3">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                    {selectedAlert.severity.toUpperCase()}
                  </span>
                </div>
              </div>
              {selectedAlert.annotations.description && (
                <div className="card p-3 sm:p-4">
                  <h3 className="text-base sm:text-lg font-semibold text-white mb-2">Description</h3>
                  <p className="text-gray-300 text-sm break-words">{selectedAlert.annotations.description}</p>
                </div>
              )}
              <div className="card p-3 sm:p-4">
                <h3 className="text-base sm:text-lg font-semibold text-white mb-3">Labels</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
                  {Object.entries(selectedAlert.labels).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2 min-w-0">
                      <span className="text-gray-400 text-sm flex-shrink-0">{key}:</span>
                      <code className="text-blue-400 text-sm break-all min-w-0">{value}</code>
                    </div>
                  ))}
                </div>
              </div>
              {/* Action buttons - stack on mobile */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                {isAdmin() && (
                <button
                  className="btn flex-1 min-h-[44px]"
                  onClick={() => {
                    const job = selectedAlert.labels.job || ''
                    const instance = selectedAlert.labels.instance || ''
                    let prometheusQuery = 'up'
                    if (job && instance) {
                      prometheusQuery = `up{job="${job}", instance="${instance}"}`
                    } else if (job) {
                      prometheusQuery = `up{job="${job}"}`
                    } else if (instance) {
                      prometheusQuery = `up{instance="${instance}"}`
                    }
                    const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                      datasource: 'victoriametrics',
                      queries: [{ refId: 'A', expr: prometheusQuery }],
                      range: { from: 'now-1h', to: 'now' }
                    }))}`
                    openGrafanaExplore(exploreUrl)
                  }}
                >
                  View in Grafana
                </button>
                )}
                <div className="flex-1 flex gap-2">
                  <select
                    value={silenceDuration}
                    onChange={(e) => setSilenceDuration(e.target.value)}
                    className="bg-surface-light border border-gray-700 text-white rounded px-2 py-1.5 text-sm w-20 flex-shrink-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <option value="30m">30m</option>
                    <option value="1h">1h</option>
                    <option value="4h">4h</option>
                    <option value="24h">24h</option>
                  </select>
                  <button
                    className="btn btn-secondary flex-1 flex items-center justify-center gap-2 min-h-[44px]"
                    disabled={silenceLoading}
                    onClick={() => handleSilence(selectedAlert.fingerprint)}
                  >
                    <VolumeX size={16} />
                    <span className="hidden sm:inline">{silenceLoading ? 'Silencing...' : 'Silence Alert'}</span>
                    <span className="sm:hidden">{silenceLoading ? '...' : 'Silence'}</span>
                  </button>
                </div>
                <button
                  className="btn btn-secondary flex-1 flex items-center justify-center gap-2 min-h-[44px]"
                  disabled={ackLoading || ackData?.[selectedAlert.fingerprint]?.acknowledged}
                  onClick={() => handleAcknowledge(selectedAlert.fingerprint)}
                >
                  <UserCheck size={16} />
                  <span className="truncate">
                  {ackData?.[selectedAlert.fingerprint]?.acknowledged
                    ? `Ack'd`
                    : ackLoading ? 'Ack...' : 'Acknowledge'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
