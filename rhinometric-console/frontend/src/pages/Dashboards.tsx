import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, Folder, Tag, Eye, Globe, Server } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaDashboard } from '../utils/grafana'

interface Dashboard {
  uid: string
  title: string
  uri: string
  url: string
  slug: string
  type: string
  tags: string[]
  isStarred: boolean
  folderId?: number
  folderUid?: string
  folderTitle?: string
  folderUrl?: string
}

// Strip leading numbering like "01 - ", "02 - ", etc.
const cleanTitle = (title: string) => title.replace(/^\d+\s*-\s*/, '')

export function DashboardsPage() {
  useEffect(() => {
    document.title = 'Dashboards - Rhinometric'
  }, [])

  const navigate = useNavigate()
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const token = useAuthStore((state) => state.token)
  const isAdmin = useAuthStore((state) => state.isAdmin)

  useEffect(() => {
    fetchDashboards()
  }, [])

  const fetchDashboards = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/dashboards', {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!response.ok) throw new Error('Failed to fetch dashboards')
      const data = await response.json()
      setDashboards(data.dashboards)
    } catch (err) {
      setError('Failed to load dashboards')
      console.error('Error fetching dashboards:', err)
    } finally {
      setLoading(false)
    }
  }

  const openInGrafana = (dashboard: Dashboard, e: React.MouseEvent) => {
    e.stopPropagation()
    openGrafanaDashboard(dashboard.uid, { kiosk: 'tv' })
  }

  const viewInConsole = (dashboard: Dashboard) => {
    navigate(`/dashboards/${dashboard.uid}/view`)
  }

  const filteredDashboards = dashboards.filter(dashboard =>
    cleanTitle(dashboard.title).toLowerCase().includes(searchTerm.toLowerCase()) ||
    dashboard.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (dashboard.folderTitle && dashboard.folderTitle.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Separate into platform (internal) and external services dashboards
  const externalDashboards = filteredDashboards.filter(d =>
    d.tags.includes('external-services')
  )
  const platformDashboards = filteredDashboards.filter(d =>
    !d.tags.includes('external-services')
  )

  const renderDashboardCard = (dashboard: Dashboard) => (
    <div
      key={dashboard.uid}
      className="card hover:border-primary/50 transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white">
            {cleanTitle(dashboard.title)}
          </h3>
          {dashboard.folderTitle && (
            <div className="flex items-center gap-2 mt-2 text-text-muted text-sm">
              <Folder className="w-4 h-4" />
              <span>{dashboard.folderTitle}</span>
            </div>
          )}
        </div>
      </div>

      {dashboard.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {dashboard.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-2 py-1 bg-surface-light rounded text-xs text-text-secondary"
            >
              <Tag className="w-3 h-3" />
              {tag}
            </span>
          ))}
          {dashboard.tags.length > 3 && (
            <span className="inline-flex items-center px-2 py-1 bg-surface-light rounded text-xs text-text-muted">
              +{dashboard.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-surface-light flex gap-2">
        <button
          onClick={() => viewInConsole(dashboard)}
          className="flex-1 btn-secondary text-sm font-medium flex items-center justify-center gap-2"
        >
          <Eye className="w-4 h-4" />
          View in Console
        </button>
        {isAdmin() && (
          <button
            onClick={(e) => openInGrafana(dashboard, e)}
            className="btn-outline text-sm font-medium flex items-center justify-center gap-1 px-3"
            title="Edit in Grafana"
          >
            <ExternalLink className="w-4 h-4" />
            Grafana
          </button>
        )}
      </div>
    </div>
  )

  const renderSection = (
    title: string,
    icon: React.ReactNode,
    description: string,
    items: Dashboard[]
  ) => {
    if (items.length === 0) return null
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{title}</h2>
            <p className="text-text-muted text-sm">{description}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map(renderDashboardCard)}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboards</h1>
            <p className="text-text-muted mt-2">Grafana dashboards collection</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-text-muted">Loading dashboards...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboards</h1>
            <p className="text-text-muted mt-2">Grafana dashboards collection</p>
          </div>
        </div>
        <div className="card bg-error/10 border-error">
          <p className="text-error">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboards</h1>
          <p className="text-text-muted mt-2">
            {filteredDashboards.length} of {dashboards.length} dashboards
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <input
          type="text"
          placeholder="Search dashboards by name, tags, or folder..."
          className="input w-full"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Platform Dashboards Section */}
      {renderSection(
        'Platform',
        <Server className="w-5 h-5" />,
        'Infrastructure, backend and system monitoring',
        platformDashboards
      )}

      {/* External Services Section */}
      {renderSection(
        'External Services',
        <Globe className="w-5 h-5" />,
        'Health, performance and SLA tracking for external endpoints',
        externalDashboards
      )}

      {filteredDashboards.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-text-muted">No dashboards found matching your search.</p>
        </div>
      )}
    </div>
  )
}