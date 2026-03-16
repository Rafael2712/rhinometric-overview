import { useEffect, useState, useCallback } from 'react'
import {
  Server, AlertCircle, CheckCircle, Activity, Globe, Database, 
  Network, Plus, Trash2, Play, Power, PowerOff, Edit, ArrowLeft,
  RefreshCw, Clock, Lock, Search, Tag, X
} from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

/* ─── Types ──────────────────────────────────────────────────── */

interface ExternalServiceData {
  id: number
  name: string
  service_type: 'http' | 'postgresql'
  environment: string | null
  description: string | null
  catalog_type: string | null
  category: string | null
  tags: string[]
  enabled: boolean
  config: Record<string, any>
  timeout_seconds: number
  check_interval_seconds: number
  status: 'unknown' | 'up' | 'down' | 'degraded' | 'error'
  status_message: string | null
  last_check_at: string | null
  last_response_time_ms: number | null
  last_status_code: number | null
  created_by: number | null
  created_at: string | null
  updated_at: string | null
}

interface PlatformService {
  name: string; instance: string; status: 'up' | 'down'
  tier: string; service_type: string; version: string
  is_platform: boolean; service_category: string
  labels: Record<string, string>
}
interface PlatformGroup { services: PlatformService[]; total: number; up: number; down: number }
interface PlatformData {
  services: PlatformService[]; total: number; up: number; down: number
  platform: PlatformGroup; external: PlatformGroup; timestamp: string
}

interface ExtSummary { total: number; enabled: number; up: number; down: number; degraded: number; unknown: number }

type Tab = 'external' | 'platform'
type View = 'list' | 'create' | 'edit'

/* ─── Helpers ────────────────────────────────────────────────── */

const STATUS_BADGE: Record<string, { bg: string; text: string; Icon: any }> = {
  up:       { bg: 'bg-green-400/10', text: 'text-green-400', Icon: CheckCircle },
  down:     { bg: 'bg-red-400/10',   text: 'text-red-400',   Icon: AlertCircle },
  degraded: { bg: 'bg-yellow-400/10',text: 'text-yellow-400', Icon: AlertCircle },
  error:    { bg: 'bg-red-400/10',   text: 'text-red-400',   Icon: AlertCircle },
  unknown:  { bg: 'bg-gray-400/10',  text: 'text-gray-400',  Icon: Clock },
}

const TYPE_META: Record<string, { label: string; color: string; Icon: any }> = {
  http:       { label: 'HTTP / HTTPS', color: 'bg-violet-400/10 text-violet-400', Icon: Network },
  postgresql: { label: 'PostgreSQL',   color: 'bg-orange-400/10 text-orange-400', Icon: Database },
}

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_BADGE[status] || STATUS_BADGE.unknown
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      <s.Icon className="w-3 h-3" /> {status.toUpperCase()}
    </span>
  )
}

