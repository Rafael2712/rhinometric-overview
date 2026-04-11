/* eslint-disable */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Shield, Plus, Pencil, Trash2, ToggleLeft, ToggleRight,
  Search, Filter, X, Save, AlertTriangle, WifiOff,
  Clock, Activity, ChevronDown, ChevronUp, Settings2,
  RefreshCw
} from 'lucide-react'

/* ── Types ── */
interface AlertPolicyRow {
  id: string
  name: string
  rule_type: string
  service_id: number | null
  service_name: string
  consecutive_failures: number
  critical_escalation_failures: number
  incident_after_seconds: number
  latency_threshold_ms: number | null
  latency_deviation_pct: number | null
  anomaly_score_threshold: number | null
  sustained_checks: number
  severity: string
  cooldown_seconds: number
  enabled: boolean
  is_default: boolean
  description: string | null
  created_at: string | null
  updated_at: string | null
}

interface ServiceOption { id: number; name: string }

const RULE_TYPES = [
  {
    value: 'SERVICE_DOWN',
    label: 'Service Down',
    icon: WifiOff,
    color: 'red',
    description: 'Alert when a service becomes unreachable after consecutive failures',
    gradient: 'from-red-500/10 to-red-900/5',
    border: 'border-red-500/30',
    iconBg: 'bg-red-500/20 text-red-400',
  },
  {
    value: 'HIGH_LATENCY',
    label: 'High Latency',
    icon: Clock,
    color: 'amber',
    description: 'Alert when response time exceeds threshold for sustained checks',
    gradient: 'from-amber-500/10 to-amber-900/5',
    border: 'border-amber-500/30',
    iconBg: 'bg-amber-500/20 text-amber-400',
  },
  {
    value: 'DEGRADED_HEALTH',
    label: 'Degraded Health',
    icon: Activity,
    color: 'purple',
    description: 'Alert when AI anomaly score exceeds threshold for sustained checks',
    gradient: 'from-purple-500/10 to-purple-900/5',
    border: 'border-purple-500/30',
    iconBg: 'bg-purple-500/20 text-purple-400',
  },
]

const SEVERITIES = ['info', 'warning', 'critical']

/* ── Helpers ── */
const ruleTypeConfig = (t: string) => RULE_TYPES.find((x) => x.value === t) || RULE_TYPES[0]

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

