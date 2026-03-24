import React, { useEffect, useState, useCallback } from 'react'
import {
  Server, AlertCircle, CheckCircle, Activity, Globe, Database, 
  Network, Plus, Trash2, Play, Power, PowerOff, Edit, ArrowLeft,
  RefreshCw, Clock, Lock, Search, Tag, X, Upload, FileText, Download, Layers, Copy,
  Radio, BarChart3, Waypoints, ToggleLeft, ToggleRight, Info, AlertTriangle, Zap, HelpCircle, CircleDot, ChevronRight, ChevronDown, FolderOpen, Folder,
  Eye, EyeOff, Shield, Terminal
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
  group_name: string | null
  enabled: boolean
  config: Record<string, any>
  timeout_seconds: number
  check_interval_seconds: number
  // ── Monitoring-mode & telemetry domain fields ──
  monitoring_mode: 'synthetic_only' | 'telemetry_enabled'
  synthetic_enabled: boolean
  metrics_enabled: boolean
  logs_enabled: boolean
  traces_enabled: boolean
  telemetry_attached: boolean
  telemetry_source_type: string | null
  telemetry_service_key: string | null
  telemetry_token: string | null
  telemetry_status: string | null
  last_telemetry_at: string | null
  capability: string                        // derived label
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


/* ─── Grouped View Types (Task 22) ──────────────────────────── */
interface GroupedServiceItem {
  id: number
  name: string
  service_type: string
  catalog_type: string | null
  category: string | null
  group_name: string
  environment: string | null
  enabled: boolean
  status: string
  status_message: string | null
  latency: number | null
  telemetry_status: string | null
  last_check: string | null
  monitoring_mode: string
  telemetry_attached: boolean
  metrics_enabled: boolean
  logs_enabled: boolean
  traces_enabled: boolean
}

interface ServiceGroup {
  group_name: string
  status: string
  total: number
  up: number
  down: number
  services: GroupedServiceItem[]
}

/* ─── Catalog Type Visual Meta (Task 22) ─────────────────── */
const CATALOG_META: Record<string, { label: string; color: string; bg: string }> = {
  REST_API:         { label: 'API',        color: 'text-blue-400',    bg: 'bg-blue-400/10' },
  DATABASE:         { label: 'Database',   color: 'text-orange-400',  bg: 'bg-orange-400/10' },
  QUEUE:            { label: 'Queue',      color: 'text-yellow-400',  bg: 'bg-yellow-400/10' },
  MICROSERVICE:     { label: 'Service',    color: 'text-violet-400',  bg: 'bg-violet-400/10' },
  EXTERNAL_SERVICE: { label: 'External',   color: 'text-teal-400',    bg: 'bg-teal-400/10' },
  WEB_APP:          { label: 'Web App',    color: 'text-pink-400',    bg: 'bg-pink-400/10' },
  INTERNAL_SERVICE: { label: 'Internal',   color: 'text-cyan-400',    bg: 'bg-cyan-400/10' },
}

function CatalogBadge({ type }: { type: string | null }) {
  const m = CATALOG_META[type || ''] || { label: type || 'Other', color: 'text-gray-400', bg: 'bg-gray-400/10' }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${m.bg} ${m.color}`}>
      {m.label}
    </span>
  )
}

/* ─── Group Health Badge (Task 22) ──────────────────────────── */
function GroupHealthBadge({ status }: { status: string }) {
  const cfg: Record<string, { bg: string; text: string; ring: string; label: string }> = {
    healthy:  { bg: 'bg-green-500/10',  text: 'text-green-400',  ring: 'ring-green-500/20',  label: 'Healthy' },
    degraded: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', ring: 'ring-yellow-500/20', label: 'Degraded' },
    down:     { bg: 'bg-red-500/10',    text: 'text-red-400',    ring: 'ring-red-500/20',    label: 'Down' },
  }
  const s = cfg[status] || cfg.down
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${s.bg} ${s.text} ${s.ring}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.text.replace('text-', 'bg-')}`} />
      {s.label}
    </span>
  )
}

type Tab = 'external' | 'platform'
type View = 'list' | 'grouped' | 'create' | 'edit' | 'bulk-http'

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

/* ─── Monitoring Badge ────────────────────────────────────── */
function MonitoringBadge({ svc }: { svc: ExternalServiceData }) {
  // Telemetry indicator dot color
  const dotColor = svc.monitoring_mode === 'synthetic_only'
    ? 'bg-gray-500'                   // grey = synthetic only
    : svc.telemetry_attached
      ? 'bg-green-400'                // green = telemetry attached
      : 'bg-blue-400';                // blue = configured but not attached

  const label = svc.capability || 'Synthetic only';

  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} title={
        svc.monitoring_mode === 'synthetic_only'
          ? 'Synthetic only'
          : svc.telemetry_attached
            ? 'Telemetry attached'
            : 'Telemetry configured, not attached'
      } />
      <span className="text-xs text-gray-300 whitespace-nowrap">{label}</span>
    </div>
  );
}

/* ─── Telemetry Status Badge ─────────────────────────────── */
const TELEMETRY_STATUS_CONFIG: Record<string, { color: string; bgColor: string; label: string; helper: string }> = {
  not_configured: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-400/10',
    label: 'Not Configured',
    helper: '',
  },
  configured: {
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    label: 'Configured',
    helper: 'Collector not connected yet. Run the collector with the configuration below.',
  },
  connected: {
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    label: 'Connected',
    helper: 'Collector connected successfully.',
  },
  receiving_data: {
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    label: 'Receiving Data',
    helper: 'Collector connected successfully.',
  },
  stale: {
    color: 'text-orange-400',
    bgColor: 'bg-orange-400/10',
    label: 'Stale',
    helper: 'No telemetry data received in the last 10 minutes. Check your collector.',
  },
  error: {
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    label: 'Error',
    helper: 'Collector configuration exists, but telemetry delivery is failing.',
  },
};