function TypeBadge({ type }: { type: string }) {
  const t = TYPE_META[type] || TYPE_META.http
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${t.color}`}>
      <t.Icon className="w-3 h-3" /> {t.label}
    </span>
  )
}

function targetDisplay(svc: ExternalServiceData): string {
  if (svc.service_type === 'http') return svc.config?.url || '-'
  if (svc.service_type === 'postgresql') {
    const h = svc.config?.host || 'localhost'
    const p = svc.config?.port || 5432
    const d = svc.config?.database_name || ''
    return `${h}:${p}/${d}`
  }
  return '-'
}

/* ─── HTTP Form ──────────────────────────────────────────────── */

function HttpForm({ config, onChange }: { config: Record<string,any>; onChange: (c: Record<string,any>) => void }) {
  const set = (k: string, v: any) => onChange({ ...config, [k]: v })
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Endpoint URL *</label>
        <input type="url" value={config.url || ''} onChange={e => set('url', e.target.value)}
          placeholder="https://api.example.com" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Health Path</label>
          <input type="text" value={config.health_path || ''} onChange={e => set('health_path', e.target.value)}
            placeholder="/health" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Method</label>
          <select value={config.method || 'GET'} onChange={e => set('method', e.target.value)}
            className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            <option value="GET">GET</option><option value="POST">POST</option><option value="HEAD">HEAD</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Auth Type</label>
          <select value={config.auth_type || ''} onChange={e => set('auth_type', e.target.value)}
            className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            <option value="">None</option><option value="bearer">Bearer Token</option><option value="api_key">API Key</option><option value="basic">Basic Auth</option>
          </select>
        </div>
        {config.auth_type && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Auth Value</label>
            <input type="password" value={config.auth_value || ''} onChange={e => set('auth_value', e.target.value)}
              placeholder="Token or key" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
        )}
      </div>
    </div>
  )
}

/* ─── PostgreSQL Form ────────────────────────────────────────── */

function PgForm({ config, onChange }: { config: Record<string,any>; onChange: (c: Record<string,any>) => void }) {
  const set = (k: string, v: any) => onChange({ ...config, [k]: v })
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-1">Host *</label>
          <input type="text" value={config.host || ''} onChange={e => set('host', e.target.value)}
            placeholder="db.example.com" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Port</label>
          <input type="number" value={config.port || 5432} onChange={e => set('port', parseInt(e.target.value) || 5432)}
            className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Database Name *</label>
        <input type="text" value={config.database_name || ''} onChange={e => set('database_name', e.target.value)}
          placeholder="mydb" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Username *</label>
          <input type="text" value={config.username || ''} onChange={e => set('username', e.target.value)}
            placeholder="postgres" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Password *</label>
          <input type="password" value={config.password || ''} onChange={e => set('password', e.target.value)}
            placeholder="password" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">SSL Mode</label>
        <select value={config.ssl_mode || 'prefer'} onChange={e => set('ssl_mode', e.target.value)}
          className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
          <option value="disable">Disable</option><option value="prefer">Prefer</option><option value="require">Require</option>
        </select>
      </div>
    </div>
  )
}
const CATALOG_TYPE_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'REST_API', label: 'REST API' },
  { value: 'SOAP_API', label: 'SOAP API' },
  { value: 'WEB_APP', label: 'Web Application' },
  { value: 'MOBILE_API', label: 'Mobile API' },
  { value: 'DATABASE', label: 'Database' },
  { value: 'INTERNAL_SERVICE', label: 'Internal Service' },
  { value: 'EXTERNAL_SERVICE', label: 'External Service' },
  { value: 'OTHER', label: 'Other' },
]

/* ─── Main Component ─────────────────────────────────────────── */

export default function Services() {
  const { token, isAdmin } = useAuthStore()
  const [activeTab, setActiveTab] = useState<Tab>('external')
  const [view, setView] = useState<View>('list')
  const [extServices, setExtServices] = useState<ExternalServiceData[]>([])
  const [extSummary, setExtSummary] = useState<ExtSummary>({ total:0, enabled:0, up:0, down:0, degraded:0, unknown:0 })
  const [platformData, setPlatformData] = useState<PlatformData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Form state
  const [formType, setFormType] = useState<'http' | 'postgresql'>('http')
  const [formName, setFormName] = useState('')
  const [formEnv, setFormEnv] = useState('')
  const [formDesc, setFormDesc] = useState('')
  const [formConfig, setFormConfig] = useState<Record<string,any>>({})
  const [formTimeout, setFormTimeout] = useState(10)
  const [formInterval, setFormInterval] = useState(60)
  const [editId, setEditId] = useState<number | null>(null)

  // Catalog metadata form state
  const [formCatalogType, setFormCatalogType] = useState('')
  const [formCategory, setFormCategory] = useState('')
  const [formTags, setFormTags] = useState<string[]>([])
  const [formTagInput, setFormTagInput] = useState('')

  // Test connection state
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  // Catalog filter state
  const [filterSearch, setFilterSearch] = useState('')
  const [filterCatalogType, setFilterCatalogType] = useState('')
  const [filterCategory, setFilterCategory] = useState('')

  const apiHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
  const canManage = isAdmin()  // Only ADMIN/OWNER can create/edit/delete/toggle

  const fetchExternal = useCallback(async () => {
    try {
      const [listRes, sumRes] = await Promise.all([
        fetch('/api/external-services', { headers: apiHeaders }),
        fetch('/api/external-services/summary', { headers: apiHeaders }),
      ])
      if (listRes.ok) setExtServices(await listRes.json())
      if (sumRes.ok) setExtSummary(await sumRes.json())
    } catch (e) { console.error('ext fetch error', e) }
  }, [token])

  const fetchPlatform = useCallback(async () => {
    try {
      const res = await fetch('/api/kpis/services', { headers: apiHeaders })
      if (res.ok) setPlatformData(await res.json())
    } catch (e) { console.error('platform fetch error', e) }
  }, [token])

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      await Promise.all([fetchExternal(), fetchPlatform()])
      setIsLoading(false)
    }
    load()
    const iv = setInterval(() => { fetchExternal(); fetchPlatform() }, 30000)
    return () => clearInterval(iv)
  }, [fetchExternal, fetchPlatform])

  // ── Form actions ───────────────────────────────────────────────
  const resetForm = () => {
    setFormType('http'); setFormName(''); setFormEnv(''); setFormDesc('')
    setFormConfig({}); setFormTimeout(10); setFormInterval(60)
    setEditId(null); setTestResult(null)
    setFormCatalogType(''); setFormCategory(''); setFormTags([]); setFormTagInput('')
  }

  const openCreate = () => { resetForm(); setView('create') }

  const openEdit = (svc: ExternalServiceData) => {
    setEditId(svc.id); setFormType(svc.service_type); setFormName(svc.name)
    setFormEnv(svc.environment || ''); setFormDesc(svc.description || '')
    setFormConfig(svc.config || {}); setFormTimeout(svc.timeout_seconds)
    setFormInterval(svc.check_interval_seconds); setTestResult(null)
    setFormCatalogType(svc.catalog_type || ''); setFormCategory(svc.category || '')
    setFormTags(svc.tags && Array.isArray(svc.tags) ? svc.tags : []); setFormTagInput('')
    setView('edit')
  }

  const handleTestConnection = async () => {
    setTesting(true); setTestResult(null)
    try {
      const res = await fetch('/api/external-services/test-connection', {
        method: 'POST', headers: apiHeaders,
        body: JSON.stringify({ service_type: formType, config: formConfig, timeout_seconds: formTimeout }),
      })
      if (!res.ok) {
        // API returned 422 (validation) or other error — build a friendly result
        const err = await res.json().catch(() => ({}))
        const detail = err.detail
        const msg = typeof detail === 'string'
          ? detail
          : detail?.error
            ? `${detail.error}${detail.details?.length ? ': ' + detail.details.join(', ') : ''}`
            : `Server returned HTTP ${res.status}`
        setTestResult({ success: false, status: 'error', message: msg, status_code: null })
      } else {
        setTestResult(await res.json())
      }
    } catch (e: any) { setTestResult({ success: false, status: 'error', message: e.message, status_code: null }) }
    setTesting(false)
  }

  const handleSave = async () => {
    const body = {
      name: formName, service_type: formType, environment: formEnv || null,
      description: formDesc || null, config: formConfig,
      timeout_seconds: formTimeout, check_interval_seconds: formInterval, enabled: true,
      catalog_type: formCatalogType || null, category: formCategory || null,
      tags: formTags.length > 0 ? formTags : null,
    }
    try {
      const url = editId ? `/api/external-services/${editId}` : '/api/external-services'
      const method = editId ? 'PUT' : 'POST'
      const res = await fetch(url, { method, headers: apiHeaders, body: JSON.stringify(body) })
      if (!res.ok) { const d = await res.json(); alert(d.detail || 'Save failed'); return }
      await fetchExternal()
      setView('list'); resetForm()
    } catch (e: any) { alert(e.message) }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this service?')) return
    setActionLoading(id)
    await fetch(`/api/external-services/${id}`, { method: 'DELETE', headers: apiHeaders })
    await fetchExternal()
    setActionLoading(null)
  }

  const handleToggle = async (id: number) => {
    setActionLoading(id)
    await fetch(`/api/external-services/${id}/toggle`, { method: 'POST', headers: apiHeaders })
    await fetchExternal()
    setActionLoading(null)
  }

  const handleTestSaved = async (id: number) => {
    setActionLoading(id)
    await fetch(`/api/external-services/${id}/test`, { method: 'POST', headers: apiHeaders })
    await fetchExternal()
    setActionLoading(null)
  }

  // ── Loading ────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Services</h1>
        <div className="flex items-center justify-center h-64">
          <Activity className="w-8 h-8 text-blue-400 animate-spin" />
        </div>
      </div>
    )
  }

  // Catalog metadata: unique values for filter dropdowns
  const catalogTypes = [...new Set(extServices.map(s => s.catalog_type).filter(Boolean))] as string[]
  const categories = [...new Set(extServices.map(s => s.category).filter(Boolean))] as string[]
  const hasActiveFilters = !!(filterSearch || filterCatalogType || filterCategory)

  // Client-side filtering
  const filteredServices = extServices.filter(svc => {
    if (filterSearch && !svc.name.toLowerCase().includes(filterSearch.toLowerCase())) return false
    if (filterCatalogType && svc.catalog_type !== filterCatalogType) return false
    if (filterCategory && svc.category !== filterCategory) return false
    return true
  })

  const clearFilters = () => { setFilterSearch(''); setFilterCatalogType(''); setFilterCategory('') }

  const platform = platformData?.platform ?? { services: [], total: 0, up: 0, down: 0 }

  // ── Create/Edit Form View ──────────────────────────────────────
  if (view === 'create' || view === 'edit') {
    const isValid = formName.trim() && (
      formType === 'http' ? !!formConfig.url :
      formType === 'postgresql' ? !!(formConfig.host && formConfig.database_name && formConfig.username) : false
    )
    return (
      <div className="space-y-6 max-w-3xl">
        <div className="flex items-center gap-3">
          <button onClick={() => { setView('list'); resetForm() }} className="p-2 rounded-lg hover:bg-gray-700/50 text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-white">
            {view === 'edit' ? 'Edit Service' : 'Connect External Service'}
          </h1>
        </div>

        {/* Read-only banner for non-admin users */}
        {!canManage && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
            <Lock className="w-5 h-5 text-yellow-400 flex-shrink-0" />
            <p className="text-yellow-300 text-sm">
              <span className="font-medium">View-only mode.</span> You can explore the configuration but only administrators can create or modify services.
            </p>
          </div>
        )}

        {/* Type selector (only on create) */}
        {view === 'create' && (
          <div className="grid grid-cols-2 gap-4">
            {(['http', 'postgresql'] as const).map(t => (
              <button key={t} onClick={() => { setFormType(t); setFormConfig({}) }}
                className={`p-4 rounded-lg border-2 transition-all ${formType === t ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
                <div className="flex items-center gap-3">
                  {t === 'http' ? <Network className="w-8 h-8 text-violet-400" /> : <Database className="w-8 h-8 text-orange-400" />}
                  <div className="text-left">
                    <p className="text-white font-semibold">{t === 'http' ? 'HTTP / HTTPS API' : 'PostgreSQL'}</p>
                    <p className="text-gray-400 text-sm">{t === 'http' ? 'Monitor REST APIs, websites, webhooks' : 'Monitor PostgreSQL databases'}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Common fields */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white mb-2">General</h2>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Service Name *</label>
            <input type="text" value={formName} onChange={e => setFormName(e.target.value)}
              placeholder="My API Service" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Environment</label>
              <input type="text" value={formEnv} onChange={e => setFormEnv(e.target.value)}
                placeholder="production" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Timeout (s)</label>
              <input type="number" value={formTimeout} onChange={e => setFormTimeout(parseInt(e.target.value) || 10)}
                min={1} max={120} className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea value={formDesc} onChange={e => setFormDesc(e.target.value)} rows={2}
              placeholder="Optional description" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
        </div>

        {/* Classification (catalog metadata) */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white mb-2">Classification</h2>
          <p className="text-gray-500 text-xs -mt-1">Optional metadata for organizing and filtering services.</p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Catalog Type</label>
              <select value={formCatalogType} onChange={e => setFormCatalogType(e.target.value)}
                className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
                {CATALOG_TYPE_OPTIONS.map((o: { value: string; label: string }) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
              <input type="text" value={formCategory} onChange={e => setFormCategory(e.target.value)}
                placeholder="e.g. payments, auth, infrastructure"
                className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Tags</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {formTags.map((tag, i) => (
                <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-400/10 text-blue-400 border border-blue-400/20">
                  {tag}
                  <button type="button" onClick={() => setFormTags(formTags.filter((_: string, j: number) => j !== i))}
                    className="ml-0.5 hover:text-red-400 transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input type="text" value={formTagInput} onChange={e => setFormTagInput(e.target.value)}
                onKeyDown={e => {
                  if ((e.key === 'Enter' || e.key === ',') && formTagInput.trim()) {
                    e.preventDefault()
                    const newTag = formTagInput.trim().toLowerCase().replace(/,/g, '')
                    if (newTag && !formTags.includes(newTag)) setFormTags([...formTags, newTag])
                    setFormTagInput('')
                  }
                }}
                placeholder="Type a tag and press Enter"
                className="flex-1 bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
              <button type="button" onClick={() => {
                  const newTag = formTagInput.trim().toLowerCase().replace(/,/g, '')
                  if (newTag && !formTags.includes(newTag)) setFormTags([...formTags, newTag])
                  setFormTagInput('')
                }}
                disabled={!formTagInput.trim()}
                className="px-3 py-2 rounded-lg text-sm bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                Add
              </button>
            </div>
            <p className="text-gray-600 text-xs mt-1.5">Press Enter or comma to add. Click ?? to remove.</p>
          </div>
        </div>

        {/* Type-specific fields */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            {formType === 'http' ? 'HTTP Connection' : 'PostgreSQL Connection'}
          </h2>
          {formType === 'http' ? <HttpForm config={formConfig} onChange={setFormConfig} /> : <PgForm config={formConfig} onChange={setFormConfig} />}
        </div>

        {/* Test Connection Result */}
        {testResult && (() => {
          const isSuccess = testResult.success === true;
          const isHttpError = !isSuccess && testResult.status_code != null;
          const borderClass = isSuccess
            ? 'border-green-500/50 bg-green-500/10'
            : isHttpError
              ? 'border-amber-500/50 bg-amber-500/10'
              : 'border-red-500/50 bg-red-500/10';
          const iconColor = isSuccess ? 'text-green-400' : isHttpError ? 'text-amber-400' : 'text-red-400';
          const label = isSuccess
            ? 'Connection successful'
            : 'Connection test failed';
          return (
            <div className={`rounded-lg border p-4 ${borderClass}`}>
              <div className="flex items-center gap-2">
                {isSuccess ? <CheckCircle className={`w-5 h-5 ${iconColor}`} /> : <AlertCircle className={`w-5 h-5 ${iconColor}`} />}
                <span className={`${iconColor} font-medium`}>{label}</span>
                {testResult.response_time_ms != null && (
                  <span className="text-gray-400 text-sm ml-2">{testResult.response_time_ms.toFixed(0)}ms</span>
                )}
              </div>
              <p className="text-gray-400 text-sm mt-1">{testResult.message}</p>
            </div>
          );
        })()}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button onClick={canManage ? handleTestConnection : undefined} disabled={!canManage || !isValid || testing}
            title={!canManage ? 'Only administrators can test connections' : ''}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:text-white hover:border-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Test Connection
          </button>
          <button onClick={canManage ? handleSave : undefined} disabled={!canManage || !isValid}
            title={!canManage ? 'Only administrators can create or modify services' : ''}
            className="flex items-center gap-2 px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
            {view === 'edit' ? 'Save Changes' : 'Create Service'}
          </button>
          <button onClick={() => { setView('list'); resetForm() }}
            className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
        </div>
      </div>
    )
  }
  // ── List View (main render) ────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Services</h1>
          <p className="text-gray-400 mt-1">Manage and monitor your connected services</p>
        </div>
        {activeTab === 'external' && (
          <button onClick={openCreate}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-500 font-medium transition-colors shadow-lg shadow-blue-600/20">
            <Plus className="w-4 h-4" /> Connect Service
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800/60 rounded-lg p-1 w-fit">
        <button onClick={() => setActiveTab('external')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'external' ? 'bg-emerald-500/20 text-emerald-400 shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/40'
          }`}>
          <Globe className="w-4 h-4" /> External Services
          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs ${activeTab === 'external' ? 'bg-emerald-400/20 text-emerald-300' : 'bg-gray-700 text-gray-400'}`}>
            {extSummary.total}
          </span>
        </button>
        <button onClick={() => setActiveTab('platform')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'platform' ? 'bg-blue-500/20 text-blue-400 shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/40'
          }`}>
          <Server className="w-4 h-4" /> Platform Services
          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs ${activeTab === 'platform' ? 'bg-blue-400/20 text-blue-300' : 'bg-gray-700 text-gray-400'}`}>
            {platform.total}
          </span>
        </button>
      </div>

      {/* ── EXTERNAL SERVICES TAB ──────────────────────────────── */}
      {activeTab === 'external' && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: 'Total', value: extSummary.total, Icon: Globe, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
              { label: 'Healthy', value: extSummary.up, Icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-400/10' },
              { label: 'Down', value: extSummary.down, Icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-400/10' },
              { label: 'Unknown', value: extSummary.unknown + extSummary.degraded, Icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
            ].map(c => (
              <div key={c.label} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-lg ${c.bg}`}><c.Icon className={`w-5 h-5 ${c.color}`} /></div>
                  <div>
                    <p className="text-gray-400 text-sm">{c.label}</p>
                    <p className="text-xl font-bold text-white">{c.value}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty state */}
          {/* Filter bar */}
          {extServices.length > 0 && (
            <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-4">
              <div className="flex flex-wrap items-center gap-3">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                  <input
                    type="text"
                    placeholder="Search services..."
                    value={filterSearch}
                    onChange={e => setFilterSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                {/* Catalog Type filter */}
                <select
                  value={filterCatalogType}
                  onChange={e => setFilterCatalogType(e.target.value)}
                  className="px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Catalog Types</option>
                  {catalogTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                </select>
                {/* Category filter */}
                <select
                  value={filterCategory}
                  onChange={e => setFilterCategory(e.target.value)}
                  className="px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                </select>
                {/* Clear button */}
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-700/50 transition-colors">
                    <X className="w-4 h-4" /> Clear
                  </button>
                )}
              </div>
              {hasActiveFilters && (
                <p className="text-gray-500 text-xs mt-2">Showing {filteredServices.length} of {extServices.length} services</p>
              )}
            </div>
          )}

          {extServices.length === 0 ? (
            <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-16 text-center">
              <Globe className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No external services connected</h3>
              <p className="text-gray-500 max-w-md mx-auto mb-6">
                Connect your APIs and databases to start monitoring them with Rhinometric.
              </p>
              <div className="flex flex-wrap justify-center gap-3 mb-8">
                <TypeBadge type="http" />
                <TypeBadge type="postgresql" />
              </div>
              <button onClick={openCreate}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-500 font-medium transition-colors shadow-lg shadow-blue-600/20">
                <Plus className="w-5 h-5" /> Connect Your First Service
              </button>
            </div>
          ) : (
            /* Service table */
            <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700/50">
                      <th className="text-left p-4 text-gray-400 font-medium">Service</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Type</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Catalog Type</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Category</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Target</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Latency</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Last Check</th>
                      <th className="text-right p-4 text-gray-400 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredServices.length === 0 && hasActiveFilters && (
                      <tr><td colSpan={9} className="p-8 text-center text-gray-500">
                        <Search className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                        <p>No services match the current filters</p>
                        <button onClick={clearFilters} className="text-blue-400 hover:text-blue-300 text-sm mt-1">Clear filters</button>
                      </td></tr>
                    )}
                    {filteredServices.map(svc => (
                      <tr key={svc.id} className={`border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors ${!svc.enabled ? 'opacity-50' : ''}`}>
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded ${svc.enabled ? 'bg-emerald-400/10' : 'bg-gray-700/50'}`}>
                              {svc.service_type === 'http' ? <Network className="w-4 h-4 text-violet-400" /> : <Database className="w-4 h-4 text-orange-400" />}
                            </div>
                            <div>
                              <p className="text-white font-medium">{svc.name}</p>
                              {svc.environment && <p className="text-gray-500 text-xs">{svc.environment}</p>}
                              {svc.tags && svc.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {svc.tags.map((tag, i) => (
                                    <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-400/10 text-blue-400">
                                      <Tag className="w-2.5 h-2.5" />{tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="p-4"><TypeBadge type={svc.service_type} /></td>
                        <td className="p-4 text-sm text-gray-300">{svc.catalog_type || <span className="text-gray-600">&ndash;</span>}</td>
                        <td className="p-4 text-sm text-gray-300">{svc.category || <span className="text-gray-600">&ndash;</span>}</td>
                        <td className="p-4">
                          <code className="text-sm text-gray-300 bg-gray-900/50 px-2 py-1 rounded truncate max-w-[200px] inline-block">
                            {targetDisplay(svc)}
                          </code>
                        </td>
                        <td className="p-4"><StatusBadge status={svc.enabled ? svc.status : 'unknown'} /></td>
                        <td className="p-4 text-gray-300 text-sm">
                          {svc.last_response_time_ms != null ? `${svc.last_response_time_ms.toFixed(0)}ms` : '-'}
                        </td>
                        <td className="p-4 text-gray-400 text-sm">
                          {svc.last_check_at ? new Date(svc.last_check_at).toLocaleString() : 'Never'}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => canManage && handleTestSaved(svc.id)} disabled={!canManage || actionLoading === svc.id}
                              title={canManage ? "Test connection" : "Admin only"} className={`p-1.5 rounded transition-colors disabled:opacity-50 ${canManage ? 'hover:bg-gray-700/50 text-gray-400 hover:text-green-400' : 'text-gray-600 cursor-not-allowed'}`}>
                              {actionLoading === svc.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            </button>
                            <button onClick={() => canManage && openEdit(svc)} disabled={!canManage}
                              title={canManage ? "Edit" : "Admin only"} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-700/50 text-gray-400 hover:text-blue-400' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              <Edit className="w-4 h-4" />
                            </button>
                            <button onClick={() => canManage && handleToggle(svc.id)} disabled={!canManage}
                              title={canManage ? (svc.enabled ? 'Disable' : 'Enable') : 'Admin only'} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-700/50 text-gray-400 hover:text-yellow-400' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              {svc.enabled ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                            </button>
                            <button onClick={() => canManage && handleDelete(svc.id)} disabled={!canManage}
                              title={canManage ? "Delete" : "Admin only"} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-700/50 text-gray-400 hover:text-red-400' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── PLATFORM SERVICES TAB ───────────────────────────────── */}
      {activeTab === 'platform' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-400/10 rounded-lg"><Server className="w-6 h-6 text-blue-400" /></div>
                <div><p className="text-gray-400 text-sm">Platform Services</p><p className="text-2xl font-bold text-white">{platform.total}</p></div>
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-400/10 rounded-lg"><CheckCircle className="w-6 h-6 text-green-400" /></div>
                <div><p className="text-gray-400 text-sm">Healthy</p><p className="text-2xl font-bold text-green-400">{platform.up}</p></div>
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-400/10 rounded-lg"><AlertCircle className="w-6 h-6 text-red-400" /></div>
                <div><p className="text-gray-400 text-sm">Down</p><p className="text-2xl font-bold text-red-400">{platform.down}</p></div>
              </div>
            </div>
          </div>

          {platform.total === 0 ? (
            <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-12 text-center">
              <Server className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300">No platform services detected</h3>
              <p className="text-gray-500 mt-2">Platform services will appear here once Prometheus is scraping them.</p>
            </div>
          ) : (
            <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700/50">
                      <th className="text-left p-4 text-gray-400 font-medium">Service</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Instance</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Tier</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Version</th>
                    </tr>
                  </thead>
                  <tbody>
                    {platform.services.map((svc, i) => (
                      <tr key={`${svc.name}-${svc.instance}-${i}`} className="border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded ${svc.status === 'up' ? 'bg-green-400/10' : 'bg-red-400/10'}`}>
                              <Server className={`w-4 h-4 ${svc.status === 'up' ? 'text-green-400' : 'text-red-400'}`} />
                            </div>
                            <div>
                              <p className="text-white font-medium">{svc.name}</p>
                              <p className="text-gray-400 text-sm">{svc.service_type}</p>
                            </div>
                          </div>
                        </td>
                        <td className="p-4"><code className="text-sm text-gray-300 bg-gray-900/50 px-2 py-1 rounded">{svc.instance}</code></td>
                        <td className="p-4">
                          <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${svc.status === 'up' ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'}`}>
                            {svc.status === 'up' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                            {svc.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-4"><span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-400/10 text-blue-400">{svc.tier}</span></td>
                        <td className="p-4 text-gray-300">{svc.version}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="text-center text-gray-500 text-sm">
            Last updated: {platformData ? new Date(platformData.timestamp).toLocaleString() : 'N/A'}
          </div>
        </>
      )}
    </div>
  )
}