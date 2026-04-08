import { Bell, Filter, Download, Clock, AlertTriangle, CheckCircle2, XCircle, VolumeX, UserCheck, Trash2, Brain, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'

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

/* ── AI Context Types (V1.7 Alert Integration) ── */
interface ServiceAiContext {
  anomaly_id: string
  anomaly_score: number
  severity: string
  status: string
  confidence: number
  confidence_label: string
  evidence_summary: string
  predicted_risk_score: number | null
  predicted_risk_level: string | null
  predicted_horizon_minutes: number | null
  prediction_confidence: string | null
  prediction_summary: string | null
  explanation_summary: string | null
  first_seen_at: string
  last_seen_at: string
}

interface AiContextResponse {
  contexts: Record<string, ServiceAiContext>
  count: number
}

/* ── AI Score Badge ── */
function AiScoreBadge({ ctx }: { ctx: ServiceAiContext | undefined }) {
  if (!ctx) return null
  const score = ctx.anomaly_score
  const color =
    score >= 70 ? 'bg-red-500/20 text-red-400 border-red-500/30' :
    score >= 40 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
    score >= 15 ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
    'bg-gray-500/20 text-gray-400 border-gray-700/50'
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border ${color}`} title={`AI Score: ${score}/100 — ${ctx.severity}`}>
      <Brain size={10} />
      {score}
    </span>
  )
}


/* ── Extract service name from alertname (after '::' delimiter) ── */
function getAlertServiceName(alert: { labels: { alertname?: string; service_name?: string; service?: string } }): string {
  // Primary: extract from alertname after '::'
  const parts = (alert.labels.alertname || '').split('::')
  if (parts.length > 1 && parts[1].trim()) return parts[1].trim()
  // Fallback: service_name label (if ever added)
  if (alert.labels.service_name) return alert.labels.service_name
  return ''
}

/* ── Task 4: Purge Modal ──────────────────────────────────────── */
function PurgeModal({ module, isOpen, onClose, token }: {
  module: 'alerts' | 'incidents' | 'anomalies'
  isOpen: boolean
  onClose: (purged: boolean) => void
  token: string | null
}) {
  const [days, setDays] = useState(30)
  const [confirming, setConfirming] = useState(false)
  const [result, setResult] = useState<{ deleted_count: number; message: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handlePurge = async () => {
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`/api/admin/purge/${module}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ confirm: true, older_than_days: days }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Purge failed')
      }
      const data = await res.json()
      setResult(data)
      setConfirming(false)
    } catch (e: any) {
      setError(e.message || 'Purge failed')
      setConfirming(false)
    }
  }

  const labels: Record<string, string> = {
    alerts: 'resolved/suppressed alert events',
    incidents: 'resolved incidents',
    anomalies: 'resolved/suppressed anomaly overrides',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Trash2 size={20} className="text-red-400" />
          Clear {module.charAt(0).toUpperCase() + module.slice(1)} History
        </h3>

        {result ? (
          <div className="space-y-4">
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-green-400 text-sm">
              {result.message}
            </div>
            <button onClick={() => onClose(true)}
              className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
              Close
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-300">
              Permanently delete <strong>{labels[module]}</strong> older than:
            </p>
            <div className="flex items-center gap-3">
              <input type="number" min={1} max={365} value={days}
                onChange={(e) => setDays(Math.max(1, Math.min(365, parseInt(e.target.value) || 30)))}
                className="w-24 px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white text-sm" />
              <span className="text-sm text-gray-400">days</span>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {!confirming ? (
              <div className="flex gap-3">
                <button onClick={() => onClose(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
                  Cancel
                </button>
                <button onClick={() => setConfirming(true)}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm">
                  Purge
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
                  ⚠️ This action is irreversible. Are you sure?
                </div>
                <div className="flex gap-3">
                  <button onClick={() => setConfirming(false)}
                    className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm">
                    Cancel
                  </button>
                  <button onClick={handlePurge}
                    className="flex-1 px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg text-sm font-semibold">
                    Confirm Purge
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
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
  const [showPurge, setShowPurge] = useState(false)

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

  // V1.7: Fetch AI context for all alert service names
  const serviceNames = alertsData?.alerts
    ?.map(a => getAlertServiceName(a))
    .filter((n): n is string => !!n && n.length > 0)
    .filter((v, i, arr) => arr.indexOf(v) === i)
    .join(',') || ''
  const { data: aiContextData } = useQuery<AiContextResponse>({
    queryKey: ['alert-ai-context', serviceNames],
    queryFn: async () => {
      if (!serviceNames) return { contexts: {}, count: 0 }
      const res = await fetch(`/api/v2/alerts/ai-context?service_names=${encodeURIComponent(serviceNames)}`)
      if (!res.ok) return { contexts: {}, count: 0 }
      return res.json()
    },
    enabled: !!serviceNames,
    refetchInterval: 60000,
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

  // Filter alerts — only show customer-facing alerts (must have a service name)
  const filteredAlerts = alertsData?.alerts?.filter(alert => {
    // Hide infrastructure alerts that have no customer service mapping
    const serviceName = getAlertServiceName(alert)
    if (!serviceName) return false
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
      <PurgeModal module="alerts" isOpen={showPurge} onClose={(purged) => { setShowPurge(false); if (purged) queryClient.invalidateQueries({ queryKey: ['alert-history'] }) }} token={token} />
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
          {isAdmin() && (
            <button onClick={() => setShowPurge(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded-lg text-sm transition-colors">
              <Trash2 size={14} />
              <span className="hidden sm:inline">Clear History</span>
            </button>
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
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">AI</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Started</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400 whitespace-nowrap">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map((alert) => {
                    const ackInfo = ackData?.[alert.fingerprint]
                    const aiCtx = aiContextData?.contexts?.[getAlertServiceName(alert)]
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
                          <AiScoreBadge ctx={aiCtx} />
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
                const aiCtx = aiContextData?.contexts?.[getAlertServiceName(alert)]
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
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <AiScoreBadge ctx={aiCtx} />
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </div>
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
              {/* V1.7: AI Analysis Context */}
              {(() => {
                const svcKey = getAlertServiceName(selectedAlert)
                const ctx = aiContextData?.contexts?.[svcKey]
                if (!ctx) return null
                const scoreColor =
                  ctx.anomaly_score >= 70 ? 'text-red-400' :
                  ctx.anomaly_score >= 40 ? 'text-amber-400' :
                  ctx.anomaly_score >= 15 ? 'text-blue-400' : 'text-gray-400'
                const riskColor =
                  ctx.predicted_risk_level === 'high' || ctx.predicted_risk_level === 'critical' ? 'text-red-400' :
                  ctx.predicted_risk_level === 'moderate' ? 'text-amber-400' :
                  ctx.predicted_risk_level === 'low' ? 'text-blue-400' : 'text-gray-400'
                return (
                  <div className="card p-3 sm:p-4 border-purple-500/30">
                    <h3 className="text-base sm:text-lg font-semibold text-white mb-3 flex items-center gap-2">
                      <Brain size={18} className="text-purple-400" />
                      AI Analysis
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30 font-normal">
                        {ctx.status === 'active' ? 'Live' : 'Recent'}
                      </span>
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                      <div>
                        <p className="text-xs text-gray-500">Anomaly Score</p>
                        <p className={`text-lg font-bold ${scoreColor}`}>{ctx.anomaly_score}<span className="text-xs font-normal text-gray-500">/100</span></p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">AI Severity</p>
                        <p className="text-sm font-medium text-gray-200 capitalize">{ctx.severity}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Predicted Risk</p>
                        <p className={`text-sm font-medium capitalize ${riskColor}`}>
                          {ctx.predicted_risk_level || 'none'}
                          {ctx.predicted_risk_score != null && <span className="text-gray-500 font-normal"> ({ctx.predicted_risk_score}%)</span>}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Confidence</p>
                        <p className="text-sm font-medium text-gray-200 capitalize">{ctx.confidence_label}</p>
                      </div>
                    </div>
                    {ctx.explanation_summary && (
                      <div className="p-2.5 bg-surface rounded border border-gray-700 mb-3">
                        <p className="text-sm text-gray-300">{ctx.explanation_summary}</p>
                      </div>
                    )}
                    {!ctx.explanation_summary && ctx.evidence_summary && (
                      <div className="p-2.5 bg-surface rounded border border-gray-700 mb-3">
                        <p className="text-sm text-gray-400">{ctx.evidence_summary}</p>
                      </div>
                    )}
                    {ctx.predicted_horizon_minutes != null && ctx.predicted_horizon_minutes > 0 && (
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <TrendingUp size={12} />
                        <span>Prediction horizon: {ctx.predicted_horizon_minutes} minutes</span>
                      </div>
                    )}
                    <a href="/ai-anomalies-v2" className="inline-flex items-center gap-1 mt-2 text-xs text-purple-400 hover:text-purple-300 transition-colors">
                      <Brain size={12} /> View full AI analysis →
                    </a>
                  </div>
                )
              })()}
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
