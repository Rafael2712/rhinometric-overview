import { Activity, Server, AlertTriangle, Bell, Shield, XCircle, BarChart3, Clock } from 'lucide-react'
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
  const pla = summaryData?.platform_components ?? null

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

      {/* ===== ROW 1: Main KPI Cards ===== */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4 lg:gap-5">

        {/* CARD 1: Monitored Services - PRINCIPAL (2-col span) */}
        <div
          className="card col-span-2 hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-4 sm:p-5 lg:p-6"
          onClick={() => navigate('/services')}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2.5 bg-primary/10 rounded-lg">
              <Server className="w-7 h-7 text-primary" />
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${ext && ext.down > 0 ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'}`}>
              {ext && ext.down > 0 ? 'Warning' : 'Healthy'}
            </span>
          </div>
          <p className="text-text-muted text-sm mb-1">Monitored Services</p>
          <p className="text-3xl sm:text-4xl font-bold text-white mb-2">{ext ? String(ext.total) : '...'}</p>
          {sparkline.length > 1 && (
            <div className="h-10 -mx-2 mb-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparkline}>
                  <Line type="monotone" dataKey="value" stroke={ext && ext.down > 0 ? '#f59e0b' : '#10b981'} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="text-xs text-text-muted">
            {ext ? `${ext.healthy} up` + (ext.degraded > 0 ? ` \u00b7 ${ext.degraded} degraded` : '') + (ext.down > 0 ? ` \u00b7 ${ext.down} down` : '') : ''}
          </p>
        </div>

        {/* CARD 2: Service Status */}
        <div
          className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-3 sm:p-4 lg:p-5"
          onClick={() => navigate('/system-health')}
        >
          <div className="flex items-start justify-between mb-2 sm:mb-3">
            <div className="p-1.5 sm:p-2 bg-primary/10 rounded-lg">
              <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
            </div>
            <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${ext ? (mapSummaryStatus(ext.status) === 'success' ? 'bg-success/10 text-success' : mapSummaryStatus(ext.status) === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-warning/10 text-warning') : 'bg-success/10 text-success'}`}>
              {ext ? (mapSummaryStatus(ext.status) === 'success' ? 'Healthy' : mapSummaryStatus(ext.status) === 'error' ? 'Critical' : 'Warning') : 'Healthy'}
            </span>
          </div>
          <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">Service Status</p>
          <p className="text-lg sm:text-2xl font-bold text-white mb-2">{ext ? mapSummaryLabel(ext.status) : 'Loading...'}</p>
          <p className="text-[10px] sm:text-xs text-text-muted">{ext ? `${ext.healthy}/${ext.total} healthy` : ''}</p>
        </div>

        {/* CARD 3: Platform Health - different format */}
        <div
          className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-3 sm:p-4 lg:p-5"
          onClick={() => navigate('/system-health')}
        >
          <div className="flex items-start justify-between mb-2 sm:mb-3">
            <div className="p-1.5 sm:p-2 bg-primary/10 rounded-lg">
              <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
            </div>
            <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${pla ? (pla.down > 0 ? 'bg-red-500/10 text-red-400' : 'bg-success/10 text-success') : 'bg-success/10 text-success'}`}>
              {pla && pla.down > 0 ? 'Critical' : 'Healthy'}
            </span>
          </div>
          <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">Platform Health</p>
          <p className="text-lg sm:text-2xl font-bold text-white mb-2">{pla ? `${pla.healthy}/${pla.total}` : '...'}</p>
          <p className="text-[10px] sm:text-xs text-text-muted">{pla ? (pla.down > 0 ? `${pla.down} component${pla.down > 1 ? 's' : ''} down` : 'All platform components up') : ''}</p>
        </div>

        {/* CARD 4: Active Anomaly Groups */}
        <div
          className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-3 sm:p-4 lg:p-5"
          onClick={() => navigate('/anomalies')}
        >
          <div className="flex items-start justify-between mb-2 sm:mb-3">
            <div className="p-1.5 sm:p-2 bg-primary/10 rounded-lg">
              <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
            </div>
            <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${kpisData?.active_anomalies?.status === 'success' ? 'bg-success/10 text-success' : kpisData?.active_anomalies?.status === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-warning/10 text-warning'}`}>
              {kpisData?.active_anomalies?.status === 'success' ? 'Healthy' : kpisData?.active_anomalies?.status === 'error' ? 'Critical' : 'Warning'}
            </span>
          </div>
          <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">Active Anomaly Groups</p>
          <p className="text-lg sm:text-2xl font-bold text-white mb-2">{kpisData?.active_anomalies?.value ?? '...'}</p>
          <p className="text-[10px] sm:text-xs text-text-muted">{kpisData?.active_anomalies?.change || 'No anomalies'}</p>
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
          className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-4 sm:p-5"
          onClick={() => navigate('/services')}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <XCircle className="w-5 h-5 text-primary" />
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${downServices.length > 0 ? 'bg-red-500/10 text-red-400' : 'bg-success/10 text-success'}`}>
              {downServices.length > 0 ? 'Alert' : 'Healthy'}
            </span>
          </div>
          <p className="text-text-muted text-sm mb-1">Services Down</p>
          <p className="text-2xl font-bold text-white mb-2">{extServices ? String(downServices.length) : '...'}</p>
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
                    <span className="text-xs text-text-muted truncate mr-2">{type}</span>
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
