import { Server, Bell, XCircle, BarChart3, Clock, ShieldAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'

interface SparklinePoint { time: number; value: number }

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

// Human-readable labels for catalog_type classification
const TYPE_LABELS: Record<string, string> = {
  REST_API: 'REST API',
  WEB_APP: 'Web App',
  SOAP_API: 'SOAP API',
  WEBHOOK: 'Webhook',
  EXTERNAL_API: 'External API',
  EXTERNAL_SERVICE: 'External',
  DATABASE: 'Database',
  INTERNAL_SERVICE: 'Internal',
  MOBILE_API: 'Mobile API',
  MICROSERVICE: 'Service',
  QUEUE: 'Queue',
  OTHER: 'Other',
  UNKNOWN: 'Unknown',
}

/* Reserved for upcoming feature
function mapSummaryStatus(s: string): 'success' | 'warning' | 'error' {
  if (s === 'OPERATIONAL') return 'success'
  if (s === 'CRITICAL') return 'error'
  return 'warning'
}
function mapSummaryLabel(s: string): string {
  if (s === 'OPERATIONAL') return 'Operational'
  if (s === 'DEGRADED') return 'Degraded'
  if (s === 'CRITICAL') return 'Critical'
  return s
}
*/

export function HomePage() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const [sparkline, setSparkline] = useState<SparklinePoint[]>([])

  useEffect(() => { document.title = 'Rhinometric - Home' }, [])

  // === DATA: Service Summary (external + platform) ===
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

  // === DATA: KPIs (anomalies + alerts) ===
  const { data: kpisData, error } = useQuery({
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

  // === DATA: External services list (for down names + catalog types) ===
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

  const ext = summaryData?.monitored_services ?? null
  // const pla = summaryData?.platform_components ?? null  // Reserved for upcoming feature

  // Sparkline for monitored services
  useEffect(() => {
    if (ext) {
      setSparkline(prev => [...prev, { time: Date.now(), value: ext.total }].slice(-20))
    }
  }, [ext?.total, ext?.healthy])

  // === Derived data for Row 2 cards ===
  const downServices = extServices?.filter(s => s.status?.toLowerCase() === 'down' || s.status?.toLowerCase() === 'critical') ?? []
  const catalogTypes: Record<string, number> = {}
  if (extServices) {
    for (const s of extServices) {
      const ct = s.catalog_type || 'UNKNOWN'
      catalogTypes[ct] = (catalogTypes[ct] || 0) + 1
    }
  }
  const uptimePct = ext && ext.total > 0 ? Math.round((ext.healthy / ext.total) * 100) : null

  // === GLOBAL SEVERITY STATE ===
  const alertsCount = parseInt(kpisData?.alerts_24h?.value ?? '0', 10) || 0
  const globalStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY' =
    downServices.length > 0 ? 'CRITICAL' : alertsCount > 0 ? 'WARNING' : 'HEALTHY'

  // ========== RENDER ==========
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Welcome to Rhinometric</h1>
        <p className="text-text-muted text-sm sm:text-base">AI-Powered Observability & Anomaly Detection Platform</p>
        {!token && <p className="text-warning text-sm mt-2">{'\u26a0\ufe0f'} No authentication token</p>}
        {error && <p className="text-error text-sm mt-2">{'\u274c'} Error: {(error as Error).message}</p>}
      </div>

      {/* ===== CRITICAL BANNER ===== */}
      {globalStatus === 'CRITICAL' && (
        <div className="bg-red-600/20 border-2 border-red-500/60 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-pulse-slow">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-red-500/20 rounded-lg flex-shrink-0">
              <ShieldAlert className="w-7 h-7 text-red-400" />
            </div>
            <div className="min-w-0">
              <p className="text-lg sm:text-xl font-bold text-red-300">CRITICAL: {downServices.length} service{downServices.length !== 1 ? 's' : ''} currently DOWN</p>
              <p className="text-sm text-red-400/80 mt-0.5">Immediate investigation required — platform operational integrity is compromised</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 w-full sm:w-auto">
            <button onClick={() => navigate('/services')} className="flex-1 sm:flex-none px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-semibold transition-colors">
              View Services
            </button>
            <button onClick={() => navigate('/alerts')} className="flex-1 sm:flex-none px-4 py-2 bg-red-600/40 hover:bg-red-600/60 text-red-200 border border-red-500/40 rounded-lg text-sm font-semibold transition-colors">
              View Alerts
            </button>
          </div>
        </div>
      )}

      {/* ===== ROW 1: Main KPI Cards ===== */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 lg:gap-5">

        {/* CARD 1: Monitored Services - PRINCIPAL (2-col span) */}
        <div
          className="card col-span-2 hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-4 sm:p-5 lg:p-6"
          onClick={() => navigate('/services')}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2.5 bg-primary/10 rounded-lg">
              <Server className="w-7 h-7 text-primary" />
            </div>
            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${globalStatus === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : globalStatus === 'WARNING' ? 'bg-warning/20 text-warning border border-warning/30' : 'bg-success/10 text-success'}`}>
              {globalStatus === 'CRITICAL' ? 'CRITICAL' : globalStatus === 'WARNING' ? 'WARNING' : 'Healthy'}
            </span>
          </div>
          <p className="text-text-muted text-sm mb-1">Monitored Services</p>
          <p className="text-3xl sm:text-4xl font-bold text-white mb-2">{ext ? String(ext.total) : '...'}</p>
          {sparkline.length > 1 && (
            <div className="h-10 -mx-2 mb-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparkline}>
                  <Line type="monotone" dataKey="value" stroke={globalStatus === 'CRITICAL' ? '#ef4444' : globalStatus === 'WARNING' ? '#f59e0b' : '#10b981'} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-xs text-text-muted">
            {ext ? (
              <>
                {ext.healthy} up
                {ext.degraded > 0 && <> &middot; {ext.degraded} degraded</>}
                {ext.down > 0 && <> &middot; <span className="text-red-400 font-bold">{ext.down} down</span></>}
              </>
            ) : ''}
          </p>
        </div>

        {/* CARD 5: Alerts (24h) */}
        <div
          className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-3 sm:p-4 lg:p-5"
          onClick={() => navigate('/alerts')}
        >
          <div className="flex items-start justify-between mb-2 sm:mb-3">
            <div className="p-1.5 sm:p-2 bg-primary/10 rounded-lg">
              <Bell className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
            </div>
            <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${kpisData?.alerts_24h?.status === 'success' ? 'bg-success/10 text-success' : kpisData?.alerts_24h?.status === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-warning/10 text-warning'}`}>
              {kpisData?.alerts_24h?.status === 'success' ? 'Healthy' : kpisData?.alerts_24h?.status === 'error' ? 'Critical' : 'Warning'}
            </span>
          </div>
          <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">Alerts (24h)</p>
          <p className="text-lg sm:text-2xl font-bold text-white mb-2">{kpisData?.alerts_24h?.value ?? '...'}</p>
          <p className="text-[10px] sm:text-xs text-text-muted">{kpisData?.alerts_24h?.change || 'No active alerts'}</p>
        </div>
      </div>

      {/* ===== ROW 2: Detail Cards ===== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4 lg:gap-5">

        {/* CARD 6: Services Down */}
        <div
          className={`card cursor-pointer transition-all duration-200 p-4 sm:p-5 ${downServices.length > 0 ? 'border-2 border-red-500/50 hover:border-red-500/80 bg-red-500/5 hover:shadow-lg hover:shadow-red-500/20' : 'hover:border-primary/50 hover:shadow-lg hover:shadow-primary/20'}`}
          onClick={() => navigate('/services')}
        >
          <div className="flex items-start justify-between mb-3">
            <div className={`p-2 rounded-lg ${downServices.length > 0 ? 'bg-red-500/20' : 'bg-primary/10'}`}>
              <XCircle className={`w-5 h-5 ${downServices.length > 0 ? 'text-red-400' : 'text-primary'}`} />
            </div>
            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${downServices.length > 0 ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-success/10 text-success'}`}>
              {downServices.length > 0 ? 'CRITICAL' : 'Healthy'}
            </span>
          </div>
          <p className={`text-sm mb-1 ${downServices.length > 0 ? 'text-red-300 font-medium' : 'text-text-muted'}`}>Services Down</p>
          <p className={`text-2xl font-bold mb-1 ${downServices.length > 0 ? 'text-red-400' : 'text-white'}`}>{extServices ? String(downServices.length) : '...'}</p>
          {downServices.length > 0 && (
            <p className="text-xs text-red-400/80 font-semibold mb-2">Immediate Attention Required</p>
          )}
          <p className="text-xs text-text-muted">
            {extServices
              ? downServices.length > 0
                ? downServices.slice(0, 3).map(s => s.name).join(', ') + (downServices.length > 3 ? ` +${downServices.length - 3} more` : '')
                : 'All services operational'
              : ''}
          </p>
        </div>

        {/* CARD 7: Coverage by Type */}
        <div className="card p-4 sm:p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
              {Object.keys(catalogTypes).length} types
            </span>
          </div>
          <p className="text-text-muted text-sm mb-3">Coverage by Type</p>
          {extServices ? (
            <div className="space-y-1.5">
              {Object.entries(catalogTypes)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-xs text-text-muted truncate mr-2">{TYPE_LABELS[type] || type}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-surface-light rounded-full overflow-hidden">
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
                <p className="text-[10px] text-text-muted mt-1">+{Object.keys(catalogTypes).length - 5} more types</p>
              )}
            </div>
          ) : (
            <p className="text-xs text-text-muted">Loading...</p>
          )}
        </div>

        {/* CARD 8: Uptime Snapshot */}
        <div className="card p-4 sm:p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Clock className="w-5 h-5 text-primary" />
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${uptimePct !== null && uptimePct >= 95 ? 'bg-success/10 text-success' : uptimePct !== null && uptimePct >= 80 ? 'bg-warning/10 text-warning' : uptimePct !== null ? 'bg-red-500/10 text-red-400' : 'bg-success/10 text-success'}`}>
              {uptimePct !== null && uptimePct >= 95 ? 'Good' : uptimePct !== null && uptimePct >= 80 ? 'Fair' : uptimePct !== null ? 'Poor' : '...'}
            </span>
          </div>
          <p className="text-text-muted text-sm mb-1">Uptime Snapshot</p>
          <p className="text-2xl font-bold text-white mb-2">
            {uptimePct !== null ? `${uptimePct}%` : '...'}
          </p>
          <p className="text-xs text-text-muted">
            {ext ? `Based on ${ext.healthy}/${ext.total} services currently up` : ''}
          </p>
        </div>

      </div>
    </div>
  )
}
