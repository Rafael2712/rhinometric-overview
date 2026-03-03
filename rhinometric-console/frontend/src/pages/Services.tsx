import { useEffect, useState } from 'react'
import {
  Server, AlertCircle, CheckCircle, Activity, Layers,
  Globe, Database, Webhook, Cpu, Radio, Wifi, Shield,
  FileText, BarChart3, Network, MonitorSmartphone, Box
} from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface Service {
  name: string
  instance: string
  status: 'up' | 'down'
  tier: string
  service_type: string
  version: string
  is_platform: boolean
  service_category: string
  labels: Record<string, string>
}

interface ServiceGroup {
  services: Service[]
  total: number
  up: number
  down: number
}

interface ServicesData {
  services: Service[]
  total: number
  up: number
  down: number
  platform: ServiceGroup
  external: ServiceGroup
  timestamp: string
}

type Tab = 'platform' | 'external'

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

const STATUS_COLORS: Record<string, string> = {
  up: 'text-green-400',
  down: 'text-red-400',
}
const STATUS_BG: Record<string, string> = {
  up: 'bg-green-400/10',
  down: 'bg-red-400/10',
}

const TIER_COLORS: Record<string, string> = {
  application: 'bg-blue-400/10 text-blue-400',
  telemetry: 'bg-purple-400/10 text-purple-400',
  health: 'bg-cyan-400/10 text-cyan-400',
  monitoring: 'bg-yellow-400/10 text-yellow-400',
  infrastructure: 'bg-gray-400/10 text-gray-400',
}

/** Visual badge per external-service category */
const CATEGORY_META: Record<string, { label: string; color: string; Icon: React.ElementType }> = {
  'website':        { label: 'Website',        color: 'bg-sky-400/10 text-sky-400',    Icon: Globe },
  'database':       { label: 'Database',       color: 'bg-orange-400/10 text-orange-400', Icon: Database },
  'api-rest':       { label: 'API / REST',     color: 'bg-violet-400/10 text-violet-400', Icon: Network },
  'webhook':        { label: 'Webhook',        color: 'bg-pink-400/10 text-pink-400',  Icon: Webhook },
  'host-metrics':   { label: 'Host Metrics',   color: 'bg-emerald-400/10 text-emerald-400', Icon: Cpu },
  'message-broker': { label: 'Message Broker', color: 'bg-amber-400/10 text-amber-400', Icon: Radio },
  'logging':        { label: 'Logging',        color: 'bg-teal-400/10 text-teal-400',  Icon: FileText },
  'tracing':        { label: 'Tracing',        color: 'bg-indigo-400/10 text-indigo-400', Icon: BarChart3 },
  'dns':            { label: 'DNS',            color: 'bg-lime-400/10 text-lime-400',  Icon: Wifi },
  'ssl-certificate':{ label: 'SSL / TLS',      color: 'bg-green-400/10 text-green-400', Icon: Shield },
  'snmp':           { label: 'SNMP',           color: 'bg-yellow-400/10 text-yellow-400', Icon: MonitorSmartphone },
  'custom':         { label: 'Custom',         color: 'bg-gray-400/10 text-gray-400',  Icon: Box },
}