function RuleTypeBadge({ ruleType }: { ruleType: string }) {
  const cfg = ruleTypeConfig(ruleType)
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${cfg.border} ${cfg.iconBg}`}>
      <Icon size={12} />
      {cfg.label}
    </span>
  )
}

function DefaultBadge() {
  return (
    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium border border-gray-600 bg-gray-700/50 text-gray-400 uppercase tracking-wider">
      Default
    </span>
  )
}

/* ── Form Field Components ── */
function FieldGroup({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[10px] text-gray-600 mt-0.5">{hint}</p>}
    </div>
  )
}

function NumberInput({ value, onChange, min, max, step }: {
  value: number; onChange: (v: number) => void; min?: number; max?: number; step?: number | string
}) {
  return (
    <input
      type="number" value={value} min={min} max={max} step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500"
    />
  )
}

/* ── Main Page ── */
export function AlertRulesPage() {
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }

  const [search, setSearch] = useState('')
  const [filterSeverity, setFilterSeverity] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertPolicyRow | null>(null)
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())

  // Form state
  const [formName, setFormName] = useState('')
  const [formRuleType, setFormRuleType] = useState('SERVICE_DOWN')
  const [formServiceId, setFormServiceId] = useState<number | null>(null)
  const [formConsecutiveFailures, setFormConsecutiveFailures] = useState(3)
  const [formCriticalEscalation, setFormCriticalEscalation] = useState(6)
  const [formIncidentAfterSeconds, setFormIncidentAfterSeconds] = useState(120)
  const [formLatencyThresholdMs, setFormLatencyThresholdMs] = useState(1000)
  const [formAnomalyScoreThreshold, setFormAnomalyScoreThreshold] = useState(70)
  const [formSustainedChecks, setFormSustainedChecks] = useState(3)
  const [formSeverity, setFormSeverity] = useState('warning')
  const [formCooldownSeconds, setFormCooldownSeconds] = useState(120)
  const [formEnabled, setFormEnabled] = useState(true)
  const [formDescription, setFormDescription] = useState('')

  // Queries
  const { data: rulesData, isLoading } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: async () => {
      const res = await fetch('/api/alert-rules', { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<{ rules: AlertPolicyRow[]; total: number }>
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

  const seedMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/alert-rules/seed-defaults', {
        method: 'POST', headers,
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
    setFormRuleType('SERVICE_DOWN')
    setFormServiceId(null)
    setFormConsecutiveFailures(3)
    setFormCriticalEscalation(6)
    setFormIncidentAfterSeconds(120)
    setFormLatencyThresholdMs(1000)
    setFormAnomalyScoreThreshold(70)
    setFormSustainedChecks(3)
    setFormSeverity('warning')
    setFormCooldownSeconds(120)
    setFormEnabled(true)
    setFormDescription('')
  }

  const openEdit = (r: AlertPolicyRow) => {
    setEditingRule(r)
    setFormName(r.name)
    setFormRuleType(r.rule_type)
    setFormServiceId(r.service_id)
    setFormConsecutiveFailures(r.consecutive_failures)
    setFormCriticalEscalation(r.critical_escalation_failures)
    setFormIncidentAfterSeconds(r.incident_after_seconds)
    setFormLatencyThresholdMs(r.latency_threshold_ms || 1000)
    setFormAnomalyScoreThreshold(r.anomaly_score_threshold || 70)
    setFormSustainedChecks(r.sustained_checks)
    setFormSeverity(r.severity)
    setFormCooldownSeconds(r.cooldown_seconds)
    setFormEnabled(r.enabled)
    setFormDescription(r.description || '')
    setShowForm(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const body: Record<string, unknown> = {
      name: formName,
      rule_type: formRuleType,
      service_id: formServiceId,
      consecutive_failures: formConsecutiveFailures,
      critical_escalation_failures: formCriticalEscalation,
      incident_after_seconds: formIncidentAfterSeconds,
      latency_threshold_ms: formLatencyThresholdMs,
      anomaly_score_threshold: formAnomalyScoreThreshold,
      sustained_checks: formSustainedChecks,
      severity: formSeverity,
      cooldown_seconds: formCooldownSeconds,
      enabled: formEnabled,
      description: formDescription || null,
    }
    if (editingRule) {
      updateMutation.mutate({ id: editingRule.id, body })
    } else {
      createMutation.mutate(body)
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const rules = rulesData?.rules || []
  const services = servicesData?.services || []

  const filtered = rules.filter((r) => {
    if (search && !r.name.toLowerCase().includes(search.toLowerCase()) &&
      !r.service_name.toLowerCase().includes(search.toLowerCase())) return false
    if (filterSeverity !== 'all' && r.severity !== filterSeverity) return false
    if (filterType !== 'all' && r.rule_type !== filterType) return false
    return true
  })

  /* ── Policy Configuration Summary helpers ── */
  const policyDetail = (r: AlertPolicyRow): string => {
    switch (r.rule_type) {
      case 'SERVICE_DOWN':
        return `${r.consecutive_failures} failures → alert, ${r.critical_escalation_failures} → critical, incident after ${r.incident_after_seconds}s`
      case 'HIGH_LATENCY':
        return `>${r.latency_threshold_ms || 1000}ms for ${r.sustained_checks} checks`
      case 'DEGRADED_HEALTH':
        return `Score ≥${r.anomaly_score_threshold || 70} for ${r.sustained_checks} checks`
      default:
        return ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="text-purple-400" size={28} />
            Alert Policies
          </h1>
          <p className="text-sm text-gray-400 mt-1">Configure monitoring policies for your synthetic checks</p>
        </div>
        <div className="flex items-center gap-2">
          {rules.length === 0 && (
            <button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors border border-green-500/30"
            >
              <RefreshCw size={16} className={seedMutation.isPending ? 'animate-spin' : ''} />
              Load Defaults
            </button>
          )}
          <button
            onClick={() => { resetForm(); setShowForm(true) }}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors border border-purple-500/30"
          >
            <Plus size={16} /> New Policy
          </button>
        </div>
      </div>

      {/* Policy Type Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {RULE_TYPES.map((rt) => {
          const Icon = rt.icon
          const count = rules.filter((r) => r.rule_type === rt.value).length
          const enabledCount = rules.filter((r) => r.rule_type === rt.value && r.enabled).length
          return (
            <div
              key={rt.value}
              onClick={() => setFilterType(filterType === rt.value ? 'all' : rt.value)}
              className={`bg-gradient-to-br ${rt.gradient} rounded-xl p-4 border cursor-pointer transition-all hover:scale-[1.02]
                ${filterType === rt.value ? rt.border + ' ring-1 ring-' + rt.color + '-500/20' : 'border-gray-700/50'}`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${rt.iconBg}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{rt.label}</p>
                  <p className="text-[10px] text-gray-500">{rt.description}</p>
                </div>
              </div>
              <div className="flex items-baseline gap-3 mt-3">
                <span className="text-2xl font-bold text-white">{count}</span>
                <span className="text-xs text-gray-500">
                  {enabledCount} enabled
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search policies or services..."
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

      {/* Create/Edit Policy Form */}
      {showForm && (
        <div className="bg-gray-800/80 rounded-xl p-6 border border-purple-500/30">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Settings2 size={18} className="text-purple-400" />
              {editingRule ? 'Edit Policy' : 'Create New Policy'}
            </h2>
            <button onClick={resetForm} className="text-gray-400 hover:text-white"><X size={18} /></button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Row 1: Identity */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-1">
                <FieldGroup label="Policy Name">
                  <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)} required
                    placeholder="e.g., Service Down — API"
                    className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500" />
                </FieldGroup>
              </div>
              <div>
                <FieldGroup label="Rule Type">
                  <select value={formRuleType} onChange={(e) => setFormRuleType(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                    {RULE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </FieldGroup>
              </div>
              <div>
                <FieldGroup label="Scope" hint="Leave empty for all services">
                  <select value={formServiceId ?? ''} onChange={(e) => setFormServiceId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                    <option value="">All Services (global)</option>
                    {services.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </FieldGroup>
              </div>
            </div>

            {/* Row 2: Rule-type specific thresholds */}
            <div className={`rounded-lg p-4 border ${ruleTypeConfig(formRuleType).border} bg-gradient-to-br ${ruleTypeConfig(formRuleType).gradient}`}>
              <div className="flex items-center gap-2 mb-3">
                {(() => { const Icon = ruleTypeConfig(formRuleType).icon; return <Icon size={14} className="text-gray-400" /> })()}
                <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  {ruleTypeConfig(formRuleType).label} Configuration
                </span>
              </div>

              {formRuleType === 'SERVICE_DOWN' && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <FieldGroup label="Consecutive Failures" hint="Failures before first alert">
                    <NumberInput value={formConsecutiveFailures} onChange={setFormConsecutiveFailures} min={1} max={100} />
                  </FieldGroup>
                  <FieldGroup label="Critical Escalation" hint="Failures before escalating to critical">
                    <NumberInput value={formCriticalEscalation} onChange={setFormCriticalEscalation} min={1} max={100} />
                  </FieldGroup>
                  <FieldGroup label="Incident After (seconds)" hint="Sustained downtime before creating incident">
                    <NumberInput value={formIncidentAfterSeconds} onChange={setFormIncidentAfterSeconds} min={0} max={86400} />
                  </FieldGroup>
                </div>
              )}

              {formRuleType === 'HIGH_LATENCY' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FieldGroup label="Latency Threshold (ms)" hint="Response time limit">
                    <NumberInput value={formLatencyThresholdMs} onChange={setFormLatencyThresholdMs} min={1} max={60000} />
                  </FieldGroup>
                  <FieldGroup label="Sustained Checks" hint="Consecutive checks exceeding threshold">
                    <NumberInput value={formSustainedChecks} onChange={setFormSustainedChecks} min={1} max={100} />
                  </FieldGroup>
                </div>
              )}

              {formRuleType === 'DEGRADED_HEALTH' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FieldGroup label="Anomaly Score Threshold" hint="Score 0–100, higher = more anomalous">
                    <NumberInput value={formAnomalyScoreThreshold} onChange={setFormAnomalyScoreThreshold} min={0} max={100} />
                  </FieldGroup>
                  <FieldGroup label="Sustained Checks" hint="Consecutive checks exceeding threshold">
                    <NumberInput value={formSustainedChecks} onChange={setFormSustainedChecks} min={1} max={100} />
                  </FieldGroup>
                </div>
              )}
            </div>

            {/* Row 3: Common controls */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <FieldGroup label="Severity">
                <select value={formSeverity} onChange={(e) => setFormSeverity(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500">
                  {SEVERITIES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                </select>
              </FieldGroup>
              <FieldGroup label="Cooldown (seconds)" hint="Silence after an alert fires">
                <NumberInput value={formCooldownSeconds} onChange={setFormCooldownSeconds} min={0} max={86400} />
              </FieldGroup>
              <div className="sm:col-span-2">
                <FieldGroup label="Description (optional)">
                  <input type="text" value={formDescription} onChange={(e) => setFormDescription(e.target.value)}
                    placeholder="Brief note about this policy..."
                    className="w-full px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-purple-500" />
                </FieldGroup>
              </div>
            </div>

            {/* Submit */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button type="button" onClick={resetForm}
                className="px-4 py-2 text-gray-400 hover:text-white text-sm transition-colors">
                Cancel
              </button>
              <button type="submit"
                disabled={createMutation.isPending || updateMutation.isPending || !formName}
                className="flex items-center gap-2 px-5 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors text-sm font-medium">
                <Save size={14} /> {editingRule ? 'Update Policy' : 'Create Policy'}
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

      {/* Policies Table (Desktop) */}
      <div className="hidden md:block overflow-x-auto rounded-xl border border-gray-700/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/50 text-gray-400 uppercase tracking-wider text-xs text-left">
              <th className="px-4 py-3">Policy</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Scope</th>
              <th className="px-4 py-3">Configuration</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Updated</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {isLoading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">Loading policies...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                {rules.length === 0
                  ? <span className="flex flex-col items-center gap-2">
                      <Shield className="text-gray-600" size={32} />
                      No alert policies configured yet.
                      <button onClick={() => seedMutation.mutate()}
                        className="mt-1 text-purple-400 hover:text-purple-300 text-xs underline">
                        Load default policies
                      </button>
                    </span>
                  : 'No policies match your filters.'}
              </td></tr>
            ) : filtered.map((r) => (
              <tr key={r.id} className={`hover:bg-gray-800/30 transition-colors ${!r.enabled ? 'opacity-50' : ''}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{r.name}</span>
                    {r.is_default && <DefaultBadge />}
                  </div>
                  {r.description && <p className="text-[10px] text-gray-600 mt-0.5">{r.description}</p>}
                </td>
                <td className="px-4 py-3"><RuleTypeBadge ruleType={r.rule_type} /></td>
                <td className="px-4 py-3 text-gray-300 text-xs">{r.service_name}</td>
                <td className="px-4 py-3 text-gray-400 text-xs font-mono">{policyDetail(r)}</td>
                <td className="px-4 py-3"><SeverityBadge severity={r.severity} /></td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleMutation.mutate({ id: r.id, enabled: !r.enabled })}
                    className={`flex items-center gap-1 text-xs font-medium ${r.enabled ? 'text-green-400' : 'text-gray-500'}`}
                  >
                    {r.enabled ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
                    {r.enabled ? 'On' : 'Off'}
                  </button>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{timeAgo(r.updated_at || r.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openEdit(r)} className="text-gray-400 hover:text-blue-400 transition-colors" title="Edit">
                      <Pencil size={14} />
                    </button>
                    <button
                      onClick={() => { if (confirm('Delete this policy?')) deleteMutation.mutate(r.id) }}
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

      {/* Mobile Policy Cards */}
      <div className="md:hidden space-y-3">
        {isLoading ? (
          <div className="text-center text-gray-500 py-8">Loading policies...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {rules.length === 0 ? (
              <div className="flex flex-col items-center gap-2">
                <Shield className="text-gray-600" size={32} />
                <span>No alert policies configured.</span>
                <button onClick={() => seedMutation.mutate()}
                  className="text-purple-400 hover:text-purple-300 text-xs underline">
                  Load defaults
                </button>
              </div>
            ) : 'No policies match filters.'}
          </div>
        ) : filtered.map((r) => {
          const cfg = ruleTypeConfig(r.rule_type)
          const Icon = cfg.icon
          const isExpanded = expandedCards.has(r.id)
          return (
            <div key={r.id} className={`bg-gradient-to-br ${cfg.gradient} rounded-xl border ${!r.enabled ? 'opacity-50 ' : ''}${cfg.border}`}>
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg ${cfg.iconBg}`}><Icon size={14} /></div>
                    <div>
                      <span className="text-white font-medium text-sm">{r.name}</span>
                      {r.is_default && <span className="ml-2"><DefaultBadge /></span>}
                    </div>
                  </div>
                  <SeverityBadge severity={r.severity} />
                </div>

                <p className="text-xs text-gray-400 font-mono mb-2">{policyDetail(r)}</p>
                <p className="text-[10px] text-gray-500 mb-3">{r.service_name} · Cooldown {r.cooldown_seconds}s</p>

                <div className="flex items-center justify-between">
                  <button
                    onClick={() => toggleMutation.mutate({ id: r.id, enabled: !r.enabled })}
                    className={`flex items-center gap-1 text-xs ${r.enabled ? 'text-green-400' : 'text-gray-500'}`}
                  >
                    {r.enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                    {r.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                  <div className="flex gap-3">
                    <button onClick={() => toggleExpand(r.id)} className="text-gray-400 hover:text-gray-300">
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    <button onClick={() => openEdit(r)} className="text-gray-400 hover:text-blue-400"><Pencil size={14} /></button>
                    <button onClick={() => { if (confirm('Delete?')) deleteMutation.mutate(r.id) }}
                      className="text-gray-400 hover:text-red-400"><Trash2 size={14} /></button>
                  </div>
                </div>
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="border-t border-gray-700/30 px-4 py-3 text-xs text-gray-400 grid grid-cols-2 gap-2">
                  {r.rule_type === 'SERVICE_DOWN' && <>
                    <span>Failures: <span className="text-gray-300">{r.consecutive_failures}</span></span>
                    <span>Escalation: <span className="text-gray-300">{r.critical_escalation_failures}</span></span>
                    <span>Incident: <span className="text-gray-300">{r.incident_after_seconds}s</span></span>
                  </>}
                  {r.rule_type === 'HIGH_LATENCY' && <>
                    <span>Threshold: <span className="text-gray-300">{r.latency_threshold_ms}ms</span></span>
                    <span>Sustained: <span className="text-gray-300">{r.sustained_checks} checks</span></span>
                  </>}
                  {r.rule_type === 'DEGRADED_HEALTH' && <>
                    <span>Anomaly: <span className="text-gray-300">≥{r.anomaly_score_threshold}</span></span>
                    <span>Sustained: <span className="text-gray-300">{r.sustained_checks} checks</span></span>
                  </>}
                  <span>Cooldown: <span className="text-gray-300">{r.cooldown_seconds}s</span></span>
                  <span>Updated: <span className="text-gray-300">{timeAgo(r.updated_at || r.created_at)}</span></span>
                  {r.description && <span className="col-span-2 text-gray-500 italic">{r.description}</span>}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
