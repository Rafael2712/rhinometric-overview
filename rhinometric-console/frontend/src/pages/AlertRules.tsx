/* eslint-disable */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Shield, Plus, Pencil, Trash2, ToggleLeft, ToggleRight,
  Search, Filter, X, Save, AlertTriangle
} from 'lucide-react'

/* ── Types ── */
interface AlertRuleRow {
  id: string
  name: string
  service_id: number
  service_name: string
  metric: string
  operator: string
  threshold: number
  window_minutes: number
  severity: string
  enabled: boolean
  created_at: string | null
  updated_at: string | null
}

interface ServiceOption {
  id: number
  name: string
}

const METRICS = [
  { value: 'latency_ms', label: 'Latency (ms)' },
  { value: 'error_rate', label: 'Error Rate (%)' },
  { value: 'availability_pct', label: 'Availability (%)' },
  { value: 'response_time_p95', label: 'P95 Response Time (ms)' },
]

const OPERATORS = ['>', '<', '>=', '<=']
const SEVERITIES = ['info', 'warning', 'critical']

/* ── Helpers ── */
const metricLabel = (m: string) => METRICS.find((x) => x.value === m)?.label || m
const timeAgo = (ts: string | null) => {
  if (!ts) return '—'
  const d = Date.now() - new Date(ts).getTime()
  if (d < 60000) return 'just now'
  if (d < 3600000) return `${Math.floor(d / 60000)}m ago`
  if (d < 86400000) return `${Math.floor(d / 3600000)}h ago`
  return `${Math.floor(d / 86400000)}d ago`
}

