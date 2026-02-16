import { Activity, Server, AlertTriangle, Bell, TrendingUp, TrendingDown } from 'lucide-react'
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
  active_anomalies: SparklinePoint[]
  alerts_24h: SparklinePoint[]
}

export function HomePage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<KPIHistory>({
    service_status: [],
    monitored_hosts: [],
    active_anomalies: [],
    alerts_24h: []
  })

  useEffect(() => {
    document.title = 'Rhinometric - Home'
  }, [])

  const token = useAuthStore((state) => state.token)

  // Fetch KPIs from backend API
  const { data: kpisData, isLoading, error } = useQuery({
    queryKey: ['kpis', token],
    queryFn: async () => {
      if (!token) throw new Error('No token available')

      const response = await fetch('/api/kpis', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) throw new Error('Failed to fetch KPIs')
      return response.json()
    },
    enabled: !!token,
    refetchInterval: 5000, // Refresh every 5 seconds for "live" feel
  })

  // Update history when new data arrives
  useEffect(() => {
    if (kpisData) {
      const now = Date.now()
      setHistory(prev => {
        const updateSeries = (series: SparklinePoint[], newValue: any) => {
          const val = typeof newValue === 'string' ? parseFloat(newValue) || 0 : newValue
          // Keep last 20 points
          const newSeries = [...series, { time: now, value: val }]
          return newSeries.slice(-20)
        }

        // Use real service status percentage instead of random
        const serviceStatusValue = kpisData.service_status.value === "Operational" ? 100 :
                                  (kpisData.service_status.operational_count / kpisData.service_status.total_count) * 100

        return {
          service_status: updateSeries(prev.service_status, serviceStatusValue),
          monitored_hosts: updateSeries(prev.monitored_hosts, kpisData.monitored_hosts.value),
          active_anomalies: updateSeries(prev.active_anomalies, kpisData.active_anomalies.value),
          alerts_24h: updateSeries(prev.alerts_24h, kpisData.alerts_24h.value)
        }
      })
    }
  }, [kpisData])

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
        time: p.timestamp * 1000, // Convert to ms
        value: p.value
      }))

      setHistory({
        service_status: mapPoints(historyData.service_status),
        monitored_hosts: mapPoints(historyData.monitored_hosts),
        active_anomalies: mapPoints(historyData.active_anomalies),
        alerts_24h: mapPoints(historyData.alerts_24h)
      })
    }
  }, [historyData])

  // Map API data to KPI cards with sparkline data
  const kpis = kpisData ? [
    {
      name: 'Service Status',
      value: kpisData.service_status.value,
      status: kpisData.service_status.status,
      icon: Activity,
      change: kpisData.service_status.change,
      sparkline: history.service_status,
      trend: 'up',
      link: '/system-health'
    },
    {
      name: 'Monitored Services',
      value: kpisData.monitored_hosts.value,
      status: kpisData.monitored_hosts.status,
      icon: Server,
      change: kpisData.monitored_hosts.change,
      sparkline: history.monitored_hosts,
      trend: 'stable',
      link: '/services'
    },
    {
      name: 'Active Anomalies',
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
    { name: 'Active Anomalies', value: '...', status: 'success', icon: AlertTriangle, change: '', sparkline: [], trend: 'stable', link: '/anomalies' },
    { name: 'Alerts (24h)', value: '...', status: 'success', icon: Bell, change: '', sparkline: [], trend: 'stable', link: '/alerts' },
  ]

  // Debug logging
  useEffect(() => {
    console.log('Home - Token:', token ? 'present' : 'missing')
    console.log('Home - Loading:', isLoading)
    console.log('Home - Error:', error)
    console.log('Home - Data:', kpisData)
  }, [token, isLoading, error, kpisData])

  if (error) {
    console.error('Failed to load KPIs:', error)
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Welcome to Rhinometric</h1>
        <p className="text-text-muted text-sm sm:text-base">AI-Powered Observability & Anomaly Detection Platform</p>
        {/* Debug info */}
        {!token && <p className="text-warning text-sm mt-2">⚠️ No authentication token</p>}
        {error && <p className="text-error text-sm mt-2">❌ Error: {(error as Error).message}</p>}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
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
                <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${kpi.status === 'success' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                  {kpi.status === 'success' ? 'Healthy' : 'Warning'}
                </span>
              </div>
              <p className="text-text-muted text-xs sm:text-sm mb-0.5 sm:mb-1">{kpi.name}</p>
              <div className="flex items-end justify-between mb-2 sm:mb-3">
                <p className="text-lg sm:text-2xl font-bold text-white">{kpi.value}</p>
                {kpi.trend !== 'stable' && (
                  <TrendIcon className={`w-4 h-4 sm:w-5 sm:h-5 ${trendColor}`} />
                )}
              </div>

              {/* Mini Sparkline Chart (últimas 24h) */}
              {kpi.sparkline.length > 0 && (
                <div className="h-8 sm:h-12 -mx-1 sm:-mx-2 mb-1 sm:mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={kpi.sparkline}>
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={kpi.status === 'success' ? '#10b981' : '#f59e0b'}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="card">
          <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">System Health</h3>
          <div className="space-y-3">
            {['Infrastructure', 'Network', 'Database', 'Applications'].map((category) => (
              <div key={category} className="flex items-center justify-between">
                <span className="text-text-secondary text-sm">{category}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-success" />
                  <span className="text-sm text-success">OK</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">Recent Activity</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
              <div>
                <p className="text-sm text-white">System started successfully</p>
                <p className="text-xs text-text-muted">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-success mt-2 flex-shrink-0" />
              <div>
                <p className="text-sm text-white">All collectors connected</p>
                <p className="text-xs text-text-muted">5 minutes ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card bg-primary/5 border-primary/20">
        <div className="flex items-start gap-3 sm:space-x-4">
          <div className="p-2 bg-primary/10 rounded-lg flex-shrink-0">
            <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
          </div>
          <div className="min-w-0">
            <h3 className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2">Real-time Metrics Integration</h3>
            <p className="text-text-muted text-xs sm:text-sm mb-3 sm:mb-4">This dashboard displays live metrics from Prometheus, active anomalies from the AI engine, and recent alerts from AlertManager.</p>
            <div className="flex flex-wrap gap-2">
              <span className="text-[10px] sm:text-xs px-2 sm:px-3 py-1 bg-success/20 text-success rounded-full">✓ Backend API: Connected</span>
              <span className="text-[10px] sm:text-xs px-2 sm:px-3 py-1 bg-success/20 text-success rounded-full">✓ Frontend: Ready</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
