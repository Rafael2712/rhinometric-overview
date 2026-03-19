import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { HardDrive, Download, Plus, CheckCircle, XCircle, Lock, Archive, RefreshCw, AlertTriangle, Info, Eye, RotateCcw, X, Shield } from 'lucide-react'

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
  contents: { external_services: number; service_dependencies: number }
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

function formatBytes(bytes: number | null): string {
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
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-success/10 text-success"><CheckCircle className="w-3 h-3" />Completed</span>
    case 'failed':
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400"><XCircle className="w-3 h-3" />Failed</span>
    case 'in_progress':
      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-400"><RefreshCw className="w-3 h-3 animate-spin" />In Progress</span>
    default:
      return <span className="text-xs text-gray-400">{status}</span>
  }
}

function errorTypeBadge(errorType: string | null) {
  if (!errorType) return null
  const colors: Record<string, string> = {
    permission_error: 'bg-orange-500/10 text-orange-400',
    storage_error: 'bg-yellow-500/10 text-yellow-400',
    integrity_error: 'bg-purple-500/10 text-purple-400',
    unexpected_error: 'bg-red-500/10 text-red-400',
  }
  const labels: Record<string, string> = {
    permission_error: 'Permission',
    storage_error: 'Storage',
    integrity_error: 'Integrity',
    unexpected_error: 'Error',
  }
  return (
    <span className={`inline-flex items-center text-[10px] px-1.5 py-0.5 rounded font-medium ${colors[errorType] || 'bg-gray-500/10 text-gray-400'}`}>
      {labels[errorType] || errorType}
    </span>
  )
}

