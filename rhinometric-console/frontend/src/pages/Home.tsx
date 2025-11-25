import { Activity, Server, AlertTriangle, Bell } from 'lucide-react'
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'

export function HomePage() {
  useEffect(() => {
    document.title = 'Rhinometric - Home'
  }, [])

  const token = useAuthStore((state) => state.token)

  // Fetch KPIs from backend API
  const { data: kpisData, isLoading, error } = useQuery({
    queryKey: ['kpis'],
    queryFn: async () => {
      const response = await fetch('/api/kpis', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) throw new Error('Failed to fetch KPIs')
      return response.json()
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Map API data to KPI cards
  const kpis = kpisData ? [
    { 
      name: 'Service Status', 
      value: kpisData.service_status.value, 
      status: kpisData.service_status.status, 
      icon: Activity, 
      change: kpisData.service_status.change 
    },
    { 
      name: 'Monitored Hosts', 
      value: kpisData.monitored_hosts.value, 
      status: kpisData.monitored_hosts.status, 
      icon: Server, 
      change: kpisData.monitored_hosts.change 
    },
    { 
      name: 'Active Anomalies', 
      value: kpisData.active_anomalies.value, 
      status: kpisData.active_anomalies.status, 
      icon: AlertTriangle, 
      change: kpisData.active_anomalies.change 
    },
    { 
      name: 'Alerts (24h)', 
      value: kpisData.alerts_24h.value, 
      status: kpisData.alerts_24h.status, 
      icon: Bell, 
      change: kpisData.alerts_24h.change 
    },
  ] : [
    { name: 'Service Status', value: 'Loading...', status: 'success', icon: Activity, change: '' },
    { name: 'Monitored Hosts', value: '...', status: 'success', icon: Server, change: '' },
    { name: 'Active Anomalies', value: '...', status: 'success', icon: AlertTriangle, change: '' },
    { name: 'Alerts (24h)', value: '...', status: 'success', icon: Bell, change: '' },
  ]

  if (error) {
    console.error('Failed to load KPIs:', error)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Welcome to Rhinometric</h1>
        <p className="text-text-muted">AI-Powered Observability & Anomaly Detection Platform</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi) => {
          const Icon = kpi.icon
          return (
            <div key={kpi.name} className="card">
              <div className="flex items-start justify-between mb-4">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${kpi.status === 'success' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                  {kpi.status === 'success' ? 'Healthy' : 'Warning'}
                </span>
              </div>
              <p className="text-text-muted text-sm mb-1">{kpi.name}</p>
              <p className="text-2xl font-bold text-white mb-2">{kpi.value}</p>
              <p className="text-xs text-text-muted">{kpi.change}</p>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
          <div className="space-y-3">
            {['Infrastructure', 'Network', 'Database', 'Applications'].map((category) => (
              <div key={category} className="flex items-center justify-between">
                <span className="text-text-secondary">{category}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-success" />
                  <span className="text-sm text-success">OK</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-primary mt-2" />
              <div>
                <p className="text-sm text-white">System started successfully</p>
                <p className="text-xs text-text-muted">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-success mt-2" />
              <div>
                <p className="text-sm text-white">All collectors connected</p>
                <p className="text-xs text-text-muted">5 minutes ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card bg-primary/5 border-primary/20">
        <div className="flex items-start space-x-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Activity className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Real-time Metrics Integration</h3>
            <p className="text-text-muted text-sm mb-4">This dashboard will display live metrics from Prometheus, active anomalies from the AI engine, and recent alerts from AlertManager once the backend API Gateway is connected.</p>
            <div className="flex space-x-2">
              <span className="text-xs px-3 py-1 bg-primary/20 text-primary rounded-full">Backend API: In Development</span>
              <span className="text-xs px-3 py-1 bg-success/20 text-success rounded-full">Frontend: Complete</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
