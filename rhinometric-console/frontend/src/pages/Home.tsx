import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { useNavigate } from 'react-router-dom'
import {
  Bell, XCircle, Server, BarChart3, Target, AlertTriangle,
  ArrowRight, Flame,
} from 'lucide-react'

// ??? Types ???????????????????????????????????????????????????

interface MonitoredServices {
  total: number; healthy: number; degraded: number; down: number; status: string
}
interface PlatformComponents {
  total: number; healthy: number; down: number; status: string
}
interface ServiceSummary {
  monitored_services: MonitoredServices
  platform_components: PlatformComponents
}
interface ExternalService {
  id: number; name: string; service_type: string; catalog_type: string
  status: string; status_message: string; last_check_at: string | null
  last_response_time_ms: number | null; enabled: boolean
}
interface SLOSummary {
  availability_pct: number | null
  latency_p95_ms: number | null
  health_score_avg: number | null
  error_budget_availability: number | null
  overall_status: string
  services_healthy: number
  services_at_risk: number
  services_breached: number
  total_services: number
}
interface Incident {
  id: string; status: string; severity: string; title: string
}
interface IncidentsResponse {
  incidents: Incident[]; total: number
}

const TYPE_LABELS: Record<string, string> = {
  REST_API: 'REST API', WEB_APP: 'Web App', SOAP_API: 'SOAP API',
  WEBHOOK: 'Webhook', EXTERNAL_API: 'External API', EXTERNAL_SERVICE: 'External',
  DATABASE: 'Database', INTERNAL_SERVICE: 'Internal', MOBILE_API: 'Mobile API',
  MICROSERVICE: 'Service', QUEUE: 'Queue', OTHER: 'Other', UNKNOWN: 'Unknown',
}

// ??? Helpers ?????????????????????????????????????????????????

function handleKeyDown(navigate: ReturnType<typeof useNavigate>, route: string) {
  return (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      navigate(route)
    }
  }
}

// ??? Component ???????????????????????????????????????????????

