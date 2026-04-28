import { Bell, Filter, Download, Clock, AlertTriangle, CheckCircle2, XCircle, VolumeX, UserCheck, Brain, TrendingUp, Siren, ExternalLink, Trash2 } from 'lucide-react'
import { useEffect, useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'

interface AiTriageDecision {
  decision?: string
  risk_level?: string
  confidence?: string
  confidence_label?: string
  summary?: string
  reason?: string
  evidence?: string[]
  recommended_actions?: string[]
  noise_assessment?: string
}

interface Alert {
  id?: string
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
  acknowledged_by?: string
  acknowledged_at?: string
  silenced_until?: string
  incident_id?: string
  ai_decision?: AiTriageDecision | null
}

interface AlertsResponse {
  alerts: Alert[]
  total: number
}

/* -- AI Context Types (V1.7 Alert Integration) -- */
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

function formatAiField(value?: string | null): string {
  if (!value) return '-'
  return String(value).trim() || '-'
}

function normalizeArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

function getAiDecisionStyles(decision?: string | null): string {
  const d = (decision || '').toLowerCase()
  if (d === 'escalate') return 'bg-red-500/10 text-red-400 border-red-500/30'
  if (d === 'notify') return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
  if (d === 'monitor') return 'bg-blue-500/10 text-blue-400 border-blue-500/30'
  if (d === 'ignore') return 'bg-gray-50 text-gray-500 border-gray-500/30'
  return 'bg-gray-50 text-gray-500 border-gray-500/30'
}

function AITriageBadge({ decision }: { decision?: AiTriageDecision | null }) {
  if (!decision?.decision) return null
  return (
    <div className="min-w-0">
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${getAiDecisionStyles(decision.decision)}`}>
        {decision.decision.toUpperCase()}
      </span>
      <p className="text-[10px] text-slate-500 mt-1 truncate">
        {formatAiField(decision.risk_level)} risk · {formatAiField(decision.confidence || decision.confidence_label)} confidence
      </p>
    </div>
  )
}

/* -- Status Badge -- */
function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() || 'active'
  if (s === 'acknowledged') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
        <UserCheck size={10} />
        ACKNOWLEDGED
      </span>
    )
  }
  if (s === 'silenced') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-500 border border-gray-200/40">
        <VolumeX size={10} />
        SILENCED
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
      <AlertTriangle size={10} />
      ACTIVE
    </span>
  )
}


/* -- Extract service name from alertname (after '::' delimiter) -- */
function getAlertServiceName(alert: { labels: { alertname?: string; service_name?: string; service?: string } }): string {
  const parts = (alert.labels.alertname || '').split('::')
  if (parts.length > 1 && parts[1].trim()) return parts[1].trim()
  if (alert.labels.service_name) return alert.labels.service_name
  return ''
}

export function AlertsPage() {
  useEffect(() => {
    document.title = 'Rhinometric – Operational Alerts'
  }, [])

  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [silenceDuration, setSilenceDuration] = useState<string>('1h')
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [showSilencesPanel, setShowSilencesPanel] = useState(false)
  const [expiringSilenceId, setExpiringSilenceId] = useState<string | null>(null)
  const [creatingIncident, setCreatingIncident] = useState(false)
  const [runningAiAlertId, setRunningAiAlertId] = useState<string | null>(null)

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

  // ── Lifecycle action handler ──
  const handleLifecycleAction = useCallback(async (
    alert: Alert,
    action: 'ack' | 'resolve' | 'dismiss' | 'silence',
    body?: Record<string, unknown>,
  ) => {
    if (!token || !alert.id) return
    setActionLoading(action)
    setActionMessage(null)
    try {
      const response = await fetch(`/api/alerts/${alert.id}/${action}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body || {}),
      })
      const data = await response.json()
      if (response.ok) {
        const labels: Record<string, string> = {
          ack: 'acknowledged', resolve: 'resolved', dismiss: 'dismissed', silence: 'silenced',
        }
        setActionMessage({ type: 'success', text: `Alert ${labels[action]} successfully` })
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
        queryClient.invalidateQueries({ queryKey: ['silences'] })
        // Resolve / Dismiss → close modal (alert removed from list)
        if (action === 'resolve' || action === 'dismiss') {
          setTimeout(() => setSelectedAlert(null), 600)
        }
      } else {
        setActionMessage({ type: 'error', text: data.detail || `Failed to ${action} alert` })
      }
    } catch (e: any) {
      setActionMessage({ type: 'error', text: e.message || `Failed to ${action} alert` })
    } finally {
      setActionLoading(null)
    }
  }, [token, queryClient])

  // ── Create Incident from alert ──
  const handleCreateIncident = useCallback(async (alert: Alert) => {
    if (!token || !alert.id) return
    setCreatingIncident(true)
    setActionMessage(null)
    try {
      const serviceName = getAlertServiceName(alert) || alert.labels.service_name || alert.labels.instance || 'unknown'
      const response = await fetch('/api/incidents', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          service_name: serviceName,
          severity: alert.severity,
          alert_fingerprint: alert.fingerprint,
          alert_id: alert.id,
        }),
      })
      const data = await response.json()
      if (response.ok) {
        const incidentId = data.incident?.id
        const wasCreated = data.created
        setActionMessage({
          type: 'success',
          text: wasCreated
            ? `Incident created successfully. Redirecting...`
            : `An open incident already exists for this service. Redirecting...`
        })
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
        setTimeout(() => {
          setSelectedAlert(null)
          if (incidentId) navigate(`/incidents?expand=${incidentId}`)
        }, 800)
      } else {
        setActionMessage({ type: 'error', text: data.detail || 'Failed to create incident' })
      }
    } catch (e: any) {
      setActionMessage({ type: 'error', text: e.message || 'Failed to create incident' })
    } finally {
      setCreatingIncident(false)
    }
  }, [token, queryClient, navigate])

  const handleRunAiDecision = useCallback(async (alert: Alert) => {
    if (!token || !alert.id) return
    setRunningAiAlertId(alert.id)
    setActionMessage(null)
    try {
      const response = await fetch(`/api/alerts/${alert.id}/ai-decision`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data?.detail || 'Failed to run AI triage')
      }
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setActionMessage({ type: 'success', text: 'AI triage decision generated successfully.' })
    } catch (e: any) {
      setActionMessage({ type: 'error', text: e?.message || 'Failed to run AI triage' })
    } finally {
      setRunningAiAlertId(null)
    }
  }, [token, queryClient])

  // ── Expire (delete) a silence ──
  const handleExpireSilence = useCallback(async (silenceId: string) => {
    if (!token) return
    setExpiringSilenceId(silenceId)
    try {
      const response = await fetch(`/api/alerts/silences/${silenceId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (response.ok) {
        queryClient.invalidateQueries({ queryKey: ['silences'] })
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
      }
    } catch (e) {
      console.error('Failed to expire silence:', e)
      setActionMessage({ type: 'error', text: 'Failed to expire silence. Please try again.' })
    } finally {
      setExpiringSilenceId(null)
    }
  }, [token, queryClient])

  // ── Deduplicate by fingerprint (belt-and-suspenders, backend already deduplicates) ──
  const dedupedAlerts = (() => {
    const alerts = alertsData?.alerts || []
    const seen = new Set<string>()
    return alerts.filter(a => {
      const fp = a.fingerprint
      if (!fp || seen.has(fp)) return false
      seen.add(fp)
      return true
    })
  })()

  // Filter alerts by severity
  const filteredAlerts = dedupedAlerts.filter(alert => {
    return severityFilter === 'all' || alert.severity === severityFilter
  })

  // Export filtered alerts as CSV
  const exportCSV = () => {
    const headers = ['Alert Name', 'Service', 'Severity', 'Status', 'Instance', 'Started At']
    const rows = filteredAlerts.map(a => [
      a.labels.alertname || '',
      getAlertServiceName(a),
      a.severity,
      a.status,
      a.labels.instance || a.labels.job || '',
      a.startsAt ? new Date(a.startsAt).toLocaleString() : '',
    ].map(v => `"${String(v).replace(/"/g, '""')}"`))
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `alerts-${severityFilter}-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-error/20 text-error'
      case 'high': return 'bg-orange-500/20 text-orange-400'
      case 'warning': return 'bg-warning/20 text-warning'
      case 'medium': return 'bg-amber-500/20 text-amber-400'
      case 'low': return 'bg-blue-500/20 text-blue-400'
      case 'info': return 'bg-blue-500/20 text-blue-400'
      default: return 'bg-gray-100 text-gray-500'
    }
  }

  const getStatusIcon = (state: string) => {
    const s = state?.toLowerCase() || ''
    if (s === 'acknowledged') {
      return <UserCheck className="text-amber-400" size={20} />
    } else if (s === 'silenced') {
      return <VolumeX className="text-gray-500" size={20} />
    } else if (s.includes('active') || s.includes('firing')) {
      return <AlertTriangle className="text-error" size={20} />
    }
    return <Bell className="text-gray-500" size={20} />
  }

  /* ── Can the alert use lifecycle actions? (needs DB id) ── */
  const canAct = (alert: Alert) => !!alert.id

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2 sm:mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-1 sm:mb-2">Operational Alerts</h1>
          <p className="text-slate-500 text-sm sm:text-base">Alerts requiring attention – generated when anomaly scores or predicted risk exceed operational thresholds</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          {silencesData?.total > 0 && (
            <button
              onClick={() => setShowSilencesPanel(!showSilencesPanel)}
              className="text-xs px-2 sm:px-3 py-1 rounded-full bg-warning/20 text-warning border border-warning/30 hover:bg-warning/30 transition-colors cursor-pointer"
            >
              <VolumeX size={12} className="inline mr-1" />
              {silencesData.total} silence{silencesData.total > 1 ? 's' : ''}
            </button>
          )}
          <button onClick={exportCSV} className="btn btn-secondary flex items-center gap-2 text-sm">
            <Download size={18} />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 sm:gap-4">
          <Filter size={18} className="text-gray-500 flex-shrink-0" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 hidden sm:inline">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white border border-slate-300 text-slate-700 rounded px-2 sm:px-3 py-1.5 text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="warning">Warning</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>

        </div>
      </div>

      {/* Silences Management Panel */}
      {showSilencesPanel && silencesData?.silences?.length > 0 && (
        <div className="card border-warning/20">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-warning flex items-center gap-2">
              <VolumeX size={16} />
              Active Silences ({silencesData.total})
            </h3>
            <button
              onClick={() => setShowSilencesPanel(false)}
              className="text-gray-500 hover:text-gray-900 transition-colors p-1"
            >
              <XCircle size={16} />
            </button>
          </div>
          <p className="text-xs text-gray-500 mb-3">Silenced alerts are hidden from the main list. Click &quot;Reactivate&quot; to expire a silence and show the alert again.</p>
          <div className="space-y-2">
            {silencesData.silences.map((silence: any) => {
              const alertname = silence.matchers?.[0]?.value || 'Unknown alert'
              const expiresAt = silence.endsAt ? new Date(silence.endsAt) : null
              const timeLeft = expiresAt ? Math.max(0, Math.round((expiresAt.getTime() - Date.now()) / 60000)) : null
              return (
                <div key={silence.id} className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-gray-50 border border-gray-200/50">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900 truncate">{alertname}</p>
                    <p className="text-xs text-gray-500">
                      {timeLeft != null && timeLeft > 0
                        ? `Expires in ${timeLeft >= 60 ? `${Math.floor(timeLeft / 60)}h ${timeLeft % 60}m` : `${timeLeft}m`}`
                        : 'Expiring soon'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleExpireSilence(silence.id)}
                    disabled={expiringSilenceId === silence.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-warning/10 text-warning hover:bg-warning/20 border border-warning/20 transition-colors disabled:opacity-50 flex-shrink-0"
                  >
                    <Bell size={12} />
                    {expiringSilenceId === silence.id ? 'Reactivating...' : 'Reactivate'}
                  </button>
                </div>
              )
            })}
            <button
              onClick={async () => {
                if (!token) return
                setExpiringSilenceId('all')
                try {
                  for (const s of silencesData.silences) {
                    await fetch(`/api/alerts/silences/${s.id}`, {
                      method: 'DELETE',
                      headers: { 'Authorization': `Bearer ${token}` },
                    })
                  }
                  queryClient.invalidateQueries({ queryKey: ['silences'] })
                  queryClient.invalidateQueries({ queryKey: ['alerts'] })
                  setShowSilencesPanel(false)
                } finally {
                  setExpiringSilenceId(null)
                }
              }}
              disabled={expiringSilenceId !== null}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-md bg-warning/10 text-warning hover:bg-warning/20 border border-warning/20 transition-colors disabled:opacity-50 mt-2"
            >
              <Trash2 size={12} />
              {expiringSilenceId === 'all' ? 'Reactivating all...' : 'Reactivate All Silences'}
            </button>
          </div>
        </div>
      )}

      {/* Alerts Table */}
      <div className="card p-0 sm:p-0">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-gray-500 text-sm">Loading alerts...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <AlertTriangle className="text-error mb-4" size={48} />
            <p className="text-gray-900 text-lg font-semibold mb-1">Failed to load alerts</p>
            <p className="text-sm text-gray-500">{(error as Error).message}</p>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <CheckCircle2 className="text-success mb-4" size={48} />
            <p className="text-gray-900 text-lg font-semibold mb-1">No Alerts</p>
            <p className="text-gray-500 text-sm">All systems operational</p>
          </div>
        ) : (
          <>
            {/* Desktop table view */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full table-fixed">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase w-[60px]">Status</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase" style={{width:'22%'}}>Alert</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase w-[88px]">Severity</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase w-[140px]">State</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase w-[52px]">AI</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase" style={{width:'12%'}}>Started</th>
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500 uppercase" style={{width:'26%'}}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map((alert) => {
                    return (
                      <tr
                        key={alert.fingerprint}
                        className="border-b border-gray-200/50 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                      >
                        <td className="py-2.5 px-3">
                          {getStatusIcon(alert.status)}
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="min-w-0">
                            <p className="text-slate-900 text-sm font-medium break-words">{alert.labels.alertname}</p>
                            <p className="text-xs text-slate-500 line-clamp-1 break-all">
                              {alert.annotations.summary || alert.annotations.description || 'No description'}
                            </p>
                          </div>
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                            {alert.severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <StatusBadge status={alert.status} />
                        </td>
                        <td className="py-2.5 px-3">
                          {alert.ai_decision?.decision ? <AITriageBadge decision={alert.ai_decision} /> : <button onClick={() => handleRunAiDecision(alert)} disabled={!alert.id || runningAiAlertId === alert.id} className="px-2 py-1 text-xs rounded border border-blue-500/30 text-blue-400 hover:bg-blue-500/10 disabled:opacity-50">{runningAiAlertId === alert.id ? 'Running...' : 'Run AI'}</button>}
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="text-xs text-slate-500">
                            {new Date(alert.startsAt).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </td>
                        <td className="py-2.5 px-3" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center gap-1">
                            {canAct(alert) && alert.status !== 'acknowledged' && (
                              <button
                                onClick={() => handleLifecycleAction(alert, 'ack')}
                                className="px-2 py-1 text-xs rounded bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 transition-colors"
                                title="Acknowledge"
                              >
                                ACK
                              </button>
                            )}
                            {canAct(alert) && (
                              <button
                                onClick={() => handleLifecycleAction(alert, 'resolve')}
                                className="px-2 py-1 text-xs rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/20 transition-colors"
                                title="Resolve"
                              >
                                Resolve
                              </button>
                            )}
                            {canAct(alert) && (
                              <button
                                onClick={() => handleLifecycleAction(alert, 'dismiss')}
                                className="px-2 py-1 text-xs rounded bg-gray-50 text-gray-500 hover:bg-gray-100 border border-gray-200/30 transition-colors"
                                title="Dismiss"
                              >
                                Dismiss
                              </button>
                            )}
                            <button
                              onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                              className="px-2 py-1 text-xs rounded text-primary hover:text-primary-light hover:bg-primary/10 transition-colors"
                            >
                              Details
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile card view */}
            <div className="md:hidden divide-y divide-gray-200/50">
              {filteredAlerts.map((alert) => {
                return (
                  <div
                    key={alert.fingerprint}
                    className="p-3 sm:p-4 hover:bg-gray-50 cursor-pointer transition-colors active:bg-gray-50"
                    onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        {getStatusIcon(alert.status)}
                        <span className="text-slate-900 font-medium text-sm truncate">{alert.labels.alertname}</span>
                      </div>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        {alert.ai_decision?.decision ? <AITriageBadge decision={alert.ai_decision} /> : <button onClick={() => handleRunAiDecision(alert)} disabled={!alert.id || runningAiAlertId === alert.id} className="px-2 py-1 text-xs rounded border border-blue-500/30 text-blue-400 hover:bg-blue-500/10 disabled:opacity-50">{runningAiAlertId === alert.id ? 'Running...' : 'Run AI'}</button>}
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-2 mb-2 ml-7">
                      {alert.annotations.summary || alert.annotations.description || 'No description'}
                    </p>
                    <div className="flex items-center justify-between ml-7 mb-2">
                      <div className="flex items-center gap-1 text-xs text-slate-500">
                        <Clock size={12} />
                        {new Date(alert.startsAt).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <StatusBadge status={alert.status} />
                    </div>
                    {/* Mobile action buttons */}
                    <div className="flex items-center flex-wrap gap-1.5 ml-7" onClick={(e) => e.stopPropagation()}>
                      {canAct(alert) && alert.status !== 'acknowledged' && (
                        <button
                          onClick={() => handleLifecycleAction(alert, 'ack')}
                          className="px-2.5 py-1.5 text-xs rounded-md bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 active:bg-amber-500/30 transition-colors font-medium"
                        >
                          ACK
                        </button>
                      )}
                      {canAct(alert) && (
                        <button
                          onClick={() => handleLifecycleAction(alert, 'resolve')}
                          className="px-2.5 py-1.5 text-xs rounded-md bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/20 active:bg-green-500/30 transition-colors font-medium"
                        >
                          Resolve
                        </button>
                      )}
                      {canAct(alert) && (
                        <button
                          onClick={() => handleLifecycleAction(alert, 'dismiss')}
                          className="px-2.5 py-1.5 text-xs rounded-md bg-gray-50 text-gray-500 hover:bg-gray-100 border border-gray-200/30 active:bg-gray-500/30 transition-colors font-medium"
                        >
                          Dismiss
                        </button>
                      )}
                      <button
                        onClick={() => { setSelectedAlert(alert); setActionMessage(null) }}
                        className="ml-auto px-2.5 py-1.5 text-xs rounded-md text-primary hover:bg-primary/10 active:bg-primary/20 border border-primary/20 transition-colors font-medium"
                      >
                        Details
                      </button>
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
          <div className="bg-surface border border-gray-200 rounded-t-xl sm:rounded-lg shadow-2xl w-full sm:max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-3 sm:p-4 border-b border-gray-200">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 truncate">{selectedAlert.labels.alertname}</h2>
                <p className="text-xs text-slate-500">Started: {new Date(selectedAlert.startsAt).toLocaleTimeString()}</p>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="p-2 bg-error/20 hover:bg-error/30 rounded-lg transition-colors flex-shrink-0"
                title="Close"
              >
                <XCircle className="text-gray-900" size={20} />
              </button>
            </div>
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {actionMessage && (
                <div className={`p-3 rounded-lg border text-sm ${actionMessage.type === 'success' ? 'bg-success/10 border-success/30 text-success' : 'bg-error/10 border-error/30 text-error'}`}>
                  {actionMessage.text}
                </div>
              )}

              {/* Acknowledged info banner */}
              {selectedAlert.status === 'acknowledged' && selectedAlert.acknowledged_by && (
                <div className="p-3 rounded-lg border bg-amber-500/10 border-amber-500/30 text-sm text-amber-400 flex items-center gap-2 flex-wrap">
                  <UserCheck size={16} className="flex-shrink-0" />
                  <span>Acknowledged by <strong>{selectedAlert.acknowledged_by}</strong>
                    {selectedAlert.acknowledged_at && ` at ${new Date(selectedAlert.acknowledged_at).toLocaleString()}`}
                  </span>
                </div>
              )}

              {/* Silenced info banner */}
              {selectedAlert.status === 'silenced' && selectedAlert.silenced_until && (
                <div className="p-3 rounded-lg border bg-gray-50 border-gray-200/30 text-sm text-gray-500 flex items-center gap-2 flex-wrap">
                  <VolumeX size={16} className="flex-shrink-0" />
                  <span>Silenced until <strong>{new Date(selectedAlert.silenced_until).toLocaleString()}</strong></span>
                </div>
              )}

              {/* Status / Severity grid */}
              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                <div className="card bg-gray-50 p-3">
                  <p className="text-xs text-gray-500 mb-1">Status</p>
                  <StatusBadge status={selectedAlert.status} />
                </div>
                <div className="card bg-gray-50 p-3">
                  <p className="text-xs text-gray-500 mb-1">Severity</p>
                  <span className={`inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                    {selectedAlert.severity.toUpperCase()}
                  </span>
                </div>
              </div>
              {selectedAlert.annotations.description && (
                <div className="card p-3 sm:p-4">
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-slate-700 text-sm break-words">{selectedAlert.annotations.description}</p>
                </div>
              )}
              {/* Anomaly Context from detection engine */}
              {(() => {
                const svcKey = getAlertServiceName(selectedAlert)
                const ctx = aiContextData?.contexts?.[svcKey]
                if (!ctx) return null
                const scoreColor =
                  ctx.anomaly_score >= 70 ? 'text-red-400' :
                  ctx.anomaly_score >= 40 ? 'text-amber-400' :
                  ctx.anomaly_score >= 15 ? 'text-blue-400' : 'text-gray-500'
                const riskColor =
                  ctx.predicted_risk_level === 'high' || ctx.predicted_risk_level === 'critical' ? 'text-red-400' :
                  ctx.predicted_risk_level === 'moderate' ? 'text-amber-400' :
                  ctx.predicted_risk_level === 'low' ? 'text-blue-400' : 'text-gray-500'
                return (
                  <div className="card p-3 sm:p-4 border-purple-500/30">
                    <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                      <Brain size={18} className="text-purple-400" />
                      Anomaly Context
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
                      <div className="p-2.5 bg-surface rounded border border-gray-200 mb-3">
                        <p className="text-sm text-gray-600">{ctx.explanation_summary}</p>
                      </div>
                    )}
                    {!ctx.explanation_summary && ctx.evidence_summary && (
                      <div className="p-2.5 bg-surface rounded border border-gray-200 mb-3">
                        <p className="text-sm text-gray-500">{ctx.evidence_summary}</p>
                      </div>
                    )}
                    {ctx.predicted_horizon_minutes != null && ctx.predicted_horizon_minutes > 0 && (
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <TrendingUp size={12} />
                        <span>Prediction horizon: {ctx.predicted_horizon_minutes} minutes</span>
                      </div>
                    )}
                    <a href={`/ai-anomalies-v2?service=${encodeURIComponent(svcKey)}${ctx.anomaly_id ? `&anomaly_id=${encodeURIComponent(ctx.anomaly_id)}` : ''}`} className="inline-flex items-center gap-1 mt-2 text-xs text-purple-400 hover:text-purple-300 transition-colors">
                      <Brain size={12} /> View full anomaly analysis
                    </a>
                  </div>
                )
              })()}

              <div className="card p-3 sm:p-4">
                <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-3">Labels</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
                  {Object.entries(selectedAlert.labels).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2 min-w-0">
                      <span className="text-slate-500 text-sm flex-shrink-0">{key}:</span>
                      <code className="text-blue-400 text-sm break-all min-w-0">{value}</code>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-3 sm:p-4 border-blue-500/20">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <h3 className="text-base sm:text-lg font-semibold text-slate-900">AI Triage</h3>
                  {selectedAlert.ai_decision?.decision ? (
                    <AITriageBadge decision={selectedAlert.ai_decision} />
                  ) : (
                    <button
                      onClick={() => handleRunAiDecision(selectedAlert)}
                      disabled={!selectedAlert.id || runningAiAlertId === selectedAlert.id}
                      className="px-2 py-1 text-xs rounded border border-blue-500/30 text-blue-400 hover:bg-blue-500/10 disabled:opacity-50"
                    >
                      {runningAiAlertId === selectedAlert.id ? 'Running...' : 'Run AI'}
                    </button>
                  )}
                </div>
                {selectedAlert.ai_decision?.decision && (
                  <div className="space-y-2 text-sm">
                    <p><span className="text-slate-500">Summary:</span> <span className="text-slate-800">{formatAiField(selectedAlert.ai_decision.summary)}</span></p>
                    <p><span className="text-slate-500">Reason:</span> <span className="text-slate-800">{formatAiField(selectedAlert.ai_decision.reason)}</span></p>
                    <p><span className="text-slate-500">Noise:</span> <span className="text-slate-800">{formatAiField(selectedAlert.ai_decision.noise_assessment)}</span></p>
                    <div>
                      <p className="text-slate-500">Evidence:</p>
                      <ul className="list-disc pl-5 text-slate-800">
                        {(normalizeArray(selectedAlert.ai_decision.evidence).length > 0 ? normalizeArray(selectedAlert.ai_decision.evidence) : ['-']).map((item, idx) => (
                          <li key={`evidence-${idx}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-slate-500">Recommended Actions:</p>
                      <ul className="list-disc pl-5 text-slate-800">
                        {(normalizeArray(selectedAlert.ai_decision.recommended_actions).length > 0 ? normalizeArray(selectedAlert.ai_decision.recommended_actions) : ['-']).map((item, idx) => (
                          <li key={`action-${idx}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>

              {/* ── Incident Link / Create ── */}
              {canAct(selectedAlert) && (
                <div className="card p-3 sm:p-4 border-blue-500/20">
                  {selectedAlert.incident_id ? (
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <Siren size={18} className="text-blue-400 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-900">Linked Incident</p>
                          <p className="text-xs text-slate-500 truncate">ID: {selectedAlert.incident_id}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => { setSelectedAlert(null); navigate(`/incidents?expand=${selectedAlert.incident_id}`) }}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition-colors flex-shrink-0"
                      >
                        <ExternalLink size={14} />
                        View Incident
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <Siren size={18} className="text-gray-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-700">No Incident Linked</p>
                          <p className="text-xs text-slate-500">Create an incident to track investigation and resolution</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleCreateIncident(selectedAlert)}
                        disabled={creatingIncident || actionLoading !== null}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition-colors disabled:opacity-50 flex-shrink-0"
                      >
                        <Siren size={14} />
                        {creatingIncident ? 'Creating...' : 'Create Incident'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* ── Lifecycle Action Buttons ── */}
              {canAct(selectedAlert) ? (
                <div className="card p-3 sm:p-4 border-gray-200/50">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Alert Actions</h3>
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                    {/* Acknowledge */}
                    {selectedAlert.status !== 'acknowledged' && (
                      <button
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20 transition-colors disabled:opacity-50 min-h-[44px]"
                        disabled={actionLoading !== null}
                        onClick={() => handleLifecycleAction(selectedAlert, 'ack')}
                      >
                        <UserCheck size={16} />
                        {actionLoading === 'ack' ? 'Acknowledging...' : 'Acknowledge'}
                      </button>
                    )}

                    {/* Silence with duration */}
                    <div className="flex-1 flex gap-2">
                      <select
                        value={silenceDuration}
                        onChange={(e) => setSilenceDuration(e.target.value)}
                        className="bg-white border border-slate-300 text-slate-700 rounded px-2 py-1.5 text-sm w-20 flex-shrink-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <option value="30m">30m</option>
                        <option value="1h">1h</option>
                        <option value="4h">4h</option>
                        <option value="24h">24h</option>
                      </select>
                      <button
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200/30 transition-colors disabled:opacity-50 min-h-[44px]"
                        disabled={actionLoading !== null}
                        onClick={() => handleLifecycleAction(selectedAlert, 'silence', { duration: silenceDuration })}
                      >
                        <VolumeX size={16} />
                        {actionLoading === 'silence' ? 'Silencing...' : 'Silence'}
                      </button>
                    </div>

                    {/* Resolve */}
                    <button
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium bg-green-500/10 text-green-400 hover:bg-green-500/20 border border-green-500/20 transition-colors disabled:opacity-50 min-h-[44px]"
                      disabled={actionLoading !== null}
                      onClick={() => handleLifecycleAction(selectedAlert, 'resolve')}
                    >
                      <CheckCircle2 size={16} />
                      {actionLoading === 'resolve' ? 'Resolving...' : 'Resolve'}
                    </button>

                    {/* Dismiss */}
                    <button
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 transition-colors disabled:opacity-50 min-h-[44px]"
                      disabled={actionLoading !== null}
                      onClick={() => handleLifecycleAction(selectedAlert, 'dismiss')}
                    >
                      <XCircle size={16} />
                      {actionLoading === 'dismiss' ? 'Dismissing...' : 'Dismiss'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="card p-3 sm:p-4 border-gray-200/50">
                  <p className="text-xs text-gray-500 text-center">Lifecycle actions are available for platform-generated alerts only.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
