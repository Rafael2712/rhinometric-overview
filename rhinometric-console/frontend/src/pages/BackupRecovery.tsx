import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { HardDrive, Download, Plus, CheckCircle, XCircle, Lock, Archive, RefreshCw, AlertTriangle, Info, Eye, RotateCcw, X, Shield, ExternalLink, Trash2, Database, Clock, Search, Filter } from 'lucide-react'

interface BackupArtifact {
  id: string
  filename: string
  status: string
  backup_type: string
  size_bytes: number | null
  storage_path: string
  created_by: string
  error_message: string | null
  error_type: string | null
  records_exported: number | null
  platform_version: string | null
  checksum: string | null
  created_at: string | null
}

interface SummaryResponse {
  total_backups: number
  latest_backup: BackupArtifact | null
  latest_successful: BackupArtifact | null
  latest_failed: BackupArtifact | null
}

interface ListResponse {
  items: BackupArtifact[]
  total: number
  limit: number
  offset: number
}

interface PreviewData {
  backup_id: string
  filename: string
  created_at: string | null
  platform_version: string | null
  created_by: string | null
  checksum: string | null
  contents: { external_services: number; service_dependencies: number; alert_rules?: number; slo_targets?: number; incidents?: number; incident_comments?: number; incident_events?: number }
  service_names: string[]
}

interface RestoreResult {
  status: string
  backup_id: string
  backup_filename: string
  restored_by: string
  previous: { external_services: number; service_dependencies: number }
  restored: { external_services: number; service_dependencies: number }
}

interface StorageData {
  total_bytes: number
  completed_count: number
  failed_count: number
  storage_path: string
  disk_free_bytes: number | null
}

interface LastRestoreData {
  backup_filename?: string
  restored_by?: string
  restored_at?: string
  services_restored?: number
  dependencies_restored?: number
  message?: string
}

interface BackupScopeItem {
  category: string
  description: string
}

