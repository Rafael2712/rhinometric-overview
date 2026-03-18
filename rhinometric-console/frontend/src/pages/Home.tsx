import { Activity, Server, AlertTriangle, Bell, TrendingUp, TrendingDown, Shield } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'

// BUILD_MARKER: 20260318_1100 ? forces new Vite content hash
interface SparklinePoint {
  time: number
  value: number
}

interface KPIHistory {
  service_status: SparklinePoint[]
  monitored_hosts: SparklinePoint[]
  platform_health: SparklinePoint[]
  active_anomalies: SparklinePoint[]
  alerts_24h: SparklinePoint[]
}

interface MonitoredServices {
  total: number
  healthy: number
  degraded: number
  down: number
  status: string
}

interface PlatformComponents {
  total: number
  healthy: number
  down: number
  status: string
}

interface ServiceSummary {
  monitored_services: MonitoredServices
  platform_components: PlatformComponents
  total_services: number
  external_services: number
  internal_services: number
  healthy: number
  degraded: number
  down: number
  overall_status: string
}

/** Map backend status to UI badge status key */
function mapSummaryStatus(overall: string): 'success' | 'warning' | 'error' {
  switch (overall) {
    case 'OPERATIONAL': return 'success'
    case 'CRITICAL':    return 'error'
    default:            return 'warning'
  }
}

/** Map backend status to human-readable label */
function mapSummaryLabel(overall: string): string {
  switch (overall) {
    case 'OPERATIONAL': return 'Operational'
    case 'DEGRADED':    return 'Degraded'
    case 'CRITICAL':    return 'Critical'
    default:            return overall
  }
}


