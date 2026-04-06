import { FileText, BarChart3, Timer, Navigation } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface Props {
  serviceKey: string
  serviceName: string
  traceId: string
  traceStartUs: number
  traceDurationUs: number
}

export function TraceActionLinks({ serviceKey, serviceName, traceStartUs, traceDurationUs }: Props) {
  const navigate = useNavigate()

  // Compute time window for log navigation
  const traceStartMs = Math.floor(traceStartUs / 1000)
  const traceEndMs   = Math.floor((traceStartUs + traceDurationUs) / 1000)
  const padMs = 60_000
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
            service: serviceKey,
            from,
            to,
          },
        })
      },
    },
    {
      label: 'Service Dashboard',
      icon: <BarChart3 size={16} />,
      description: `Service detail dashboard for ${serviceName}`,
      onClick: () => {
        navigate('/dashboards/ext-svc-detail/view')
      },
    },
    {
      label: 'Latency Dashboard',
      icon: <Timer size={16} />,
      description: `Latency deep-dive for ${serviceName}`,
      onClick: () => {
        navigate('/dashboards/ext-svc-latency/view')
      },
    },
  ]

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 p-4 border-b border-white/5">
        <Navigation size={18} className="text-primary" />
        <h3 className="text-sm font-semibold text-white">Actions</h3>
      </div>
      <div className="grid grid-cols-3 gap-2 p-4">
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
