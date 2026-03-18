import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { HardDrive, Download, Plus, CheckCircle, XCircle, Lock, Archive, RefreshCw, AlertTriangle, Info } from 'lucide-react'

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
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
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
  const colorClass = colors[errorType] || 'bg-gray-500/10 text-gray-400'
  const labels: Record<string, string> = {
    permission_error: 'Permission',
    storage_error: 'Storage',
    integrity_error: 'Integrity',
    unexpected_error: 'Error',
  }
  return (
    <span className={`inline-flex items-center text-[10px] px-1.5 py-0.5 rounded font-medium ${colorClass}`}>
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
      const r = await fetch('/api/backups/create', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!r.ok) {
        const err = await r.json().catch(() => ({ detail: 'Backup failed' }))
        throw new Error(err.detail || 'Backup failed')
      }
      return r.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['backups-summary'] })
      queryClient.invalidateQueries({ queryKey: ['backups-list'] })
      setCreating(false)
      if (data?.status === 'failed') {
        createMutation.reset()
      }
    },
    onError: () => {
      setCreating(false)
    },
  })

  const handleCreate = () => {
    setCreating(true)
    createMutation.mutate()
  }

  const handleDownload = async (id: string, filename: string) => {
    try {
      const r = await fetch(`/api/backups/${id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!r.ok) throw new Error('Download failed')
      const blob = await r.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch {
      // silently fail
    }
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
          <p className="text-gray-400 text-sm">Manual backup of platform configuration and service data</p>
        </div>
        <button
          onClick={handleCreate}
          disabled={!canManage || creating || createMutation.isPending}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${canManage ? 'bg-primary hover:bg-primary/80 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed'}`}
        >
          {creating || createMutation.isPending ? (
            <><RefreshCw className="w-4 h-4 animate-spin" />Creating...</>
          ) : (
            <><Plus className="w-4 h-4" />Create Backup</>
          )}
        </button>
      </div>

      {/* RBAC banner */}
      {!canManage && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
          <Lock className="w-5 h-5 text-yellow-400 flex-shrink-0" />
          <p className="text-yellow-300 text-sm">
            <span className="font-medium">View-only mode.</span> You can view backup history but only administrators can create or download backups.
          </p>
        </div>
      )}

      {/* Mutation feedback */}
      {createMutation.isError && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-300 text-sm">Backup failed: {createMutation.error?.message}</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'completed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/30">
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          <p className="text-green-300 text-sm">Backup created successfully.</p>
        </div>
      )}
      {createMutation.isSuccess && createMutation.data?.status === 'failed' && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div className="text-red-300 text-sm">
            <span>Backup failed</span>
            {createMutation.data?.error_type && (
              <span className="ml-2">{errorTypeBadge(createMutation.data.error_type)}</span>
            )}
            <p className="text-red-400/80 text-xs mt-1">{createMutation.data?.error_message}</p>
          </div>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Last Successful */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-success" />
            <span className="text-sm text-text-muted">Last Successful</span>
          </div>
          <p className="text-lg font-semibold text-white">{lastOk ? formatDate(lastOk.created_at) : 'Never'}</p>
          {lastOk && <p className="text-xs text-gray-400 mt-1">{lastOk.filename} ({formatBytes(lastOk.size_bytes)})</p>}
        </div>

        {/* Last Failed */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-text-muted">Last Failed</span>
          </div>
          <p className="text-lg font-semibold text-white">{lastFail ? formatDate(lastFail.created_at) : 'None'}</p>
          {lastFail && (
            <div className="mt-1 flex items-center gap-1.5">
              {errorTypeBadge(lastFail.error_type)}
              <span className="text-xs text-red-400 truncate">{lastFail.error_message?.slice(0, 60)}</span>
            </div>
          )}
        </div>

        {/* Total */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <Archive className="w-4 h-4 text-primary" />
            <span className="text-sm text-text-muted">Total Backups</span>
          </div>
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
                  <th className="px-4 py-3">Action</th>
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
                      {b.status === 'completed' && canManage ? (
                        <button
                          onClick={() => handleDownload(b.id, b.filename)}
                          className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />Download
                        </button>
                      ) : b.status === 'completed' ? (
                        <span className="text-xs text-gray-500">Admin only</span>
                      ) : b.status === 'failed' ? (
                        <div className="flex flex-col gap-1 max-w-[200px]">
                          <div className="flex items-center gap-1.5">
                            {errorTypeBadge(b.error_type)}
                            <button
                              onClick={() => setExpandedError(expandedError === b.id ? null : b.id)}
                              className="text-gray-400 hover:text-gray-300"
                              title="Show details"
                            >
                              <Info className="w-3 h-3" />
                            </button>
                          </div>
                          {expandedError === b.id && (
                            <span className="text-[11px] text-red-400/80 break-words">
                              {b.error_message || 'Unknown error'}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