export function HomePage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<KPIHistory>({
    service_status: [],
    monitored_hosts: [],
    platform_health: [],
    active_anomalies: [],
    alerts_24h: []
  })

  useEffect(() => {
    document.title = 'Rhinometric - Home'
  }, [])

  const token = useAuthStore((state) => state.token)

  // Fetch KPIs from backend API (used ONLY for anomalies + alerts)
  const { data: kpisData, isLoading, error } = useQuery({
    queryKey: ['kpis', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      const response = await fetch('/api/kpis', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Failed to fetch KPIs')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  // Fetch service summary ? SINGLE SOURCE OF TRUTH for service health.
  // This endpoint returns ALREADY-SEPARATED data:
  //   monitored_services  = external/client services ONLY
  //   platform_components = internal platform services ONLY
  // We NEVER fall back to KPIs or flat fields for service/platform cards.
  const { data: summaryData } = useQuery<ServiceSummary>({
    queryKey: ['services-summary', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      const response = await fetch('/api/services/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Failed to fetch service summary')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  // ??????????????????????????????????????????????
  // STRICT separation: derive from sub-objects ONLY
  // ??????????????????????????????????????????????
  const mon  = summaryData?.monitored_services   // external-only
  const plat = summaryData?.platform_components  // internal-only

  // DEBUG: log separation to console so we can verify no intersection
  useEffect(() => {
    if (summaryData) {
      const m = summaryData.monitored_services
      const p = summaryData.platform_components
      console.group('[Home] Data-source separation audit')
      console.log('Monitored Services (external):', m)
      console.log('Platform Components (internal):', p)
      console.log(`Monitored total=${m.total}, healthy=${m.healthy}, degraded=${m.degraded}, down=${m.down}, status=${m.status}`)
      console.log(`Platform  total=${p.total}, healthy=${p.healthy}, down=${p.down}, status=${p.status}`)
      console.log(`Intersection check: monitored_total(${m.total}) + platform_total(${p.total}) = ${m.total + p.total}, grand_total=${summaryData.total_services}`)
      console.assert(
        m.total + p.total === summaryData.total_services,
        'DATA LEAK: monitored + platform !== total_services'
      )
      console.groupEnd()
    }
  }, [summaryData])

  // Update sparkline history
  useEffect(() => {
    if (kpisData) {
      const now = Date.now()
      setHistory(prev => {
        const updateSeries = (series: SparklinePoint[], newValue: any) => {
          const val = typeof newValue === 'string' ? parseFloat(newValue) || 0 : newValue
          const newSeries = [...series, { time: now, value: val }]
          return newSeries.slice(-20)
        }

        // Service status sparkline: % healthy of EXTERNALS ONLY
        const serviceStatusValue = mon
          ? (mon.total > 0 ? (mon.healthy / mon.total) * 100 : 100)
          : 100

        // Platform health sparkline: % healthy of INTERNALS ONLY
        const platformHealthValue = plat
          ? (plat.total > 0 ? (plat.healthy / plat.total) * 100 : 100)
          : 100

        return {
          service_status: updateSeries(prev.service_status, serviceStatusValue),
          monitored_hosts: updateSeries(prev.monitored_hosts, mon ? mon.total : 0),
          platform_health: updateSeries(prev.platform_health, platformHealthValue),
          active_anomalies: updateSeries(prev.active_anomalies, kpisData.active_anomalies.value),
          alerts_24h: updateSeries(prev.alerts_24h, kpisData.alerts_24h.value)
        }
      })
    }
  }, [kpisData, summaryData])

  // Fetch historical data once on mount
  const { data: historyData } = useQuery({
    queryKey: ['kpis-history', token],
    queryFn: async () => {
      if (!token) return null
      const response = await fetch('/api/kpis/historical', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) return null
      return response.json()
    },
    enabled: !!token,
    staleTime: Infinity
  })

  // Initialize history with fetched data
  useEffect(() => {
    if (historyData) {
      const mapPoints = (points: any[]) => points.map(p => ({
        time: p.timestamp * 1000,
        value: p.value
      }))

      setHistory({
        service_status: mapPoints(historyData.service_status),
        monitored_hosts: mapPoints(historyData.monitored_hosts),
        platform_health: historyData.platform_health ? mapPoints(historyData.platform_health) : [],
        active_anomalies: mapPoints(historyData.active_anomalies),
        alerts_24h: mapPoints(historyData.alerts_24h)
      })
    }
  }, [historyData])

  // ??????????????????????????????????????????????
  // KPI CARDS ? each card uses ONE exclusive data source
  // ??????????????????????????????????????????????
  //
  // Service Status   ? mon  (monitored_services, externals ONLY)
  // Monitored Svcs   ? mon  (monitored_services, externals ONLY)
  // Platform Health  ? plat (platform_components, internals ONLY)
  // Anomaly Groups   ? kpisData.active_anomalies (independent)
  // Alerts (24h)     ? kpisData.alerts_24h       (independent)
  //
  // NO fallback to flat/mixed fields. If summary hasn't loaded ? "Loading?"

  const kpis = kpisData ? [
    // ?? Card 1: Service Status (EXTERNAL ONLY) ??????????????
    {
      name: 'Service Status',
      value: mon ? mapSummaryLabel(mon.status) : 'Loading...',
      status: mon ? mapSummaryStatus(mon.status) : ('success' as const),
      icon: Activity,
      change: mon
        ? `${mon.healthy}/${mon.total} healthy` + (mon.down > 0 ? ` \u00b7 ${mon.down} down` : ' \u00b7 All up')
        : '',
      sparkline: history.service_status,
      trend: 'up',
      link: '/system-health'
    },
    // ?? Card 2: Monitored Services (EXTERNAL ONLY) ??????????
    {
      name: 'Monitored Services',
      value: mon ? String(mon.total) : '...',
      status: mon ? (mon.down > 0 ? 'warning' : 'success') : ('success' as const),
      icon: Server,
      change: mon
        ? `${mon.healthy} up` + (mon.degraded > 0 ? ` \u00b7 ${mon.degraded} degraded` : '') + (mon.down > 0 ? ` \u00b7 ${mon.down} down` : '')
        : '',
      sparkline: history.monitored_hosts,
      trend: 'stable',
      link: '/services'
    },
    // ?? Card 3: Platform Health (INTERNAL ONLY) ?????????????
    {
      name: 'Platform Health',
      value: plat ? mapSummaryLabel(plat.status) : 'Loading...',
      status: plat ? mapSummaryStatus(plat.status) : ('success' as const),
      icon: Shield,
      change: plat
        ? `${plat.healthy}/${plat.total} components` + (plat.down > 0 ? ` \u00b7 ${plat.down} down` : ' \u00b7 All up')
        : '',
      sparkline: history.platform_health,
      trend: 'stable',
      link: '/system-health'
    },
    // ?? Card 4: Active Anomaly Groups (independent) ?????????
    {
      name: 'Active Anomaly Groups',
      value: kpisData.active_anomalies.value,
      status: kpisData.active_anomalies.status,
      icon: AlertTriangle,
      change: kpisData.active_anomalies.change,
      sparkline: history.active_anomalies,
      trend: 'down',
      link: '/anomalies'
    },
    // ?? Card 5: Alerts 24h (independent) ????????????????????
    {
      name: 'Alerts (24h)',
      value: kpisData.alerts_24h.value,
      status: kpisData.alerts_24h.status,
      icon: Bell,
      change: kpisData.alerts_24h.change,
      sparkline: history.alerts_24h,
      trend: 'up',
      link: '/alerts'
    },
  ] : [
    { name: 'Service Status', value: 'Loading...', status: 'success', icon: Activity, change: '', sparkline: [], trend: 'stable', link: '/system-health' },
    { name: 'Monitored Services', value: '...', status: 'success', icon: Server, change: '', sparkline: [], trend: 'stable', link: '/services' },
    { name: 'Platform Health', value: '...', status: 'success', icon: Shield, change: '', sparkline: [], trend: 'stable', link: '/system-health' },
    { name: 'Active Anomaly Groups', value: '...', status: 'success', icon: AlertTriangle, change: '', sparkline: [], trend: 'stable', link: '/anomalies' },
    { name: 'Alerts (24h)', value: '...', status: 'success', icon: Bell, change: '', sparkline: [], trend: 'stable', link: '/alerts' },
  ]

  // Debug logging ? BUILD v2026.03.18a
  useEffect(() => {
    console.log('%c[Home BUILD 2026-03-18a]', 'background:#1e40af;color:#fff;padding:2px 6px;border-radius:3px')
    console.log('Home - Token:', token ? 'present' : 'missing')
    console.log('Home - Loading:', isLoading)
    console.log('Home - Error:', error)
    console.log('Home - KPIs:', kpisData)
    console.log('Home - Summary:', summaryData)
    if (mon) {
      console.log('%cMonitored Services card value = ' + mon.total + ' (source: summaryData.monitored_services.total)', 'color:#10b981;font-weight:bold')
    }
    if (plat) {
      console.log('%cPlatform Health card value = ' + plat.total + ' (source: summaryData.platform_components.total)', 'color:#6366f1;font-weight:bold')
    }
  }, [token, isLoading, error, kpisData, summaryData, mon, plat])

  if (error) {
    console.error('Failed to load KPIs:', error)
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Welcome to Rhinometric</h1>
        <p className="text-text-muted text-sm sm:text-base">AI-Powered Observability & Anomaly Detection Platform</p>
        {!token && <p className="text-warning text-sm mt-2">{'\u26a0\ufe0f'} No authentication token</p>}
        {error && <p className="text-error text-sm mt-2">{'\u274c'} Error: {(error as Error).message}</p>}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 lg:gap-6">
        {kpis.map((kpi) => {
          const Icon = kpi.icon
          const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown
          const trendColor = kpi.trend === 'up' ? 'text-success' : kpi.trend === 'down' ? 'text-error' : 'text-gray-400'

          return (
            <div
              key={kpi.name}
              className="card hover:border-primary/50 cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 p-3 sm:p-4 lg:p-6"
              onClick={() => navigate(kpi.link)}
            >
              <div className="flex items-start justify-between mb-2 sm:mb-4">
                <div className="p-1.5 sm:p-2 bg-primary/10 rounded-lg">
                  <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
                </div>
                <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${kpi.status === 'success' ? 'bg-success/10 text-success' : kpi.status === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-warning/10 text-warning'}`}>
                  {kpi.status === 'success' ? 'Healthy' : kpi.status === 'error' ? 'Critical' : 'Warning'}
                </span>
              </div>
              <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">{kpi.name}</p>
              <div className="flex items-end justify-between mb-2 sm:mb-3">
                <p className="text-lg sm:text-2xl font-bold text-white">{kpi.value}</p>
                {kpi.trend !== 'stable' && (
                  <TrendIcon className={`w-4 h-4 sm:w-5 sm:h-5 ${trendColor}`} />
                )}
              </div>

              {kpi.sparkline.length > 0 && (
                <div className="h-8 sm:h-12 -mx-1 sm:-mx-2 mb-1 sm:mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={kpi.sparkline}>
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={kpi.status === 'success' ? '#10b981' : kpi.status === 'error' ? '#ef4444' : '#f59e0b'}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <p className="text-[10px] sm:text-xs text-text-muted">{kpi.change || 'Last 24 hours'}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