function TelemetryStatusBadge({ status }: { status: string | null }) {
  const cfg = TELEMETRY_STATUS_CONFIG[status || 'not_configured'] || TELEMETRY_STATUS_CONFIG.not_configured;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bgColor} ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.color.replace('text-', 'bg-')}`} />
      {cfg.label}
    </span>
  );
}


/* ─── Telemetry Readiness Card (Task 20, Part 1) ─────────── */
function TelemetryReadinessCard({ svc }: { svc: ExternalServiceData }) {
  const statusCfg = TELEMETRY_STATUS_CONFIG[svc.telemetry_status || 'not_configured'] || TELEMETRY_STATUS_CONFIG.not_configured;
  const lastTelemetry = svc.last_telemetry_at
    ? new Date(svc.last_telemetry_at).toLocaleString()
    : null;

  // Derive conservative per-signal state from overall telemetry_status
  function signalState(enabled: boolean): { label: string; color: string; dotColor: string } {
    if (!enabled) return { label: 'Disabled', color: 'text-gray-600', dotColor: 'bg-gray-600' };
    const status = svc.telemetry_status || 'not_configured';
    if (status === 'receiving_data' || status === 'connected') {
      return { label: 'Receiving', color: 'text-green-400', dotColor: 'bg-green-400' };
    }
    if (status === 'stale') {
      return { label: 'Stale', color: 'text-orange-400', dotColor: 'bg-orange-400' };
    }
    if (status === 'error') {
      return { label: 'Error', color: 'text-red-400', dotColor: 'bg-red-400' };
    }
    return { label: 'Awaiting data', color: 'text-blue-400', dotColor: 'bg-blue-400' };
  }

  const signals = [
    { label: 'Metrics', enabled: svc.metrics_enabled, Icon: BarChart3 },
    { label: 'Logs', enabled: svc.logs_enabled, Icon: FileText },
    { label: 'Traces', enabled: svc.traces_enabled, Icon: Waypoints },
  ];

  return (
    <div className="mt-5 bg-gray-800/40 rounded-lg border border-gray-700/30 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-emerald-400" />
        <h4 className="text-sm font-semibold text-white">Telemetry Readiness</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Collector Status */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Collector Status</p>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusCfg.color.replace('text-', 'bg-')}`} />
            <span className={`text-sm font-medium ${statusCfg.color}`}>{statusCfg.label}</span>
          </div>
        </div>

        {/* Last Telemetry */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Last Data Received</p>
          <div className="flex items-center gap-2">
            <Clock className={`w-3.5 h-3.5 ${lastTelemetry ? 'text-green-400' : 'text-gray-500'}`} />
            <span className={`text-sm ${lastTelemetry ? 'text-gray-200' : 'text-gray-500 italic'}`}>
              {lastTelemetry || 'No telemetry received yet'}
            </span>
          </div>
        </div>

        {/* Signal Readiness */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Signal Readiness</p>
          <div className="space-y-1.5">
            {signals.map(s => {
              const state = signalState(s.enabled);
              return (
                <div key={s.label} className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${state.dotColor}`} />
                  <s.Icon className={`w-3 h-3 ${state.color}`} />
                  <span className={`text-xs ${state.color}`}>{s.label}</span>
                  <span className={`text-xs ml-auto ${state.color} opacity-70`}>{state.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Setup Checklist (Task 20, Part 2) ──────────────────── */
function SetupChecklist({ svc }: { svc: ExternalServiceData }) {
  const status = svc.telemetry_status || 'not_configured';

  const steps = [
    {
      label: 'Service created',
      done: true,
    },
    {
      label: 'Telemetry mode enabled',
      done: svc.monitoring_mode === 'telemetry_enabled',
    },
    {
      label: 'Service key generated',
      done: !!svc.telemetry_service_key,
    },
    {
      label: 'Token generated',
      done: !!svc.telemetry_token,
    },
    {
      label: 'Collector command copied / .env downloaded',
      done: status === 'connected' || status === 'receiving_data' || status === 'stale' || status === 'error',
    },
    {
      label: 'Collector connected',
      done: status === 'connected' || status === 'receiving_data' || status === 'stale',
    },
    {
      label: 'Data received',
      done: status === 'receiving_data' || (!!svc.last_telemetry_at),
    },
  ];

  return (
    <div className="mt-4 bg-gray-800/40 rounded-lg border border-gray-700/30 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <CircleDot className="w-4 h-4 text-blue-400" />
        <h4 className="text-sm font-semibold text-white">Setup Checklist</h4>
        <span className="text-xs text-gray-500 ml-auto">
          {steps.filter(s => s.done).length}/{steps.length} complete
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 py-0.5">
            {step.done ? (
              <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
            ) : (
              <div className="w-3.5 h-3.5 rounded-full border border-gray-600 flex-shrink-0" />
            )}
            <span className={`text-xs ${step.done ? 'text-gray-300' : 'text-gray-500'}`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Troubleshooting Block (Task 20, Part 4) ────────────── */
function TroubleshootingBlock({ svc }: { svc: ExternalServiceData }) {
  const status = svc.telemetry_status || 'not_configured';
  const messages: Record<string, { icon: string; color: string; bgColor: string; borderColor: string; text: string }> = {
    not_configured: {
      icon: 'info',
      color: 'text-gray-400',
      bgColor: 'bg-gray-500/10',
      borderColor: 'border-gray-500/20',
      text: 'Enable telemetry for this service to attach a collector.',
    },
    configured: {
      icon: 'info',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/20',
      text: 'Collector not connected yet. Run the collector with the configuration above.',
    },
    connected: {
      icon: 'check',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/20',
      text: 'Telemetry is arriving correctly.',
    },
    receiving_data: {
      icon: 'check',
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/20',
      text: 'Telemetry is arriving correctly.',
    },
    stale: {
      icon: 'warn',
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/20',
      text: 'Telemetry stopped arriving. Check whether the collector is still running and can reach the API.',
    },
    error: {
      icon: 'error',
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20',
      text: 'Telemetry delivery is failing. Verify token, service key, connectivity, and enabled signals.',
    },
  };

  const msg = messages[status] || messages.not_configured;

  return (
    <div className="mt-4 bg-gray-800/40 rounded-lg border border-gray-700/30 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <HelpCircle className="w-4 h-4 text-gray-400" />
        <h4 className="text-sm font-semibold text-white">Troubleshooting</h4>
      </div>
      <div className={`flex items-start gap-2 px-3 py-2.5 rounded-lg border ${msg.bgColor} ${msg.borderColor}`}>
        {msg.icon === 'check' ? (
          <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${msg.color}`} />
        ) : msg.icon === 'warn' ? (
          <AlertTriangle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${msg.color}`} />
        ) : msg.icon === 'error' ? (
          <AlertCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${msg.color}`} />
        ) : (
          <Info className={`w-4 h-4 flex-shrink-0 mt-0.5 ${msg.color}`} />
        )}
        <p className={`text-xs leading-relaxed ${msg.color}`}>{msg.text}</p>
      </div>
      {(status === 'stale' || status === 'error' || status === 'configured') && (
        <div className="text-xs text-gray-500 space-y-1 pl-1">
          <p className="font-medium text-gray-400 mb-1">Common checks:</p>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-gray-600 flex-shrink-0" />
            <span>Verify the collector container is running: <code className="text-gray-400 bg-gray-900/50 px-1 rounded text-[10px]">docker ps</code></span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-gray-600 flex-shrink-0" />
            <span>Check collector logs: <code className="text-gray-400 bg-gray-900/50 px-1 rounded text-[10px]">docker logs &lt;container&gt;</code></span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-gray-600 flex-shrink-0" />
            <span>Confirm RHYNO_API_URL, RHYNO_SERVICE_KEY, and RHYNO_TELEMETRY_TOKEN are correct.</span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-gray-600 flex-shrink-0" />
            <span>Ensure the collector can reach the API endpoint from its network.</span>
          </div>
        </div>
      )}
    </div>
  );
}


