import { useEffect, useState } from 'react'
import { Activity, Server, AlertTriangle, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

interface ComponentHealth {
  name: string
  status: 'ok' | 'warning' | 'critical'
  category: string
  message?: string
  uptime?: number
}

interface HealthEvent {
  timestamp: string
  event: string
  severity: 'info' | 'warning' | 'error'
  source: string
}

interface SystemHealthData {
  overall_status: 'operational' | 'degraded' | 'critical'
  uptime_percentage: number
  uptime_period: string
  platform_services: {
    total: number
    healthy: number
    unhealthy: number
  }
  client_services: {
    total: number
    healthy: number
  }
  active_issues: number
  components: ComponentHealth[]
  recent_events: HealthEvent[]
  last_check: string
}

export function SystemHealthPage() {
  const [healthData, setHealthData] = useState<SystemHealthData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const token = useAuthStore((state) => state.token)

  useEffect(() => {
    document.title = 'System Health - Rhinometric'
    fetchHealthData()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchHealthData = async () => {
    try {
      const response = await fetch('/api/kpis/system-health', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      setHealthData(data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch system health:', err)
      setError(err instanceof Error ? err.message : 'Failed to load system health')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
      case 'ok':
        return 'text-green-400'
      case 'degraded':
      case 'warning':
        return 'text-yellow-400'
      case 'critical':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'operational':
      case 'ok':
        return 'bg-green-400/10 border-green-400/50'
      case 'degraded':
      case 'warning':
        return 'bg-yellow-400/10 border-yellow-400/50'
      case 'critical':
        return 'bg-red-400/10 border-red-400/50'
      default:
        return 'bg-gray-400/10 border-gray-400/50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
      case 'ok':
        return <CheckCircle className="w-6 h-6 text-green-400" />
      case 'degraded':
      case 'warning':
        return <AlertTriangle className="w-6 h-6 text-yellow-400" />
      case 'critical':
        return <XCircle className="w-6 h-6 text-red-400" />
      default:
        return <Activity className="w-6 h-6 text-gray-400" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    const colors = {
      info: 'bg-blue-400/10 text-blue-400',
      warning: 'bg-yellow-400/10 text-yellow-400',
      error: 'bg-red-400/10 text-red-400'
    }
    return colors[severity as keyof typeof colors] || 'bg-gray-400/10 text-gray-400'
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    
    if (minutes < 1) return 'just now'
    if (minutes < 60) return `${minutes} min ago`
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
    return `${days} day${days > 1 ? 's' : ''} ago`
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">System Health</h1>
        </div>
        <div className="flex items-center justify-center h-64">
          <Activity className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">System Health</h1>
        </div>
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <XCircle className="w-6 h-6 text-red-400" />
            <div>
              <p className="text-red-400 font-medium">Failed to load system health</p>
              <p className="text-gray-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!healthData) return null

  return (
    <div className="space-y-6">
      {/* Header with Overall Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">System Health</h1>
          <p className="text-gray-400 mt-1">Platform health overview and diagnostics</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          <span>Last check: {formatTimestamp(healthData.last_check)}</span>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className={`rounded-lg border p-6 ${getStatusBg(healthData.overall_status)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {getStatusIcon(healthData.overall_status)}
            <div>
              <h2 className={`text-2xl font-bold uppercase ${getStatusColor(healthData.overall_status)}`}>
                {healthData.overall_status}
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                {healthData.uptime_percentage.toFixed(1)}% Uptime ({healthData.uptime_period})
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <span className="text-sm text-gray-400">System stable</span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-400/10 rounded-lg">
              <Server className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Platform Services</p>
              <p className="text-2xl font-bold text-white">
                {healthData.platform_services.healthy}/{healthData.platform_services.total}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {healthData.platform_services.unhealthy} unhealthy
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-400/10 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Client Services</p>
              <p className="text-2xl font-bold text-green-400">
                {healthData.client_services.healthy}/{healthData.client_services.total}
              </p>
              <p className="text-xs text-gray-500 mt-1">All operational</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${healthData.active_issues > 0 ? 'bg-red-400/10' : 'bg-green-400/10'}`}>
              {healthData.active_issues > 0 ? (
                <AlertTriangle className="w-6 h-6 text-red-400" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-400" />
              )}
            </div>
            <div>
              <p className="text-gray-400 text-sm">Active Issues</p>
              <p className={`text-2xl font-bold ${healthData.active_issues > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {healthData.active_issues}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {healthData.active_issues === 0 ? 'No issues detected' : 'Requires attention'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Components Health Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700/50">
          <h3 className="text-lg font-semibold text-white">Infrastructure Components</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/50">
                <th className="text-left p-4 text-gray-400 font-medium">Component</th>
                <th className="text-left p-4 text-gray-400 font-medium">Category</th>
                <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                <th className="text-left p-4 text-gray-400 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {healthData.components.map((component, index) => (
                <tr 
                  key={`${component.name}-${index}`}
                  className="border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded ${getStatusBg(component.status)}`}>
                        {getStatusIcon(component.status)}
                      </div>
                      <span className="text-white font-medium">{component.name}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="px-3 py-1 bg-gray-700/50 rounded-full text-xs text-gray-300">
                      {component.category}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusBg(component.status)}`}>
                      <span className={getStatusColor(component.status)}>
                        {component.status.toUpperCase()}
                      </span>
                    </span>
                  </td>
                  <td className="p-4 text-gray-400 text-sm">
                    {component.message || 'Operating normally'}
                    {component.uptime !== undefined && (
                      <span className="ml-2 text-gray-500">
                        ({component.uptime.toFixed(1)}% uptime)
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Events Timeline */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Events (24h)</h3>
        <div className="space-y-3">
          {healthData.recent_events.length > 0 ? (
            healthData.recent_events.map((event, index) => (
              <div key={index} className="flex items-start gap-3 pb-3 border-b border-gray-700/30 last:border-0 last:pb-0">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  event.severity === 'error' ? 'bg-red-400' :
                  event.severity === 'warning' ? 'bg-yellow-400' :
                  'bg-blue-400'
                }`} />
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <p className="text-white text-sm">{event.event}</p>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityBadge(event.severity)}`}>
                      {event.severity}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-500">{event.source}</span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500">{formatTimestamp(event.timestamp)}</span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-gray-500">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No recent events</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
