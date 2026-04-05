import { ExternalLink, FileText, BarChart3, Network, Layers } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { openGrafanaDashboard, openGrafanaExplore } from '../utils/grafana'
import { getGrafanaLogsUrl, getGrafanaMetricsUrl } from '../utils/externalLinks'

interface Props {
  serviceKey: string          // e.g. "rhinometric-web-produccion"
  serviceName: string         // e.g. "rhinometric-web"
  traceId: string
  traceStartUs: number
  traceDurationUs: number
}

export function TraceActionLinks({ serviceKey, serviceName, traceId, traceStartUs, traceDurationUs }: Props) {
  const navigate = useNavigate()

  const traceStartMs = Math.floor(traceStartUs / 1000)
  const traceEndMs   = Math.floor((traceStartUs + traceDurationUs) / 1000)
  const padMs = 60_000 // 1 min padding
  const from = traceStartMs - padMs
  const to   = traceEndMs + padMs

  const actions = [
    {
      label: 'View Logs',
      icon: <FileText size={16} />,
      description: `Logs for ${serviceKey} around trace time`,
      onClick: () => {
        navigate('/logs', {
          state: {
            prefillService: serviceKey,
            prefillFrom: new Date(from).toISOString(),
            prefillTo: new Date(to).toISOString(),
          },
        })
      },
    },
    {
      label: 'Service Dashboard',
      icon: <BarChart3 size={16} />,
      description: `Grafana dashboard for ${serviceName}`,
      onClick: () => {
        openGrafanaDashboard('ext-svc-detail', {
          'var-service_name': serviceName,
          from: String(from),
          to: String(to),
        })
      },
    },
    {
      label: 'Explore Logs',
      icon: <Layers size={16} />,
      description: 'Open in Grafana Explore (Loki)',
      onClick: () => {
        const url = getGrafanaLogsUrl(
          `{job="${serviceKey}"}`,
          new Date(from).toISOString(),
          new Date(to).toISOString()
        )
        window.open(url, '_blank', 'noopener,noreferrer')
      },
    },
    {
      label: 'Explore Metrics',
      icon: <Network size={16} />,
      description: 'Open in Grafana Explore (VictoriaMetrics)',
      onClick: () => {
        const url = getGrafanaMetricsUrl(
          `external_service_latency_ms{service_name="${serviceName}"}`,
          new Date(from).toISOString(),
          new Date(to).toISOString()
        )
        window.open(url, '_blank', 'noopener,noreferrer')
      },
    },
    {
      label: 'Explore Trace',
      icon: <ExternalLink size={16} />,
      description: 'Open in Grafana Explore (Jaeger)',
      onClick: () => {
        const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
          datasource: 'jaeger',
          queries: [{ refId: 'A', query: traceId }],
          range: { from: 'now-1h', to: 'now' },
        }))}`
        openGrafanaExplore(exploreUrl)
      },
    },
  ]

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 p-4 border-b border-white/5">
        <ExternalLink size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-white">Actions</h3>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-4">
        {actions.map((action) => (
          <button
            key={action.label}
            onClick={action.onClick}
            title={action.description}
            className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-surface-light/50 hover:bg-surface-light transition-colors text-center group"
          >
            <span className="text-gray-400 group-hover:text-primary transition-colors">
              {action.icon}
            </span>
            <span className="text-xs text-gray-300 group-hover:text-white transition-colors">
              {action.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
