/* eslint-disable */
import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import {
  Shield, Plus, Pencil, Trash2, ToggleLeft, ToggleRight,
  Search, Filter, X, Save, AlertTriangle, WifiOff,
  Clock, Activity, ChevronDown, ChevronUp, Settings2,
  RefreshCw, RotateCcw
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

/* ── Default values (must match backend seed exactly) ── */
const DEFAULTS: Record<string, {
  consecutive_failures: number
  critical_escalation_failures: number
  incident_after_seconds: number
  latency_threshold_ms: number
  anomaly_score_threshold: number
  sustained_checks: number
  severity: string
  cooldown_seconds: number
}> = {
  SERVICE_DOWN: {
    consecutive_failures: 3,
    critical_escalation_failures: 6,
    incident_after_seconds: 120,
    latency_threshold_ms: 1000,
    anomaly_score_threshold: 70,
    sustained_checks: 3,
    severity: 'warning',
    cooldown_seconds: 120,
  },
  HIGH_LATENCY: {
    consecutive_failures: 3,
    critical_escalation_failures: 6,
    incident_after_seconds: 300,
    latency_threshold_ms: 1000,
    anomaly_score_threshold: 70,
    sustained_checks: 3,
    severity: 'warning',
    cooldown_seconds: 120,
  },
  DEGRADED_HEALTH: {
    consecutive_failures: 3,
    critical_escalation_failures: 6,
    incident_after_seconds: 300,
    latency_threshold_ms: 1000,
    anomaly_score_threshold: 70,
    sustained_checks: 3,
    severity: 'warning',
    cooldown_seconds: 120,
  },
}

/** Check whether a policy's values differ from recommended defaults */
function isCustomConfig(r: AlertPolicyRow): boolean {
  const d = DEFAULTS[r.rule_type]
  if (!d) return true
  switch (r.rule_type) {
    case 'SERVICE_DOWN':
      return r.consecutive_failures !== d.consecutive_failures
        || r.critical_escalation_failures !== d.critical_escalation_failures
        || r.incident_after_seconds !== d.incident_after_seconds
        || r.cooldown_seconds !== d.cooldown_seconds
        || r.severity !== d.severity
    case 'HIGH_LATENCY':
      return (r.latency_threshold_ms ?? 1000) !== d.latency_threshold_ms
        || r.sustained_checks !== d.sustained_checks
        || r.cooldown_seconds !== d.cooldown_seconds
        || r.severity !== d.severity
    case 'DEGRADED_HEALTH':
      return (r.anomaly_score_threshold ?? 70) !== d.anomaly_score_threshold
        || r.sustained_checks !== d.sustained_checks
        || r.cooldown_seconds !== d.cooldown_seconds
        || r.severity !== d.severity
    default:
      return true
  }
}

const RULE_TYPES = [
  {
    value: 'SERVICE_DOWN',
    label: 'Service Down',
    icon: WifiOff,
    color: 'red',
    description: 'Detects when a service becomes unreachable',
    gradient: 'from-slate-50 to-white dark:from-red-500/10 dark:to-red-900/5',
    border: 'border-red-200 dark:border-red-500/30',
    iconBg: 'bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400',
  },
  {
    value: 'HIGH_LATENCY',
    label: 'High Latency',
    icon: Clock,
    color: 'amber',
    description: 'Detects when response time is too slow',
    gradient: 'from-slate-50 to-white dark:from-amber-500/10 dark:to-amber-900/5',
    border: 'border-amber-200 dark:border-amber-500/30',
    iconBg: 'bg-amber-50 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400',
  },
  {
    value: 'DEGRADED_HEALTH',
    label: 'Degraded Health',
    icon: Activity,
    color: 'purple',
    description: 'Detects AI-scored anomalies in service behavior',
    gradient: 'from-slate-50 to-white dark:from-purple-500/10 dark:to-purple-900/5',
    border: 'border-purple-200 dark:border-purple-500/30',
    iconBg: 'bg-purple-50 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400',
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

/* ── Validation ── */
interface FieldError { field: string; message: string }

function validateForm(
  name: string,
  ruleType: string,
  failures: number,
  escalation: number,
  incidentSec: number,
  latencyMs: number,
  anomalyScore: number,
  sustained: number,
  cooldown: number,
): FieldError[] {
  const errors: FieldError[] = []
  if (!name.trim()) errors.push({ field: 'name', message: 'Policy name is required' })
  if (failures < 1)        errors.push({ field: 'consecutive_failures', message: 'Must be at least 1' })
  if (failures > 100)      errors.push({ field: 'consecutive_failures', message: 'Maximum is 100' })
  if (escalation < 1)      errors.push({ field: 'critical_escalation', message: 'Must be at least 1' })
  if (escalation > 100)    errors.push({ field: 'critical_escalation', message: 'Maximum is 100' })
  if (ruleType === 'SERVICE_DOWN' && escalation <= failures) {
    errors.push({ field: 'critical_escalation', message: 'Must be greater than failures before alert' })
  }
  if (incidentSec < 0)     errors.push({ field: 'incident_after', message: 'Cannot be negative' })
  if (incidentSec > 86400) errors.push({ field: 'incident_after', message: 'Maximum is 86400 (24h)' })
  if (latencyMs < 1)       errors.push({ field: 'latency_threshold', message: 'Must be at least 1 ms' })
  if (latencyMs > 60000)   errors.push({ field: 'latency_threshold', message: 'Maximum is 60000 ms' })
  if (anomalyScore < 0)    errors.push({ field: 'anomaly_score', message: 'Must be 0–100' })
  if (anomalyScore > 100)  errors.push({ field: 'anomaly_score', message: 'Must be 0–100' })
  if (sustained < 1)       errors.push({ field: 'sustained_checks', message: 'Must be at least 1' })
  if (sustained > 100)     errors.push({ field: 'sustained_checks', message: 'Maximum is 100' })
  if (cooldown < 0)        errors.push({ field: 'cooldown', message: 'Cannot be negative' })
  if (cooldown > 3600)     errors.push({ field: 'cooldown', message: 'Maximum is 3600 (1 hour)' })
  return errors
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
function FieldGroup({ label, hint, error, children }: {
  label: string; hint?: string; error?: string; children: React.ReactNode
}) {
  return (
    <div>
      <label className="block text-xs text-slate-600 dark:text-gray-400 mb-1 font-medium">{label}</label>
      {children}
      {error
        ? <p className="text-[10px] text-red-400 mt-0.5">{error}</p>
        : hint ? <p className="text-[10px] text-slate-400 dark:text-gray-600 mt-0.5">{hint}</p> : null}
    </div>
  )
}

function NumberInput({ value, onChange, min, max, step, hasError }: {
  value: number; onChange: (v: number) => void; min?: number; max?: number; step?: number | string; hasError?: boolean
}) {
  return (
    <input
      type="number" value={value} min={min} max={max} step={step}
      onChange={(e) => onChange(Number(e.target.value))}
      className={`w-full px-3 py-2 bg-white dark:bg-gray-900/50 border rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500 ${hasError ? 'border-red-500/60' : 'border-slate-300 dark:border-gray-700'}`}
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
  const [formErrors, setFormErrors] = useState<FieldError[]>([])

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

  const fieldError = (field: string) => formErrors.find(e => e.field === field)?.message

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
    setFormErrors([])
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

  /** Reset current form fields to recommended defaults for the selected rule type */
  const resetToDefaults = () => {
    const d = DEFAULTS[formRuleType]
    if (!d) return
    setFormConsecutiveFailures(d.consecutive_failures)
    setFormCriticalEscalation(d.critical_escalation_failures)
    setFormIncidentAfterSeconds(d.incident_after_seconds)
    setFormLatencyThresholdMs(d.latency_threshold_ms)
    setFormAnomalyScoreThreshold(d.anomaly_score_threshold)
    setFormSustainedChecks(d.sustained_checks)
    setFormSeverity(d.severity)
    setFormCooldownSeconds(d.cooldown_seconds)
    setFormErrors([])
  }

  const openEdit = (r: AlertPolicyRow) => {
    setEditingRule(r)
    setFormErrors([])
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
    const errors = validateForm(
      formName, formRuleType,
      formConsecutiveFailures, formCriticalEscalation, formIncidentAfterSeconds,
      formLatencyThresholdMs, formAnomalyScoreThreshold, formSustainedChecks,
      formCooldownSeconds,
    )
    setFormErrors(errors)
    if (errors.length > 0) return

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

  /* ── Policy state label for overview cards ── */
  const policyStateLabel = (ruleType: string): string => {
    const typePolicies = rules.filter(r => r.rule_type === ruleType)
    if (typePolicies.length === 0) return 'Not configured'
    const enabledPolicies = typePolicies.filter(r => r.enabled)
    if (enabledPolicies.length === 0) return 'All disabled'
    const hasCustom = enabledPolicies.some(r => isCustomConfig(r))
    if (hasCustom) return 'Custom configuration'
    return 'Active — recommended settings'
  }

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

  /* ── Check if form has been modified from defaults (for reset button visibility) ── */
  const formDiffersFromDefaults = useMemo(() => {
    const d = DEFAULTS[formRuleType]
    if (!d) return false
    return formConsecutiveFailures !== d.consecutive_failures
      || formCriticalEscalation !== d.critical_escalation_failures
      || formIncidentAfterSeconds !== d.incident_after_seconds
      || formLatencyThresholdMs !== d.latency_threshold_ms
      || formAnomalyScoreThreshold !== d.anomaly_score_threshold
      || formSustainedChecks !== d.sustained_checks
      || formSeverity !== d.severity
      || formCooldownSeconds !== d.cooldown_seconds
  }, [formRuleType, formConsecutiveFailures, formCriticalEscalation, formIncidentAfterSeconds,
      formLatencyThresholdMs, formAnomalyScoreThreshold, formSustainedChecks, formSeverity, formCooldownSeconds])

  /* ════════════════════ EMPTY STATE ════════════════════ */
  if (!isLoading && rules.length === 0) {
    return (
      <div className="space-y-6">
        {/* Header — always visible */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Shield className="text-purple-400" size={28} />
            Alert Policies
          </h1>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Configure monitoring policies for your synthetic checks</p>
        </div>

        {/* Empty state card */}
        <div className="flex flex-col items-center justify-center py-20 px-6 bg-white dark:bg-gray-800/30 rounded-2xl border border-slate-200 dark:border-gray-700/40">
          <div className="p-4 rounded-2xl bg-purple-500/10 mb-5">
            <Shield className="text-purple-400" size={40} />
          </div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white mb-2">No alert policies configured</h2>
          <p className="text-sm text-slate-500 dark:text-gray-400 max-w-md text-center mb-6">
            Load recommended policies to start monitoring your services.
            Default policies detect outages, high latency, and health degradation automatically.
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
              className="flex items-center gap-2 px-5 py-2.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              <RefreshCw size={16} className={seedMutation.isPending ? 'animate-spin' : ''} />
              Load recommended policies
            </button>
            <button
              onClick={() => { resetForm(); setShowForm(true) }}
              className="flex items-center gap-2 px-5 py-2.5 bg-white dark:bg-gray-700/50 text-slate-700 dark:text-gray-300 rounded-lg hover:bg-slate-50 dark:hover:bg-gray-700 transition-colors text-sm border border-slate-200 dark:border-gray-600/50"
            >
              <Plus size={16} /> Create custom
            </button>
          </div>
          {seedMutation.isError && (
            <p className="mt-4 text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
              <AlertTriangle size={14} /> Failed to load policies. Please try again.
            </p>
          )}
        </div>

        {/* Show form even in empty state if user clicked "Create custom" */}
        {showForm && <PolicyForm
          editingRule={editingRule} formName={formName} formRuleType={formRuleType}
          formServiceId={formServiceId} formConsecutiveFailures={formConsecutiveFailures}
          formCriticalEscalation={formCriticalEscalation} formIncidentAfterSeconds={formIncidentAfterSeconds}
          formLatencyThresholdMs={formLatencyThresholdMs} formAnomalyScoreThreshold={formAnomalyScoreThreshold}
          formSustainedChecks={formSustainedChecks} formSeverity={formSeverity}
          formCooldownSeconds={formCooldownSeconds} formDescription={formDescription}
          formErrors={formErrors} fieldError={fieldError} services={services}
          formDiffersFromDefaults={formDiffersFromDefaults}
          createMutation={createMutation} updateMutation={updateMutation}
          setFormName={setFormName} setFormRuleType={setFormRuleType}
          setFormServiceId={setFormServiceId} setFormConsecutiveFailures={setFormConsecutiveFailures}
          setFormCriticalEscalation={setFormCriticalEscalation} setFormIncidentAfterSeconds={setFormIncidentAfterSeconds}
          setFormLatencyThresholdMs={setFormLatencyThresholdMs} setFormAnomalyScoreThreshold={setFormAnomalyScoreThreshold}
          setFormSustainedChecks={setFormSustainedChecks} setFormSeverity={setFormSeverity}
          setFormCooldownSeconds={setFormCooldownSeconds} setFormDescription={setFormDescription}
          handleSubmit={handleSubmit} resetForm={resetForm} resetToDefaults={resetToDefaults}
        />}
      </div>
    )
  }

  /* ════════════════════ MAIN RENDER ════════════════════ */
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Shield className="text-purple-400" size={28} />
            Alert Policies
          </h1>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Configure monitoring policies for your synthetic checks</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-500/30 transition-colors border border-purple-200 dark:border-purple-500/30"
        >
          <Plus size={16} /> New Policy
        </button>
      </div>

      {/* Policy Type Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {RULE_TYPES.map((rt) => {
          const Icon = rt.icon
          const count = rules.filter((r) => r.rule_type === rt.value).length
          const stateLabel = policyStateLabel(rt.value)
          const isActive = stateLabel.startsWith('Active')
          const isCustom = stateLabel === 'Custom configuration'
          return (
            <div
              key={rt.value}
              onClick={() => setFilterType(filterType === rt.value ? 'all' : rt.value)}
              className={`bg-gradient-to-br ${rt.gradient} rounded-xl p-4 border cursor-pointer transition-all hover:scale-[1.02]
                ${filterType === rt.value ? rt.border + ' ring-2 ring-offset-1 ring-' + rt.color + '-300 dark:ring-' + rt.color + '-500/20' : 'border-slate-200 dark:border-gray-700/50'}`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg ${rt.iconBg}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-white">{rt.label}</p>
                  <p className="text-[10px] text-slate-500 dark:text-gray-500">{rt.description}</p>
                </div>
              </div>
              <div className="flex items-baseline gap-3 mt-3">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">{count}</span>
                <span className={`text-[11px] ${isActive ? 'text-green-600 dark:text-green-400' : isCustom ? 'text-amber-600 dark:text-amber-400' : 'text-slate-500 dark:text-gray-500'}`}>
                  {stateLabel}
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
            className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800/50 border border-slate-300 dark:border-gray-700 rounded-lg text-sm text-slate-700 dark:text-gray-300 focus:outline-none focus:border-purple-500"
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
                  ? 'bg-purple-50 dark:bg-purple-500/20 text-purple-700 dark:text-purple-400 border border-purple-300 dark:border-purple-500/30'
                  : 'bg-white dark:bg-gray-800/50 text-slate-500 dark:text-gray-400 border border-slate-200 dark:border-gray-700/50 hover:text-slate-700 dark:hover:text-gray-300'
              }`}
            >
              {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Create/Edit Policy Form */}
      {showForm && <PolicyForm
        editingRule={editingRule} formName={formName} formRuleType={formRuleType}
        formServiceId={formServiceId} formConsecutiveFailures={formConsecutiveFailures}
        formCriticalEscalation={formCriticalEscalation} formIncidentAfterSeconds={formIncidentAfterSeconds}
        formLatencyThresholdMs={formLatencyThresholdMs} formAnomalyScoreThreshold={formAnomalyScoreThreshold}
        formSustainedChecks={formSustainedChecks} formSeverity={formSeverity}
        formCooldownSeconds={formCooldownSeconds} formDescription={formDescription}
        formErrors={formErrors} fieldError={fieldError} services={services}
        formDiffersFromDefaults={formDiffersFromDefaults}
        createMutation={createMutation} updateMutation={updateMutation}
        setFormName={setFormName} setFormRuleType={setFormRuleType}
        setFormServiceId={setFormServiceId} setFormConsecutiveFailures={setFormConsecutiveFailures}
        setFormCriticalEscalation={setFormCriticalEscalation} setFormIncidentAfterSeconds={setFormIncidentAfterSeconds}
        setFormLatencyThresholdMs={setFormLatencyThresholdMs} setFormAnomalyScoreThreshold={setFormAnomalyScoreThreshold}
        setFormSustainedChecks={setFormSustainedChecks} setFormSeverity={setFormSeverity}
        setFormCooldownSeconds={setFormCooldownSeconds} setFormDescription={setFormDescription}
        handleSubmit={handleSubmit} resetForm={resetForm} resetToDefaults={resetToDefaults}
      />}

      {/* Policies Table (Desktop) */}
      <div className="hidden md:block overflow-x-auto rounded-xl border border-slate-200 dark:border-gray-700/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 dark:bg-gray-800/50 text-slate-500 dark:text-gray-400 uppercase tracking-wider text-xs text-left">
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
          <tbody className="divide-y divide-slate-100 dark:divide-gray-700/30">
            {isLoading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-400 dark:text-gray-500">Loading policies...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-400 dark:text-gray-500">
                No policies match your filters.
              </td></tr>
            ) : filtered.map((r) => {
              const custom = isCustomConfig(r)
              return (
              <tr key={r.id} className={`hover:bg-slate-50 dark:hover:bg-gray-800/30 border-b border-slate-100 dark:border-gray-800/50 transition-colors ${!r.enabled ? 'opacity-50' : ''}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-800 dark:text-white font-medium">{r.name}</span>
                    {r.is_default && <DefaultBadge />}
                  </div>
                  {r.description && <p className="text-[10px] text-slate-500 dark:text-gray-600 mt-0.5">{r.description}</p>}
                  {custom && <p className="text-[10px] text-amber-600 dark:text-amber-500/70 mt-0.5">Custom configuration</p>}
                </td>
                <td className="px-4 py-3"><RuleTypeBadge ruleType={r.rule_type} /></td>
                <td className="px-4 py-3 text-slate-600 dark:text-gray-300 text-xs">{r.service_name}</td>
                <td className="px-4 py-3 text-slate-500 dark:text-gray-400 text-xs font-mono">{policyDetail(r)}</td>
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
                <td className="px-4 py-3 text-slate-400 dark:text-gray-500 text-xs">{timeAgo(r.updated_at || r.created_at)}</td>
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
            )})}
          </tbody>
        </table>
      </div>

      {/* Mobile Policy Cards */}
      <div className="md:hidden space-y-3">
        {isLoading ? (
          <div className="text-center text-gray-500 py-8">Loading policies...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No policies match filters.</div>
        ) : filtered.map((r) => {
          const cfg = ruleTypeConfig(r.rule_type)
          const Icon = cfg.icon
          const isExpanded = expandedCards.has(r.id)
          const custom = isCustomConfig(r)
          return (
            <div key={r.id} className={`bg-gradient-to-br ${cfg.gradient} rounded-xl border ${!r.enabled ? 'opacity-50 ' : ''}${cfg.border}`}>
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg ${cfg.iconBg}`}><Icon size={14} /></div>
                    <div>
                      <span className="text-slate-800 dark:text-white font-medium text-sm">{r.name}</span>
                      {r.is_default && <span className="ml-2"><DefaultBadge /></span>}
                    </div>
                  </div>
                  <SeverityBadge severity={r.severity} />
                </div>

                <p className="text-xs text-gray-400 font-mono mb-1">{policyDetail(r)}</p>
                <p className="text-[10px] text-gray-500 mb-3">
                  {r.service_name} · Cooldown {r.cooldown_seconds}s
                  {custom && <span className="text-amber-500/70 ml-1">· Custom</span>}
                </p>

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
                <div className="border-t border-slate-200 dark:border-gray-700/30 px-4 py-3 text-xs text-slate-500 dark:text-gray-400 grid grid-cols-2 gap-2">
                  {r.rule_type === 'SERVICE_DOWN' && <>
                    <span>Failures before alert: <span className="text-gray-300">{r.consecutive_failures}</span></span>
                    <span>Before critical: <span className="text-gray-300">{r.critical_escalation_failures}</span></span>
                    <span>Incident after: <span className="text-gray-300">{r.incident_after_seconds}s</span></span>
                  </>}
                  {r.rule_type === 'HIGH_LATENCY' && <>
                    <span>Threshold: <span className="text-gray-300">{r.latency_threshold_ms}ms</span></span>
                    <span>Checks before alert: <span className="text-gray-300">{r.sustained_checks}</span></span>
                  </>}
                  {r.rule_type === 'DEGRADED_HEALTH' && <>
                    <span>Anomaly score: <span className="text-gray-300">≥{r.anomaly_score_threshold}</span></span>
                    <span>Checks before alert: <span className="text-gray-300">{r.sustained_checks}</span></span>
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


/* ════════════════════════════════════════════════════════════════
   Policy Form — extracted as a component to avoid duplication
   between the empty-state view and the main view.
   ════════════════════════════════════════════════════════════════ */

function PolicyForm({
  editingRule, formName, formRuleType, formServiceId,
  formConsecutiveFailures, formCriticalEscalation, formIncidentAfterSeconds,
  formLatencyThresholdMs, formAnomalyScoreThreshold, formSustainedChecks,
  formSeverity, formCooldownSeconds, formDescription,
  formErrors, fieldError, services, formDiffersFromDefaults,
  createMutation, updateMutation,
  setFormName, setFormRuleType, setFormServiceId,
  setFormConsecutiveFailures, setFormCriticalEscalation, setFormIncidentAfterSeconds,
  setFormLatencyThresholdMs, setFormAnomalyScoreThreshold, setFormSustainedChecks,
  setFormSeverity, setFormCooldownSeconds, setFormDescription,
  handleSubmit, resetForm, resetToDefaults,
}: any) {
  return (
    <div className="bg-white dark:bg-gray-800/80 rounded-xl p-6 border border-purple-200 dark:border-purple-500/30 shadow-sm">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2">
          <Settings2 size={18} className="text-purple-400" />
          {editingRule ? 'Edit Policy' : 'Create New Policy'}
        </h2>
        <div className="flex items-center gap-2">
          {formDiffersFromDefaults && (
            <button type="button" onClick={resetToDefaults}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors border border-slate-200 dark:border-gray-700 rounded-lg hover:border-purple-400 dark:hover:border-purple-500/30"
              title="Restore recommended default values for this rule type"
            >
              <RotateCcw size={12} /> Reset to recommended
            </button>
          )}
          <button onClick={resetForm} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Row 1: Identity */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-1">
            <FieldGroup label="Policy Name" error={fieldError('name')}>
              <input type="text" value={formName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormName(e.target.value)} required
                placeholder="e.g., Service Down — API"
                className={`w-full px-3 py-2 bg-white dark:bg-gray-900/50 border rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500 ${fieldError('name') ? 'border-red-500/60' : 'border-slate-300 dark:border-gray-700'}`} />
            </FieldGroup>
          </div>
          <div>
            <FieldGroup label="Rule Type">
              <select value={formRuleType} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormRuleType(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-gray-900/50 border border-slate-300 dark:border-gray-700 rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500">
                {RULE_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </FieldGroup>
          </div>
          <div>
            <FieldGroup label="Scope" hint="Leave empty to apply to all services">
              <select value={formServiceId ?? ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormServiceId(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 bg-white dark:bg-gray-900/50 border border-slate-300 dark:border-gray-700 rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500">
                <option value="">All Services (global)</option>
                {services.map((s: ServiceOption) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </FieldGroup>
          </div>
        </div>

        {/* Row 2: Rule-type specific thresholds */}
        <div className={`rounded-lg p-4 border ${ruleTypeConfig(formRuleType).border} bg-gradient-to-br ${ruleTypeConfig(formRuleType).gradient}`}>
          <div className="flex items-center gap-2 mb-3">
            {(() => { const Icon = ruleTypeConfig(formRuleType).icon; return <Icon size={14} className="text-gray-400" /> })()}
            <span className="text-xs font-semibold text-slate-600 dark:text-gray-300 uppercase tracking-wider">
              {ruleTypeConfig(formRuleType).label} Configuration
            </span>
          </div>

          {formRuleType === 'SERVICE_DOWN' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FieldGroup label="Failures before alert" hint="Avoid alerts from temporary failures" error={fieldError('consecutive_failures')}>
                <NumberInput value={formConsecutiveFailures} onChange={setFormConsecutiveFailures} min={1} max={100} hasError={!!fieldError('consecutive_failures')} />
              </FieldGroup>
              <FieldGroup label="Failures before critical" hint="Escalates severity if the issue persists" error={fieldError('critical_escalation')}>
                <NumberInput value={formCriticalEscalation} onChange={setFormCriticalEscalation} min={1} max={100} hasError={!!fieldError('critical_escalation')} />
              </FieldGroup>
              <FieldGroup label="Create incident after (seconds)" hint="Creates an incident if downtime continues" error={fieldError('incident_after')}>
                <NumberInput value={formIncidentAfterSeconds} onChange={setFormIncidentAfterSeconds} min={0} max={86400} hasError={!!fieldError('incident_after')} />
              </FieldGroup>
            </div>
          )}

          {formRuleType === 'HIGH_LATENCY' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FieldGroup label="Latency threshold (ms)" hint="Maximum acceptable response time" error={fieldError('latency_threshold')}>
                <NumberInput value={formLatencyThresholdMs} onChange={setFormLatencyThresholdMs} min={1} max={60000} hasError={!!fieldError('latency_threshold')} />
              </FieldGroup>
              <FieldGroup label="Checks before alert" hint="Only alert if the issue persists across multiple checks" error={fieldError('sustained_checks')}>
                <NumberInput value={formSustainedChecks} onChange={setFormSustainedChecks} min={1} max={100} hasError={!!fieldError('sustained_checks')} />
              </FieldGroup>
            </div>
          )}

          {formRuleType === 'DEGRADED_HEALTH' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FieldGroup label="Anomaly score threshold" hint="Score 0–100, higher means more anomalous" error={fieldError('anomaly_score')}>
                <NumberInput value={formAnomalyScoreThreshold} onChange={setFormAnomalyScoreThreshold} min={0} max={100} hasError={!!fieldError('anomaly_score')} />
              </FieldGroup>
              <FieldGroup label="Checks before alert" hint="Only alert if the issue persists across multiple checks" error={fieldError('sustained_checks')}>
                <NumberInput value={formSustainedChecks} onChange={setFormSustainedChecks} min={1} max={100} hasError={!!fieldError('sustained_checks')} />
              </FieldGroup>
            </div>
          )}
        </div>

        {/* Row 3: Common controls */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <FieldGroup label="Severity" hint="Initial severity when the alert fires">
            <select value={formSeverity} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormSeverity(e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-gray-900/50 border border-slate-300 dark:border-gray-700 rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500">
              {SEVERITIES.map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
            </select>
          </FieldGroup>
          <FieldGroup label="Cooldown (seconds)" hint="Prevents repeated alerts for the same issue" error={fieldError('cooldown')}>
            <NumberInput value={formCooldownSeconds} onChange={setFormCooldownSeconds} min={0} max={3600} hasError={!!fieldError('cooldown')} />
          </FieldGroup>
          <div className="sm:col-span-2">
            <FieldGroup label="Description (optional)" hint="Internal note for your team">
              <input type="text" value={formDescription} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormDescription(e.target.value)}
                placeholder="Brief note about this policy..."
                className="w-full px-3 py-2 bg-white dark:bg-gray-900/50 border border-slate-300 dark:border-gray-700 rounded-lg text-sm text-slate-800 dark:text-gray-200 focus:outline-none focus:border-purple-500" />
            </FieldGroup>
          </div>
        </div>

        {/* Validation summary */}
        {formErrors.length > 0 && (
          <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <AlertTriangle size={14} className="text-red-400 mt-0.5 shrink-0" />
            <p className="text-xs text-red-600 dark:text-red-400">
              Please fix {formErrors.length} {formErrors.length === 1 ? 'issue' : 'issues'} before saving.
            </p>
          </div>
        )}

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button type="button" onClick={resetForm}
            className="px-4 py-2 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white text-sm transition-colors">
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
        <p className="mt-3 text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
          <AlertTriangle size={14} />
          {(createMutation.error || updateMutation.error)?.message || 'Operation failed'}
        </p>
      )}
    </div>
  )
}