/* ── Badges ── */
function SeverityBadge({ severity }: { severity: string }) {
  const cls: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${cls[severity] || cls.info}`}>
      {severity}
    </span>
  )
}

/* ── Main Page ── */
export function AlertRulesPage() {
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }

  const [search, setSearch] = useState('')
  const [filterSeverity, setFilterSeverity] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRuleRow | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formServiceId, setFormServiceId] = useState<number>(0)
  const [formMetric, setFormMetric] = useState('latency_ms')
  const [formOperator, setFormOperator] = useState('>')
  const [formThreshold, setFormThreshold] = useState<number>(500)
  const [formWindow, setFormWindow] = useState<number>(5)
  const [formSeverity, setFormSeverity] = useState('warning')
  const [formEnabled, setFormEnabled] = useState(true)

  // Queries
  const { data: rulesData, isLoading } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: async () => {
      const res = await fetch('/api/alert-rules', { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<{ rules: AlertRuleRow[]; total: number }>
    },
    refetchInterval: 15000,
  })

  const { data: servicesData } = useQuery({
    queryKey: ['alert-rules-services'],
    queryFn: async () => {
      const res = await fetch('/api/alert-rules/services/list', { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<{ services: ServiceOption[] }>
    },
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const res = await fetch('/api/alert-rules', {
        method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Failed') }
      return res.json()
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['alert-rules'] }); resetForm() },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, body }: { id: string; body: Record<string, unknown> }) => {
      const res = await fetch(`/api/alert-rules/${id}`, {
        method: 'PATCH', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Failed') }
      return res.json()
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['alert-rules'] }); resetForm() },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/alert-rules/${id}`, { method: 'DELETE', headers })
      if (!res.ok) throw new Error('Failed')
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alert-rules'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: async ({ id, enabled }: { id: string; enabled: boolean }) => {
      const res = await fetch(`/api/alert-rules/${id}`, {
        method: 'PATCH', headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alert-rules'] }),
  })

  const resetForm = () => {
    setShowForm(false)
    setEditingRule(null)
    setFormName('')
    setFormServiceId(0)
    setFormMetric('latency_ms')
    setFormOperator('>')
    setFormThreshold(500)
    setFormWindow(5)
    setFormSeverity('warning')
    setFormEnabled(true)
  }

  const openEdit = (r: AlertRuleRow) => {
    setEditingRule(r)
    setFormName(r.name)
    setFormServiceId(r.service_id)
    setFormMetric(r.metric)
    setFormOperator(r.operator)
    setFormThreshold(r.threshold)
    setFormWindow(r.window_minutes)
    setFormSeverity(r.severity)
    setFormEnabled(r.enabled)
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const body = {
      name: formName, service_id: formServiceId, metric: formMetric,
      operator: formOperator, threshold: formThreshold,
      window_minutes: formWindow, severity: formSeverity, enabled: formEnabled,
    }
    if (editingRule) {
      updateMutation.mutate({ id: editingRule.id, body })
    } else {
      createMutation.mutate(body)
    }
  }

  const rules = rulesData?.rules || []
  const services = servicesData?.services || []

  const filtered = rules.filter((r) => {
    if (search && !r.name.toLowerCase().includes(search.toLowerCase()) &&
        !r.service_name.toLowerCase().includes(search.toLowerCase())) return false
    if (filterSeverity !== 'all' && r.severity !== filterSeverity) return false
    return true
  })

  const stats = {
    total: rules.length,
    enabled: rules.filter((r) => r.enabled).length,
    critical: rules.filter((r) => r.severity === 'critical').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="text-purple-400" size={28} />
            Alert Rules
          </h1>
          <p className="text-sm text-gray-400 mt-1">Define custom alert rules for your monitored services</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors border border-purple-500/30"
        >
          <Plus size={16} /> New Rule
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Total Rules', value: stats.total, color: 'text-blue-400' },
          { label: 'Enabled', value: stats.enabled, color: 'text-green-400' },
          { label: 'Critical', value: stats.critical, color: 'text-red-400' },
        ].map((s) => (
          <div key={s.label} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
            <p className="text-xs text-gray-500 uppercase tracking-wider">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search rules or services..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-gray-300 focus:outline-none focus:border-purple-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-500" />
          {['all', ...SEVERITIES].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterSeverity === sev
                  ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                  : 'bg-gray-800/50 text-gray-400 border border-gray-700/50 hover:text-gray-300'
              }`}
            >
              {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Create/Edit Form Modal */}
      {showForm && (
        <div className="bg-gray-800/80 rounded-xl p-6 border border-purple-500/30">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              {editingRule ? 'Edit Rule' : 'Create New Rule'}
            </h2>
            <button onClick={resetForm} className="text-gray-400 hover:text-white"><X size={18} /></button>
          </div>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs text-gray-400 mb-1">Rule Name</label>
              <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)} required
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Service</label>
              <select value={formServiceId} onChange={(e) => setFormServiceId(Number(e.target.value))} required
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                <option value={0} disabled>Select service...</option>
                {services.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Metric</label>
              <select value={formMetric} onChange={(e) => setFormMetric(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                {METRICS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Operator</label>
              <select value={formOperator} onChange={(e) => setFormOperator(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                {OPERATORS.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Threshold</label>
              <input type="number" step="any" value={formThreshold} onChange={(e) => setFormThreshold(Number(e.target.value))} required
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Window (min)</label>
              <input type="number" min={1} max={1440} value={formWindow} onChange={(e) => setFormWindow(Number(e.target.value))} required
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Severity</label>
              <select value={formSeverity} onChange={(e) => setFormSeverity(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                {SEVERITIES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
            <div className="flex items-end">
              <button type="submit"
                disabled={createMutation.isPending || updateMutation.isPending || !formName || !formServiceId}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors">
                <Save size={16} /> {editingRule ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
          {(createMutation.isError || updateMutation.isError) && (
            <p className="mt-3 text-sm text-red-400 flex items-center gap-1">
              <AlertTriangle size={14} />
              {(createMutation.error || updateMutation.error)?.message || 'Operation failed'}
            </p>
          )}
        </div>
      )}

      {/* Rules Table (Desktop) */}
      <div className="hidden md:block overflow-x-auto rounded-xl border border-gray-700/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/50 text-gray-400 uppercase tracking-wider text-xs text-left">
              <th className="px-4 py-3">Rule Name</th>
              <th className="px-4 py-3">Service</th>
              <th className="px-4 py-3">Metric</th>
              <th className="px-4 py-3">Threshold</th>
              <th className="px-4 py-3">Window</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {isLoading ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                {rules.length === 0 ? 'No alert rules defined yet. Click "New Rule" to create one.' : 'No rules match your filters.'}
              </td></tr>
            ) : filtered.map((r) => (
              <tr key={r.id} className={`hover:bg-gray-800/30 transition-colors ${!r.enabled ? 'opacity-50' : ''}`}>
                <td className="px-4 py-3 text-white font-medium">{r.name}</td>
                <td className="px-4 py-3 text-gray-300">{r.service_name}</td>
                <td className="px-4 py-3 text-gray-300">{metricLabel(r.metric)}</td>
                <td className="px-4 py-3 text-gray-300 font-mono">{r.operator} {r.threshold}</td>
                <td className="px-4 py-3 text-gray-400">{r.window_minutes}m</td>
                <td className="px-4 py-3"><SeverityBadge severity={r.severity} /></td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleMutation.mutate({ id: r.id, enabled: !r.enabled })}
                    className={`flex items-center gap-1 text-xs font-medium ${r.enabled ? 'text-green-400' : 'text-gray-500'}`}
                  >
                    {r.enabled ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                    {r.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{timeAgo(r.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(r)} className="text-gray-400 hover:text-blue-400 transition-colors" title="Edit">
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => { if (confirm('Delete this rule?')) deleteMutation.mutate(r.id) }}
                      className="text-gray-400 hover:text-red-400 transition-colors" title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-3">
        {filtered.map((r) => (
          <div key={r.id} className={`bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 ${!r.enabled ? 'opacity-50' : ''}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium text-sm">{r.name}</span>
              <SeverityBadge severity={r.severity} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3">
              <span>Service: <span className="text-gray-300">{r.service_name}</span></span>
              <span>Metric: <span className="text-gray-300">{metricLabel(r.metric)}</span></span>
              <span>Threshold: <span className="text-gray-300 font-mono">{r.operator} {r.threshold}</span></span>
              <span>Window: <span className="text-gray-300">{r.window_minutes}m</span></span>
            </div>
            <div className="flex items-center justify-between">
              <button
                onClick={() => toggleMutation.mutate({ id: r.id, enabled: !r.enabled })}
                className={`flex items-center gap-1 text-xs ${r.enabled ? 'text-green-400' : 'text-gray-500'}`}
              >
                {r.enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                {r.enabled ? 'Enabled' : 'Disabled'}
              </button>
              <div className="flex gap-3">
                <button onClick={() => openEdit(r)} className="text-gray-400 hover:text-blue-400"><Pencil size={14} /></button>
                <button onClick={() => { if (confirm('Delete?')) deleteMutation.mutate(r.id) }}
                  className="text-gray-400 hover:text-red-400"><Trash2 size={14} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