/* ─── Telemetry Setup Block ─────────────────────────────── */
function TelemetrySetupBlock({ svc }: { svc: ExternalServiceData }) {
  const [showToken, setShowToken] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = async (value: string, field: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = value;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    }
  };

  const maskedToken = svc.telemetry_token
    ? svc.telemetry_token.slice(0, 8) + '\u2022'.repeat(24) + svc.telemetry_token.slice(-6)
    : '';

  const statusCfg = TELEMETRY_STATUS_CONFIG[svc.telemetry_status || 'not_configured'] || TELEMETRY_STATUS_CONFIG.not_configured;

  const signals = [
    { label: 'Metrics', enabled: svc.metrics_enabled, Icon: BarChart3, color: 'text-blue-400', endpoint: '/api/telemetry/metrics' },
    { label: 'Logs',    enabled: svc.logs_enabled,    Icon: FileText, color: 'text-yellow-400', endpoint: '/api/telemetry/logs' },
    { label: 'Traces',  enabled: svc.traces_enabled,  Icon: Waypoints, color: 'text-purple-400', endpoint: '/api/telemetry/traces' },
  ];

  const lastTelemetry = svc.last_telemetry_at
    ? new Date(svc.last_telemetry_at).toLocaleString()
    : null;

  return (
    <div className="mt-6 space-y-4">
      {/* Section Header */}
      <div className="flex items-center gap-2 border-t border-gray-700/30 pt-5">
        <Shield className="w-4 h-4 text-emerald-400" />
        <h4 className="text-sm font-semibold text-white">Telemetry Setup</h4>
        <TelemetryStatusBadge status={svc.telemetry_status} />
      </div>

      {/* Explanation text (Task 20, Part 3) */}
      <p className="text-xs text-gray-400 leading-relaxed">
        Run this collector on the customer side to send real metrics, logs, and traces for this service.
      </p>

      {/* Deployment warning (Task 20, Part 3) */}
      <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
        <p className="text-xs text-amber-300/80">
          The collector is not deployed by Rhinometric automatically. It must run in the customer environment.
        </p>
      </div>

      {/* Status Helper Text */}
      {statusCfg.helper && (
        <div className={`flex items-start gap-2 px-3 py-2 rounded-lg border ${
          svc.telemetry_status === 'error'
            ? 'bg-red-500/10 border-red-500/20'
            : svc.telemetry_status === 'stale'
              ? 'bg-orange-500/10 border-orange-500/20'
              : svc.telemetry_status === 'receiving_data' || svc.telemetry_status === 'connected'
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-blue-500/10 border-blue-500/20'
        }`}>
          <Info className={`w-4 h-4 flex-shrink-0 mt-0.5 ${statusCfg.color}`} />
          <p className={`text-xs ${statusCfg.color.replace('text-', 'text-').replace('-400', '-300/80')}`}>{statusCfg.helper}</p>
        </div>
      )}

      {/* Credentials Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Service Key */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Telemetry Service Key</p>
          <div className="flex items-center gap-2 bg-gray-800/60 rounded-lg px-3 py-2 border border-gray-700/40">
            <code className="text-sm text-gray-200 font-mono flex-1 truncate">{svc.telemetry_service_key || '—'}</code>
            {svc.telemetry_service_key && (
              <button
                onClick={() => copyToClipboard(svc.telemetry_service_key!, 'key')}
                className="p-1 rounded hover:bg-gray-700/50 text-gray-400 hover:text-white transition-colors flex-shrink-0"
                title="Copy Service Key"
              >
                {copiedField === 'key' ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            )}
          </div>
        </div>

        {/* Token */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Telemetry Token</p>
          <div className="flex items-center gap-2 bg-gray-800/60 rounded-lg px-3 py-2 border border-gray-700/40">
            <code className="text-sm text-gray-200 font-mono flex-1 truncate">
              {svc.telemetry_token ? (showToken ? svc.telemetry_token : maskedToken) : '—'}
            </code>
            {svc.telemetry_token && (
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  onClick={() => setShowToken(!showToken)}
                  className="p-1 rounded hover:bg-gray-700/50 text-gray-400 hover:text-white transition-colors"
                  title={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => copyToClipboard(svc.telemetry_token!, 'token')}
                  className="p-1 rounded hover:bg-gray-700/50 text-gray-400 hover:text-white transition-colors"
                  title="Copy Token"
                >
                  {copiedField === 'token' ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Signals + Last Telemetry Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Enabled Signals */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Enabled Signals</p>
          <div className="flex flex-wrap gap-2">
            {signals.map(s => (
              <span key={s.label} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${s.enabled ? 'bg-gray-700/50 text-white border border-gray-600/40' : 'bg-gray-800/30 text-gray-600 line-through border border-gray-800/30'}`}>
                <s.Icon className={`w-3 h-3 ${s.enabled ? s.color : 'text-gray-600'}`} />
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {/* Last Telemetry */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Last Telemetry Received</p>
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-gray-500" />
            <span className={`text-sm ${lastTelemetry ? 'text-gray-200' : 'text-gray-500 italic'}`}>
              {lastTelemetry || 'No telemetry received yet'}
            </span>
          </div>
        </div>
      </div>

            {/* ── Collector Setup ────────────────────────────────── */}
      {svc.telemetry_token && (
        <div className="bg-gray-800/40 rounded-lg border border-gray-700/30 p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-400" />
            <h5 className="text-sm font-semibold text-white">Collector Setup</h5>
          </div>

          {/* Collector Image */}
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Collector Image</p>
            <div className="flex items-center gap-2 bg-gray-900/50 rounded-lg px-3 py-2 border border-gray-700/30">
              <Layers className="w-3.5 h-3.5 text-gray-400" />
              <code className="text-sm text-gray-200 font-mono">rhinometric-collector:v1.1.0</code>
            </div>
          </div>

          {/* Environment Variables */}
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Required Environment Variables</p>
            <div className="space-y-2">
              {[
                { name: 'RHYNO_API_URL', value: `${window.location.origin}/api`, field: 'env_api' },
                { name: 'RHYNO_SERVICE_KEY', value: svc.telemetry_service_key || '', field: 'env_key' },
                { name: 'RHYNO_TELEMETRY_TOKEN', value: svc.telemetry_token || '', field: 'env_token' },
              ].map(env => (
                <div key={env.name} className="flex items-center gap-2 bg-gray-900/50 rounded-lg px-3 py-2 border border-gray-700/30">
                  <code className="text-xs text-gray-500 font-mono w-48 flex-shrink-0">{env.name}</code>
                  <code className="text-xs text-gray-200 font-mono flex-1 truncate">{env.value}</code>
                  <button
                    onClick={() => copyToClipboard(env.value, env.field)}
                    className="p-1 rounded hover:bg-gray-700/50 text-gray-400 hover:text-white transition-colors flex-shrink-0"
                    title={`Copy ${env.name}`}
                  >
                    {copiedField === env.field ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Docker Run Command */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Docker Run Command</p>
              <button
                onClick={() => {
                  const cmd = [
                    'docker run --rm \\',
                    `  -e RHYNO_API_URL=${window.location.origin}/api \\`,
                    `  -e RHYNO_SERVICE_KEY=${svc.telemetry_service_key || ''} \\`,
                    `  -e RHYNO_TELEMETRY_TOKEN=${svc.telemetry_token || ''} \\`,
                    '  rhinometric-collector:v1.1.0',
                  ].join('\n');
                  copyToClipboard(cmd, 'docker');
                }}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20 transition-colors"
              >
                {copiedField === 'docker' ? <CheckCircle className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                {copiedField === 'docker' ? 'Copied!' : 'Copy Docker Command'}
              </button>
            </div>
            <pre className="bg-gray-900/70 rounded-lg px-4 py-3 border border-gray-700/30 text-xs text-gray-200 font-mono overflow-x-auto whitespace-pre leading-relaxed">
{`docker run --rm \\
  -e RHYNO_API_URL=${window.location.origin}/api \\
  -e RHYNO_SERVICE_KEY=${svc.telemetry_service_key || '...'} \\
  -e RHYNO_TELEMETRY_TOKEN=${svc.telemetry_token || '...'} \\
  rhinometric-collector:v1.1.0`}
            </pre>
          </div>

          {/* Download .env Template */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 pt-1">
            <button
              onClick={() => {
                const content = [
                  `RHYNO_API_URL=${window.location.origin}/api`,
                  `RHYNO_SERVICE_KEY=${svc.telemetry_service_key || ''}`,
                  `RHYNO_TELEMETRY_TOKEN=${svc.telemetry_token || ''}`,
                  'COLLECT_INTERVAL=15',
                  'ENABLE_METRICS=true',
                  'ENABLE_LOGS=true',
                  'ENABLE_TRACES=true',
                ].join('\n');
                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${svc.telemetry_service_key || 'collector'}.env`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-700/50 text-gray-300 hover:bg-gray-600/50 hover:text-white border border-gray-600/30 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Download .env Template
            </button>
            <p className="text-xs text-gray-500">Pre-filled with this service's credentials</p>
          </div>

          {/* Ingestion Endpoints */}
          <div className="space-y-1.5 pt-1">
            <p className="text-xs text-gray-500 font-medium">Ingestion Endpoints:</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {signals.filter(s => s.enabled).map(s => (
                <div key={s.label} className="flex items-center gap-2 px-2.5 py-1.5 bg-gray-900/50 rounded border border-gray-700/30">
                  <s.Icon className={`w-3 h-3 ${s.color}`} />
                  <code className="text-xs text-gray-300 font-mono">{s.endpoint}</code>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Monitoring Detail Panel (expanded row) ───────────── */
function MonitoringDetailPanel({ svc }: { svc: ExternalServiceData }) {
  const isTelemetry = svc.monitoring_mode === 'telemetry_enabled';
  const signals = [
    { label: 'Metrics', enabled: svc.metrics_enabled, Icon: BarChart3, color: 'text-blue-400' },
    { label: 'Logs',    enabled: svc.logs_enabled,    Icon: FileText, color: 'text-yellow-400' },
    { label: 'Traces',  enabled: svc.traces_enabled,  Icon: Waypoints, color: 'text-purple-400' },
  ];

  return (
    <div className="bg-gray-900/60 border-t border-gray-700/30 px-6 py-5">
      <h4 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4 text-blue-400" />
        Monitoring Configuration
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Column 1: Monitoring Mode */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Monitoring Mode</p>
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-white font-medium">
              {isTelemetry ? 'Telemetry Enabled' : 'Synthetic Only'}
            </span>
          </div>
        </div>

        {/* Column 2: Synthetic Monitoring */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Synthetic Monitoring</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${svc.synthetic_enabled ? 'bg-green-400' : 'bg-gray-600'}`} />
              <span className="text-gray-400">Status:</span>
              <span className="text-white">{svc.synthetic_enabled ? 'Enabled' : 'Disabled'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Target:</span>
              <code className="text-gray-300 bg-gray-800/50 px-1.5 py-0.5 rounded text-xs">{targetDisplay(svc)}</code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Interval:</span>
              <span className="text-white">{svc.check_interval_seconds}s</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Timeout:</span>
              <span className="text-white">{svc.timeout_seconds}s</span>
            </div>
          </div>
        </div>

        {/* Column 3: Telemetry Status Summary */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-gray-500 font-medium">Telemetry Status</p>
          {isTelemetry ? (
            <div className="space-y-2 text-sm">
              <TelemetryStatusBadge status={svc.telemetry_status} />
              <div className="space-y-1">
                <p className="text-gray-400 text-xs">Signals enabled:</p>
                <div className="flex flex-wrap gap-2">
                  {signals.map(s => (
                    <span key={s.label} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${s.enabled ? 'bg-gray-700/50 text-white' : 'bg-gray-800/30 text-gray-600 line-through'}`}>
                      <s.Icon className={`w-3 h-3 ${s.enabled ? s.color : 'text-gray-600'}`} />
                      {s.label}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/30">
              <Info className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
              <p className="text-gray-500 text-xs">This service is monitored using synthetic checks only.</p>
            </div>
          )}
        </div>
      </div>

      {/* Telemetry Readiness Card (Task 20, Part 1) */}
      {isTelemetry && <TelemetryReadinessCard svc={svc} />}

      {/* Setup Checklist (Task 20, Part 2) */}
      {isTelemetry && <SetupChecklist svc={svc} />}

      {/* Telemetry Setup Block — only for telemetry-enabled services */}
      {isTelemetry && <TelemetrySetupBlock svc={svc} />}

      {/* Troubleshooting (Task 20, Part 4) */}
      {isTelemetry && <TroubleshootingBlock svc={svc} />}
    </div>
  );
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
  const [formGroupName, setFormGroupName] = useState('Default')
  const [formCatalogType, setFormCatalogType] = useState('')
  const [formCategory, setFormCategory] = useState('')
  const [formTags, setFormTags] = useState<string[]>([])
  const [formTagInput, setFormTagInput] = useState('')

  // ── Monitoring mode & telemetry form state ──
  const [formMonitoringMode, setFormMonitoringMode] = useState<'synthetic_only' | 'telemetry_enabled'>('synthetic_only')
  const [formMetricsEnabled, setFormMetricsEnabled] = useState(false)
  const [formLogsEnabled, setFormLogsEnabled] = useState(false)
  const [formTracesEnabled, setFormTracesEnabled] = useState(false)
  const [formTelemetryServiceKey, setFormTelemetryServiceKey] = useState('')
  const [showTelemetryWarning, setShowTelemetryWarning] = useState(false)

  // Test connection state
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [expandedServiceId, setExpandedServiceId] = useState<number | null>(null)

  // ── Grouped view state (Task 22) ──
  const [groupedData, setGroupedData] = useState<ServiceGroup[]>([])
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [groupViewMode, setGroupViewMode] = useState<'list' | 'grouped'>('grouped')

  // Catalog filter state
  const [filterSearch, setFilterSearch] = useState('')
  const [filterCatalogType, setFilterCatalogType] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterGroupName, setFilterGroupName] = useState('')

  // Bulk Import state
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importStep, setImportStep] = useState<'upload' | 'preview' | 'result'>('upload')
  const [importLoading, setImportLoading] = useState(false)
  const [importPreview, setImportPreview] = useState<any>(null)
  const [importResult, setImportResult] = useState<any>(null)

  // Bulk HTTP state
  const [bulkBaseUrl, setBulkBaseUrl] = useState('')
  const [bulkMethod, setBulkMethod] = useState('GET')
  const [bulkEnv, setBulkEnv] = useState('')
  const [bulkTimeout, setBulkTimeout] = useState(10)
  const [bulkInterval, setBulkInterval] = useState(60)
  const [bulkEnabled, setBulkEnabled] = useState(true)
  const [bulkGroupName, setBulkGroupName] = useState('Default')
  const [bulkCatalogType, setBulkCatalogType] = useState('REST_API')
  const [bulkCategory, setBulkCategory] = useState('')
  const [bulkTags, setBulkTags] = useState<string[]>([])
  const [bulkTagInput, setBulkTagInput] = useState('')
  const [bulkAuthType, setBulkAuthType] = useState('')
  const [bulkAuthValue, setBulkAuthValue] = useState('')
  const [bulkItems, setBulkItems] = useState<{name: string; path: string; method?: string}[]>([{name: '', path: ''}])
  const [bulkPasteMode, setBulkPasteMode] = useState(false)
  const [bulkPasteText, setBulkPasteText] = useState('')
  const [bulkStep, setBulkStep] = useState<'form' | 'preview' | 'result'>('form')
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkPreview, setBulkPreview] = useState<any>(null)
  const [bulkResult, setBulkResult] = useState<any>(null)

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

  const fetchGrouped = useCallback(async () => {
    try {
      const res = await fetch('/api/services/grouped', { headers: apiHeaders })
      if (res.ok) {
        const data: ServiceGroup[] = await res.json()
        setGroupedData(data)
        // Auto-expand all groups on first load
        if (expandedGroups.size === 0 && data.length > 0) {
          setExpandedGroups(new Set(data.map(g => g.group_name)))
        }
      }
    } catch (e) { console.error('grouped fetch error', e) }
  }, [token])

  useEffect(() => {
    const load = async () => {
      setIsLoading(true)
      await Promise.all([fetchExternal(), fetchPlatform(), fetchGrouped()])
      setIsLoading(false)
    }
    load()
    const iv = setInterval(() => { fetchExternal(); fetchPlatform(); fetchGrouped() }, 30000)
    return () => clearInterval(iv)
  }, [fetchExternal, fetchPlatform, fetchGrouped])

  // ── Form actions ───────────────────────────────────────────────
  const resetForm = () => {
    setFormType('http'); setFormName(''); setFormEnv(''); setFormDesc('')
    setFormConfig({}); setFormTimeout(10); setFormInterval(60)
    setEditId(null); setTestResult(null)
    setFormGroupName('Default'); setFormCatalogType(''); setFormCategory(''); setFormTags([]); setFormTagInput('')
    setFormMonitoringMode('synthetic_only'); setFormMetricsEnabled(false)
    setFormLogsEnabled(false); setFormTracesEnabled(false)
    setFormTelemetryServiceKey(''); setShowTelemetryWarning(false)
  }

  const openCreate = () => { resetForm(); setView('create') }

  const openEdit = (svc: ExternalServiceData) => {
    setEditId(svc.id); setFormType(svc.service_type); setFormName(svc.name)
    setFormEnv(svc.environment || ''); setFormDesc(svc.description || '')
    setFormConfig(svc.config || {}); setFormTimeout(svc.timeout_seconds)
    setFormInterval(svc.check_interval_seconds); setTestResult(null)
    setFormGroupName(svc.group_name || 'Default'); setFormCatalogType(svc.catalog_type || ''); setFormCategory(svc.category || '')
    setFormTags(svc.tags && Array.isArray(svc.tags) ? svc.tags : []); setFormTagInput('')
    setFormMonitoringMode(svc.monitoring_mode || 'synthetic_only')
    setFormMetricsEnabled(svc.metrics_enabled || false)
    setFormLogsEnabled(svc.logs_enabled || false)
    setFormTracesEnabled(svc.traces_enabled || false)
    setFormTelemetryServiceKey(svc.telemetry_service_key || '')
    setShowTelemetryWarning(false)
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
    const isTelemetry = formMonitoringMode === 'telemetry_enabled'
    const body = {
      name: formName, service_type: formType, environment: formEnv || null,
      description: formDesc || null, config: formConfig,
      timeout_seconds: formTimeout, check_interval_seconds: formInterval, enabled: true,
      catalog_type: formCatalogType || null, category: formCategory || null,
      tags: formTags.length > 0 ? formTags : null,
      monitoring_mode: formMonitoringMode,
      synthetic_enabled: true,
      metrics_enabled: isTelemetry ? formMetricsEnabled : false,
      logs_enabled: isTelemetry ? formLogsEnabled : false,
      traces_enabled: isTelemetry ? formTracesEnabled : false,
      telemetry_attached: isTelemetry,
      telemetry_source_type: isTelemetry ? 'collector' : null,
      telemetry_service_key: isTelemetry ? (formTelemetryServiceKey || null) : null,
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
  const groupNames = [...new Set(extServices.map(s => s.group_name).filter(Boolean))] as string[]
  const hasActiveFilters = !!(filterSearch || filterCatalogType || filterCategory || filterGroupName)

  // Client-side filtering
  const filteredServices = extServices.filter(svc => {
    if (filterSearch && !svc.name.toLowerCase().includes(filterSearch.toLowerCase())) return false
    if (filterCatalogType && svc.catalog_type !== filterCatalogType) return false
    if (filterCategory && svc.category !== filterCategory) return false
    if (filterGroupName && svc.group_name !== filterGroupName) return false
    return true
  })

  const clearFilters = () => { setFilterSearch(''); setFilterCatalogType(''); setFilterCategory(''); setFilterGroupName('') }

  // ── Grouped view helpers (Task 22) ──
  const toggleGroup = (name: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }
  const expandAllGroups = () => setExpandedGroups(new Set(groupedData.map(g => g.group_name)))
  const collapseAllGroups = () => setExpandedGroups(new Set())

  // ── Import handlers ──────────────────────────────────────
  const resetImport = () => {
    setImportFile(null); setImportStep('upload'); setImportPreview(null); setImportResult(null)
  }
  const openImportModal = () => { resetImport(); setShowImportModal(true) }
  const closeImportModal = () => { setShowImportModal(false); resetImport() }

  const downloadTemplate = async (format: 'csv' | 'json') => {
    try {
      const res = await fetch(`/api/external-services/import/template/${format}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `import_template.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (e) { console.error('Template download error:', e) }
  }

  const resetBulkHttp = () => {
    setBulkBaseUrl(''); setBulkMethod('GET'); setBulkEnv(''); setBulkTimeout(10); setBulkInterval(60)
    setBulkEnabled(true); setBulkGroupName('Default'); setBulkCatalogType('REST_API'); setBulkCategory(''); setBulkTags([]); setBulkTagInput('')
    setBulkAuthType(''); setBulkAuthValue('')
    setBulkItems([{name: '', path: ''}]); setBulkPasteMode(false); setBulkPasteText('')
    setBulkStep('form'); setBulkPreview(null); setBulkResult(null); setBulkLoading(false)
  }

  const openBulkHttp = () => { resetBulkHttp(); setView('bulk-http') }

  const bulkAddItem = () => setBulkItems([...bulkItems, {name: '', path: ''}])

  const bulkRemoveItem = (idx: number) => {
    if (bulkItems.length <= 1) return
    setBulkItems(bulkItems.filter((_: any, i: number) => i !== idx))
  }

  const bulkUpdateItem = (idx: number, field: string, value: string) => {
    setBulkItems(bulkItems.map((item: any, i: number) => i === idx ? {...item, [field]: value} : item))
  }

  const bulkParsePaste = () => {
    const lines = bulkPasteText.split('\n').filter((l: string) => l.trim())
    const parsed = lines.map((line: string) => {
      const parts = line.split(',').map((s: string) => s.trim())
      if (parts.length >= 2) return { name: parts[0], path: parts[1], method: parts[2] || '' }
      // Single column: use as path, auto-generate name
      const p = parts[0]
      const autoName = p.replace(/^\//,'').replace(/\//g,' ').replace(/[_-]/g,' ')
        .split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') + ' API'
      return { name: autoName, path: p }
    })
    if (parsed.length > 0) {
      setBulkItems(parsed)
      setBulkPasteMode(false)
      setBulkPasteText('')
    }
  }

  const buildBulkPayload = (dryRun: boolean) => ({
    dry_run: dryRun,
    common: {
      base_url: bulkBaseUrl || undefined,
      method: bulkMethod,
      environment: bulkEnv || undefined,
      timeout_seconds: bulkTimeout,
      check_interval_seconds: bulkInterval,
      enabled: bulkEnabled,
      group_name: bulkGroupName || 'Default',
      catalog_type: bulkCatalogType || 'REST_API',
      category: bulkCategory || undefined,
      tags: bulkTags.length > 0 ? bulkTags : undefined,
      auth_type: bulkAuthType || undefined,
      auth_value: bulkAuthValue || undefined,
    },
    items: bulkItems.filter((it: any) => it.name.trim() || it.path.trim()).map((it: any) => ({
      name: it.name.trim(),
      path: it.path.trim(),
      ...(it.method ? { method: it.method.trim().toUpperCase() } : {}),
    })),
  })

  const handleBulkPreview = async () => {
    setBulkLoading(true)
    try {
      const res = await fetch('/api/external-services/bulk-http', {
        method: 'POST', headers: apiHeaders,
        body: JSON.stringify(buildBulkPayload(true)),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setBulkPreview({ error: err.detail || `Server error ${res.status}` })
      } else {
        setBulkPreview(await res.json())
      }
      setBulkStep('preview')
    } catch (e: any) {
      setBulkPreview({ error: e.message })
      setBulkStep('preview')
    }
    setBulkLoading(false)
  }

  const handleBulkConfirm = async () => {
    setBulkLoading(true)
    try {
      const res = await fetch('/api/external-services/bulk-http', {
        method: 'POST', headers: apiHeaders,
        body: JSON.stringify(buildBulkPayload(false)),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setBulkResult({ error: err.detail || `Server error ${res.status}` })
      } else {
        setBulkResult(await res.json())
        await fetchExternal()
      }
      setBulkStep('result')
    } catch (e: any) {
      setBulkResult({ error: e.message })
      setBulkStep('result')
    }
    setBulkLoading(false)
  }

  const handleImportValidate = async () => {
    if (!importFile) return
    setImportLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      const res = await fetch('/api/external-services/import?dry_run=true', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setImportPreview({ error: err.detail || `Server error ${res.status}` })
      } else {
        setImportPreview(await res.json())
      }
      setImportStep('preview')
    } catch (e: any) {
      setImportPreview({ error: e.message })
      setImportStep('preview')
    }
    setImportLoading(false)
  }

  const handleImportConfirm = async () => {
    if (!importFile) return
    setImportLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      const res = await fetch('/api/external-services/import?dry_run=false', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setImportResult({ error: err.detail || `Server error ${res.status}` })
      } else {
        setImportResult(await res.json())
        await fetchExternal()
      }
      setImportStep('result')
    } catch (e: any) {
      setImportResult({ error: e.message })
      setImportStep('result')
    }
    setImportLoading(false)
  }

  const platform = platformData?.platform ?? { services: [], total: 0, up: 0, down: 0 }

  // ── Create/Edit Form View ──────────────────────────────────────

  // ── Bulk HTTP View ───────────────────────────────────────────
  if (view === 'bulk-http') {
    const filledItems = bulkItems.filter((it: any) => it.name.trim() || it.path.trim())
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center gap-3">
          <button onClick={() => { setView('list'); resetBulkHttp() }} className="p-2 rounded-lg hover:bg-gray-700/50 text-gray-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">Multiple APIs</h1>
            <p className="text-gray-400 text-sm">Create multiple HTTP services in one operation</p>
          </div>
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

        {bulkStep === 'form' && (
          <div className="space-y-6">
            {/* Common Settings */}
            <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-5 space-y-4">
              <h3 className="text-white font-medium flex items-center gap-2"><Globe className="w-4 h-4 text-blue-400" /> Common Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm text-gray-400 mb-1">Base URL <span className="text-gray-600">(optional)</span></label>
                  <input value={bulkBaseUrl} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkBaseUrl(e.target.value)} readOnly={!canManage}
                    placeholder="https://api.company.com" className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                  <p className="text-gray-600 text-xs mt-1">If set, endpoint paths will be appended to this URL</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Method</label>
                  <select value={bulkMethod} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkMethod(e.target.value)} disabled={!canManage}
                    className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`}>
                    {['GET','POST','PUT','DELETE','PATCH','HEAD','OPTIONS'].map((m: string) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Environment</label>
                  <input value={bulkEnv} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkEnv(e.target.value)} readOnly={!canManage}
                    placeholder="production" className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Timeout (s)</label>
                  <input type="number" value={bulkTimeout} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkTimeout(Number(e.target.value))} readOnly={!canManage}
                    min={1} max={120} className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Check Interval (s)</label>
                  <input type="number" value={bulkInterval} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkInterval(Number(e.target.value))} readOnly={!canManage}
                    min={10} max={86400} className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Catalog Type</label>
                  <select value={bulkCatalogType} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkCatalogType(e.target.value)} disabled={!canManage}
                    className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`}>
                    {CATALOG_TYPE_OPTIONS.map((o: {value:string;label:string}) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Category</label>
                  <input value={bulkCategory} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkCategory(e.target.value)} readOnly={!canManage}
                    placeholder="payments, auth, mobile..." className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                </div>
              </div>
              {/* Tags */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Common Tags</label>
                <div className="flex items-center gap-2">
                  <input value={bulkTagInput} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkTagInput(e.target.value)} readOnly={!canManage}
                    onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                      if (canManage && e.key === 'Enter' && bulkTagInput.trim()) {
                        e.preventDefault()
                        const t = bulkTagInput.trim().toLowerCase()
                        if (!bulkTags.includes(t)) setBulkTags([...bulkTags, t])
                        setBulkTagInput('')
                      }
                    }}
                    placeholder="Press Enter to add tag" className={`flex-1 bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none text-sm ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                </div>
                {bulkTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {bulkTags.map((t: string) => (
                      <span key={t} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-400/10 text-blue-400">
                        {t}
                        <button onClick={() => canManage && setBulkTags(bulkTags.filter((x: string) => x !== t))} disabled={!canManage}
                          className={canManage ? "hover:text-blue-300" : "cursor-not-allowed opacity-50"}>
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {/* Auth */}
              <details className="text-sm">
                <summary className="text-gray-400 cursor-pointer hover:text-gray-300">Authentication (optional)</summary>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Auth Type</label>
                    <select value={bulkAuthType} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkAuthType(e.target.value)} disabled={!canManage}
                      className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`}>
                      <option value="">None</option>
                      <option value="bearer">Bearer Token</option>
                      <option value="api_key">API Key</option>
                      <option value="basic">Basic Auth</option>
                    </select>
                  </div>
                  {bulkAuthType && (
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Auth Value</label>
                      <input value={bulkAuthValue} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkAuthValue(e.target.value)} readOnly={!canManage}
                        placeholder="Token or credentials" className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                    </div>
                  )}
                </div>
              </details>
              {/* Enabled toggle */}
              <div className="flex items-center gap-3">
                <button onClick={() => canManage && setBulkEnabled(!bulkEnabled)} disabled={!canManage}
                  className={`relative w-10 h-5 rounded-full transition-colors ${!canManage ? 'bg-gray-700 cursor-not-allowed opacity-50' : bulkEnabled ? 'bg-emerald-500' : 'bg-gray-600'}`}>
                  <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${bulkEnabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
                </button>
                <span className="text-sm text-gray-400">Enable monitoring after creation</span>
              </div>
            </div>

            {/* Endpoints List */}
            <div className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-medium flex items-center gap-2"><Layers className="w-4 h-4 text-emerald-400" /> API Endpoints</h3>
                <div className="flex items-center gap-2">
                  <button onClick={() => canManage && setBulkPasteMode(!bulkPasteMode)} disabled={!canManage}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border transition-colors ${canManage ? 'border-gray-600 text-gray-400 hover:text-white hover:border-gray-500' : 'border-gray-700 text-gray-600 cursor-not-allowed opacity-50'}`}>
                    <Copy className="w-3.5 h-3.5" /> {bulkPasteMode ? 'Manual Entry' : 'Quick Paste'}
                  </button>
                  {!bulkPasteMode && (
                    <button onClick={canManage ? bulkAddItem : undefined} disabled={!canManage}
                      title={!canManage ? 'Only administrators can create services' : ''}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${canManage ? 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white' : 'bg-gray-800 text-gray-600 cursor-not-allowed opacity-50'}`}>
                      <Plus className="w-3.5 h-3.5" /> Add Row
                    </button>
                  )}
                </div>
              </div>

              {bulkPasteMode ? (
                <div className="space-y-3">
                  <p className="text-gray-500 text-xs">Paste one API per line. Format: <code className="text-gray-400">Name, /path</code> or just <code className="text-gray-400">/path</code> (name auto-generated)</p>
                  <textarea value={bulkPasteText} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => canManage && setBulkPasteText(e.target.value)} readOnly={!canManage}
                    rows={8} placeholder={"Auth API, /auth\nPayments API, /payments\nCustomers API, /customers\n/orders\n/inventory"}
                    className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none font-mono text-sm ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                  <button onClick={canManage ? bulkParsePaste : undefined} disabled={!canManage || !bulkPasteText.trim()}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors">
                    Parse {bulkPasteText.split('\n').filter((l: string) => l.trim()).length} lines
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {/* Header */}
                  <div className="grid grid-cols-12 gap-2 text-xs text-gray-500 px-1">
                    <div className="col-span-1">#</div>
                    <div className="col-span-4">Service Name</div>
                    <div className="col-span-5">Path / URL</div>
                    <div className="col-span-1">Method</div>
                    <div className="col-span-1"></div>
                  </div>
                  {/* Rows */}
                  {bulkItems.map((item: any, idx: number) => (
                    <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-1 text-gray-600 text-sm text-center">{idx + 1}</div>
                      <div className="col-span-4">
                        <input value={item.name} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && bulkUpdateItem(idx, 'name', e.target.value)} readOnly={!canManage}
                          placeholder="API name" className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-2.5 py-1.5 text-sm placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                      </div>
                      <div className="col-span-5">
                        <input value={item.path} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && bulkUpdateItem(idx, 'path', e.target.value)} readOnly={!canManage}
                          placeholder="/endpoint or https://..." className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-2.5 py-1.5 text-sm placeholder-gray-600 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} />
                      </div>
                      <div className="col-span-1">
                        <input value={item.method || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && bulkUpdateItem(idx, 'method', e.target.value)} readOnly={!canManage}
                          placeholder="" className={`w-full bg-gray-900/50 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-center placeholder-gray-700 focus:outline-none ${canManage ? 'text-white focus:border-blue-500' : 'text-gray-500 cursor-not-allowed'}`} title="Override method (leave empty for common)" />
                      </div>
                      <div className="col-span-1 flex justify-center">
                        <button onClick={() => canManage && bulkRemoveItem(idx)} disabled={!canManage || bulkItems.length <= 1}
                          title={!canManage ? 'Only administrators can modify services' : ''}
                          className={`p-1 rounded transition-colors disabled:opacity-30 ${canManage ? 'text-gray-600 hover:text-red-400' : 'text-gray-700 cursor-not-allowed'}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                  {/* Quick add more */}
                  <button onClick={canManage ? bulkAddItem : undefined} disabled={!canManage}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className={`w-full py-2 border border-dashed rounded-lg text-sm transition-colors ${canManage ? 'border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600' : 'border-gray-800 text-gray-700 cursor-not-allowed opacity-50'}`}>
                    + Add another endpoint
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <p className="text-gray-500 text-sm">{filledItems.length} endpoint{filledItems.length !== 1 ? 's' : ''} ready</p>
              <div className="flex items-center gap-3">
                <button onClick={() => { setView('list'); resetBulkHttp() }}
                  className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">Cancel</button>
                <button onClick={canManage ? handleBulkPreview : undefined} disabled={!canManage || filledItems.length === 0 || bulkLoading}
                  title={!canManage ? 'Only administrators can create services' : ''}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
                  {bulkLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  Validate & Preview
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Preview Step */}
        {bulkStep === 'preview' && bulkPreview && (
          <div className="space-y-5">
            {bulkPreview.error ? (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                <p className="font-medium">Validation failed</p>
                <p className="text-sm mt-1">{bulkPreview.error}</p>
              </div>
            ) : (
              <>
                {/* Summary cards */}
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { label: 'Total', value: bulkPreview.total_received, color: 'text-gray-300' },
                    { label: 'Valid', value: bulkPreview.valid_count, color: 'text-green-400' },
                    { label: 'Invalid', value: bulkPreview.invalid_count, color: 'text-red-400' },
                    { label: 'Duplicates', value: bulkPreview.duplicate_count, color: 'text-yellow-400' },
                  ].map((c: { label: string; value: number; color: string }) => (
                    <div key={c.label} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 text-center">
                      <p className="text-gray-500 text-xs">{c.label}</p>
                      <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
                    </div>
                  ))}
                </div>

                {/* Valid preview table */}
                {bulkPreview.valid_preview?.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Services to be created:</p>
                    <div className="max-h-60 overflow-y-auto bg-gray-900/50 rounded-lg border border-gray-700/50">
                      <table className="w-full text-sm">
                        <thead><tr className="border-b border-gray-700/50">
                          <th className="text-left p-2 text-gray-500 text-xs">#</th>
                          <th className="text-left p-2 text-gray-500 text-xs">Name</th>
                          <th className="text-left p-2 text-gray-500 text-xs">URL</th>
                          <th className="text-left p-2 text-gray-500 text-xs">Method</th>
                        </tr></thead>
                        <tbody>
                          {bulkPreview.valid_preview.map((s: any) => (
                            <tr key={s.row} className="border-b border-gray-700/30">
                              <td className="p-2 text-gray-500">{s.row}</td>
                              <td className="p-2 text-white">{s.name}</td>
                              <td className="p-2 text-gray-400 truncate max-w-[300px]">{s.url}</td>
                              <td className="p-2 text-gray-500">{s.method}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Errors */}
                {bulkPreview.errors?.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Issues found:</p>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {bulkPreview.errors.map((e: any, i: number) => (
                        <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                          <span className="font-medium">#{e.row}: {e.name}</span>{' \u2014 '}{e.errors?.join('; ')}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Actions */}
            <div className="flex justify-between">
              <button onClick={() => { setBulkStep('form'); setBulkPreview(null) }}
                className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">\u2190 Back</button>
              <div className="flex gap-3">
                <button onClick={() => { setView('list'); resetBulkHttp() }}
                  className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">Cancel</button>
                {bulkPreview && !bulkPreview.error && bulkPreview.valid_count > 0 && (
                  <button onClick={canManage ? handleBulkConfirm : undefined} disabled={!canManage || bulkLoading}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className="flex items-center gap-2 px-5 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
                    {bulkLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    Create {bulkPreview.valid_count} Service{bulkPreview.valid_count !== 1 ? 's' : ''}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Result Step */}
        {bulkStep === 'result' && bulkResult && (
          <div className="space-y-5">
            {bulkResult.error ? (
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                <p className="font-medium">Creation failed</p>
                <p className="text-sm mt-1">{bulkResult.error}</p>
              </div>
            ) : (
              <>
                <div className={`p-4 rounded-lg border ${bulkResult.created_count > 0 ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className={`w-5 h-5 ${bulkResult.created_count > 0 ? 'text-green-400' : 'text-yellow-400'}`} />
                    <span className={`font-medium ${bulkResult.created_count > 0 ? 'text-green-400' : 'text-yellow-400'}`}>Bulk creation complete</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div><span className="text-gray-500">Created:</span> <span className="text-green-400 font-medium">{bulkResult.created_count}</span></div>
                    <div><span className="text-gray-500">Skipped:</span> <span className="text-yellow-400 font-medium">{bulkResult.skipped_count}</span></div>
                    <div><span className="text-gray-500">Invalid:</span> <span className="text-red-400 font-medium">{bulkResult.invalid_count}</span></div>
                  </div>
                </div>

                {bulkResult.created_services?.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Created services:</p>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {bulkResult.created_services.map((s: any) => (
                        <div key={s.id} className="flex items-center gap-2 p-2 bg-green-500/5 rounded text-sm border border-green-500/10">
                          <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                          <span className="text-white">{s.name}</span>
                          <span className="text-gray-500 truncate ml-auto max-w-[250px]">{s.url}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {bulkResult.errors?.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Issues:</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {bulkResult.errors.map((e: any, i: number) => (
                        <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-red-500/10 text-red-400'}`}>
                          <span className="font-medium">{e.name}</span>{' \u2014 '}{e.errors?.join('; ')}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="flex justify-end">
              <button onClick={() => { setView('list'); resetBulkHttp() }}
                className="px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 font-medium transition-colors">Done</button>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (view === 'create' || view === 'edit') {
    const baseFieldsValid = formName.trim() && (
      formType === 'http' ? !!formConfig.url :
      formType === 'postgresql' ? !!(formConfig.host && formConfig.database_name && formConfig.username) : false
    )
    const telemetryValid = formMonitoringMode === 'synthetic_only' ||
      ((formMetricsEnabled || formLogsEnabled || formTracesEnabled) && formTelemetryServiceKey.trim() !== '')
    const isValid = baseFieldsValid && telemetryValid
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
              <label className="block text-sm font-medium text-gray-300 mb-1">Group Name</label>
              <input type="text" value={formGroupName} onChange={e => setFormGroupName(e.target.value)}
                placeholder="Default" className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm" />
              <p className="text-gray-500 text-xs mt-1">Group for organizing services (e.g., Payments, Infrastructure)</p>
            </div>
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

        {/* ── Monitoring Mode ── */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700/50 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
            <Radio className="w-5 h-5 text-blue-400" /> Monitoring Mode
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <button type="button" onClick={() => {
                if (formMonitoringMode === 'telemetry_enabled' && view === 'edit') {
                  setShowTelemetryWarning(true)
                }
                setFormMonitoringMode('synthetic_only')
                setFormMetricsEnabled(false); setFormLogsEnabled(false); setFormTracesEnabled(false)
                setFormTelemetryServiceKey('')
              }}
              className={`p-4 rounded-lg border-2 transition-all text-left ${formMonitoringMode === 'synthetic_only' ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
              <p className="text-white font-semibold text-sm">Synthetic monitoring only</p>
              <p className="text-gray-400 text-xs mt-1">Availability, latency, SSL, health checks</p>
            </button>
            <button type="button" onClick={() => {
                setFormMonitoringMode('telemetry_enabled')
                setShowTelemetryWarning(false)
              }}
              className={`p-4 rounded-lg border-2 transition-all text-left ${formMonitoringMode === 'telemetry_enabled' ? 'border-cyan-500 bg-cyan-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
              <p className="text-white font-semibold text-sm">Advanced monitoring (with telemetry)</p>
              <p className="text-gray-400 text-xs mt-1">Metrics, logs, traces via collector</p>
            </button>
          </div>

          {/* Helper text */}
          <div className={`flex items-start gap-2 px-3 py-2.5 rounded-lg text-sm ${formMonitoringMode === 'synthetic_only' ? 'bg-blue-500/5 border border-blue-500/20' : 'bg-cyan-500/5 border border-cyan-500/20'}`}>
            <Info className={`w-4 h-4 mt-0.5 flex-shrink-0 ${formMonitoringMode === 'synthetic_only' ? 'text-blue-400' : 'text-cyan-400'}`} />
            <p className={formMonitoringMode === 'synthetic_only' ? 'text-blue-300' : 'text-cyan-300'}>
              {formMonitoringMode === 'synthetic_only'
                ? 'This service will be monitored using synthetic checks only (availability, latency, SSL, health).'
                : 'This service will receive real telemetry data (metrics, logs, traces) via a collector.'}
            </p>
          </div>

          {/* Warning when switching from telemetry to synthetic in edit mode */}
          {showTelemetryWarning && formMonitoringMode === 'synthetic_only' && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-400" />
              <p className="text-amber-300 text-sm">
                <span className="font-medium">Warning:</span> Telemetry configuration will be disabled. Metrics, logs, and traces collection will stop for this service.
              </p>
            </div>
          )}
        </div>

        {/* ── Telemetry Configuration (only when telemetry_enabled) ── */}
        {formMonitoringMode === 'telemetry_enabled' && (
          <div className="bg-gray-800/50 rounded-lg border border-cyan-500/30 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
              <Waypoints className="w-5 h-5 text-cyan-400" /> Telemetry Configuration
            </h2>
            <p className="text-gray-400 text-xs -mt-1">Select which telemetry signals this service should receive. At least one must be enabled.</p>

            {/* Signal toggles */}
            <div className="grid grid-cols-3 gap-3">
              {/* Metrics toggle */}
              <button type="button" onClick={() => setFormMetricsEnabled(!formMetricsEnabled)}
                className={`p-3 rounded-lg border-2 transition-all text-left ${formMetricsEnabled ? 'border-emerald-500 bg-emerald-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <BarChart3 className={`w-5 h-5 ${formMetricsEnabled ? 'text-emerald-400' : 'text-gray-500'}`} />
                  {formMetricsEnabled ? <ToggleRight className="w-5 h-5 text-emerald-400" /> : <ToggleLeft className="w-5 h-5 text-gray-500" />}
                </div>
                <p className={`font-semibold text-sm ${formMetricsEnabled ? 'text-emerald-300' : 'text-gray-400'}`}>Metrics</p>
                <p className="text-gray-500 text-xs">Prometheus</p>
              </button>

              {/* Logs toggle */}
              <button type="button" onClick={() => setFormLogsEnabled(!formLogsEnabled)}
                className={`p-3 rounded-lg border-2 transition-all text-left ${formLogsEnabled ? 'border-amber-500 bg-amber-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <FileText className={`w-5 h-5 ${formLogsEnabled ? 'text-amber-400' : 'text-gray-500'}`} />
                  {formLogsEnabled ? <ToggleRight className="w-5 h-5 text-amber-400" /> : <ToggleLeft className="w-5 h-5 text-gray-500" />}
                </div>
                <p className={`font-semibold text-sm ${formLogsEnabled ? 'text-amber-300' : 'text-gray-400'}`}>Logs</p>
                <p className="text-gray-500 text-xs">Loki</p>
              </button>

              {/* Traces toggle */}
              <button type="button" onClick={() => setFormTracesEnabled(!formTracesEnabled)}
                className={`p-3 rounded-lg border-2 transition-all text-left ${formTracesEnabled ? 'border-violet-500 bg-violet-500/10' : 'border-gray-700 hover:border-gray-600 bg-gray-800/50'}`}>
                <div className="flex items-center justify-between mb-1">
                  <Waypoints className={`w-5 h-5 ${formTracesEnabled ? 'text-violet-400' : 'text-gray-500'}`} />
                  {formTracesEnabled ? <ToggleRight className="w-5 h-5 text-violet-400" /> : <ToggleLeft className="w-5 h-5 text-gray-500" />}
                </div>
                <p className={`font-semibold text-sm ${formTracesEnabled ? 'text-violet-300' : 'text-gray-400'}`}>Traces</p>
                <p className="text-gray-500 text-xs">OpenTelemetry</p>
              </button>
            </div>

            {/* Validation: at least one signal */}
            {!formMetricsEnabled && !formLogsEnabled && !formTracesEnabled && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <p className="text-red-300 text-sm">At least one telemetry signal must be enabled.</p>
              </div>
            )}

            {/* Telemetry Service Key */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Telemetry Service Key *</label>
              <input type="text" value={formTelemetryServiceKey} onChange={e => setFormTelemetryServiceKey(e.target.value)}
                placeholder="e.g. my-api-production"
                className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500" />
              <p className="text-gray-500 text-xs mt-1.5">Unique identifier used by collectors to associate telemetry with this service.</p>
            </div>

            {/* Validation: service key required */}
            {(formMetricsEnabled || formLogsEnabled || formTracesEnabled) && !formTelemetryServiceKey.trim() && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <p className="text-red-300 text-sm">Telemetry Service Key is required when telemetry signals are enabled.</p>
              </div>
            )}
          </div>
        )}

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
          <div className="flex items-center gap-3">
            {/* View mode toggle (Task 22) */}
            <div className="flex items-center bg-gray-800/60 rounded-lg p-0.5">
              <button onClick={() => setGroupViewMode('grouped')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${groupViewMode === 'grouped' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}>
                <FolderOpen className="w-3.5 h-3.5" /> Grouped
              </button>
              <button onClick={() => setGroupViewMode('list')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${groupViewMode === 'list' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}>
                <Layers className="w-3.5 h-3.5" /> Flat List
              </button>
            </div>
            <button onClick={openImportModal}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-gray-600 text-gray-300 hover:text-white hover:border-gray-500 font-medium transition-colors">
              <Upload className="w-4 h-4" /> Import
            </button>
            <button onClick={openBulkHttp}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-emerald-600/50 text-emerald-400 hover:text-emerald-300 hover:border-emerald-500/60 font-medium transition-colors">
              <Layers className="w-4 h-4" /> Multiple APIs
            </button>
            <button onClick={openCreate}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-500 font-medium transition-colors shadow-lg shadow-blue-600/20">
              <Plus className="w-4 h-4" /> Connect Service
            </button>
          </div>
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
                {/* Group filter (Task 22) */}
                <select
                  value={filterGroupName}
                  onChange={e => setFilterGroupName(e.target.value)}
                  className="px-3 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Groups</option>
                  {groupNames.map(gn => <option key={gn} value={gn}>{gn}</option>)}
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

          {/* ── GROUPED VIEW (Task 22) ─────────────────────── */}
          {groupViewMode === 'grouped' && groupedData.length > 0 && (
            <div className="space-y-4">
              {/* Group controls */}
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-400">
                  {groupedData.length} group{groupedData.length !== 1 ? 's' : ''} &middot; {groupedData.reduce((a, g) => a + g.total, 0)} services
                </p>
                <div className="flex items-center gap-2">
                  <button onClick={expandAllGroups} className="text-xs text-gray-400 hover:text-white transition-colors">Expand all</button>
                  <span className="text-gray-600">|</span>
                  <button onClick={collapseAllGroups} className="text-xs text-gray-400 hover:text-white transition-colors">Collapse all</button>
                </div>
              </div>

              {/* Group Cards */}
              {groupedData.map(group => {
                const isExpanded = expandedGroups.has(group.group_name)
                return (
                  <div key={group.group_name} className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
                    {/* Group Header */}
                    <button
                      className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30 transition-colors"
                      onClick={() => toggleGroup(group.group_name)}
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded
                          ? <ChevronDown className="w-5 h-5 text-gray-400" />
                          : <ChevronRight className="w-5 h-5 text-gray-400" />}
                        {isExpanded
                          ? <FolderOpen className="w-5 h-5 text-emerald-400" />
                          : <Folder className="w-5 h-5 text-gray-400" />}
                        <div className="text-left">
                          <h3 className="text-white font-semibold text-sm">{group.group_name}</h3>
                          <p className="text-gray-500 text-xs mt-0.5">
                            {group.total} service{group.total !== 1 ? 's' : ''}
                            {group.up > 0 && <span className="text-green-400 ml-2">{group.up} up</span>}
                            {group.down > 0 && <span className="text-red-400 ml-2">{group.down} down</span>}
                            {group.total - group.up - group.down > 0 && <span className="text-yellow-400 ml-2">{group.total - group.up - group.down} other</span>}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <GroupHealthBadge status={group.status} />
                        {/* Health bar */}
                        <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden flex">
                          {group.up > 0 && <div className="bg-green-500 h-full" style={{ width: `${(group.up / group.total) * 100}%` }} />}
                          {group.total - group.up - group.down > 0 && <div className="bg-yellow-500 h-full" style={{ width: `${((group.total - group.up - group.down) / group.total) * 100}%` }} />}
                          {group.down > 0 && <div className="bg-red-500 h-full" style={{ width: `${(group.down / group.total) * 100}%` }} />}
                        </div>
                      </div>
                    </button>

                    {/* Expanded Service List */}
                    {isExpanded && (
                      <div className="border-t border-gray-700/30">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-gray-700/30">
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Service</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Type</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Category</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Environment</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Status</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Latency</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Telemetry</th>
                              <th className="text-left px-4 py-2.5 text-gray-500 font-medium text-xs uppercase tracking-wider">Last Check</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.services.map(svc => (
                              <tr key={svc.id} className="border-b border-gray-700/20 hover:bg-gray-700/20 transition-colors">
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2.5">
                                    <div className={`p-1.5 rounded ${svc.enabled ? 'bg-emerald-400/10' : 'bg-gray-700/50'}`}>
                                      {svc.service_type === 'http'
                                        ? <Network className="w-3.5 h-3.5 text-violet-400" />
                                        : <Database className="w-3.5 h-3.5 text-orange-400" />}
                                    </div>
                                    <span className="text-white text-sm font-medium">{svc.name}</span>
                                  </div>
                                </td>
                                <td className="px-4 py-3"><CatalogBadge type={svc.catalog_type} /></td>
                                <td className="px-4 py-3 text-sm text-gray-400">{svc.category || <span className="text-gray-600">&ndash;</span>}</td>
                                <td className="px-4 py-3 text-sm text-gray-400">{svc.environment || <span className="text-gray-600">&ndash;</span>}</td>
                                <td className="px-4 py-3"><StatusBadge status={svc.enabled ? svc.status : 'unknown'} /></td>
                                <td className="px-4 py-3 text-sm text-gray-300">{svc.latency != null && svc.latency > 0 ? `${svc.latency.toFixed(0)}ms` : '-'}</td>
                                <td className="px-4 py-3"><TelemetryStatusBadge status={svc.telemetry_status} /></td>
                                <td className="px-4 py-3 text-sm text-gray-400">{svc.last_check ? new Date(svc.last_check).toLocaleString() : 'Never'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {groupViewMode === 'list' && (extServices.length === 0 ? (
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
                      <th className="text-left p-4 text-gray-400 font-medium">Monitoring</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Status</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Latency</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Last Check</th>
                      <th className="text-right p-4 text-gray-400 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredServices.length === 0 && hasActiveFilters && (
                      <tr><td colSpan={10} className="p-8 text-center text-gray-500">
                        <Search className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                        <p>No services match the current filters</p>
                        <button onClick={clearFilters} className="text-blue-400 hover:text-blue-300 text-sm mt-1">Clear filters</button>
                      </td></tr>
                    )}
                    {filteredServices.map(svc => (
                      <React.Fragment key={svc.id}>
                      <tr className={`border-b border-gray-700/30 hover:bg-gray-700/30 transition-colors cursor-pointer ${!svc.enabled ? 'opacity-50' : ''}`}
                        onClick={() => setExpandedServiceId(expandedServiceId === svc.id ? null : svc.id)}>
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
                        <td className="p-4"><MonitoringBadge svc={svc} /></td>
                        <td className="p-4"><StatusBadge status={svc.enabled ? svc.status : 'unknown'} /></td>
                        <td className="p-4 text-gray-300 text-sm">
                          {svc.last_response_time_ms != null ? `${svc.last_response_time_ms.toFixed(0)}ms` : '-'}
                        </td>
                        <td className="p-4 text-gray-400 text-sm">
                          {svc.last_check_at ? new Date(svc.last_check_at).toLocaleString() : 'Never'}
                        </td>
                        <td className="p-4" onClick={e => e.stopPropagation()}>
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
                      {expandedServiceId === svc.id && (
                        <tr className="bg-gray-900/40">
                          <td colSpan={10} className="p-0">
                            <MonitoringDetailPanel svc={svc} />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
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

      {/* ── BULK IMPORT MODAL ────────────────────────────────── */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-400/10 rounded-lg"><Upload className="w-5 h-5 text-blue-400" /></div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Import Services</h2>
                  <p className="text-gray-400 text-sm">Bulk import from CSV or JSON</p>
                </div>
              </div>
              <button onClick={closeImportModal} className="p-2 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Read-only banner for non-admin users */}
              {!canManage && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                  <Lock className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                  <p className="text-yellow-300 text-sm">
                    <span className="font-medium">View-only mode.</span> You can explore the configuration but only administrators can create or modify services.
                  </p>
                </div>
              )}

              {/* Step 1: Upload */}
              {importStep === 'upload' && (
                <>
                  {/* Templates */}
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-900/50 border border-gray-700/50">
                    <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span className="text-gray-400 text-sm">Download template:</span>
                    <button onClick={() => downloadTemplate('csv')} className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" /> CSV
                    </button>
                    <button onClick={() => downloadTemplate('json')} className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" /> JSON
                    </button>
                  </div>

                  {/* File input */}
                  <div className="space-y-3">
                    <label className="block">
                      <div className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${!canManage ? 'border-gray-700 bg-gray-800/30 cursor-not-allowed opacity-60' : importFile ? 'border-blue-500/50 bg-blue-500/5 cursor-pointer' : 'border-gray-600 hover:border-gray-500 cursor-pointer'}`}>
                        <input type="file" accept=".csv,.json" className="hidden" disabled={!canManage}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => { if (canManage && e.target.files?.[0]) setImportFile(e.target.files[0]) }} />
                        {importFile ? (
                          <div className="space-y-1">
                            <FileText className="w-8 h-8 text-blue-400 mx-auto" />
                            <p className="text-white font-medium">{importFile.name}</p>
                            <p className="text-gray-500 text-sm">{(importFile.size / 1024).toFixed(1)} KB</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <Upload className="w-8 h-8 text-gray-500 mx-auto" />
                            <p className="text-gray-300">Click to select a file</p>
                            <p className="text-gray-500 text-sm">Supports .csv and .json (max 1 MB, 200 services)</p>
                          </div>
                        )}
                      </div>
                    </label>
                  </div>

                  {/* Expected columns help */}
                  <details className="text-sm">
                    <summary className="text-gray-400 cursor-pointer hover:text-gray-300">Expected columns &amp; aliases</summary>
                    <div className="mt-2 p-3 bg-gray-900/50 rounded-lg border border-gray-700/50 text-gray-500 text-xs space-y-1">
                      <p><span className="text-gray-300">Required:</span> name, service_type (http | postgresql)</p>
                      <p><span className="text-gray-300">HTTP:</span> url, method, health_path, auth_type, auth_value</p>
                      <p><span className="text-gray-300">PostgreSQL:</span> host, port, database_name, username, password</p>
                      <p><span className="text-gray-300">Optional:</span> environment, description, timeout_seconds, check_interval_seconds, enabled, catalog_type, category, tags</p>
                      <p className="pt-1 border-t border-gray-700/30"><span className="text-gray-300">Aliases accepted:</span> type or serviceType &rarr; service_type &bull; target or endpoint &rarr; url &bull; catalogType &rarr; catalog_type &bull; timeout &rarr; timeout_seconds &bull; checkInterval &rarr; check_interval_seconds &bull; authType &rarr; auth_type &bull; authValue &rarr; auth_value</p>
                      <p><span className="text-gray-300">Delimiters:</span> CSV can use comma, semicolon, or tab as column separator (auto-detected)</p>
                      <p><span className="text-gray-300">Tags:</span> comma, semicolon, or pipe separated (e.g. &quot;critical,external,api&quot;)</p>
                      <p><span className="text-gray-300">Auth:</span> leave auth_type empty if not needed &mdash; do not use &quot;None&quot;</p>
                    </div>
                  </details>

                  {/* Action */}
                  <div className="flex justify-end gap-3 pt-2">
                    <button onClick={closeImportModal} className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">Cancel</button>
                    <button onClick={canManage ? handleImportValidate : undefined} disabled={!canManage || !importFile || importLoading}
                      title={!canManage ? 'Only administrators can import services' : ''}
                      className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
                      {importLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                      Validate & Preview
                    </button>
                  </div>
                </>
              )}

              {/* Step 2: Preview */}
              {importStep === 'preview' && importPreview && (
                <>
                  {importPreview.error ? (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                      <p className="font-medium">Validation failed</p>
                      <p className="text-sm mt-1">{importPreview.error}</p>
                    </div>
                  ) : (
                    <>
                      {/* Summary cards */}
                      <div className="grid grid-cols-4 gap-3">
                        {[
                          { label: 'Total', value: importPreview.total_received, color: 'text-gray-300' },
                          { label: 'Valid', value: importPreview.valid_count, color: 'text-green-400' },
                          { label: 'Invalid', value: importPreview.invalid_count, color: 'text-red-400' },
                          { label: 'Duplicates', value: importPreview.duplicate_count, color: 'text-yellow-400' },
                        ].map((c: { label: string; value: number; color: string }) => (
                          <div key={c.label} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700/50 text-center">
                            <p className="text-gray-500 text-xs">{c.label}</p>
                            <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
                          </div>
                        ))}
                      </div>

                      {/* Valid services preview */}
                      {importPreview.valid_preview?.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Services to be created:</p>
                          <div className="max-h-40 overflow-y-auto bg-gray-900/50 rounded-lg border border-gray-700/50">
                            <table className="w-full text-sm">
                              <thead><tr className="border-b border-gray-700/50">
                                <th className="text-left p-2 text-gray-500 text-xs">Row</th>
                                <th className="text-left p-2 text-gray-500 text-xs">Name</th>
                                <th className="text-left p-2 text-gray-500 text-xs">Type</th>
                                <th className="text-left p-2 text-gray-500 text-xs">Target</th>
                              </tr></thead>
                              <tbody>
                                {importPreview.valid_preview.map((s: any) => (
                                  <tr key={s.row} className="border-b border-gray-700/30">
                                    <td className="p-2 text-gray-500">{s.row}</td>
                                    <td className="p-2 text-white">{s.name}</td>
                                    <td className="p-2 text-gray-400">{s.service_type}</td>
                                    <td className="p-2 text-gray-500 truncate max-w-[200px]">{s.target}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Errors/skipped */}
                      {importPreview.errors?.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Issues found:</p>
                          <div className="max-h-40 overflow-y-auto space-y-1">
                            {importPreview.errors.map((e: any, i: number) => (
                              <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                                <span className="font-medium">Row {e.row}: {e.name}</span>
                                {' — '}{e.errors?.join('; ')}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* Actions */}
                  <div className="flex justify-between pt-2">
                    <button onClick={() => { setImportStep('upload'); setImportPreview(null) }}
                      className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">
                      ← Back
                    </button>
                    <div className="flex gap-3">
                      <button onClick={closeImportModal} className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors">Cancel</button>
                      {importPreview && !importPreview.error && importPreview.valid_count > 0 && (
                        <button onClick={canManage ? handleImportConfirm : undefined} disabled={!canManage || importLoading}
                          title={!canManage ? 'Only administrators can import services' : ''}
                          className="flex items-center gap-2 px-5 py-2 rounded-lg bg-green-600 text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
                          {importLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                          Import {importPreview.valid_count} Service{importPreview.valid_count !== 1 ? 's' : ''}
                        </button>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* Step 3: Result */}
              {importStep === 'result' && importResult && (
                <>
                  {importResult.error ? (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                      <p className="font-medium">Import failed</p>
                      <p className="text-sm mt-1">{importResult.error}</p>
                    </div>
                  ) : (
                    <>
                      <div className={`p-4 rounded-lg border ${importResult.created_count > 0 ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className={`w-5 h-5 ${importResult.created_count > 0 ? 'text-green-400' : 'text-yellow-400'}`} />
                          <span className={`font-medium ${importResult.created_count > 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                            Import complete
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <div><span className="text-gray-500">Created:</span> <span className="text-green-400 font-medium">{importResult.created_count}</span></div>
                          <div><span className="text-gray-500">Skipped:</span> <span className="text-yellow-400 font-medium">{importResult.skipped_count}</span></div>
                          <div><span className="text-gray-500">Invalid:</span> <span className="text-red-400 font-medium">{importResult.invalid_count}</span></div>
                        </div>
                      </div>

                      {/* Created services list */}
                      {importResult.created_services?.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Created services:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {importResult.created_services.map((s: any) => (
                              <div key={s.id} className="flex items-center gap-2 p-2 bg-green-500/5 rounded text-sm border border-green-500/10">
                                <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                                <span className="text-white">{s.name}</span>
                                <span className="text-gray-500">({s.service_type})</span>
                                <span className="text-gray-600 ml-auto">id={s.id}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {importResult.errors?.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Issues:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {importResult.errors.map((e: any, i: number) => (
                              <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-yellow-500/10 text-yellow-400' : 'bg-red-500/10 text-red-400'}`}>
                                <span className="font-medium">{e.name}</span>{' — '}{e.errors?.join('; ')}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  <div className="flex justify-end pt-2">
                    <button onClick={closeImportModal}
                      className="px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 font-medium transition-colors">
                      Done
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}