export function BackupRecoveryPage() {
  const { token, isAdmin } = useAuthStore()
  const queryClient = useQueryClient()
  const canManage = isAdmin()
  const [creating, setCreating] = useState(false)
  const [expandedError, setExpandedError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [previewLoading, setPreviewLoading] = useState<string | null>(null)
  const [restoreTarget, setRestoreTarget] = useState<{ id: string; filename: string; preview?: PreviewData } | null>(null)
  const [restoreResult, setRestoreResult] = useState<RestoreResult | null>(null)
  const [restoreError, setRestoreError] = useState<string | null>(null)

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

  const createMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch('/api/backups/create', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) { const err = await r.json().catch(() => ({ detail: 'Backup failed' })); throw new Error(err.detail || 'Backup failed') }
      return r.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['backups-summary'] })
      queryClient.invalidateQueries({ queryKey: ['backups-list'] })
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
      // Sync other pages so restored data is visible immediately
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Backup & Recovery</h1>
          <p className="text-gray-400 text-sm">Backup, preview, and restore platform configuration</p>
        </div>
        <button onClick={handleCreate} disabled={!canManage || creating || createMutation.isPending}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${canManage ? 'bg-primary hover:bg-primary/80 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed'}`}>
          {creating || createMutation.isPending ? <><RefreshCw className="w-4 h-4 animate-spin" />Creating...</> : <><Plus className="w-4 h-4" />Create Backup</>}
        </button>
      </div>

      {/* RBAC banner */}
      {!canManage && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
          <Lock className="w-5 h-5 text-yellow-400 flex-shrink-0" />
          <p className="text-yellow-300 text-sm"><span className="font-medium">View-only mode.</span> Only administrators can create, restore, or download backups.</p>
        </div>
      )}

      {/* Feedback banners */}
      {createMutation.isError && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-300 text-sm">Backup failed: {createMutation.error?.message}</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'completed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/30">
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          <p className="text-green-300 text-sm">Backup created successfully.{createMutation.data?.checksum && <span className="ml-1 text-green-400/60 text-xs">SHA256: {createMutation.data.checksum.slice(0, 16)}...</span>}</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'failed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div className="text-red-300 text-sm">
            <span>Backup failed</span>
            {createMutation.data?.error_type && <span className="ml-2">{errorTypeBadge(createMutation.data.error_type)}</span>}
            <p className="text-red-400/80 text-xs mt-1">{createMutation.data?.error_message}</p>
          </div>
        </div>
      )}
      {restoreResult && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/30">
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          <div className="text-green-300 text-sm">
            <p className="font-medium">Restore completed successfully</p>
            <p className="text-green-400/70 text-xs mt-0.5">Restored {restoreResult.restored.external_services} services and {restoreResult.restored.service_dependencies} dependencies from {restoreResult.backup_filename}</p>
          </div>
          <button onClick={() => setRestoreResult(null)} className="ml-auto text-green-400/60 hover:text-green-300"><X className="w-4 h-4" /></button>
        </div>
      )}
      {restoreError && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-300 text-sm">Restore failed: {restoreError}</p>
          <button onClick={() => setRestoreError(null)} className="ml-auto text-red-400/60 hover:text-red-300"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><CheckCircle className="w-4 h-4 text-success" /><span className="text-sm text-text-muted">Last Successful</span></div>
          <p className="text-lg font-semibold text-white">{lastOk ? formatDate(lastOk.created_at) : 'Never'}</p>
          {lastOk && <p className="text-xs text-gray-400 mt-1">{lastOk.filename} ({formatBytes(lastOk.size_bytes)})</p>}
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><XCircle className="w-4 h-4 text-red-400" /><span className="text-sm text-text-muted">Last Failed</span></div>
          <p className="text-lg font-semibold text-white">{lastFail ? formatDate(lastFail.created_at) : 'None'}</p>
          {lastFail && <div className="mt-1 flex items-center gap-1.5">{errorTypeBadge(lastFail.error_type)}<span className="text-xs text-red-400 truncate">{lastFail.error_message?.slice(0, 60)}</span></div>}
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2"><Archive className="w-4 h-4 text-primary" /><span className="text-sm text-text-muted">Total Backups</span></div>
          <p className="text-lg font-semibold text-white">{totalBackups}</p>
        </div>
      </div>

      {/* Backup History Table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-primary" />
          <h2 className="text-white font-medium">Backup History</h2>
          <span className="text-xs text-gray-400 ml-auto">{listData?.total ?? 0} total</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : !listData?.items?.length ? (
          <div className="p-8 text-center text-gray-400">No backups yet. Create your first backup to get started.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 text-xs uppercase border-b border-gray-700">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Filename</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Records</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created By</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {listData.items.map((b) => (
                  <tr key={b.id} className="border-b border-gray-700/50 hover:bg-surface-light/30">
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{formatDate(b.created_at)}</td>
                    <td className="px-4 py-3 text-white font-mono text-xs">{b.filename}</td>
                    <td className="px-4 py-3 text-gray-300">{formatBytes(b.size_bytes)}</td>
                    <td className="px-4 py-3 text-gray-300">{b.records_exported ?? '-'}</td>
                    <td className="px-4 py-3">{statusBadge(b.status)}</td>
                    <td className="px-4 py-3 text-gray-300">{b.created_by}</td>
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
                            </>
                          )}
                        </div>
                      ) : b.status === 'failed' ? (
                        <div className="flex flex-col gap-1 max-w-[200px]">
                          <div className="flex items-center gap-1.5">
                            {errorTypeBadge(b.error_type)}
                            <button onClick={() => setExpandedError(expandedError === b.id ? null : b.id)} className="text-gray-400 hover:text-gray-300" title="Show details"><Info className="w-3 h-3" /></button>
                          </div>
                          {expandedError === b.id && <span className="text-[11px] text-red-400/80 break-words">{b.error_message || 'Unknown error'}</span>}
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
          <div className="bg-surface border border-gray-700 rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2"><Eye className="w-5 h-5 text-blue-400" />Backup Preview</h3>
              <button onClick={() => setPreviewData(null)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div><span className="text-gray-400 block text-xs">Filename</span><span className="text-white font-mono text-xs">{previewData.filename}</span></div>
                <div><span className="text-gray-400 block text-xs">Created At</span><span className="text-white">{formatDate(previewData.created_at)}</span></div>
                <div><span className="text-gray-400 block text-xs">Platform Version</span><span className="text-white">{previewData.platform_version || '-'}</span></div>
                <div><span className="text-gray-400 block text-xs">Created By</span><span className="text-white">{previewData.created_by || '-'}</span></div>
                <div><span className="text-gray-400 block text-xs">External Services</span><span className="text-white text-lg font-semibold">{previewData.contents.external_services}</span></div>
                <div><span className="text-gray-400 block text-xs">Service Dependencies</span><span className="text-white text-lg font-semibold">{previewData.contents.service_dependencies}</span></div>
              </div>
              {previewData.checksum && (
                <div><span className="text-gray-400 block text-xs">SHA256 Checksum</span><span className="text-green-400/80 font-mono text-[11px] break-all">{previewData.checksum}</span></div>
              )}
              {previewData.service_names.length > 0 && (
                <div>
                  <span className="text-gray-400 block text-xs mb-1">Services included</span>
                  <div className="flex flex-wrap gap-1">
                    {previewData.service_names.map((name, i) => (
                      <span key={i} className="text-[11px] px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-300">{name}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              {canManage && (
                <button onClick={() => { setPreviewData(null); handleRestoreClick(previewData.backup_id, previewData.filename) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 transition-colors">
                  <RotateCcw className="w-3.5 h-3.5" />Restore this backup
                </button>
              )}
              <button onClick={() => setPreviewData(null)} className="px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-700 transition-colors">Close</button>
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
                <h3 className="text-lg font-semibold text-white">Confirm Restore</h3>
                <p className="text-xs text-gray-400">This action cannot be undone</p>
              </div>
            </div>
            <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 mb-4">
              <p className="text-red-300 text-sm font-medium mb-1">Warning: This will overwrite current configuration</p>
              <p className="text-red-400/70 text-xs">All existing External Services and Service Dependencies will be replaced with data from this backup. Users, roles, alerts, logs, and metrics are NOT affected.</p>
            </div>
            <div className="text-sm space-y-1 mb-4">
              <p className="text-gray-300"><span className="text-gray-500">File:</span> <span className="font-mono text-xs">{restoreTarget.filename}</span></p>
              {restoreTarget.preview && (
                <>
                  <p className="text-gray-300"><span className="text-gray-500">Services:</span> {restoreTarget.preview.contents.external_services}</p>
                  <p className="text-gray-300"><span className="text-gray-500">Dependencies:</span> {restoreTarget.preview.contents.service_dependencies}</p>
                  {restoreTarget.preview.checksum && (
                    <p className="text-gray-300 flex items-center gap-1"><Shield className="w-3 h-3 text-green-400" /><span className="text-green-400 text-xs">Checksum verified on restore</span></p>
                  )}
                </>
              )}
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setRestoreTarget(null)} disabled={restoreMutation.isPending}
                className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-700 transition-colors">Cancel</button>
              <button onClick={() => restoreMutation.mutate(restoreTarget.id)} disabled={restoreMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50">
                {restoreMutation.isPending ? <><RefreshCw className="w-4 h-4 animate-spin" />Restoring...</> : <><RotateCcw className="w-4 h-4" />Restore Now</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