interface BackupScope {
  included: BackupScopeItem[]
  excluded: BackupScopeItem[]
  retention_days: number
  retention_mode: string
  storage_format: string
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '-'
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

function statusBadge(status: string) {
  switch (status) {
    case 'completed':
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200"><CheckCircle className="w-3 h-3" />Completed</span>
    case 'failed':
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200"><XCircle className="w-3 h-3" />Failed</span>
    case 'in_progress':
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200"><RefreshCw className="w-3 h-3 animate-spin" />In Progress</span>
    default:
      return <span className="text-xs text-gray-500">{status}</span>
  }
}

function errorTypeBadge(errorType: string | null) {
  if (!errorType) return null
  const colors: Record<string, string> = {
    permission_error: 'bg-orange-50 text-orange-700',
    storage_error: 'bg-amber-50 text-amber-700',
    integrity_error: 'bg-purple-50 text-purple-700',
    unexpected_error: 'bg-red-50 text-red-700',
  }
  const labels: Record<string, string> = {
    permission_error: 'Permission',
    storage_error: 'Storage',
    integrity_error: 'Integrity',
    unexpected_error: 'Error',
  }
  return (
    <span className={`inline-flex items-center text-[10px] px-1.5 py-0.5 rounded font-medium ${colors[errorType] || 'bg-gray-50 text-gray-500'}`}>
      {labels[errorType] || errorType}
    </span>
  )
}

export function BackupRecoveryPage() {
  const { token, isAdmin } = useAuthStore()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const canManage = isAdmin()
  const [creating, setCreating] = useState(false)
  const [expandedError, setExpandedError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [previewLoading, setPreviewLoading] = useState<string | null>(null)
  const [restoreTarget, setRestoreTarget] = useState<{ id: string; filename: string; preview?: PreviewData } | null>(null)
  const [restoreResult, setRestoreResult] = useState<RestoreResult | null>(null)
  const [restoreError, setRestoreError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; filename: string } | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: summaryData } = useQuery<SummaryResponse>({
    queryKey: ['backups-summary', token],
    queryFn: async () => {
      const r = await fetch('/api/backups/summary', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 10000,
  })

  const { data: listData, isLoading } = useQuery<ListResponse>({
    queryKey: ['backups-list', token],
    queryFn: async () => {
      const r = await fetch('/api/backups/history?limit=50', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 10000,
  })

  const { data: storageData } = useQuery<StorageData>({
    queryKey: ['backups-storage', token],
    queryFn: async () => {
      const r = await fetch('/api/backups/storage', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  const { data: lastRestoreData } = useQuery<LastRestoreData>({
    queryKey: ['backups-last-restore', token],
    queryFn: async () => {
      const r = await fetch('/api/backups/last-restore', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  const { data: scopeData } = useQuery<BackupScope>({
    queryKey: ['backups-scope', token],
    queryFn: async () => {
      const r = await fetch('/api/backups/scope', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Failed')
      return r.json()
    },
    enabled: !!token,
    staleTime: 300000,
  })


  const createMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch('/api/backups/create', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) { const err = await r.json().catch(() => ({ detail: 'Backup failed' })); throw new Error(err.detail || 'Backup failed') }
      return r.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['backups-summary'] })
      queryClient.invalidateQueries({ queryKey: ['backups-list'] })
      queryClient.invalidateQueries({ queryKey: ['backups-storage'] })
      setCreating(false)
      if (data?.status === 'failed') createMutation.reset()
    },
    onError: () => setCreating(false),
  })

  const restoreMutation = useMutation({
    mutationFn: async (backupId: string) => {
      const r = await fetch(`/api/backups/${backupId}/restore`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      })
      if (!r.ok) { const err = await r.json().catch(() => ({ detail: 'Restore failed' })); throw new Error(err.detail || 'Restore failed') }
      return r.json()
    },
    onSuccess: (data) => {
      setRestoreResult(data)
      setRestoreTarget(null)
      setRestoreError(null)
      queryClient.invalidateQueries({ queryKey: ['backups-summary'] })
      queryClient.invalidateQueries({ queryKey: ['backups-list'] })
      queryClient.invalidateQueries({ queryKey: ['backups-last-restore'] })
      queryClient.invalidateQueries({ queryKey: ['services-summary'] })
      queryClient.invalidateQueries({ queryKey: ['kpis'] })
      queryClient.invalidateQueries({ queryKey: ['external-services'] })
      queryClient.invalidateQueries({ queryKey: ['service-map'] })
      queryClient.invalidateQueries({ queryKey: ['service-map-services'] })
    },
    onError: (err: Error) => {
      setRestoreError(err.message)
      setRestoreTarget(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (backupId: string) => {
      const r = await fetch(`/api/backups/${backupId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      })
      if (!r.ok) { const err = await r.json().catch(() => ({ detail: 'Delete failed' })); throw new Error(err.detail || 'Delete failed') }
      return r.json()
    },
    onSuccess: () => {
      setDeleteTarget(null)
      queryClient.invalidateQueries({ queryKey: ['backups-summary'] })
      queryClient.invalidateQueries({ queryKey: ['backups-list'] })
      queryClient.invalidateQueries({ queryKey: ['backups-storage'] })
    },
    onError: () => setDeleteTarget(null),
  })

  const handleCreate = () => { setCreating(true); createMutation.mutate() }

  const handlePreview = async (id: string) => {
    setPreviewLoading(id)
    try {
      const r = await fetch(`/api/backups/${id}/preview`, { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Preview failed')
      const data = await r.json()
      setPreviewData(data)
    } catch { /* silent */ }
    setPreviewLoading(null)
  }

  const handleRestoreClick = async (id: string, filename: string) => {
    try {
      const r = await fetch(`/api/backups/${id}/preview`, { headers: { Authorization: `Bearer ${token}` } })
      const preview = r.ok ? await r.json() : undefined
      setRestoreTarget({ id, filename, preview })
      setRestoreResult(null)
      setRestoreError(null)
    } catch {
      setRestoreTarget({ id, filename })
    }
  }

  const handleDownload = async (id: string, filename: string) => {
    try {
      const r = await fetch(`/api/backups/${id}/download`, { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error('Download failed')
      const blob = await r.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = filename
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch { /* silent */ }
  }

  const lastOk = summaryData?.latest_successful
  const lastFail = summaryData?.latest_failed
  const totalBackups = summaryData?.total_backups ?? 0

  // Filter and search
  const filteredItems = (listData?.items ?? []).filter((b) => {
    if (statusFilter !== 'all' && b.status !== statusFilter) return false
    if (searchQuery && !b.filename.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Backup & Recovery</h1>
          <p className="text-slate-500 text-sm">Backup, preview, and restore platform configuration — services, alert policies, SLO targets, and incidents</p>
        </div>
        <button onClick={handleCreate} disabled={!canManage || creating || createMutation.isPending}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${canManage ? 'bg-primary hover:bg-primary/80 text-white' : 'bg-gray-100 text-gray-500 cursor-not-allowed'}`}>
          {creating || createMutation.isPending ? <><RefreshCw className="w-4 h-4 animate-spin" />Creating...</> : <><Plus className="w-4 h-4" />Create Backup</>}
        </button>
      </div>

      {/* RBAC banner */}
      {!canManage && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200">
          <Lock className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <p className="text-amber-800 text-sm"><span className="font-medium">View-only mode.</span> Only administrators can create, restore, delete, or download backups.</p>
        </div>
      )}

      {/* Feedback banners */}
      {createMutation.isError && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-50 border border-red-200">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <p className="text-red-700 text-sm">Backup failed: {createMutation.error?.message}</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'completed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-green-50 border border-green-200">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
          <p className="text-green-700 text-sm">Backup created successfully.{createMutation.data?.checksum && <span className="ml-1 text-green-400/60 text-xs">SHA256: {createMutation.data.checksum.slice(0, 16)}...</span>}</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'failed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-50 border border-red-200">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div className="text-red-700 text-sm">
            <span>Backup failed</span>
            {createMutation.data?.error_type && <span className="ml-2">{errorTypeBadge(createMutation.data.error_type)}</span>}
            <p className="text-red-400/80 text-xs mt-1">{createMutation.data?.error_message}</p>
          </div>
        </div>
      )}
      {restoreResult && (
        <div className="px-4 py-3 rounded-lg bg-green-50 border border-green-200">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            <div className="text-green-700 text-sm">
              <p className="font-medium">Restore completed successfully</p>
              <p className="text-green-600 text-xs mt-0.5">Restored {restoreResult.restored.external_services} services and {restoreResult.restored.service_dependencies} dependencies from {restoreResult.backup_filename}</p>
            </div>
            <button onClick={() => setRestoreResult(null)} className="ml-auto text-green-400/60 hover:text-green-300"><X className="w-4 h-4" /></button>
          </div>
          <div className="flex items-center gap-2 mt-3 ml-8">
            <button onClick={() => navigate('/services')} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-green-500/20 text-green-300 hover:bg-green-500/30 border border-green-500/30 transition-colors">
              <ExternalLink className="w-3.5 h-3.5" />Go to Services
            </button>
            <button onClick={() => navigate('/')} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-surface-raised text-text-muted hover:text-text-primary hover:bg-surface-hover border border-border transition-colors">
              <ExternalLink className="w-3.5 h-3.5" />Go to Home
            </button>
          </div>
        </div>
      )}
      {restoreError && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-50 border border-red-200">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-700 text-sm">Restore failed: {restoreError}</p>
          <button onClick={() => setRestoreError(null)} className="ml-auto text-red-400/60 hover:text-red-300"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Summary cards row 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><CheckCircle className="w-4 h-4 text-success" /><span className="text-sm text-text-muted">Last Successful</span></div>
          <p className="text-lg font-semibold text-slate-800">{lastOk ? formatDate(lastOk.created_at) : 'Never'}</p>
          {lastOk && <p className="text-xs text-slate-500 mt-1">{lastOk.filename} ({formatBytes(lastOk.size_bytes)})</p>}
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><XCircle className="w-4 h-4 text-red-400" /><span className="text-sm text-text-muted">Last Failed</span></div>
          <p className="text-lg font-semibold text-slate-800">{lastFail ? formatDate(lastFail.created_at) : 'None'}</p>
          {lastFail && <div className="mt-1 flex items-center gap-1.5">{errorTypeBadge(lastFail.error_type)}<span className="text-xs text-red-400 truncate">{lastFail.error_message?.slice(0, 60)}</span></div>}
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><Archive className="w-4 h-4 text-primary" /><span className="text-sm text-text-muted">Total Backups</span></div>
          <p className="text-lg font-semibold text-slate-800">{totalBackups}</p>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><Database className="w-4 h-4 text-blue-400" /><span className="text-sm text-text-muted">Storage Used</span></div>
          <p className="text-lg font-semibold text-slate-800">{storageData ? formatBytes(storageData.total_bytes) : '-'}</p>
          {storageData && storageData.disk_free_bytes !== null && <p className="text-xs text-slate-500 mt-1">{formatBytes(storageData.disk_free_bytes)} free on disk</p>}
        </div>
      </div>

      {/* Info panels row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Retention Policy */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3"><Shield className="w-4 h-4 text-yellow-500" /><span className="text-sm font-medium text-slate-700">Retention Policy</span></div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">Mode</span><span className="text-slate-800">Manual retention</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Storage Path</span><span className="text-slate-800 font-mono text-xs">{storageData?.storage_path || '-'}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Auto Cleanup</span><span className="text-amber-600 text-xs">No automatic cleanup configured</span></div>
          </div>
        </div>

        {/* Last Restore Audit */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3"><Clock className="w-4 h-4 text-purple-500" /><span className="text-sm font-medium text-slate-700">Last Restore</span></div>
          {lastRestoreData && !lastRestoreData.message ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Date</span><span className="text-slate-800">{formatDate(lastRestoreData.restored_at || null)}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Restored By</span><span className="text-slate-800">{lastRestoreData.restored_by}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Backup File</span><span className="text-slate-800 font-mono text-xs truncate max-w-[200px]">{lastRestoreData.backup_filename}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Records</span><span className="text-slate-800">{lastRestoreData.services_restored} services, {lastRestoreData.dependencies_restored} deps</span></div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No restores performed yet</p>
          )}
        </div>
      </div>


      {/* Backup Scope */}
      {scopeData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="w-4 h-4 text-success" />
              <span className="text-sm font-medium text-slate-700">Included in Backup</span>
            </div>
            <div className="space-y-2">
              {scopeData.included.map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-success mt-1.5 flex-shrink-0" />
                  <div>
                    <span className="text-sm text-slate-800">{item.category}</span>
                    <p className="text-xs text-gray-500">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-slate-700">Not Included</span>
            </div>
            <div className="space-y-2">
              {scopeData.excluded.map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-300 mt-1.5 flex-shrink-0" />
                  <div>
                    <span className="text-sm text-slate-600">{item.category}</span>
                    <p className="text-xs text-slate-500">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Backup History Table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-3 flex-wrap">
          <HardDrive className="w-4 h-4 text-primary" />
          <h2 className="text-slate-800 font-medium">Backup History</h2>
          <div className="flex items-center gap-2 ml-auto">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search filename..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-md bg-white border border-slate-300 text-slate-700 placeholder-slate-400 focus:outline-none focus:border-primary w-48"
              />
            </div>
            <div className="relative">
              <Filter className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-8 pr-6 py-1.5 text-xs rounded-md bg-white border border-slate-300 text-slate-700 appearance-none focus:outline-none focus:border-primary cursor-pointer"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>
            <span className="text-xs text-slate-500">{filteredItems.length} of {listData?.total ?? 0}</span>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500">Loading...</div>
        ) : !filteredItems.length ? (
          <div className="p-8 text-center text-gray-500">{listData?.items?.length ? 'No backups match your filters.' : 'No backups yet. Create your first backup to get started.'}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 text-xs uppercase border-b border-slate-200">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Filename</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Records</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created By</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((b) => (
                  <tr key={b.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-700 whitespace-nowrap">{formatDate(b.created_at)}</td>
                    <td className="px-4 py-3 text-slate-900 font-mono text-xs">{b.filename}</td>
                    <td className="px-4 py-3"><span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">{b.backup_type}</span></td>
                    <td className="px-4 py-3 text-slate-700">{formatBytes(b.size_bytes)}</td>
                    <td className="px-4 py-3 text-slate-700">{b.records_exported ?? '-'}</td>
                    <td className="px-4 py-3">{statusBadge(b.status)}</td>
                    <td className="px-4 py-3 text-slate-700">{b.created_by}</td>
                    <td className="px-4 py-3">
                      {b.status === 'completed' ? (
                        <div className="flex items-center gap-2">
                          <button onClick={() => handlePreview(b.id)} disabled={previewLoading === b.id}
                            className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors" title="Preview">
                            {previewLoading === b.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3" />}Preview
                          </button>
                          {canManage && (
                            <>
                              <button onClick={() => handleDownload(b.id, b.filename)}
                                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors" title="Download">
                                <Download className="w-3 h-3" />
                              </button>
                              <button onClick={() => handleRestoreClick(b.id, b.filename)}
                                className="flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300 transition-colors" title="Restore">
                                <RotateCcw className="w-3 h-3" />Restore
                              </button>
                              <button onClick={() => setDeleteTarget({ id: b.id, filename: b.filename })}
                                className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors" title="Delete">
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </>
                          )}
                        </div>
                      ) : b.status === 'failed' ? (
                        <div className="flex items-center gap-1.5">
                          {errorTypeBadge(b.error_type)}
                          <button onClick={() => setExpandedError(expandedError === b.id ? null : b.id)} className="text-gray-500 hover:text-gray-600" title="Show details"><Info className="w-3 h-3" /></button>
                          {canManage && (
                            <button onClick={() => setDeleteTarget({ id: b.id, filename: b.filename })}
                              className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors ml-1" title="Delete">
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                          {expandedError === b.id && <span className="text-[11px] text-red-400/80 break-words max-w-[200px]">{b.error_message || 'Unknown error'}</span>}
                        </div>
                      ) : <span className="text-xs text-gray-500">-</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setPreviewData(null)}>
          <div className="bg-surface border border-gray-200 rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Eye className="w-5 h-5 text-blue-400" />Backup Preview</h3>
              <button onClick={() => setPreviewData(null)} className="text-gray-500 hover:text-gray-900"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div><span className="text-gray-500 block text-xs">Filename</span><span className="text-gray-900 font-mono text-xs">{previewData.filename}</span></div>
                <div><span className="text-gray-500 block text-xs">Created At</span><span className="text-gray-900">{formatDate(previewData.created_at)}</span></div>
                <div><span className="text-gray-500 block text-xs">Platform Version</span><span className="text-gray-900">{previewData.platform_version || '-'}</span></div>
                <div><span className="text-gray-500 block text-xs">Created By</span><span className="text-gray-900">{previewData.created_by || '-'}</span></div>
              </div>
              <div className="mt-3 p-3 rounded-lg bg-surface-raised border border-border">
                <span className="text-gray-500 text-xs block mb-2">Backup Contents</span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Services</span><span className="text-gray-900 font-semibold">{previewData.contents.external_services}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Dependencies</span><span className="text-gray-900 font-semibold">{previewData.contents.service_dependencies}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Alert Rules</span><span className="text-gray-900 font-semibold">{previewData.contents.alert_rules ?? 0}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">SLO Targets</span><span className="text-gray-900 font-semibold">{previewData.contents.slo_targets ?? 0}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Incidents</span><span className="text-gray-900 font-semibold">{previewData.contents.incidents ?? 0}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Comments</span><span className="text-gray-900 font-semibold">{previewData.contents.incident_comments ?? 0}</span></div>
                </div>
              </div>
              {previewData.checksum && (
                <div><span className="text-gray-500 block text-xs">SHA256 Checksum</span><span className="text-green-600 font-mono text-[11px] break-all">{previewData.checksum}</span></div>
              )}
              {previewData.service_names.length > 0 && (
                <div>
                  <span className="text-gray-500 block text-xs mb-1">Services included</span>
                  <div className="flex flex-wrap gap-1">
                    {previewData.service_names.map((name, i) => (
                      <span key={i} className="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">{name}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              {canManage && (
                <button onClick={() => { setPreviewData(null); handleRestoreClick(previewData.backup_id, previewData.filename) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition-colors">
                  <RotateCcw className="w-3.5 h-3.5" />Restore this backup
                </button>
              )}
              <button onClick={() => setPreviewData(null)} className="px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Restore Confirmation Modal */}
      {restoreTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface border border-red-500/30 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center"><AlertTriangle className="w-5 h-5 text-red-400" /></div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Confirm Restore</h3>
                <p className="text-xs text-gray-500">This action cannot be undone</p>
              </div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-red-700 text-sm font-medium mb-1">Warning: This will overwrite current configuration</p>
              <p className="text-red-600 text-xs">All existing Services, Alert Policies, SLO Targets, and Incidents will be replaced with data from this backup. Users (Keycloak), logs, traces, and metrics are NOT affected.</p>
            </div>
            <div className="text-sm space-y-1 mb-4">
              <p className="text-gray-600"><span className="text-gray-500">File:</span> <span className="font-mono text-xs">{restoreTarget.filename}</span></p>
              {restoreTarget.preview && (
                <>
                  <p className="text-gray-600"><span className="text-gray-500">Services:</span> {restoreTarget.preview.contents.external_services}</p>
                  <p className="text-gray-600"><span className="text-gray-500">Dependencies:</span> {restoreTarget.preview.contents.service_dependencies}</p>
                  {restoreTarget.preview.checksum && (
                    <p className="text-gray-600 flex items-center gap-1"><Shield className="w-3 h-3 text-green-400" /><span className="text-green-400 text-xs">Checksum verified on restore</span></p>
                  )}
                </>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setRestoreTarget(null)} disabled={restoreMutation.isPending}
                className="px-4 py-2 rounded-lg text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">Cancel</button>
              <button onClick={() => restoreMutation.mutate(restoreTarget.id)} disabled={restoreMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50">
                {restoreMutation.isPending ? <><RefreshCw className="w-4 h-4 animate-spin" />Restoring...</> : <><RotateCcw className="w-4 h-4" />Restore Now</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface border border-red-500/30 rounded-xl shadow-2xl w-full max-w-sm mx-4 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center"><Trash2 className="w-5 h-5 text-red-400" /></div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Backup</h3>
                <p className="text-xs text-gray-500">This cannot be undone</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm mb-1">Are you sure you want to delete this backup?</p>
            <p className="text-gray-500 font-mono text-xs mb-4">{deleteTarget.filename}</p>
            <p className="text-red-600 text-xs mb-4">The backup file will be permanently removed from disk and the record will be deleted from the database.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setDeleteTarget(null)} disabled={deleteMutation.isPending}
                className="px-4 py-2 rounded-lg text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors">Cancel</button>
              <button onClick={() => deleteMutation.mutate(deleteTarget.id)} disabled={deleteMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50">
                {deleteMutation.isPending ? <><RefreshCw className="w-4 h-4 animate-spin" />Deleting...</> : <><Trash2 className="w-4 h-4" />Delete</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