function categoryBadge(cat: string) {
  const meta = CATEGORY_META[cat] || CATEGORY_META['custom']
  const { label, color, Icon } = meta
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      <Icon className="w-3 h-3" />
      {label}
    </span>
  )
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function Services() {
  const [servicesData, setServicesData] = useState<ServicesData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('platform')
  const { token } = useAuthStore()

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch('/api/kpis/services', {
          headers: { 'Authorization': `Bearer ${token}` },
        })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
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
    const interval = setInterval(fetchServices, 30000)
    return () => clearInterval(interval)
  }, [token])

  /* ---------- Loading / Error states ---------- */

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Services</h1>
        <div className="flex items-center justify-center h-64">
          <Activity className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Services</h1>
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

  const platform = servicesData?.platform ?? { services: [], total: 0, up: 0, down: 0 }
  const external = servicesData?.external ?? { services: [], total: 0, up: 0, down: 0 }
  const current = activeTab === 'platform' ? platform : external

  /* ---------- Render ---------- */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Services</h1>
        <p className="text-gray-400 mt-1">Real-time service health monitoring</p>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 bg-gray-800/60 rounded-lg p-1 w-fit">
        <button
          onClick={() => setActiveTab('platform')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'platform'
              ? 'bg-blue-500/20 text-blue-400 shadow-sm'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/40'
          }`}
        >
          <Server className="w-4 h-4" />
          Platform Services
          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs ${
            activeTab === 'platform' ? 'bg-blue-400/20 text-blue-300' : 'bg-gray-700 text-gray-400'
          }`}>
            {platform.total}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('external')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'external'
              ? 'bg-emerald-500/20 text-emerald-400 shadow-sm'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/40'
          }`}
        >
          <Globe className="w-4 h-4" />
          External Services
          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs ${
            activeTab === 'external' ? 'bg-emerald-400/20 text-emerald-300' : 'bg-gray-700 text-gray-400'
          }`}>
            {external.total}
          </span>
        </button>
      </div>

      {/* ── Stats Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${activeTab === 'platform' ? 'bg-blue-400/10' : 'bg-emerald-400/10'}`}>
              <Server className={`w-6 h-6 ${activeTab === 'platform' ? 'text-blue-400' : 'text-emerald-400'}`} />
            </div>
            <div>
              <p className="text-gray-400 text-sm">
                {activeTab === 'platform' ? 'Platform Services' : 'External Services'}
              </p>
              <p className="text-2xl font-bold text-white">{current.total}</p>
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
              <p className="text-2xl font-bold text-green-400">{current.up}</p>
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
              <p className="text-2xl font-bold text-red-400">{current.down}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Table or Empty State ── */}
      {current.total === 0 ? (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-12 text-center">
          {activeTab === 'external' ? (
            <>
              <Globe className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">
                No external services configured
              </h3>
              <p className="text-gray-500 max-w-md mx-auto mb-6">
                Connect up to <span className="text-emerald-400 font-semibold">100 hosts</span> — websites,
                databases, APIs, webhooks, MQTT brokers, and more.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {Object.entries(CATEGORY_META).filter(([k]) => k !== 'custom').map(([key]) => (
                  <span key={key}>{categoryBadge(key)}</span>
                ))}
              </div>
            </>
          ) : (
            <>
              <Server className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300">
                No platform services detected
              </h3>
              <p className="text-gray-500 mt-2">Platform services will appear here once Prometheus is scraping them.</p>
            </>
          )}
        </div>
      ) : (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/50">
                  <th className="text-left p-4 text-gray-400 font-medium">Service</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Instance</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                  <th className="text-left p-4 text-gray-400 font-medium">
                    {activeTab === 'external' ? 'Category' : 'Tier'}
                  </th>
                  <th className="text-left p-4 text-gray-400 font-medium">Version</th>
                </tr>
              </thead>
              <tbody>
                {current.services.map((service, index) => (
                  <tr
                    key={`${service.name}-${service.instance}-${index}`}
                    className="border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded ${STATUS_BG[service.status] || ''}`}>
                          <Layers className={`w-4 h-4 ${STATUS_COLORS[service.status] || ''}`} />
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
                      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                        STATUS_BG[service.status] || ''
                      }`}>
                        {service.status === 'up' ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span className={STATUS_COLORS[service.status] || ''}>
                          {service.status.toUpperCase()}
                        </span>
                      </span>
                    </td>
                    <td className="p-4">
                      {activeTab === 'external' ? (
                        categoryBadge(service.service_category)
                      ) : (
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          TIER_COLORS[service.tier] || TIER_COLORS['infrastructure']
                        }`}>
                          {service.tier}
                        </span>
                      )}
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
      )}

      {/* Footer */}
      {activeTab === 'external' && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            {external.total} / 100 external hosts connected
          </span>
          <span>
            Last updated: {servicesData ? new Date(servicesData.timestamp).toLocaleString() : 'N/A'}
          </span>
        </div>
      )}
      {activeTab === 'platform' && (
        <div className="text-center text-gray-500 text-sm">
          Last updated: {servicesData ? new Date(servicesData.timestamp).toLocaleString() : 'N/A'}
        </div>
      )}
    </div>
  )
}
