import { useEffect, useState } from 'react'
import { Server, AlertCircle, CheckCircle, Activity, Layers } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

interface Service {
  name: string
  instance: string
  status: 'up' | 'down'
  tier: string
  service_type: string
  version: string
  labels: Record<string, string>
}

interface ServicesData {
  services: Service[]
  total: number
  up: number
  down: number
  timestamp: string
}

export default function Services() {
  const [servicesData, setServicesData] = useState<ServicesData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuthStore()

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch('/api/kpis/services', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const data = await response.json()
        setServicesData(data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch services:', err)
        setError(err instanceof Error ? err.message : 'Failed to load services')
      } finally {
        setIsLoading(false)
      }
    }

    fetchServices()
    const interval = setInterval(fetchServices, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    return status === 'up' ? 'text-green-400' : 'text-red-400'
  }

  const getStatusBg = (status: string) => {
    return status === 'up' ? 'bg-green-400/10' : 'bg-red-400/10'
  }

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      application: 'bg-blue-400/10 text-blue-400',
      telemetry: 'bg-purple-400/10 text-purple-400',
      health: 'bg-cyan-400/10 text-cyan-400',
      monitoring: 'bg-yellow-400/10 text-yellow-400',
      infrastructure: 'bg-gray-400/10 text-gray-400'
    }
    return colors[tier] || 'bg-gray-400/10 text-gray-400'
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Monitored Services</h1>
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
          <h1 className="text-3xl font-bold text-white">Monitored Services</h1>
        </div>
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-red-400" />
            <div>
              <p className="text-red-400 font-medium">Failed to load services</p>
              <p className="text-gray-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Monitored Services</h1>
          <p className="text-gray-400 mt-1">Real-time service health monitoring</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-400/10 rounded-lg">
              <Server className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Total Services</p>
              <p className="text-2xl font-bold text-white">{servicesData?.total || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-400/10 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Healthy</p>
              <p className="text-2xl font-bold text-green-400">{servicesData?.up || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-400/10 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Down</p>
              <p className="text-2xl font-bold text-red-400">{servicesData?.down || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Services Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700/50">
                <th className="text-left p-4 text-gray-400 font-medium">Service</th>
                <th className="text-left p-4 text-gray-400 font-medium">Instance</th>
                <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                <th className="text-left p-4 text-gray-400 font-medium">Tier</th>
                <th className="text-left p-4 text-gray-400 font-medium">Version</th>
              </tr>
            </thead>
            <tbody>
              {servicesData?.services.map((service, index) => (
                <tr 
                  key={`${service.name}-${service.instance}-${index}`}
                  className="border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded ${getStatusBg(service.status)}`}>
                        <Layers className={`w-4 h-4 ${getStatusColor(service.status)}`} />
                      </div>
                      <div>
                        <p className="text-white font-medium">{service.name}</p>
                        <p className="text-gray-400 text-sm">{service.service_type}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <code className="text-sm text-gray-300 bg-gray-900/50 px-2 py-1 rounded">
                      {service.instance}
                    </code>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusBg(service.status)}`}>
                      {service.status === 'up' ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className={getStatusColor(service.status)}>
                        {service.status.toUpperCase()}
                      </span>
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getTierColor(service.tier)}`}>
                      {service.tier}
                    </span>
                  </td>
                  <td className="p-4 text-gray-300">
                    {service.version}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-center text-gray-500 text-sm">
        Last updated: {servicesData ? new Date(servicesData.timestamp).toLocaleString() : 'N/A'}
      </div>
    </div>
  )
}
