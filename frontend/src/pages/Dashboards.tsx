import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Folder, Tag, Eye, Globe } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { DashboardSelector } from '../components/DashboardSelector'
import { loadSelection, saveSelection } from '../config/dashboardLibrary'

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

/** Tags that mark infrastructure / internal dashboards — hidden from catalog */
const EXCLUDED_TAGS = ['docker', 'backend', 'stack', 'system']

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

  // ── Dashboard selection state (Phase 1) ─────────────────────
  const [activeDashboards, setActiveDashboards] = useState<string[]>(loadSelection)

  const handleSelectionChange = (uids: string[]) => {
    setActiveDashboards(uids)
    saveSelection(uids)
  }

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

  const viewInConsole = (dashboard: Dashboard) => {
    navigate(`/dashboards/${dashboard.uid}/view`)
  }

  // Only show external-services dashboards; exclude infra tags
  const clientDashboards = dashboards.filter(d =>
    d.tags.includes('external-services') &&
    !d.tags.some(t => EXCLUDED_TAGS.includes(t.toLowerCase()))
  )

  // ── Phase 1 filter: only render user-selected dashboards ────
  const selectedDashboards = clientDashboards.filter(d =>
    activeDashboards.includes(d.uid)
  )

  const filteredDashboards = selectedDashboards.filter(dashboard =>
    cleanTitle(dashboard.title).toLowerCase().includes(searchTerm.toLowerCase()) ||
    dashboard.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (dashboard.folderTitle && dashboard.folderTitle.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Count of dashboards hidden by selector (not by search)
  const hiddenCount = clientDashboards.length - selectedDashboards.length

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
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboards</h1>
            <p className="text-text-muted mt-2">Service monitoring dashboards</p>
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
            <p className="text-text-muted mt-2">Service monitoring dashboards</p>
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
            {filteredDashboards.length} dashboard{filteredDashboards.length !== 1 ? 's' : ''}
            {hiddenCount > 0 && (
              <span className="text-text-muted/70"> · {hiddenCount} hidden</span>
            )}
          </p>
        </div>
        <DashboardSelector
          activeDashboards={activeDashboards}
          onChange={handleSelectionChange}
        />
      </div>

      {/* Search */}
      {selectedDashboards.length > 3 && (
        <div className="card">
          <input
            type="text"
            placeholder="Search dashboards by name, tags, or folder..."
            className="input w-full"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      )}

      {/* External Services Dashboards */}
      {filteredDashboards.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">External Services</h2>
              <p className="text-text-muted text-sm">Health, performance and SLA tracking for external endpoints</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDashboards.map(renderDashboardCard)}
          </div>
        </div>
      )}

      {/* Empty state: user has dashboards selected but search yields nothing */}
      {filteredDashboards.length === 0 && selectedDashboards.length > 0 && (
        <div className="card text-center py-12">
          <p className="text-text-muted">No dashboards found matching your search.</p>
        </div>
      )}

      {/* Empty state: no dashboards selected at all */}
      {selectedDashboards.length === 0 && (
        <div className="card text-center py-16 space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-surface-light/50 flex items-center justify-center">
              <Globe className="w-8 h-8 text-text-muted" />
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">No dashboards selected</h3>
            <p className="text-text-muted text-sm mt-1">
              Use the <strong>Manage Dashboards</strong> button to choose which dashboards to display.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
