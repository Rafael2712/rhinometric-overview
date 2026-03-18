import { Activity, Server, AlertTriangle, Bell, TrendingUp, TrendingDown, Shield } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { useNavigate } from 'react-router-dom'

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
}

function mapSummaryStatus(overall: string): 'success' | 'warning' | 'error' {
  switch (overall) {
    case 'OPERATIONAL': return 'success'
    case 'CRITICAL':    return 'error'
    default:            return 'warning'
  }
}

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

  const { data: kpisData, error } = useQuery({
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

  // EXTERNAL services only (for Service Status + Monitored Services cards)
  const ext = summaryData?.monitored_services ?? null
  // INTERNAL platform services only (for Platform Health card)
  const pla = summaryData?.platform_components ?? null

  useEffect(() => {
    if (kpisData) {
      const now = Date.now()
      setHistory(prev => {
        const push = (series: SparklinePoint[], v: any) => {
          const val = typeof v === 'string' ? parseFloat(v) || 0 : v
          return [...series, { time: now, value: val }].slice(-20)
        }
        return {
          service_status: push(prev.service_status, ext ? (ext.total > 0 ? (ext.healthy / ext.total) * 100 : 100) : 100),
          monitored_hosts: push(prev.monitored_hosts, ext ? ext.total : 0),
          platform_health: push(prev.platform_health, pla ? (pla.total > 0 ? (pla.healthy / pla.total) * 100 : 100) : 100),
          active_anomalies: push(prev.active_anomalies, kpisData.active_anomalies.value),
          alerts_24h: push(prev.alerts_24h, kpisData.alerts_24h.value)
        }
      })
    }
  }, [kpisData, summaryData])

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

  const kpis = kpisData ? [
    {
      name: 'Service Status',
      value: ext ? mapSummaryLabel(ext.status) : 'Loading...',
      status: ext ? mapSummaryStatus(ext.status) : ('success' as const),
      icon: Activity,
      change: ext ? `${ext.healthy}/${ext.total} healthy` + (ext.down > 0 ? ` \u00b7 ${ext.down} down` : ' \u00b7 All up') : '',
      sparkline: history.service_status,
      trend: 'up',
      link: '/system-health'
    },
    {
      name: 'Monitored Services',
      value: ext ? String(ext.total) : '...',
      status: ext ? (ext.down > 0 ? 'warning' : 'success') : ('success' as const),
      icon: Server,
      change: ext ? `${ext.healthy} up` + (ext.degraded > 0 ? ` \u00b7 ${ext.degraded} degraded` : '') + (ext.down > 0 ? ` \u00b7 ${ext.down} down` : '') : '',
      sparkline: history.monitored_hosts,
      trend: 'stable',
      link: '/services'
    },
    {
      name: 'Platform Health',
      value: pla ? mapSummaryLabel(pla.status) : 'Loading...',
      status: pla ? mapSummaryStatus(pla.status) : ('success' as const),
      icon: Shield,
      change: pla ? `${pla.healthy}/${pla.total} components` + (pla.down > 0 ? ` \u00b7 ${pla.down} down` : ' \u00b7 All up') : '',
      sparkline: history.platform_health,
      trend: 'stable',
      link: '/system-health'
    },
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
