/* eslint-disable */ console.info("anomaly-ui-v2.1.1");
import { AlertTriangle, TrendingUp, Filter, Download, X, GitMerge,
  Globe, CheckCircle2, Server, Monitor, Layers, MapPin, Shield,
  Clock, Hash, Activity } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'

interface AnomalyOccurrence {
  timestamp: string
  current_value: number
  expected_value: number
  deviation_percent: number
  severity: string
  confidence: number | null
  analysis: string | null
}

interface AnomalyGroup {
  fingerprint: string
  entity_type: string
  entity_name: string
  metric_name: string
  source: string
  first_seen: string
  last_seen: string
  occurrence_count: number
  severity_current: string
  status: string
  occurrences: AnomalyOccurrence[]
  environment: string
  service_group: string
  region: string | null
  cluster: string | null
  priority: number
  tags: string[] | null
  metadata: Record<string, any> | null
}

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

function PriorityBadge({ priority, entityType }: { priority: number; entityType: string }) {
  if (priority === 1 || entityType === 'service') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/25">
        <Shield size={9} />
        SERVICE
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-500/10 text-gray-500 border border-gray-600/20">
      INFRA
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    active: { color: 'bg-error/20 text-error border-error/30', label: 'ACTIVE' },
    acknowledged: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'ACKED' },
    false_positive: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', label: 'FALSE POS' },
    suppressed: { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', label: 'SUPPRESSED' },
    resolved: { color: 'bg-green-500/20 text-green-400 border-green-500/30', label: 'RESOLVED' },
    alert_created: { color: 'bg-purple-500/20 text-purple-400 border-purple-500/30', label: 'ALERTED' },
  }
  const c = config[status] || config.active
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${c.color}`}>
      {c.label}
    </span>
  )
}

export function AnomaliesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const urlMetric = searchParams.get('metric') || ''
  const urlEntity = searchParams.get('entity') || ''
  const urlEntityType = searchParams.get('entity_type') || ''

  const [selectedGroup, setSelectedGroup] = useState<AnomalyGroup | null>(null)
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>(urlEntityType)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [deepLinkHandled, setDeepLinkHandled] = useState(false)
  const token = useAuthStore((state) => state.token)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  useEffect(() => {
    document.title = 'Rhinometric - AI Anomaly Detection'
  }, [])

  const { data: groupsData, isLoading, error } = useQuery({
    queryKey: ['anomalies', token, entityTypeFilter, statusFilter],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({ page_size: '50' })
      if (entityTypeFilter) params.set('entity_type', entityTypeFilter)
      if (statusFilter) params.set('status', statusFilter)
      const response = await fetch(`/api/anomalies?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.status === 503) throw new Error('AI_SERVICE_UNAVAILABLE')
      if (!response.ok) throw new Error('Failed to fetch anomalies')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
    retry: false,
  })

  // ── Deep link: auto-select matching anomaly group from URL params ──
  useEffect(() => {
    if (deepLinkHandled || !groupsData?.anomaly_groups?.length) return
    if (!urlMetric && !urlEntity) return

    const groups: AnomalyGroup[] = groupsData.anomaly_groups
    const match = groups.find((g: AnomalyGroup) => {
      const metricMatch = !urlMetric || g.metric_name === urlMetric
      const entityMatch = !urlEntity || g.entity_name === urlEntity
      return metricMatch && entityMatch
    })
    if (match) {
      setSelectedGroup(match)
    }
    setDeepLinkHandled(true)
    // Clean URL params after handling (keeps URL clean)
    if (urlMetric || urlEntity) {
      setSearchParams({}, { replace: true })
    }
  }, [groupsData, urlMetric, urlEntity, deepLinkHandled, setSearchParams])

  const statusMutation = useMutation({
    mutationFn: async ({ fingerprint, status }: { fingerprint: string; status: string }) => {
      const response = await fetch(`/api/anomalies/${fingerprint}/status`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })
      if (!response.ok) throw new Error('Failed to update status')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] })
    }
  })

  const groups: AnomalyGroup[] = groupsData?.anomaly_groups || []
  const isAIUnavailable = error && (error as Error).message === 'AI_SERVICE_UNAVAILABLE'

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2 sm:mb-6">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">AI Anomaly Detection</h1>
            <span className="inline-flex items-center self-start px-3 py-1 rounded-full text-xs font-medium bg-warning/10 text-warning border border-warning/30" title="Experimental AI algorithms">
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
            <span className="text-sm text-gray-400 hidden sm:inline">Status:</span>
            <select
              className="bg-surface-light border border-gray-700 text-white rounded px-2 sm:px-3 py-1.5 text-sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
              <option value="suppressed">Suppressed</option>
              <option value="alert_created">Alert Created</option>
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

      {/* AI Service Unavailable */}
      {isAIUnavailable && (
        <div className="card bg-warning/10 border-warning/30">
          <div className="flex items-start gap-3 sm:gap-4">
            <AlertTriangle className="text-warning mt-1 flex-shrink-0" size={24} />
            <div className="flex-1 min-w-0">
              <h3 className="text-warning font-semibold mb-2 text-sm sm:text-base">AI Anomaly Detection Engine Unavailable</h3>
              <p className="text-warning/80 text-xs sm:text-sm mb-3">The AI Detection Engine is temporarily unavailable.</p>
              <ul className="list-disc list-inside text-warning/80 text-xs sm:text-sm space-y-1 mb-3">
                <li>Service is starting up (please wait 30 seconds)</li>
                <li>Service crashed or stopped (check container logs)</li>
                <li>Network connectivity issues</li>
              </ul>
              <p className="text-warning/80 text-xs sm:text-sm">
                <strong>Note:</strong> Check that rhinometric-ai-anomaly container is running on port 8085.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Anomaly Groups Table */}
      <div className="card p-0 sm:p-0">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-gray-400 text-sm">Loading anomaly groups...</p>
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
        ) : groups.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <CheckCircle2 className="text-success mb-4" size={48} />
            <p className="text-white text-lg font-semibold mb-1">No Anomalies Detected</p>
            <p className="text-gray-400 text-sm">AI engine is monitoring &mdash; all metrics within expected ranges</p>
          </div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-center px-3 py-3 text-sm font-semibold text-gray-400 w-[70px]"></th>
                    <th className="text-left px-3 py-3 text-sm font-semibold text-gray-400">Entity</th>
                    <th className="text-left px-3 py-3 text-sm font-semibold text-gray-400">Metric</th>
                    <th className="text-center px-3 py-3 text-sm font-semibold text-gray-400">Hits</th>
                    <th className="text-left px-3 py-3 text-sm font-semibold text-gray-400">Severity</th>
                    <th className="text-left px-3 py-3 text-sm font-semibold text-gray-400">Last Seen</th>
                    <th className="text-center px-3 py-3 text-sm font-semibold text-gray-400">Status</th>
                    <th className="text-left px-3 py-3 text-sm font-semibold text-gray-400">Context</th>
                    <th className="text-center px-3 py-3 text-sm font-semibold text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map((group) => (
                    <tr key={group.fingerprint} className="border-b border-gray-700/50 hover:bg-surface-light cursor-pointer transition-colors" onClick={() => setSelectedGroup(group)}>
                      <td className="px-3 py-3 text-center">
                        <PriorityBadge priority={group.priority} entityType={group.entity_type} />
                      </td>
                      <td className="px-3 py-3">
                        <EntityBadge entityType={group.entity_type} entityName={group.entity_name} />
                      </td>
                      <td className="px-3 py-3">
                        <code className="text-xs text-primary bg-primary/10 px-2 py-1 rounded block truncate max-w-[180px]" title={group.metric_name}>
                          {group.metric_name}
                        </code>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-primary/15 text-primary border border-primary/25">
                          <Hash size={10} />
                          {group.occurrence_count}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          group.severity_current === 'critical' || group.severity_current === 'high' ? 'bg-error/20 text-error' :
                          group.severity_current === 'medium' ? 'bg-warning/20 text-warning' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {group.severity_current.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-xs text-gray-300 whitespace-nowrap">
                        {new Date(group.last_seen).toLocaleTimeString()}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <StatusBadge status={group.status} />
                      </td>
                      <td className="px-3 py-3">
                        <div className="space-y-1">
                          {group.environment && group.environment !== 'unknown' && (
                            <div className="flex items-center gap-1">
                              <MapPin size={10} className="text-emerald-400" />
                              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                group.environment === 'production' || group.environment === 'produccion'
                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  : group.environment === 'staging' || group.environment === 'Staging'
                                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                                  : 'bg-gray-500/15 text-gray-400 border border-gray-500/30'
                              }`}>{group.environment}</span>
                            </div>
                          )}
                          {group.service_group && group.service_group !== 'default' && (
                            <div className="flex items-center gap-1">
                              <Layers size={10} className="text-violet-400" />
                              <span className="text-[10px] text-violet-300 bg-violet-500/10 px-1.5 py-0.5 rounded border border-violet-500/20">{group.service_group}</span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${group.last_seen}?entity_type=${encodeURIComponent(group.entity_type)}&entity_name=${encodeURIComponent(group.entity_name)}&metric_name=${encodeURIComponent(group.metric_name)}&source=${encodeURIComponent(group.source)}`) }}
                            className="text-purple-400 hover:bg-purple-500/10 text-xs font-medium px-3 py-1 rounded transition-colors flex items-center gap-1"
                            title="Full correlation analysis"
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
              {groups.map((group) => (
                <div key={group.fingerprint} className="p-3 sm:p-4 hover:bg-surface-light cursor-pointer transition-colors active:bg-surface-light" onClick={() => setSelectedGroup(group)}>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <EntityBadge entityType={group.entity_type} entityName={group.entity_name} />
                      <PriorityBadge priority={group.priority} entityType={group.entity_type} />
                    </div>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                      group.severity_current === 'critical' || group.severity_current === 'high' ? 'bg-error/20 text-error' :
                      group.severity_current === 'medium' ? 'bg-warning/20 text-warning' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {group.severity_current.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <code className="text-xs text-primary bg-primary/10 px-2 py-0.5 rounded truncate">{group.metric_name}</code>
                    <span className="text-[10px] text-gray-500 bg-gray-700/50 px-1.5 py-0.5 rounded flex-shrink-0">{group.source}</span>
                    <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded flex-shrink-0">
                      <Hash size={8} />{group.occurrence_count}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">{new Date(group.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      <StatusBadge status={group.status} />
                    </div>
                    {group.environment && group.environment !== 'unknown' && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${
                        group.environment === 'production' || group.environment === 'produccion'
                          ? 'bg-emerald-500/15 text-emerald-400'
                          : 'bg-amber-500/15 text-amber-400'
                      }`}>{group.environment}</span>
                    )}
                  </div>
                  <div className="flex items-center justify-end text-xs">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/correlations/${group.last_seen}?entity_type=${encodeURIComponent(group.entity_type)}&entity_name=${encodeURIComponent(group.entity_name)}&metric_name=${encodeURIComponent(group.metric_name)}&source=${encodeURIComponent(group.source)}`) }}
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

      {/* Detail Modal */}
      {selectedGroup && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-surface border border-gray-700 rounded-t-xl sm:rounded-lg shadow-2xl w-full sm:max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-surface z-10 flex items-center justify-between p-3 sm:p-4 border-b border-gray-700">
              <div className="min-w-0 flex-1 mr-3">
                <h2 className="text-lg sm:text-xl font-bold text-white truncate">Anomaly Group Details</h2>
                <p className="text-xs text-gray-400 truncate font-mono">{selectedGroup.fingerprint}</p>
              </div>
              <button onClick={() => setSelectedGroup(null)} className="p-2 bg-error/20 hover:bg-error/30 rounded-lg transition-colors flex-shrink-0" title="Close">
                <X className="text-white" size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {/* Entity & status badge row */}
              <div className="flex items-center gap-3 flex-wrap">
                <EntityBadge entityType={selectedGroup.entity_type} entityName={selectedGroup.entity_name} />
                <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-1 rounded">Source: {selectedGroup.source}</span>
                {selectedGroup.environment && selectedGroup.environment !== 'unknown' && (
                  <span className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${
                    selectedGroup.environment === 'production' || selectedGroup.environment === 'produccion'
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : selectedGroup.environment === 'staging' || selectedGroup.environment === 'Staging'
                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                      : 'bg-gray-500/15 text-gray-400 border border-gray-500/30'
                  }`}>
                    <MapPin size={12} />
                    {selectedGroup.environment}
                  </span>
                )}
                {selectedGroup.service_group && selectedGroup.service_group !== 'default' && (
                  <span className="text-xs text-violet-300 bg-violet-500/10 px-2 py-1 rounded border border-violet-500/20 flex items-center gap-1">
                    <Layers size={12} />
                    {selectedGroup.service_group}
                  </span>
                )}
                <StatusBadge status={selectedGroup.status} />
              </div>

              {/* Overview grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Metric</p>
                  <code className="text-sm text-primary font-mono break-all">{selectedGroup.metric_name}</code>
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Severity</p>
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                    selectedGroup.severity_current === 'critical' || selectedGroup.severity_current === 'high' ? 'bg-error/20 text-error' :
                    selectedGroup.severity_current === 'medium' ? 'bg-warning/20 text-warning' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {selectedGroup.severity_current.toUpperCase()}
                  </span>
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Occurrences</p>
                  <div className="text-lg font-bold text-primary flex items-center gap-1">
                    <Hash size={14} />
                    {selectedGroup.occurrence_count}
                  </div>
                </div>
                <div className="card bg-surface-light p-2 sm:p-3">
                  <p className="text-xs text-gray-400 mb-1">Time Range</p>
                  <div className="text-xs text-white">
                    <div className="flex items-center gap-1">
                      <Clock size={10} className="text-gray-400" />
                      {new Date(selectedGroup.first_seen).toLocaleTimeString()}
                    </div>
                    <div className="flex items-center gap-1 text-gray-400 mt-0.5">
                      <Activity size={10} />
                      {new Date(selectedGroup.last_seen).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Occurrence Timeline */}
              <div className="card p-3 sm:p-4">
                <h3 className="text-sm sm:text-base font-semibold text-white mb-3 flex items-center gap-2">
                  <Activity size={16} className="text-primary" />
                  Occurrence Timeline ({selectedGroup.occurrence_count})
                </h3>
                <div className="space-y-2 max-h-[240px] overflow-y-auto">
                  {selectedGroup.occurrences.map((occ, i) => (
                    <div key={i} className="flex items-center justify-between py-2 px-3 rounded bg-surface-light/50 border border-gray-700/30">
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-400 font-mono whitespace-nowrap">
                          {new Date(occ.timestamp).toLocaleTimeString()}
                        </span>
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          occ.severity === 'critical' || occ.severity === 'high' ? 'bg-error/20 text-error' :
                          occ.severity === 'medium' ? 'bg-warning/20 text-warning' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {occ.severity.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-white font-medium">{occ.current_value.toFixed(1)}</span>
                        <span className="text-gray-500">/ {occ.expected_value.toFixed(1)}</span>
                        <span className={`font-semibold ${occ.deviation_percent > 0 ? 'text-error' : 'text-green-400'}`}>
                          <TrendingUp size={10} className="inline mr-0.5" />
                          {occ.deviation_percent > 0 ? '+' : ''}{occ.deviation_percent.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Analysis from latest occurrence */}
              {selectedGroup.occurrences[0]?.analysis && (
                <div className="card bg-primary/5 border-primary/20 p-3 sm:p-4">
                  <h3 className="text-sm sm:text-base font-semibold text-primary mb-2">AI Analysis</h3>
                  <p className="text-xs sm:text-sm text-gray-300">{selectedGroup.occurrences[0].analysis}</p>
                </div>
              )}

              {/* Tags */}
              {selectedGroup.tags && selectedGroup.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {selectedGroup.tags.map((tag, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-gray-700/50 text-gray-400">{tag}</span>
                  ))}
                </div>
              )}

              {/* Lifecycle Actions */}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Lifecycle</p>
                <div className="flex flex-wrap gap-2">
                  {selectedGroup.status === 'active' && (
                    <>
                      <button
                        className="btn btn-secondary flex-1 min-h-[40px] text-sm flex items-center justify-center gap-2"
                        onClick={() => { statusMutation.mutate({ fingerprint: selectedGroup.fingerprint, status: 'acknowledged' }); setSelectedGroup({ ...selectedGroup, status: 'acknowledged' }) }}
                      >
                        Acknowledge
                      </button>
                      <button
                        className="btn btn-secondary flex-1 min-h-[40px] text-sm flex items-center justify-center gap-2"
                        onClick={() => { statusMutation.mutate({ fingerprint: selectedGroup.fingerprint, status: 'false_positive' }); setSelectedGroup({ ...selectedGroup, status: 'false_positive' }) }}
                      >
                        False Positive
                      </button>
                      <button
                        className="btn btn-secondary flex-1 min-h-[40px] text-sm flex items-center justify-center gap-2"
                        onClick={() => { statusMutation.mutate({ fingerprint: selectedGroup.fingerprint, status: 'suppressed' }); setSelectedGroup({ ...selectedGroup, status: 'suppressed' }) }}
                      >
                        Suppress
                      </button>
                    </>
                  )}
                  {selectedGroup.status !== 'active' && selectedGroup.status !== 'resolved' && (
                    <button
                      className="btn btn-secondary flex-1 min-h-[40px] text-sm flex items-center justify-center gap-2"
                      onClick={() => { statusMutation.mutate({ fingerprint: selectedGroup.fingerprint, status: 'active' }); setSelectedGroup({ ...selectedGroup, status: 'active' }) }}
                    >
                      Reactivate
                    </button>
                  )}
                  {selectedGroup.status !== 'resolved' && (
                    <button
                      className="btn btn-secondary flex-1 min-h-[40px] text-sm flex items-center justify-center gap-2 text-green-400"
                      onClick={() => { statusMutation.mutate({ fingerprint: selectedGroup.fingerprint, status: 'resolved' }); setSelectedGroup({ ...selectedGroup, status: 'resolved' }) }}
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>

              {/* Correlate */}
              <div>
                <button
                  onClick={() => { setSelectedGroup(null); navigate(`/correlations/${selectedGroup.last_seen}?entity_type=${encodeURIComponent(selectedGroup.entity_type)}&entity_name=${encodeURIComponent(selectedGroup.entity_name)}&metric_name=${encodeURIComponent(selectedGroup.metric_name)}&source=${encodeURIComponent(selectedGroup.source)}`) }}
                  className="btn w-full min-h-[44px] text-sm flex items-center justify-center gap-2 bg-purple-500/15 text-purple-400 border border-purple-500/25 hover:bg-purple-500/25"
                >
                  <GitMerge size={16} />
                  Full Correlation Analysis
                </button>
              </div>

              {/* Footer */}
              <div className="text-xs text-gray-500 text-center">
                Anomaly Lifecycle Engine v2.1 &mdash; Deduplication with occurrence tracking
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}