export function HomePage() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)

  useEffect(() => { document.title = 'Rhinometric - Home' }, [])

  // DATA: Service Summary
  const { data: summaryData } = useQuery<ServiceSummary>({
    queryKey: ['services-summary', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/services/summary', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  // DATA: KPIs
  const { data: kpisData } = useQuery({
    queryKey: ['kpis', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/kpis', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  // DATA: External services
  const { data: extServices } = useQuery<ExternalService[]>({
    queryKey: ['external-services', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/external-services', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 10000,
  })

  // DATA: SLO Summary
  const { data: sloSummary } = useQuery<SLOSummary>({
    queryKey: ['slo-summary-home', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/slo/summary?time_range=24h', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  // DATA: Incidents
  const { data: incidentsData } = useQuery<IncidentsResponse>({
    queryKey: ['incidents-home', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/incidents', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  // ??? Derived ?????????????????????????????????????????????

  const ext = summaryData?.monitored_services ?? null
  const downServices = extServices?.filter(s => s.status?.toLowerCase() === 'down' || s.status?.toLowerCase() === 'critical') ?? []
  const alertsCount = Number(kpisData?.alerts_24h?.value ?? 0)
  const anomaliesCount = Number(kpisData?.active_anomalies?.value ?? 0)
  const servicesDown = downServices.length

  // Catalog type distribution
  const catalogTypes: Record<string, number> = {}
  if (extServices) {
    for (const s of extServices) {
      const ct = s.catalog_type || 'UNKNOWN'
      catalogTypes[ct] = (catalogTypes[ct] || 0) + 1
    }
  }

  // Incidents
  const allIncidents = incidentsData?.incidents ?? []
  const openIncidents = allIncidents.filter(i => i.status === 'open' || i.status === 'investigating' || i.status === 'triggered')

  // Global status
  const globalStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY' =
    servicesDown > 0 ? 'CRITICAL'
    : (alertsCount > 0 || anomaliesCount > 0) ? 'WARNING'
    : 'HEALTHY'

  const statusConfig = {
    CRITICAL: { bg: 'bg-red-500/10', border: 'border-red-500/40', text: 'text-red-400', label: 'CRITICAL', dot: 'bg-red-400' },
    WARNING: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/40', text: 'text-yellow-400', label: 'WARNING', dot: 'bg-yellow-400' },
    HEALTHY: { bg: 'bg-green-500/10', border: 'border-green-500/40', text: 'text-green-400', label: 'HEALTHY', dot: 'bg-green-400' },
  }[globalStatus]

  // SLO helpers
  const sloStatus = sloSummary?.overall_status || 'no_data'
  const sloAvail = sloSummary?.availability_pct
  const sloLabel = sloStatus === 'healthy' ? 'Meeting SLO' : sloStatus === 'at_risk' ? 'At Risk' : sloStatus === 'breached' ? 'Breached' : 'No Data'
  const sloColor = sloStatus === 'healthy' ? 'text-green-400' : sloStatus === 'at_risk' ? 'text-yellow-400' : sloStatus === 'breached' ? 'text-red-400' : 'text-gray-500'

  // ??? RENDER ??????????????????????????????????????????????

  return (
    <div className="space-y-6">

      {/* ??? 1. GLOBAL STATUS BAR ??? */}
      <div className={`rounded-lg border ${statusConfig.border} ${statusConfig.bg} p-4 sm:p-5`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <span className={`w-3 h-3 rounded-full flex-shrink-0 ${statusConfig.dot}`} />
            <div className="min-w-0">
              <span className={`text-lg font-bold ${statusConfig.text}`}>{statusConfig.label}</span>
              <p className="text-sm text-gray-400 mt-0.5">
                {servicesDown} service{servicesDown !== 1 ? 's' : ''} down
                {' \u00b7 '}{alertsCount} alert{alertsCount !== 1 ? 's' : ''}
                {' \u00b7 '}{anomaliesCount} anomal{anomaliesCount !== 1 ? 'ies' : 'y'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={() => navigate('/alerts')}
              className="px-3 py-1.5 text-sm font-medium rounded-md bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              View Alerts
            </button>
            <button
              onClick={() => navigate('/services')}
              className="px-3 py-1.5 text-sm font-medium rounded-md bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            >
              View Services
            </button>
          </div>
        </div>
      </div>

      {/* ??? 2. PRIMARY ACTION ROW ??? */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* Alerts */}
        <div
          role="button"
          tabIndex={0}
          aria-label={`${alertsCount} active alerts. View Alerts.`}
          onClick={() => navigate('/alerts')}
          onKeyDown={handleKeyDown(navigate, '/alerts')}
          className={`rounded-lg border p-5 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 ${
            alertsCount > 0
              ? 'border-yellow-500/40 bg-yellow-500/5 hover:bg-yellow-500/10'
              : 'border-gray-700/50 bg-gray-800/50 hover:bg-gray-700/40'
          }`}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-lg ${alertsCount > 0 ? 'bg-yellow-500/15' : 'bg-gray-700/50'}`}>
              <Bell className={`w-5 h-5 ${alertsCount > 0 ? 'text-yellow-400' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-sm font-medium text-gray-400">Alerts</h3>
          </div>
          <p className={`text-3xl font-bold mb-3 ${alertsCount > 0 ? 'text-yellow-400' : 'text-white'}`}>
            {kpisData ? alertsCount : '\u2026'}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            View Alerts <ArrowRight className="w-3 h-3" />
          </span>
        </div>

        {/* AI Anomalies */}
        <div
          role="button"
          tabIndex={0}
          aria-label={`${anomaliesCount} active anomalies. Investigate.`}
          onClick={() => navigate('/ai-anomalies-v2')}
          onKeyDown={handleKeyDown(navigate, '/ai-anomalies-v2')}
          className={`rounded-lg border p-5 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 ${
            anomaliesCount > 0
              ? 'border-yellow-500/40 bg-yellow-500/5 hover:bg-yellow-500/10'
              : 'border-gray-700/50 bg-gray-800/50 hover:bg-gray-700/40'
          }`}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-lg ${anomaliesCount > 0 ? 'bg-yellow-500/15' : 'bg-gray-700/50'}`}>
              <AlertTriangle className={`w-5 h-5 ${anomaliesCount > 0 ? 'text-yellow-400' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-sm font-medium text-gray-400">AI Anomalies</h3>
          </div>
          <p className={`text-3xl font-bold mb-3 ${anomaliesCount > 0 ? 'text-yellow-400' : 'text-white'}`}>
            {kpisData ? anomaliesCount : '\u2026'}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            Investigate <ArrowRight className="w-3 h-3" />
          </span>
        </div>

        {/* Services Down */}
        <div
          role="button"
          tabIndex={0}
          aria-label={`${servicesDown} services down. View Services.`}
          onClick={() => navigate('/services')}
          onKeyDown={handleKeyDown(navigate, '/services')}
          className={`rounded-lg border p-5 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 ${
            servicesDown > 0
              ? 'border-red-500/40 bg-red-500/5 hover:bg-red-500/10'
              : 'border-gray-700/50 bg-gray-800/50 hover:bg-gray-700/40'
          }`}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-lg ${servicesDown > 0 ? 'bg-red-500/15' : 'bg-gray-700/50'}`}>
              <XCircle className={`w-5 h-5 ${servicesDown > 0 ? 'text-red-400' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-sm font-medium text-gray-400">Services Down</h3>
          </div>
          <p className={`text-3xl font-bold mb-3 ${servicesDown > 0 ? 'text-red-400' : 'text-white'}`}>
            {extServices ? servicesDown : '\u2026'}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            View Services <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </div>

      {/* ??? 3. SECONDARY SECTION ??? */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* Monitored Services */}
        <div
          role="button"
          tabIndex={0}
          aria-label={`${ext?.total ?? 0} monitored services. Open Services.`}
          onClick={() => navigate('/services')}
          onKeyDown={handleKeyDown(navigate, '/services')}
          className="rounded-lg border border-gray-700/50 bg-gray-800/50 p-5 cursor-pointer transition-colors hover:bg-gray-700/40 focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-gray-700/50">
              <Server className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-gray-400">Monitored Services</h3>
          </div>
          <p className="text-3xl font-bold text-white mb-3">{ext ? ext.total : '\u2026'}</p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            Open Services <ArrowRight className="w-3 h-3" />
          </span>
        </div>

        {/* Coverage by Type (NOT clickable) */}
        <div className="rounded-lg border border-gray-700/50 bg-gray-800/50 p-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-gray-700/50">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-gray-400">Coverage by Type</h3>
          </div>
          {extServices ? (
            <div className="space-y-2">
              {Object.entries(catalogTypes)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-xs text-gray-400 truncate mr-2">{TYPE_LABELS[type] || type}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${(count / (extServices?.length || 1)) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-white w-5 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              {Object.keys(catalogTypes).length > 5 && (
                <p className="text-[10px] text-gray-500 mt-1">+{Object.keys(catalogTypes).length - 5} more</p>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-500">Loading\u2026</p>
          )}
        </div>

        {/* Service Levels (SLO) */}
        <div
          role="button"
          tabIndex={0}
          aria-label={`SLO status: ${sloLabel}. View details.`}
          onClick={() => navigate('/slo')}
          onKeyDown={handleKeyDown(navigate, '/slo')}
          className="rounded-lg border border-gray-700/50 bg-gray-800/50 p-5 cursor-pointer transition-colors hover:bg-gray-700/40 focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${sloStatus === 'breached' ? 'bg-red-500/15' : sloStatus === 'at_risk' ? 'bg-yellow-500/15' : 'bg-gray-700/50'}`}>
                <Target className={`w-5 h-5 ${sloStatus === 'breached' ? 'text-red-400' : sloStatus === 'at_risk' ? 'text-yellow-400' : 'text-primary'}`} />
              </div>
              <h3 className="text-sm font-medium text-gray-400">Service Levels</h3>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              sloStatus === 'healthy' ? 'bg-green-500/10 text-green-400'
              : sloStatus === 'at_risk' ? 'bg-yellow-500/10 text-yellow-400'
              : sloStatus === 'breached' ? 'bg-red-500/10 text-red-400'
              : 'bg-gray-700/30 text-gray-500'
            }`}>
              {sloLabel}
            </span>
          </div>
          <p className={`text-3xl font-bold mb-3 ${sloColor}`}>
            {sloAvail != null ? `${sloAvail}%` : '\u2014'}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            View details <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </div>

      {/* ??? 4. INCIDENTS (optional ? data available) ??? */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          role="button"
          tabIndex={0}
          aria-label={`${openIncidents.length} open incidents. View Incidents.`}
          onClick={() => navigate('/incidents')}
          onKeyDown={handleKeyDown(navigate, '/incidents')}
          className={`rounded-lg border p-5 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 ${
            openIncidents.length > 0
              ? 'border-red-500/40 bg-red-500/5 hover:bg-red-500/10'
              : 'border-gray-700/50 bg-gray-800/50 hover:bg-gray-700/40'
          }`}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className={`p-2 rounded-lg ${openIncidents.length > 0 ? 'bg-red-500/15' : 'bg-gray-700/50'}`}>
              <Flame className={`w-5 h-5 ${openIncidents.length > 0 ? 'text-red-400' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-sm font-medium text-gray-400">Open Incidents</h3>
          </div>
          <p className={`text-3xl font-bold mb-3 ${openIncidents.length > 0 ? 'text-red-400' : 'text-white'}`}>
            {incidentsData ? openIncidents.length : '\u2026'}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
            View Incidents <ArrowRight className="w-3 h-3" />
          </span>
        </div>
      </div>

    </div>
  )
}
