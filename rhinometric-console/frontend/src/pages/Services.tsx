import React, { useEffect, useState, useCallback } from 'react'
import {
  Server, AlertCircle, CheckCircle, Activity, Globe, Database, 
  Network, Plus, Trash2, Play, Power, PowerOff, Edit, ArrowLeft,
  RefreshCw, Clock, Lock, Search, Tag, X, Upload, FileText, Download, Layers, Copy,
  BarChart3, Waypoints, Info, AlertTriangle, Zap, HelpCircle, CircleDot, ChevronRight, ChevronDown, FolderOpen, Folder,
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
// CATALOG_META removed — replaced by CATALOG_DISPLAY in TypeBadge

// CatalogBadge removed — TypeBadge now handles catalog_type display

/* ─── Group Health Badge (Task 22) ──────────────────────────── */
function GroupHealthBadge({ status }: { status: string }) {
  const cfg: Record<string, { bg: string; text: string; ring: string; label: string }> = {
    healthy:  { bg: 'bg-success/10',  text: 'text-success',  ring: 'ring-green-500/20',  label: 'Healthy' },
    degraded: { bg: 'bg-warning/10', text: 'text-warning', ring: 'ring-yellow-500/20', label: 'Degraded' },
    down:     { bg: 'bg-critical/10',    text: 'text-critical',    ring: 'ring-red-500/20',    label: 'Down' },
  }
  const s = cfg[status] || cfg.down
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${s.bg} ${s.text} ${s.ring}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.text.replace('text-', 'bg-')}`} />
      {s.label}
    </span>
  )
}

// type Tab removed - platform tab hidden
type View = 'list' | 'grouped' | 'create' | 'edit' | 'bulk-http'

/* ─── Helpers ────────────────────────────────────────────────── */

const STATUS_BADGE: Record<string, { bg: string; text: string; Icon: any }> = {
  up:       { bg: 'bg-success/10', text: 'text-success', Icon: CheckCircle },
  down:     { bg: 'bg-critical/10',   text: 'text-critical',   Icon: AlertCircle },
  degraded: { bg: 'bg-warning/10',text: 'text-warning', Icon: AlertCircle },
  error:    { bg: 'bg-critical/10',   text: 'text-critical',   Icon: AlertCircle },
  unknown:  { bg: 'bg-surface/40',  text: 'text-muted',  Icon: Clock },
}

const TYPE_META: Record<string, { label: string; color: string; Icon: any }> = {
  http:       { label: 'HTTP / HTTPS', color: 'bg-violet-400/10 text-violet-400', Icon: Network },
  postgresql: { label: 'PostgreSQL',   color: 'bg-orange-400/10 text-orange-400', Icon: Database },
}

// Catalog-type display labels (rich classification)
const CATALOG_DISPLAY: Record<string, { label: string; color: string; Icon: any }> = {
  REST_API:         { label: 'REST API',     color: 'bg-info-bg text-info', Icon: Network },
  WEB_APP:          { label: 'Web App',      color: 'bg-pink-400/10 text-pink-400', Icon: Globe },
  SOAP_API:         { label: 'SOAP API',     color: 'bg-purple-400/10 text-purple-400', Icon: Network },
  WEBHOOK:          { label: 'Webhook',      color: 'bg-amber-400/10 text-amber-400', Icon: Zap },
  EXTERNAL_API:     { label: 'External API', color: 'bg-teal-400/10 text-teal-400', Icon: Globe },
  EXTERNAL_SERVICE: { label: 'External',     color: 'bg-teal-400/10 text-teal-400', Icon: Globe },
  DATABASE:         { label: 'Database',     color: 'bg-orange-400/10 text-orange-400', Icon: Database },
  INTERNAL_SERVICE: { label: 'Internal',     color: 'bg-cyan-400/10 text-cyan-400', Icon: Server },
  MOBILE_API:       { label: 'Mobile API',   color: 'bg-indigo-400/10 text-indigo-400', Icon: Network },
  MICROSERVICE:     { label: 'Service',      color: 'bg-violet-400/10 text-violet-400', Icon: Server },
  QUEUE:            { label: 'Queue',        color: 'bg-warning/10 text-warning', Icon: Layers },
  OTHER:            { label: 'Other',        color: 'bg-surface/40 text-muted', Icon: HelpCircle },
}

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_BADGE[status] || STATUS_BADGE.unknown
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${s.bg} ${s.text}`}>
      <s.Icon className="w-3 h-3" /> {status.toUpperCase()}
    </span>
  )
}

function TypeBadge({ type, catalogType }: { type: string; catalogType?: string | null }) {
  // Prefer catalog classification for display, fallback to monitoring type
  const ct = catalogType?.toUpperCase()
  if (ct && CATALOG_DISPLAY[ct]) {
    const d = CATALOG_DISPLAY[ct]
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${d.color}`}>
        <d.Icon className="w-3 h-3" /> {d.label}
      </span>
    )
  }
  const t = TYPE_META[type] || TYPE_META.http
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${t.color}`}>
      <t.Icon className="w-3 h-3" /> {t.label}
    </span>
  )
}

/* ─── Monitoring Badge ────────────────────────────────────── */
// @ts-expect-error MonitoringBadge preserved for future use
function MonitoringBadge({ svc }: { svc: ExternalServiceData }) {
  // Telemetry indicator dot color
  const dotColor = svc.monitoring_mode === 'synthetic_only'
    ? 'bg-gray-50'                   // grey = synthetic only
    : svc.telemetry_attached
      ? 'bg-success'                // green = telemetry attached
      : 'bg-info';                // blue = configured but not attached

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
      <span className="text-xs text-secondary whitespace-nowrap">{label}</span>
    </div>
  );
}

/* ─── Telemetry Status Badge ─────────────────────────────── */
const TELEMETRY_STATUS_CONFIG: Record<string, { color: string; bgColor: string; label: string; helper: string }> = {
  not_configured: {
    color: 'text-muted',
    bgColor: 'bg-surface/40',
    label: 'Not Configured',
    helper: '',
  },
  configured: {
    color: 'text-info',
    bgColor: 'bg-info/10',
    label: 'Configured',
    helper: 'Collector not connected yet. Run the collector with the configuration below.',
  },
  connected: {
    color: 'text-success',
    bgColor: 'bg-success/10',
    label: 'Connected',
    helper: 'Collector connected successfully.',
  },
  receiving_data: {
    color: 'text-success',
    bgColor: 'bg-success/10',
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
    color: 'text-critical',
    bgColor: 'bg-critical/10',
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
// @ts-expect-error TelemetryReadinessCard preserved for future telemetry edition
function TelemetryReadinessCard({ svc }: { svc: ExternalServiceData }) {
  const statusCfg = TELEMETRY_STATUS_CONFIG[svc.telemetry_status || 'not_configured'] || TELEMETRY_STATUS_CONFIG.not_configured;
  const lastTelemetry = svc.last_telemetry_at
    ? new Date(svc.last_telemetry_at).toLocaleString()
    : null;

  // Derive conservative per-signal state from overall telemetry_status
  function signalState(enabled: boolean): { label: string; color: string; dotColor: string } {
    if (!enabled) return { label: 'Disabled', color: 'text-muted', dotColor: 'bg-gray-50' };
    const status = svc.telemetry_status || 'not_configured';
    if (status === 'receiving_data' || status === 'connected') {
      return { label: 'Receiving', color: 'text-success', dotColor: 'bg-success' };
    }
    if (status === 'stale') {
      return { label: 'Stale', color: 'text-orange-400', dotColor: 'bg-orange-400' };
    }
    if (status === 'error') {
      return { label: 'Error', color: 'text-critical', dotColor: 'bg-critical' };
    }
    return { label: 'Awaiting data', color: 'text-info', dotColor: 'bg-info' };
  }

  const signals = [
    { label: 'Metrics', enabled: svc.metrics_enabled, Icon: BarChart3 },
    { label: 'Logs', enabled: svc.logs_enabled, Icon: FileText },
    { label: 'Traces', enabled: svc.traces_enabled, Icon: Waypoints },
  ];

  return (
    <div className="mt-5 bg-surface/40 rounded-lg border border-border/30 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-emerald-400" />
        <h4 className="text-sm font-semibold text-gray-900">Telemetry Readiness</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Collector Status */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Collector Status</p>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusCfg.color.replace('text-', 'bg-')}`} />
            <span className={`text-sm font-medium ${statusCfg.color}`}>{statusCfg.label}</span>
          </div>
        </div>

        {/* Last Telemetry */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Last Data Received</p>
          <div className="flex items-center gap-2">
            <Clock className={`w-3.5 h-3.5 ${lastTelemetry ? 'text-success' : 'text-muted'}`} />
            <span className={`text-sm ${lastTelemetry ? 'text-primary' : 'text-muted italic'}`}>
              {lastTelemetry || 'No telemetry received yet'}
            </span>
          </div>
        </div>

        {/* Signal Readiness */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Signal Readiness</p>
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
// @ts-expect-error SetupChecklist preserved for future telemetry edition
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
    <div className="mt-4 bg-surface/40 rounded-lg border border-border/30 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <CircleDot className="w-4 h-4 text-info" />
        <h4 className="text-sm font-semibold text-gray-900">Setup Checklist</h4>
        <span className="text-xs text-muted ml-auto">
          {steps.filter(s => s.done).length}/{steps.length} complete
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-2 py-0.5">
            {step.done ? (
              <CheckCircle className="w-3.5 h-3.5 text-success flex-shrink-0" />
            ) : (
              <div className="w-3.5 h-3.5 rounded-full border border-border flex-shrink-0" />
            )}
            <span className={`text-xs ${step.done ? 'text-secondary' : 'text-muted'}`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Troubleshooting Block (Task 20, Part 4) ────────────── */
// @ts-expect-error TroubleshootingBlock preserved for future telemetry edition
function TroubleshootingBlock({ svc }: { svc: ExternalServiceData }) {
  const status = svc.telemetry_status || 'not_configured';
  const messages: Record<string, { icon: string; color: string; bgColor: string; borderColor: string; text: string }> = {
    not_configured: {
      icon: 'info',
      color: 'text-muted',
      bgColor: 'bg-surface/40',
      borderColor: 'border-border/30',
      text: 'Enable telemetry for this service to attach a collector.',
    },
    configured: {
      icon: 'info',
      color: 'text-info',
      bgColor: 'bg-primary/10',
      borderColor: 'border-blue-500/20',
      text: 'Collector not connected yet. Run the collector with the configuration above.',
    },
    connected: {
      icon: 'check',
      color: 'text-success',
      bgColor: 'bg-success/10',
      borderColor: 'border-green-500/20',
      text: 'Telemetry is arriving correctly.',
    },
    receiving_data: {
      icon: 'check',
      color: 'text-success',
      bgColor: 'bg-success/10',
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
      color: 'text-critical',
      bgColor: 'bg-critical/10',
      borderColor: 'border-red-500/20',
      text: 'Telemetry delivery is failing. Verify token, service key, connectivity, and enabled signals.',
    },
  };

  const msg = messages[status] || messages.not_configured;

  return (
    <div className="mt-4 bg-surface/40 rounded-lg border border-border/30 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <HelpCircle className="w-4 h-4 text-muted" />
        <h4 className="text-sm font-semibold text-gray-900">Troubleshooting</h4>
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
        <div className="text-xs text-muted space-y-1 pl-1">
          <p className="font-medium text-muted mb-1">Common checks:</p>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-muted flex-shrink-0" />
            <span>Verify the collector container is running: <code className="text-muted bg-background/50 px-1 rounded text-[10px]">docker ps</code></span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-muted flex-shrink-0" />
            <span>Check collector logs: <code className="text-muted bg-background/50 px-1 rounded text-[10px]">docker logs &lt;container&gt;</code></span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-muted flex-shrink-0" />
            <span>Confirm RHYNO_API_URL, RHYNO_SERVICE_KEY, and RHYNO_TELEMETRY_TOKEN are correct.</span>
          </div>
          <div className="flex items-start gap-1.5">
            <ChevronRight className="w-3 h-3 mt-0.5 text-muted flex-shrink-0" />
            <span>Ensure the collector can reach the API endpoint from its network.</span>
          </div>
        </div>
      )}
    </div>
  );
}


/* ─── Telemetry Setup Block ─────────────────────────────── */
// @ts-expect-error TelemetrySetupBlock preserved for future telemetry edition
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
    { label: 'Metrics', enabled: svc.metrics_enabled, Icon: BarChart3, color: 'text-info', endpoint: '/api/telemetry/metrics' },
    { label: 'Logs',    enabled: svc.logs_enabled,    Icon: FileText, color: 'text-warning', endpoint: '/api/telemetry/logs' },
    { label: 'Traces',  enabled: svc.traces_enabled,  Icon: Waypoints, color: 'text-purple-400', endpoint: '/api/telemetry/traces' },
  ];

  const lastTelemetry = svc.last_telemetry_at
    ? new Date(svc.last_telemetry_at).toLocaleString()
    : null;

  return (
    <div className="mt-6 space-y-4">
      {/* Section Header */}
      <div className="flex items-center gap-2 border-t border-border/30 pt-5">
        <Shield className="w-4 h-4 text-emerald-400" />
        <h4 className="text-sm font-semibold text-gray-900">Telemetry Setup</h4>
        <TelemetryStatusBadge status={svc.telemetry_status} />
      </div>

      {/* Explanation text (Task 20, Part 3) */}
      <p className="text-xs text-muted leading-relaxed">
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
            ? 'bg-critical/10 border-red-500/20'
            : svc.telemetry_status === 'stale'
              ? 'bg-orange-500/10 border-orange-500/20'
              : svc.telemetry_status === 'receiving_data' || svc.telemetry_status === 'connected'
                ? 'bg-success/10 border-green-500/20'
                : 'bg-primary/10 border-blue-500/20'
        }`}>
          <Info className={`w-4 h-4 flex-shrink-0 mt-0.5 ${statusCfg.color}`} />
          <p className={`text-xs ${statusCfg.color.replace('text-', 'text-').replace('-400', '-300/80')}`}>{statusCfg.helper}</p>
        </div>
      )}

      {/* Credentials Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Service Key */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Telemetry Service Key</p>
          <div className="flex items-center gap-2 bg-surface/60 rounded-lg px-3 py-2 border border-border/40">
            <code className="text-sm text-primary font-mono flex-1 truncate">{svc.telemetry_service_key || '—'}</code>
            {svc.telemetry_service_key && (
              <button
                onClick={() => copyToClipboard(svc.telemetry_service_key!, 'key')}
                className="p-1 rounded hover:bg-gray-50/50 text-muted hover:text-gray-900 transition-colors flex-shrink-0"
                title="Copy Service Key"
              >
                {copiedField === 'key' ? <CheckCircle className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            )}
          </div>
        </div>

        {/* Token */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Telemetry Token</p>
          <div className="flex items-center gap-2 bg-surface/60 rounded-lg px-3 py-2 border border-border/40">
            <code className="text-sm text-primary font-mono flex-1 truncate">
              {svc.telemetry_token ? (showToken ? svc.telemetry_token : maskedToken) : '—'}
            </code>
            {svc.telemetry_token && (
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  onClick={() => setShowToken(!showToken)}
                  className="p-1 rounded hover:bg-gray-50/50 text-muted hover:text-gray-900 transition-colors"
                  title={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => copyToClipboard(svc.telemetry_token!, 'token')}
                  className="p-1 rounded hover:bg-gray-50/50 text-muted hover:text-gray-900 transition-colors"
                  title="Copy Token"
                >
                  {copiedField === 'token' ? <CheckCircle className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
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
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Enabled Signals</p>
          <div className="flex flex-wrap gap-2">
            {signals.map(s => (
              <span key={s.label} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${s.enabled ? 'bg-gray-50/50 text-gray-900 border border-border/40' : 'bg-surface/30 text-muted line-through border border-border/30'}`}>
                <s.Icon className={`w-3 h-3 ${s.enabled ? s.color : 'text-muted'}`} />
                {s.label}
              </span>
            ))}
          </div>
        </div>

        {/* Last Telemetry */}
        <div className="space-y-1.5">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Last Telemetry Received</p>
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-muted" />
            <span className={`text-sm ${lastTelemetry ? 'text-primary' : 'text-muted italic'}`}>
              {lastTelemetry || 'No telemetry received yet'}
            </span>
          </div>
        </div>
      </div>

            {/* ── Collector Setup ────────────────────────────────── */}
      {svc.telemetry_token && (
        <div className="bg-surface/40 rounded-lg border border-border/30 p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-info" />
            <h5 className="text-sm font-semibold text-gray-900">Collector Setup</h5>
          </div>

          {/* Collector Image */}
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-muted font-medium">Collector Image</p>
            <div className="flex items-center gap-2 bg-background/50 rounded-lg px-3 py-2 border border-border/30">
              <Layers className="w-3.5 h-3.5 text-muted" />
              <code className="text-sm text-primary font-mono">rhinometric-collector:v1.1.0</code>
            </div>
          </div>

          {/* Environment Variables */}
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-muted font-medium">Required Environment Variables</p>
            <div className="space-y-2">
              {[
                { name: 'RHYNO_API_URL', value: `${window.location.origin}/api`, field: 'env_api' },
                { name: 'RHYNO_SERVICE_KEY', value: svc.telemetry_service_key || '', field: 'env_key' },
                { name: 'RHYNO_TELEMETRY_TOKEN', value: svc.telemetry_token || '', field: 'env_token' },
              ].map(env => (
                <div key={env.name} className="flex items-center gap-2 bg-background/50 rounded-lg px-3 py-2 border border-border/30">
                  <code className="text-xs text-muted font-mono w-48 flex-shrink-0">{env.name}</code>
                  <code className="text-xs text-primary font-mono flex-1 truncate">{env.value}</code>
                  <button
                    onClick={() => copyToClipboard(env.value, env.field)}
                    className="p-1 rounded hover:bg-gray-50/50 text-muted hover:text-gray-900 transition-colors flex-shrink-0"
                    title={`Copy ${env.name}`}
                  >
                    {copiedField === env.field ? <CheckCircle className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Docker Run Command */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-wider text-muted font-medium">Docker Run Command</p>
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
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-primary/10 text-info hover:bg-primary/20 border border-blue-500/20 transition-colors"
              >
                {copiedField === 'docker' ? <CheckCircle className="w-3 h-3 text-success" /> : <Copy className="w-3 h-3" />}
                {copiedField === 'docker' ? 'Copied!' : 'Copy Docker Command'}
              </button>
            </div>
            <pre className="bg-background/70 rounded-lg px-4 py-3 border border-border/30 text-xs text-primary font-mono overflow-x-auto whitespace-pre leading-relaxed">
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
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-50/50 text-secondary hover:bg-gray-50/50 hover:text-gray-900 border border-border/30 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Download .env Template
            </button>
            <p className="text-xs text-muted">Pre-filled with this service's credentials</p>
          </div>

          {/* Ingestion Endpoints */}
          <div className="space-y-1.5 pt-1">
            <p className="text-xs text-muted font-medium">Ingestion Endpoints:</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {signals.filter(s => s.enabled).map(s => (
                <div key={s.label} className="flex items-center gap-2 px-2.5 py-1.5 bg-background/50 rounded border border-border/30">
                  <s.Icon className={`w-3 h-3 ${s.color}`} />
                  <code className="text-xs text-secondary font-mono">{s.endpoint}</code>
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
  return (
    <div className="bg-background/60 border-t border-border/30 px-6 py-5">
      <h4 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <Activity className="w-4 h-4 text-info" />
        Endpoint Configuration
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Synthetic Monitoring */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Synthetic Monitoring</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${svc.enabled ? 'bg-success' : 'bg-gray-50'}`} />
              <span className="text-muted">Status:</span>
              <span className="text-slate-900">{svc.enabled ? 'Enabled' : 'Disabled'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted">Target:</span>
              <code className="text-secondary bg-surface/50 px-1.5 py-0.5 rounded text-xs">{targetDisplay(svc)}</code>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted">Interval:</span>
              <span className="text-slate-900">{svc.check_interval_seconds}s</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted">Timeout:</span>
              <span className="text-slate-900">{svc.timeout_seconds}s</span>
            </div>
          </div>
        </div>
        {/* Classification */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Classification</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted">Group:</span>
              <span className="text-slate-900">{svc.group_name || 'Default'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted">Category:</span>
              <span className="text-slate-900">{svc.category || '—'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted">Type:</span>
              <span className="text-slate-900">{svc.catalog_type || 'default'}</span>
            </div>
          </div>
        </div>
        {/* Last Check Info */}
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-wider text-muted font-medium">Last Check</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted">Status:</span>
              <span className={`text-sm font-medium ${svc.status === 'up' ? 'text-success' : svc.status === 'down' ? 'text-critical' : 'text-muted'}`}>{svc.status || 'unknown'}</span>
            </div>
            {svc.last_response_time_ms != null && (
              <div className="flex items-center gap-2">
                <span className="text-muted">Response:</span>
                <span className="text-slate-900">{svc.last_response_time_ms.toFixed(0)}ms</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-muted">Checked:</span>
              <span className="text-slate-900">{svc.last_check_at ? new Date(svc.last_check_at).toLocaleString() : 'Never'}</span>
            </div>
          </div>
        </div>
      </div>
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
        <label className="block text-sm font-medium text-secondary mb-1">Endpoint URL *</label>
        <input type="url" value={config.url || ''} onChange={e => set('url', e.target.value)}
          placeholder="https://api.example.com" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Health Path</label>
          <input type="text" value={config.health_path || ''} onChange={e => set('health_path', e.target.value)}
            placeholder="/health" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Method</label>
          <select value={config.method || 'GET'} onChange={e => set('method', e.target.value)}
            className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            <option value="GET">GET</option><option value="POST">POST</option><option value="HEAD">HEAD</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Auth Type</label>
          <select value={config.auth_type || ''} onChange={e => set('auth_type', e.target.value)}
            className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            <option value="">None</option><option value="bearer">Bearer Token</option><option value="api_key">API Key</option><option value="basic">Basic Auth</option>
          </select>
        </div>
        {config.auth_type && (
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">Auth Value</label>
            <input type="password" value={config.auth_value || ''} onChange={e => set('auth_value', e.target.value)}
              placeholder="Token or key" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
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
          <label className="block text-sm font-medium text-secondary mb-1">Host *</label>
          <input type="text" value={config.host || ''} onChange={e => set('host', e.target.value)}
            placeholder="db.example.com" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Port</label>
          <input type="number" value={config.port || 5432} onChange={e => set('port', parseInt(e.target.value) || 5432)}
            className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-secondary mb-1">Database Name *</label>
        <input type="text" value={config.database_name || ''} onChange={e => set('database_name', e.target.value)}
          placeholder="mydb" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Username *</label>
          <input type="text" value={config.username || ''} onChange={e => set('username', e.target.value)}
            placeholder="postgres" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-1">Password *</label>
          <input type="password" value={config.password || ''} onChange={e => set('password', e.target.value)}
            placeholder="password" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-secondary mb-1">SSL Mode</label>
        <select value={config.ssl_mode || 'prefer'} onChange={e => set('ssl_mode', e.target.value)}
          className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
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
  // Platform tab removed - always show external services
  const [view, setView] = useState<View>('list')
  const [extServices, setExtServices] = useState<ExternalServiceData[]>([])
  const [extSummary, setExtSummary] = useState<ExtSummary>({ total:0, enabled:0, up:0, down:0, degraded:0, unknown:0 })
  const [_platformData, setPlatformData] = useState<PlatformData | null>(null)
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
  // @ts-expect-error formMonitoringMode — setter used in resetForm/loadEdit; value reserved for telemetry edition
  const [formMonitoringMode, setFormMonitoringMode] = useState<'synthetic_only' | 'telemetry_enabled'>('synthetic_only')
  // @ts-expect-error formMetricsEnabled — setter used in resetForm/loadEdit; value reserved for telemetry edition
  const [formMetricsEnabled, setFormMetricsEnabled] = useState(false)
  // @ts-expect-error formLogsEnabled — setter used in resetForm/loadEdit; value reserved for telemetry edition
  const [formLogsEnabled, setFormLogsEnabled] = useState(false)
  // @ts-expect-error formTracesEnabled — setter used in resetForm/loadEdit; value reserved for telemetry edition
  const [formTracesEnabled, setFormTracesEnabled] = useState(false)
  // @ts-expect-error formTelemetryServiceKey — setter used in resetForm/loadEdit; value reserved for telemetry edition
  const [formTelemetryServiceKey, setFormTelemetryServiceKey] = useState('')
  // @ts-expect-error showTelemetryWarning — setter used in resetForm/loadEdit; value reserved for telemetry edition
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

  // Add Services modal
  const [showAddModal, setShowAddModal] = useState(false)

  // Assertions state (for edit view)
  const [assertions, setAssertions] = useState<any[]>([])
  const [assertionsLoading, setAssertionsLoading] = useState(false)
  const [assertionForm, setAssertionForm] = useState<{type: string, expected: string, jsonPath: string, name: string, severity: string}>({type: 'status_code', expected: '200', jsonPath: '', name: '', severity: 'warning'})
  const [showAssertionForm, setShowAssertionForm] = useState(false)
  const [editTab, setEditTab] = useState<'connection' | 'assertions' | 'classification'>('connection')

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

  // Fetch assertions for a service (used in edit view)
  const fetchAssertions = useCallback(async (serviceId: number) => {
    setAssertionsLoading(true)
    try {
      const res = await fetch(`/api/external-services/${serviceId}/assertions`, { headers: apiHeaders })
      if (res.ok) setAssertions(await res.json())
    } catch (e) { console.error('assertions fetch error', e) }
    setAssertionsLoading(false)
  }, [token])

  const createAssertion = async (serviceId: number) => {
    const body: any = {
      assertion_type: assertionForm.type,
      expected_value: assertionForm.expected,
      name: assertionForm.name || undefined,
      severity: assertionForm.severity,
      enabled: true,
      order: assertions.length,
    }
    if (assertionForm.type === 'json_path_equals') body.json_path = assertionForm.jsonPath
    try {
      const res = await fetch(`/api/external-services/${serviceId}/assertions`, {
        method: 'POST', headers: apiHeaders, body: JSON.stringify(body)
      })
      if (!res.ok) { const d = await res.json().catch(() => ({})); alert(d.detail || 'Failed to create assertion'); return }
      await fetchAssertions(serviceId)
      setShowAssertionForm(false)
      setAssertionForm({type: 'status_code', expected: '200', jsonPath: '', name: '', severity: 'warning'})
    } catch (e: any) { alert(e.message) }
  }

  const deleteAssertion = async (serviceId: number, assertionId: string) => {
    if (!confirm('Delete this assertion?')) return
    try {
      const res = await fetch(`/api/external-services/${serviceId}/assertions/${assertionId}`, {
        method: 'DELETE', headers: apiHeaders
      })
      if (!res.ok && res.status !== 204) { alert('Failed to delete assertion'); }
      await fetchAssertions(serviceId)
    } catch (e: any) { alert(e.message) }
  }

  const toggleAssertion = async (serviceId: number, assertionId: string, enabled: boolean) => {
    try {
      const res = await fetch(`/api/external-services/${serviceId}/assertions/${assertionId}`, {
        method: 'PUT', headers: apiHeaders, body: JSON.stringify({ enabled: !enabled })
      })
      if (!res.ok) { alert('Failed to toggle assertion'); }
      await fetchAssertions(serviceId)
    } catch (e: any) { alert(e.message) }
  }

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
    setEditTab('connection'); fetchAssertions(svc.id)
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
    const body: Record<string, any> = {
      name: formName, service_type: formType, environment: formEnv || null,
      description: formDesc || null, config: formConfig,
      timeout_seconds: formTimeout, check_interval_seconds: formInterval,
      catalog_type: formCatalogType || null, category: formCategory || null,
      group_name: formGroupName || 'Default',
      tags: formTags.length > 0 ? formTags : null,
      monitoring_mode: 'synthetic_only',
      synthetic_enabled: true,
      metrics_enabled: false,
      logs_enabled: false,
      traces_enabled: false,
      telemetry_attached: false,
      telemetry_source_type: null,
      telemetry_service_key: null,
    }
    try {
      const url = editId ? `/api/external-services/${editId}` : '/api/external-services'
      const method = editId ? 'PUT' : 'POST'
      const res = await fetch(url, { method, headers: apiHeaders, body: JSON.stringify(body) })
      if (!res.ok) {
        const text = await res.text()
        let detail = 'Save failed'
        try { const d = JSON.parse(text); detail = d.detail || detail } catch {}
        alert(detail)
        return
      }
      await fetchExternal()
      setView('list'); resetForm()
    } catch (e: any) { alert(e.message) }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this service?')) return
    setActionLoading(id)
    try {
      const res = await fetch(`/api/external-services/${id}`, { method: 'DELETE', headers: apiHeaders })
      if (!res.ok && res.status !== 204) { alert('Failed to delete service'); }
    } catch (e: any) { alert(e.message) }
    await fetchExternal()
    setActionLoading(null)
  }

  const handleToggle = async (id: number) => {
    setActionLoading(id)
    try {
      const res = await fetch(`/api/external-services/${id}/toggle`, { method: 'POST', headers: apiHeaders })
      if (!res.ok) { alert('Failed to toggle service'); }
    } catch (e: any) { alert(e.message) }
    await fetchExternal()
    setActionLoading(null)
  }

  const handleTestSaved = async (id: number) => {
    setActionLoading(id)
    try {
      const res = await fetch(`/api/external-services/${id}/test`, { method: 'POST', headers: apiHeaders })
      if (!res.ok) { alert('Connection test failed'); }
    } catch (e: any) { alert(e.message) }
    await fetchExternal()
    setActionLoading(null)
  }

  // ── Loading ────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Services</h1>
        <div className="flex items-center justify-center h-64">
          <Activity className="w-8 h-8 text-info animate-spin" />
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

  // platform variable removed - tab hidden from UI

  // ── Create/Edit Form View ──────────────────────────────────────

  // ── Bulk HTTP View ───────────────────────────────────────────
  if (view === 'bulk-http') {
    const filledItems = bulkItems.filter((it: any) => it.name.trim() || it.path.trim())
    return (
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center gap-3">
          <button onClick={() => { setView('list'); resetBulkHttp() }} className="p-2 rounded-lg hover:bg-gray-50/50 text-muted hover:text-gray-900">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Multiple Endpoints</h1>
            <p className="text-muted text-sm">Create multiple HTTP services in one operation</p>
          </div>
        </div>

        {/* Read-only banner for non-admin users */}
        {!canManage && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-warning/10 border border-yellow-500/30">
            <Lock className="w-5 h-5 text-warning flex-shrink-0" />
            <p className="text-yellow-300 text-sm">
              <span className="font-medium">View-only mode.</span> You can explore the configuration but only administrators can create or modify services.
            </p>
          </div>
        )}

        {bulkStep === 'form' && (
          <div className="space-y-6">
            {/* Common Settings */}
            <div className="bg-surface/50 rounded-xl border border-border/50 p-5 space-y-4">
              <h3 className="text-gray-900 font-medium flex items-center gap-2"><Globe className="w-4 h-4 text-info" /> Common Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm text-muted mb-1">Base URL <span className="text-gray-600">(optional)</span></label>
                  <input value={bulkBaseUrl} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkBaseUrl(e.target.value)} readOnly={!canManage}
                    placeholder="https://api.company.com" className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                  <p className="text-gray-600 text-xs mt-1">If set, endpoint paths will be appended to this URL</p>
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Method</label>
                  <select value={bulkMethod} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkMethod(e.target.value)} disabled={!canManage}
                    className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`}>
                    {['GET','POST','PUT','DELETE','PATCH','HEAD','OPTIONS'].map((m: string) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Environment</label>
                  <input value={bulkEnv} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkEnv(e.target.value)} readOnly={!canManage}
                    placeholder="production" className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Timeout (s)</label>
                  <input type="number" value={bulkTimeout} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkTimeout(Number(e.target.value))} readOnly={!canManage}
                    min={1} max={120} className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Check Interval (s)</label>
                  <input type="number" value={bulkInterval} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkInterval(Number(e.target.value))} readOnly={!canManage}
                    min={10} max={86400} className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Catalog Type</label>
                  <select value={bulkCatalogType} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkCatalogType(e.target.value)} disabled={!canManage}
                    className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`}>
                    {CATALOG_TYPE_OPTIONS.map((o: {value:string;label:string}) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-muted mb-1">Category</label>
                  <input value={bulkCategory} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkCategory(e.target.value)} readOnly={!canManage}
                    placeholder="payments, auth, mobile..." className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                </div>
              </div>
              {/* Tags */}
              <div>
                <label className="block text-sm text-muted mb-1">Common Tags</label>
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
                    placeholder="Press Enter to add tag" className={`flex-1 bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none text-sm ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                </div>
                {bulkTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {bulkTags.map((t: string) => (
                      <span key={t} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-info-bg text-info">
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
                <summary className="text-muted cursor-pointer hover:text-secondary">Authentication (optional)</summary>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <label className="block text-sm text-muted mb-1">Auth Type</label>
                    <select value={bulkAuthType} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => canManage && setBulkAuthType(e.target.value)} disabled={!canManage}
                      className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`}>
                      <option value="">None</option>
                      <option value="bearer">Bearer Token</option>
                      <option value="api_key">API Key</option>
                      <option value="basic">Basic Auth</option>
                    </select>
                  </div>
                  {bulkAuthType && (
                    <div>
                      <label className="block text-sm text-muted mb-1">Auth Value</label>
                      <input value={bulkAuthValue} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && setBulkAuthValue(e.target.value)} readOnly={!canManage}
                        placeholder="Token or credentials" className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                    </div>
                  )}
                </div>
              </details>
              {/* Enabled toggle */}
              <div className="flex items-center gap-3">
                <button onClick={() => canManage && setBulkEnabled(!bulkEnabled)} disabled={!canManage}
                  className={`relative w-10 h-5 rounded-full transition-colors ${!canManage ? 'bg-gray-50 cursor-not-allowed opacity-50' : bulkEnabled ? 'bg-emerald-500' : 'bg-gray-50'}`}>
                  <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${bulkEnabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
                </button>
                <span className="text-sm text-muted">Enable monitoring after creation</span>
              </div>
            </div>

            {/* Endpoints List */}
            <div className="bg-surface/50 rounded-xl border border-border/50 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-gray-900 font-medium flex items-center gap-2"><Layers className="w-4 h-4 text-emerald-400" /> API Endpoints</h3>
                <div className="flex items-center gap-2">
                  <button onClick={() => canManage && setBulkPasteMode(!bulkPasteMode)} disabled={!canManage}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border transition-colors ${canManage ? 'border-border text-muted hover:text-gray-900 hover:border-gray-500' : 'border-border text-gray-600 cursor-not-allowed opacity-50'}`}>
                    <Copy className="w-3.5 h-3.5" /> {bulkPasteMode ? 'Manual Entry' : 'Quick Paste'}
                  </button>
                  {!bulkPasteMode && (
                    <button onClick={canManage ? bulkAddItem : undefined} disabled={!canManage}
                      title={!canManage ? 'Only administrators can create services' : ''}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${canManage ? 'bg-gray-50 text-secondary hover:bg-gray-50 hover:text-gray-900' : 'bg-surface text-gray-600 cursor-not-allowed opacity-50'}`}>
                      <Plus className="w-3.5 h-3.5" /> Add Row
                    </button>
                  )}
                </div>
              </div>

              {bulkPasteMode ? (
                <div className="space-y-3">
                  <p className="text-muted text-xs">Paste one API per line. Format: <code className="text-muted">Name, /path</code> or just <code className="text-muted">/path</code> (name auto-generated)</p>
                  <textarea value={bulkPasteText} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => canManage && setBulkPasteText(e.target.value)} readOnly={!canManage}
                    rows={8} placeholder={"Auth API, /auth\nPayments API, /payments\nCustomers API, /customers\n/orders\n/inventory"}
                    className={`w-full bg-background/50 border border-border rounded-lg px-3 py-2 placeholder-gray-600 focus:outline-none font-mono text-sm ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                  <button onClick={canManage ? bulkParsePaste : undefined} disabled={!canManage || !bulkPasteText.trim()}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className="px-4 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors">
                    Parse {bulkPasteText.split('\n').filter((l: string) => l.trim()).length} lines
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {/* Header */}
                  <div className="grid grid-cols-12 gap-2 text-xs text-muted px-1">
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
                          placeholder="API name" className={`w-full bg-background/50 border border-border rounded-lg px-2.5 py-1.5 text-sm placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                      </div>
                      <div className="col-span-5">
                        <input value={item.path} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && bulkUpdateItem(idx, 'path', e.target.value)} readOnly={!canManage}
                          placeholder="/endpoint or https://..." className={`w-full bg-background/50 border border-border rounded-lg px-2.5 py-1.5 text-sm placeholder-gray-600 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} />
                      </div>
                      <div className="col-span-1">
                        <input value={item.method || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => canManage && bulkUpdateItem(idx, 'method', e.target.value)} readOnly={!canManage}
                          placeholder="" className={`w-full bg-background/50 border border-border rounded-lg px-2 py-1.5 text-sm text-center placeholder-gray-700 focus:outline-none ${canManage ? 'text-gray-900 focus:border-blue-500' : 'text-muted cursor-not-allowed'}`} title="Override method (leave empty for common)" />
                      </div>
                      <div className="col-span-1 flex justify-center">
                        <button onClick={() => canManage && bulkRemoveItem(idx)} disabled={!canManage || bulkItems.length <= 1}
                          title={!canManage ? 'Only administrators can modify services' : ''}
                          className={`p-1 rounded transition-colors disabled:opacity-30 ${canManage ? 'text-gray-600 hover:text-critical' : 'text-gray-700 cursor-not-allowed'}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                  {/* Quick add more */}
                  <button onClick={canManage ? bulkAddItem : undefined} disabled={!canManage}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className={`w-full py-2 border border-dashed rounded-lg text-sm transition-colors ${canManage ? 'border-border text-muted hover:text-secondary hover:border-border' : 'border-border text-gray-700 cursor-not-allowed opacity-50'}`}>
                    + Add another endpoint
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <p className="text-muted text-sm">{filledItems.length} endpoint{filledItems.length !== 1 ? 's' : ''} ready</p>
              <div className="flex items-center gap-3">
                <button onClick={() => { setView('list'); resetBulkHttp() }}
                  className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">Cancel</button>
                <button onClick={canManage ? handleBulkPreview : undefined} disabled={!canManage || filledItems.length === 0 || bulkLoading}
                  title={!canManage ? 'Only administrators can create services' : ''}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
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
              <div className="p-4 rounded-lg bg-critical/10 border border-red-500/30 text-critical">
                <p className="font-medium">Validation failed</p>
                <p className="text-sm mt-1">{bulkPreview.error}</p>
              </div>
            ) : (
              <>
                {/* Summary cards */}
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { label: 'Total', value: bulkPreview.total_received, color: 'text-secondary' },
                    { label: 'Valid', value: bulkPreview.valid_count, color: 'text-success' },
                    { label: 'Invalid', value: bulkPreview.invalid_count, color: 'text-critical' },
                    { label: 'Duplicates', value: bulkPreview.duplicate_count, color: 'text-warning' },
                  ].map((c: { label: string; value: number; color: string }) => (
                    <div key={c.label} className="bg-surface/50 rounded-lg p-3 border border-border/50 text-center">
                      <p className="text-muted text-xs">{c.label}</p>
                      <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
                    </div>
                  ))}
                </div>

                {/* Valid preview table */}
                {bulkPreview.valid_preview?.length > 0 && (
                  <div>
                    <p className="text-sm text-muted mb-2">Services to be created:</p>
                    <div className="max-h-60 overflow-y-auto bg-background/50 rounded-lg border border-border/50">
                      <table className="w-full text-sm">
                        <thead><tr className="border-b border-border/50">
                          <th className="text-left p-2 text-muted text-xs">#</th>
                          <th className="text-left p-2 text-muted text-xs">Name</th>
                          <th className="text-left p-2 text-muted text-xs">URL</th>
                          <th className="text-left p-2 text-muted text-xs">Method</th>
                        </tr></thead>
                        <tbody>
                          {bulkPreview.valid_preview.map((s: any) => (
                            <tr key={s.row} className="border-b border-border/30">
                              <td className="p-2 text-muted">{s.row}</td>
                              <td className="p-2 text-gray-900">{s.name}</td>
                              <td className="p-2 text-muted truncate max-w-[300px]">{s.url}</td>
                              <td className="p-2 text-muted">{s.method}</td>
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
                    <p className="text-sm text-muted mb-2">Issues found:</p>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {bulkPreview.errors.map((e: any, i: number) => (
                        <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-warning/10 border border-yellow-500/20 text-warning' : 'bg-critical/10 border border-red-500/20 text-critical'}`}>
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
                className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">\u2190 Back</button>
              <div className="flex gap-3">
                <button onClick={() => { setView('list'); resetBulkHttp() }}
                  className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">Cancel</button>
                {bulkPreview && !bulkPreview.error && bulkPreview.valid_count > 0 && (
                  <button onClick={canManage ? handleBulkConfirm : undefined} disabled={!canManage || bulkLoading}
                    title={!canManage ? 'Only administrators can create services' : ''}
                    className="flex items-center gap-2 px-5 py-2 rounded-lg bg-green-600 text-white hover:bg-success disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
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
              <div className="p-4 rounded-lg bg-critical/10 border border-red-500/30 text-critical">
                <p className="font-medium">Creation failed</p>
                <p className="text-sm mt-1">{bulkResult.error}</p>
              </div>
            ) : (
              <>
                <div className={`p-4 rounded-lg border ${bulkResult.created_count > 0 ? 'bg-success/10 border-green-500/30' : 'bg-warning/10 border-yellow-500/30'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className={`w-5 h-5 ${bulkResult.created_count > 0 ? 'text-success' : 'text-warning'}`} />
                    <span className={`font-medium ${bulkResult.created_count > 0 ? 'text-success' : 'text-warning'}`}>Bulk creation complete</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div><span className="text-muted">Created:</span> <span className="text-success font-medium">{bulkResult.created_count}</span></div>
                    <div><span className="text-muted">Skipped:</span> <span className="text-warning font-medium">{bulkResult.skipped_count}</span></div>
                    <div><span className="text-muted">Invalid:</span> <span className="text-critical font-medium">{bulkResult.invalid_count}</span></div>
                  </div>
                </div>

                {bulkResult.created_services?.length > 0 && (
                  <div>
                    <p className="text-sm text-muted mb-2">Created services:</p>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {bulkResult.created_services.map((s: any) => (
                        <div key={s.id} className="flex items-center gap-2 p-2 bg-success/5 rounded text-sm border border-green-500/10">
                          <CheckCircle className="w-3.5 h-3.5 text-success flex-shrink-0" />
                          <span className="text-slate-900">{s.name}</span>
                          <span className="text-muted truncate ml-auto max-w-[250px]">{s.url}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {bulkResult.errors?.length > 0 && (
                  <div>
                    <p className="text-sm text-muted mb-2">Issues:</p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {bulkResult.errors.map((e: any, i: number) => (
                        <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-warning/10 text-warning' : 'bg-critical/10 text-critical'}`}>
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
                className="px-5 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary font-medium transition-colors">Done</button>
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
    const isValid = baseFieldsValid
    return (
      <div className="space-y-6 max-w-3xl">
        <div className="flex items-center gap-3">
          <button onClick={() => { setView('list'); resetForm() }} className="p-2 rounded-lg hover:bg-gray-50/50 text-muted hover:text-gray-900">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900">
            {view === 'edit' ? 'Edit Service' : 'Add Endpoint'}
          </h1>
        </div>

        {/* Read-only banner for non-admin users */}
        {!canManage && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-warning/10 border border-yellow-500/30">
            <Lock className="w-5 h-5 text-warning flex-shrink-0" />
            <p className="text-yellow-300 text-sm">
              <span className="font-medium">View-only mode.</span> You can explore the configuration but only administrators can create or modify services.
            </p>
          </div>
        )}

        {/* Edit tabs */}
        {view === 'edit' && (
          <div className="flex items-center bg-surface/60 rounded-lg p-1 gap-1">
            <button onClick={() => setEditTab('connection')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${editTab === 'connection' ? 'bg-gray-50 text-gray-900 shadow-sm' : 'text-muted hover:text-primary'}`}>
              <Network className="w-4 h-4" /> Connection
            </button>
            <button onClick={() => setEditTab('assertions')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${editTab === 'assertions' ? 'bg-gray-50 text-gray-900 shadow-sm' : 'text-muted hover:text-primary'}`}>
              <Shield className="w-4 h-4" /> Assertions
              {assertions.length > 0 && (
                <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${assertions.some((a: any) => a.enabled) ? 'bg-primary/20 text-info' : 'bg-gray-50 text-muted'}`}>
                  {assertions.length}
                </span>
              )}
            </button>
            <button onClick={() => setEditTab('classification')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${editTab === 'classification' ? 'bg-gray-50 text-gray-900 shadow-sm' : 'text-muted hover:text-primary'}`}>
              <Tag className="w-4 h-4" /> Classification
            </button>
          </div>
        )}

        {/* Service type - HTTP default, PG available via "Add Services > Advanced" */}
        {view === 'create' && formType === 'postgresql' && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500/10 border border-orange-500/30">
            <Database className="w-4 h-4 text-orange-400" />
            <span className="text-orange-300 text-sm">PostgreSQL mode</span>
            <button onClick={() => { setFormType('http'); setFormConfig({}) }} className="ml-auto text-xs text-muted hover:text-gray-900">Switch to HTTP</button>
          </div>
        )}

        {/* Common fields — visible in create, in edit only on connection tab */}
        {(view === 'create' || editTab === 'connection') && (
        <div className="bg-surface/50 rounded-lg border border-border/50 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">General</h2>
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">Service Name *</label>
            <input type="text" value={formName} onChange={e => setFormName(e.target.value)}
              placeholder="My API Service" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Environment</label>
              <input type="text" value={formEnv} onChange={e => setFormEnv(e.target.value)}
                placeholder="production" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Timeout (s)</label>
              <input type="number" value={formTimeout} onChange={e => setFormTimeout(parseInt(e.target.value) || 10)}
                min={1} max={120} className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Check Interval (s)</label>
              <input type="number" value={formInterval} onChange={e => setFormInterval(parseInt(e.target.value) || 60)}
                min={10} max={86400} className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
              <p className="text-gray-600 text-xs mt-1">How often to check (default: 60s)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Method</label>
              <select value={formConfig.method || 'GET'} onChange={e => setFormConfig({...formConfig, method: e.target.value})}
                className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
                <option value="GET">GET</option><option value="POST">POST</option><option value="HEAD">HEAD</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">Description</label>
            <textarea value={formDesc} onChange={e => setFormDesc(e.target.value)} rows={2}
              placeholder="Optional description" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
        </div>
        )}

        {/* Classification — shown in create, in edit only on classification tab */}
        {(view === 'create' || editTab === 'classification') && (
        <div className="bg-surface/50 rounded-lg border border-border/50 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Classification</h2>
          <p className="text-muted text-xs -mt-1">Optional metadata for organizing and filtering services.</p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Group Name</label>
              <input type="text" value={formGroupName} onChange={e => setFormGroupName(e.target.value)}
                placeholder="Default" className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm" />
              <p className="text-muted text-xs mt-1">Group for organizing services (e.g., Payments, Infrastructure)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Catalog Type</label>
              <select value={formCatalogType} onChange={e => setFormCatalogType(e.target.value)}
                className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
                {CATALOG_TYPE_OPTIONS.map((o: { value: string; label: string }) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">Category</label>
              <input type="text" value={formCategory} onChange={e => setFormCategory(e.target.value)}
                placeholder="e.g. payments, auth, infrastructure"
                className="w-full bg-white border border-border rounded-lg px-3 py-2 text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary mb-1">Tags</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {formTags.map((tag, i) => (
                <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-info-bg text-info border border-blue-400/20">
                  {tag}
                  <button type="button" onClick={() => setFormTags(formTags.filter((_: string, j: number) => j !== i))}
                    className="ml-0.5 hover:text-critical transition-colors">
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
                className="flex-1 bg-background/50 border border-border rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
              <button type="button" onClick={() => {
                  const newTag = formTagInput.trim().toLowerCase().replace(/,/g, '')
                  if (newTag && !formTags.includes(newTag)) setFormTags([...formTags, newTag])
                  setFormTagInput('')
                }}
                disabled={!formTagInput.trim()}
                className="px-3 py-2 rounded-lg text-sm bg-primary/20 text-info hover:bg-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
                Add
              </button>
            </div>
            <p className="text-gray-600 text-xs mt-1.5">Press Enter or comma to add. Click ?? to remove.</p>
          </div>
        </div>

        )}

        {/* Assertions Tab (edit view only) */}
        {view === 'edit' && editTab === 'assertions' && editId && (
          <div className="bg-surface/50 rounded-lg border border-border/50 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Shield className="w-5 h-5 text-info" /> Assertions
              </h2>
              {canManage && (
                <button onClick={() => setShowAssertionForm(!showAssertionForm)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-primary/20 text-info hover:bg-primary/30 transition-colors">
                  <Plus className="w-3.5 h-3.5" /> Add Assertion
                </button>
              )}
            </div>
            <p className="text-muted text-xs">Define rules to validate response behavior. Assertions run on every successful check.</p>

            {/* Assertion create form */}
            {showAssertionForm && (
              <div className="bg-background/50 rounded-lg border border-border p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-muted mb-1">Type</label>
                    <select value={assertionForm.type} onChange={e => {
                        const t = e.target.value
                        setAssertionForm({...assertionForm, type: t, expected: t === 'status_code' ? '200' : t === 'response_time' ? '5000' : '', jsonPath: '', name: ''})
                      }}
                      className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-gray-900 focus:border-blue-500">
                      <option value="status_code">Status Code</option>
                      <option value="response_time">Response Time (ms)</option>
                      <option value="text_contains">Body Contains Text</option>
                      <option value="json_path_equals">JSON Path Equals</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted mb-1">Severity</label>
                    <select value={assertionForm.severity} onChange={e => setAssertionForm({...assertionForm, severity: e.target.value})}
                      className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-gray-900 focus:border-blue-500">
                      <option value="info">Info</option>
                      <option value="warning">Warning</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>
                {assertionForm.type === 'json_path_equals' && (
                  <div>
                    <label className="block text-xs font-medium text-muted mb-1">JSON Path</label>
                    <input type="text" value={assertionForm.jsonPath}
                      onChange={e => setAssertionForm({...assertionForm, jsonPath: e.target.value})}
                      placeholder="$.data.status" className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500" />
                  </div>
                )}
                <div>
                  <label className="block text-xs font-medium text-muted mb-1">
                    {assertionForm.type === 'status_code' ? 'Expected Status Code' : assertionForm.type === 'response_time' ? 'Max Response Time (ms)' : assertionForm.type === 'text_contains' ? 'Expected Text' : 'Expected Value'}
                  </label>
                  <input type="text" value={assertionForm.expected}
                    onChange={e => setAssertionForm({...assertionForm, expected: e.target.value})}
                    placeholder={assertionForm.type === 'status_code' ? '200' : assertionForm.type === 'response_time' ? '5000' : 'expected value'}
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted mb-1">Name (optional)</label>
                  <input type="text" value={assertionForm.name}
                    onChange={e => setAssertionForm({...assertionForm, name: e.target.value})}
                    placeholder="e.g. Check status is 200"
                    className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500" />
                </div>
                {/* Quick templates */}
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="text-xs text-muted">Quick:</span>
                  <button onClick={() => setAssertionForm({type: 'status_code', expected: '200', jsonPath: '', name: 'Status is 200', severity: 'warning'})}
                    className="px-2 py-0.5 rounded text-xs bg-success/10 text-success hover:bg-success/20">status = 200</button>
                  <button onClick={() => setAssertionForm({type: 'response_time', expected: '5000', jsonPath: '', name: 'Response under 5s', severity: 'warning'})}
                    className="px-2 py-0.5 rounded text-xs bg-primary/10 text-info hover:bg-primary/20">&lt; 5000ms</button>
                  <button onClick={() => setAssertionForm({type: 'status_code', expected: '201', jsonPath: '', name: 'Status is 201', severity: 'info'})}
                    className="px-2 py-0.5 rounded text-xs bg-success/10 text-success hover:bg-success/20">status = 201</button>
                  <button onClick={() => setAssertionForm({type: 'response_time', expected: '2000', jsonPath: '', name: 'Response under 2s', severity: 'critical'})}
                    className="px-2 py-0.5 rounded text-xs bg-critical/10 text-critical hover:bg-critical/20">&lt; 2000ms</button>
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button onClick={() => setShowAssertionForm(false)}
                    className="px-3 py-1.5 rounded-lg text-sm text-muted hover:text-gray-900">Cancel</button>
                  <button onClick={() => editId && createAssertion(editId)}
                    disabled={!assertionForm.expected.trim() || (assertionForm.type === 'json_path_equals' && !assertionForm.jsonPath.trim())}
                    className="px-4 py-1.5 rounded-lg text-sm bg-primary text-gray-900 hover:bg-primary disabled:opacity-50 disabled:cursor-not-allowed font-medium">
                    Create Assertion
                  </button>
                </div>
              </div>
            )}

            {/* Existing assertions list */}
            {assertionsLoading ? (
              <div className="flex justify-center py-8"><RefreshCw className="w-5 h-5 text-info animate-spin" /></div>
            ) : assertions.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                <p className="text-muted text-sm">No assertions configured</p>
                <p className="text-gray-600 text-xs mt-1">Add assertions to validate response behavior on every check</p>
              </div>
            ) : (
              <div className="space-y-2">
                {assertions.map((a: any) => (
                  <div key={a.id} className={`flex items-center gap-3 p-3 rounded-lg border ${a.enabled ? 'border-border bg-background/30' : 'border-border bg-background/10 opacity-60'}`}>
                    <button onClick={() => canManage && editId && toggleAssertion(editId, a.id, a.enabled)}
                      className={`w-8 h-5 rounded-full transition-colors flex items-center ${a.enabled ? 'bg-primary justify-end' : 'bg-gray-50 justify-start'}`}>
                      <span className="w-3.5 h-3.5 rounded-full bg-white mx-0.5 shadow-sm" />
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-gray-50 text-secondary">{a.assertion_type}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${a.severity === 'critical' ? 'bg-critical/10 text-critical' : a.severity === 'warning' ? 'bg-warning/10 text-warning' : 'bg-primary/10 text-info'}`}>{a.severity}</span>
                        {a.name && <span className="text-sm text-secondary truncate">{a.name}</span>}
                      </div>
                      <p className="text-xs text-muted mt-0.5">
                        {a.assertion_type === 'status_code' && <>expects <span className="text-secondary">{a.expected_value}</span></>}
                        {a.assertion_type === 'response_time' && <>under <span className="text-secondary">{a.expected_value}ms</span></>}
                        {a.assertion_type === 'text_contains' && <>contains "<span className="text-secondary">{a.expected_value}</span>"</>}
                        {a.assertion_type === 'json_path_equals' && <><span className="font-mono text-muted">{a.json_path}</span> = <span className="text-secondary">{a.expected_value}</span></>}
                      </p>
                    </div>
                    {canManage && (
                      <button onClick={() => editId && deleteAssertion(editId, a.id)}
                        className="p-1.5 rounded hover:bg-gray-50/50 text-muted hover:text-critical transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}



        {/* Type-specific fields */}
        {(view === 'create' || editTab === 'connection') && (
        <div className="bg-surface/50 rounded-lg border border-border/50 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            {formType === 'http' ? 'HTTP Connection' : 'PostgreSQL Connection'}
          </h2>
          {formType === 'http' ? <HttpForm config={formConfig} onChange={setFormConfig} /> : <PgForm config={formConfig} onChange={setFormConfig} />}
        </div>

        )}

        {/* Test Connection Result */}
        {testResult && (() => {
          const isSuccess = testResult.success === true;
          const isHttpError = !isSuccess && testResult.status_code != null;
          const borderClass = isSuccess
            ? 'border-green-500/50 bg-success/10'
            : isHttpError
              ? 'border-amber-500/50 bg-amber-500/10'
              : 'border-red-500/50 bg-critical/10';
          const iconColor = isSuccess ? 'text-success' : isHttpError ? 'text-amber-400' : 'text-critical';
          const label = isSuccess
            ? 'Connection successful'
            : 'Connection test failed';
          return (
            <div className={`rounded-lg border p-4 ${borderClass}`}>
              <div className="flex items-center gap-2">
                {isSuccess ? <CheckCircle className={`w-5 h-5 ${iconColor}`} /> : <AlertCircle className={`w-5 h-5 ${iconColor}`} />}
                <span className={`${iconColor} font-medium`}>{label}</span>
                {testResult.response_time_ms != null && (
                  <span className="text-muted text-sm ml-2">{testResult.response_time_ms.toFixed(0)}ms</span>
                )}
              </div>
              <p className="text-muted text-sm mt-1">{testResult.message}</p>
            </div>
          );
        })()}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button onClick={canManage ? handleTestConnection : undefined} disabled={!canManage || !isValid || testing}
            title={!canManage ? 'Only administrators can test connections' : ''}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-secondary hover:text-gray-900 hover:border-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Test Connection
          </button>
          <button onClick={canManage ? handleSave : undefined} disabled={!canManage || !isValid}
            title={!canManage ? 'Only administrators can create or modify services' : ''}
            className="flex items-center gap-2 px-6 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
            {view === 'edit' ? 'Save Changes' : 'Create Service'}
          </button>
          <button onClick={() => { setView('list'); resetForm() }}
            className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">
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
          <h1 className="text-3xl font-bold text-gray-900">Services</h1>
          <p className="text-muted mt-1">Monitor your HTTP endpoints and API services</p>
        </div>
          <div className="flex items-center gap-3">
            {/* View mode toggle (Task 22) */}
            <div className="flex items-center bg-surface/60 rounded-lg p-0.5">
              <button onClick={() => setGroupViewMode('grouped')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${groupViewMode === 'grouped' ? 'bg-gray-50 text-gray-900 shadow-sm' : 'text-muted hover:text-primary'}`}>
                <FolderOpen className="w-3.5 h-3.5" /> Grouped
              </button>
              <button onClick={() => setGroupViewMode('list')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${groupViewMode === 'list' ? 'bg-gray-50 text-gray-900 shadow-sm' : 'text-muted hover:text-primary'}`}>
                <Layers className="w-3.5 h-3.5" /> Flat List
              </button>
            </div>
            <button onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-gray-900 hover:bg-primary font-medium transition-colors shadow-md">
              <Plus className="w-4 h-4" /> Add Services
            </button>
          </div>
      </div>

      {/* ── EXTERNAL SERVICES TAB ──────────────────────────────── */}
      {/* External Services Content */}
        <>
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: 'Total', value: extSummary.total, Icon: Globe, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
              { label: 'Healthy', value: extSummary.up, Icon: CheckCircle, color: 'text-success', bg: 'bg-success/10' },
              { label: 'Down', value: extSummary.down, Icon: AlertCircle, color: 'text-critical', bg: 'bg-critical/10' },
              { label: 'Unknown', value: extSummary.unknown, Icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
            ].map(c => (
              <div key={c.label} className="bg-surface/50 rounded-lg p-4 border border-border/50">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-lg ${c.bg}`}><c.Icon className={`w-5 h-5 ${c.color}`} /></div>
                  <div>
                    <p className="text-muted text-sm">{c.label}</p>
                    <p className="text-xl font-bold text-gray-900">{c.value}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty state */}
          {/* Filter bar */}
          {extServices.length > 0 && (
            <div className="bg-surface/50 rounded-lg border border-border/50 p-4">
              <div className="flex flex-wrap items-center gap-3">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                  <input
                    type="text"
                    placeholder="Search services..."
                    value={filterSearch}
                    onChange={e => setFilterSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-background/50 border border-border rounded-lg text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                {/* Catalog Type filter */}
                <select
                  value={filterCatalogType}
                  onChange={e => setFilterCatalogType(e.target.value)}
                  className="px-3 py-2 bg-background/50 border border-border rounded-lg text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Catalog Types</option>
                  {catalogTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                </select>
                {/* Category filter */}
                <select
                  value={filterCategory}
                  onChange={e => setFilterCategory(e.target.value)}
                  className="px-3 py-2 bg-background/50 border border-border rounded-lg text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
                </select>
                {/* Group filter (Task 22) */}
                <select
                  value={filterGroupName}
                  onChange={e => setFilterGroupName(e.target.value)}
                  className="px-3 py-2 bg-background/50 border border-border rounded-lg text-sm text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">All Groups</option>
                  {groupNames.map(gn => <option key={gn} value={gn}>{gn}</option>)}
                </select>
                {/* Clear button */}
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-muted hover:text-gray-900 hover:bg-gray-50/50 transition-colors">
                    <X className="w-4 h-4" /> Clear
                  </button>
                )}
              </div>
              {hasActiveFilters && (
                <p className="text-muted text-xs mt-2">Showing {filteredServices.length} of {extServices.length} services</p>
              )}
            </div>
          )}

          {/* ── GROUPED VIEW (Task 22) ─────────────────────── */}
          {groupViewMode === 'grouped' && groupedData.length > 0 && (
            <div className="space-y-4">
              {/* Group controls */}
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted">
                  {groupedData.length} group{groupedData.length !== 1 ? 's' : ''} &middot; {groupedData.reduce((a, g) => a + g.total, 0)} services
                </p>
                <div className="flex items-center gap-2">
                  <button onClick={expandAllGroups} className="text-xs text-muted hover:text-gray-900 transition-colors">Expand all</button>
                  <span className="text-gray-600">|</span>
                  <button onClick={collapseAllGroups} className="text-xs text-muted hover:text-gray-900 transition-colors">Collapse all</button>
                </div>
              </div>

              {/* Group Cards */}
              {groupedData.map(group => {
                const isExpanded = expandedGroups.has(group.group_name)
                return (
                  <div key={group.group_name} className="bg-surface/50 rounded-lg border border-border/50 overflow-hidden">
                    {/* Group Header */}
                    <button
                      className="w-full flex items-center justify-between p-4 hover:bg-gray-50/30 transition-colors"
                      onClick={() => toggleGroup(group.group_name)}
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded
                          ? <ChevronDown className="w-5 h-5 text-muted" />
                          : <ChevronRight className="w-5 h-5 text-muted" />}
                        {isExpanded
                          ? <FolderOpen className="w-5 h-5 text-emerald-400" />
                          : <Folder className="w-5 h-5 text-muted" />}
                        <div className="text-left">
                          <h3 className="text-gray-900 font-semibold text-sm">{group.group_name}</h3>
                          <p className="text-muted text-xs mt-0.5">
                            {group.total} service{group.total !== 1 ? 's' : ''}
                            {group.up > 0 && <span className="text-success ml-2">{group.up} up</span>}
                            {group.down > 0 && <span className="text-critical ml-2">{group.down} down</span>}
                            {group.total - group.up - group.down > 0 && <span className="text-warning ml-2">{group.total - group.up - group.down} other</span>}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <GroupHealthBadge status={group.status} />
                        {/* Health bar */}
                        <div className="w-24 h-2 bg-gray-50 rounded-full overflow-hidden flex">
                          {group.up > 0 && <div className="bg-success h-full" style={{ width: `${(group.up / group.total) * 100}%` }} />}
                          {group.total - group.up - group.down > 0 && <div className="bg-warning h-full" style={{ width: `${((group.total - group.up - group.down) / group.total) * 100}%` }} />}
                          {group.down > 0 && <div className="bg-critical h-full" style={{ width: `${(group.down / group.total) * 100}%` }} />}
                        </div>
                      </div>
                    </button>

                    {/* Expanded Service List */}
                    {isExpanded && (
                      <div className="border-t border-border/30">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-border/30">
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Service</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Type</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Category</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Environment</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Status</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Latency</th>
                              <th className="text-left px-4 py-2.5 text-muted font-medium text-xs uppercase tracking-wider">Last Check</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.services.map(svc => (
                              <tr key={svc.id} className="border-b border-border/20 hover:bg-gray-50/20 transition-colors">
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2.5">
                                    <div className={`p-1.5 rounded ${svc.enabled ? 'bg-emerald-400/10' : 'bg-gray-50/50'}`}>
                                      {svc.service_type === 'http'
                                        ? <Network className="w-3.5 h-3.5 text-violet-400" />
                                        : <Database className="w-3.5 h-3.5 text-orange-400" />}
                                    </div>
                                    <span className="text-gray-900 text-sm font-medium">{svc.name}</span>
                                  </div>
                                </td>
                                <td className="px-4 py-3"><TypeBadge type={svc.service_type} catalogType={svc.catalog_type} /></td>
                                <td className="px-4 py-3 text-sm text-muted">{svc.category || <span className="text-gray-600">&ndash;</span>}</td>
                                <td className="px-4 py-3 text-sm text-muted">{svc.environment || <span className="text-gray-600">&ndash;</span>}</td>
                                <td className="px-4 py-3"><StatusBadge status={svc.enabled ? svc.status : 'unknown'} /></td>
                                <td className="px-4 py-3 text-sm text-secondary">{svc.latency != null && svc.latency > 0 ? `${svc.latency.toFixed(0)}ms` : '-'}</td>
                                <td className="px-4 py-3 text-sm text-muted">{svc.last_check ? new Date(svc.last_check).toLocaleString() : 'Never'}</td>
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
            <div className="bg-surface/50 rounded-lg border border-border/50 p-16 text-center">
              <Globe className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-secondary mb-2">No external services connected</h3>
              <p className="text-muted max-w-md mx-auto mb-6">
                Connect your APIs and databases to start monitoring them with Rhinometric.
              </p>
              <div className="flex flex-wrap justify-center gap-3 mb-8">
                <TypeBadge type="http" />
                <TypeBadge type="postgresql" />
              </div>
              <button onClick={openCreate}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-gray-900 hover:bg-primary font-medium transition-colors shadow-md">
                <Plus className="w-5 h-5" /> Connect Your First Service
              </button>
            </div>
          ) : (
            /* Service table */
            <div className="bg-surface/50 rounded-lg border border-border/50 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left p-4 text-muted font-medium">Service</th>
                      <th className="text-left p-4 text-muted font-medium">Type</th>
                      <th className="text-left p-4 text-muted font-medium">Category</th>
                      <th className="text-left p-4 text-muted font-medium">Target</th>
                      <th className="text-left p-4 text-muted font-medium">Assertions</th>
                      <th className="text-left p-4 text-muted font-medium">Status</th>
                      <th className="text-left p-4 text-muted font-medium">Latency</th>
                      <th className="text-left p-4 text-muted font-medium">Last Check</th>
                      <th className="text-right p-4 text-muted font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredServices.length === 0 && hasActiveFilters && (
                      <tr><td colSpan={9} className="p-8 text-center text-muted">
                        <Search className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                        <p>No services match the current filters</p>
                        <button onClick={clearFilters} className="text-info hover:text-blue-300 text-sm mt-1">Clear filters</button>
                      </td></tr>
                    )}
                    {filteredServices.map(svc => (
                      <React.Fragment key={svc.id}>
                      <tr className={`border-b border-border/30 hover:bg-gray-50/30 transition-colors cursor-pointer ${!svc.enabled ? 'opacity-50' : ''}`}
                        onClick={() => setExpandedServiceId(expandedServiceId === svc.id ? null : svc.id)}>
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded ${svc.enabled ? 'bg-emerald-400/10' : 'bg-gray-50/50'}`}>
                              {svc.service_type === 'http' ? <Network className="w-4 h-4 text-violet-400" /> : <Database className="w-4 h-4 text-orange-400" />}
                            </div>
                            <div>
                              <p className="text-gray-900 font-medium">{svc.name}</p>
                              {svc.environment && <p className="text-muted text-xs">{svc.environment}</p>}
                              {svc.tags && svc.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {svc.tags.map((tag, i) => (
                                    <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-info-bg text-info">
                                      <Tag className="w-2.5 h-2.5" />{tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="p-4"><TypeBadge type={svc.service_type} catalogType={svc.catalog_type} /></td>
                        <td className="p-4 text-sm text-secondary">{svc.category || <span className="text-gray-600">&ndash;</span>}</td>
                        <td className="p-4">
                          <code className="text-sm text-secondary bg-background/50 px-2 py-1 rounded truncate max-w-[200px] inline-block">
                            {targetDisplay(svc)}
                          </code>
                        </td>
                        <td className="p-4">
                          {(svc as any).assertions_total > 0 ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-info-bg text-info">
                              <Shield className="w-3 h-3" />
                              {(svc as any).assertions_total} {(svc as any).assertions_total === 1 ? 'rule' : 'rules'}
                            </span>
                          ) : (
                            <span className="text-gray-600 text-xs">&mdash;</span>
                          )}
                        </td>
                        <td className="p-4"><StatusBadge status={svc.enabled ? svc.status : 'unknown'} /></td>
                        <td className="p-4 text-secondary text-sm">
                          {svc.last_response_time_ms != null ? `${svc.last_response_time_ms.toFixed(0)}ms` : '-'}
                        </td>
                        <td className="p-4 text-muted text-sm">
                          {svc.last_check_at ? new Date(svc.last_check_at).toLocaleString() : 'Never'}
                        </td>
                        <td className="p-4" onClick={e => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => canManage && handleTestSaved(svc.id)} disabled={!canManage || actionLoading === svc.id}
                              title={canManage ? "Test connection" : "Admin only"} className={`p-1.5 rounded transition-colors disabled:opacity-50 ${canManage ? 'hover:bg-gray-50/50 text-muted hover:text-success' : 'text-gray-600 cursor-not-allowed'}`}>
                              {actionLoading === svc.id ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            </button>
                            <button onClick={() => canManage && openEdit(svc)} disabled={!canManage}
                              title={canManage ? "Edit" : "Admin only"} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-50/50 text-muted hover:text-info' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              <Edit className="w-4 h-4" />
                            </button>
                            <button onClick={() => canManage && handleToggle(svc.id)} disabled={!canManage}
                              title={canManage ? (svc.enabled ? 'Disable' : 'Enable') : 'Admin only'} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-50/50 text-muted hover:text-warning' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              {svc.enabled ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                            </button>
                            <button onClick={() => canManage && handleDelete(svc.id)} disabled={!canManage}
                              title={canManage ? "Delete" : "Admin only"} className={`p-1.5 rounded transition-colors ${canManage ? 'hover:bg-gray-50/50 text-muted hover:text-critical' : 'text-gray-600 cursor-not-allowed opacity-50'}`}>
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                      {expandedServiceId === svc.id && (
                        <tr className="bg-background/40">
                          <td colSpan={9} className="p-0">
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

      {/* ── PLATFORM SERVICES TAB (HIDDEN) ───────────────────────────────── */}

            {/* Add Services Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface rounded-xl border border-border shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Add Services</h2>
                <p className="text-muted text-sm mt-0.5">Choose how you want to add endpoints</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="p-2 rounded-lg hover:bg-gray-50 text-muted hover:text-gray-900 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-3">
              <button onClick={() => { setShowAddModal(false); openCreate() }}
                className="w-full flex items-center gap-4 p-4 rounded-lg border border-border hover:border-blue-500/50 hover:bg-primary/5 transition-all text-left group">
                <div className="p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <Network className="w-6 h-6 text-info" />
                </div>
                <div className="flex-1">
                  <p className="text-gray-900 font-semibold">Single endpoint</p>
                  <p className="text-muted text-sm">Monitor one HTTP/API endpoint with full configuration</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-info transition-colors" />
              </button>
              <button onClick={() => { setShowAddModal(false); openBulkHttp() }}
                className="w-full flex items-center gap-4 p-4 rounded-lg border border-border hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all text-left group">
                <div className="p-3 rounded-lg bg-emerald-500/10 group-hover:bg-emerald-500/20 transition-colors">
                  <Layers className="w-6 h-6 text-emerald-400" />
                </div>
                <div className="flex-1">
                  <p className="text-gray-900 font-semibold">Multiple endpoints</p>
                  <p className="text-muted text-sm">Quickly add many endpoints with shared settings</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-emerald-400 transition-colors" />
              </button>
              <button onClick={() => { setShowAddModal(false); openImportModal() }}
                className="w-full flex items-center gap-4 p-4 rounded-lg border border-border hover:border-violet-500/50 hover:bg-violet-500/5 transition-all text-left group">
                <div className="p-3 rounded-lg bg-violet-500/10 group-hover:bg-violet-500/20 transition-colors">
                  <Upload className="w-6 h-6 text-violet-400" />
                </div>
                <div className="flex-1">
                  <p className="text-gray-900 font-semibold">Import file</p>
                  <p className="text-muted text-sm">Upload a CSV or JSON file with service definitions</p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-violet-400 transition-colors" />
              </button>
              <details className="pt-2">
                <summary className="text-xs text-muted cursor-pointer hover:text-muted">Advanced options</summary>
                <button onClick={() => { setShowAddModal(false); setFormType('postgresql'); setFormConfig({}); setView('create') }}
                  className="w-full mt-2 flex items-center gap-4 p-3 rounded-lg border border-border/50 hover:border-orange-500/30 hover:bg-orange-500/5 transition-all text-left group">
                  <div className="p-2 rounded-lg bg-orange-500/10">
                    <Database className="w-5 h-5 text-orange-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium text-sm">PostgreSQL database</p>
                    <p className="text-muted text-xs">Monitor database connectivity</p>
                  </div>
                </button>
              </details>
            </div>
          </div>
        </div>
      )}

      {/* ── BULK IMPORT MODAL ────────────────────────────────── */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-surface rounded-xl border border-border shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-info/10 rounded-lg"><Upload className="w-5 h-5 text-info" /></div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Import File</h2>
                  <p className="text-muted text-sm">Upload a CSV or JSON file with service definitions</p>
                </div>
              </div>
              <button onClick={closeImportModal} className="p-2 rounded-lg hover:bg-gray-50 text-muted hover:text-gray-900 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Read-only banner for non-admin users */}
              {!canManage && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-warning/10 border border-yellow-500/30">
                  <Lock className="w-5 h-5 text-warning flex-shrink-0" />
                  <p className="text-yellow-300 text-sm">
                    <span className="font-medium">View-only mode.</span> You can explore the configuration but only administrators can create or modify services.
                  </p>
                </div>
              )}

              {/* Step 1: Upload */}
              {importStep === 'upload' && (
                <>
                  {/* Templates */}
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-background/50 border border-border/50">
                    <FileText className="w-4 h-4 text-muted flex-shrink-0" />
                    <span className="text-muted text-sm">Download template:</span>
                    <button onClick={() => downloadTemplate('csv')} className="text-info hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" /> CSV
                    </button>
                    <button onClick={() => downloadTemplate('json')} className="text-info hover:text-blue-300 text-sm font-medium flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" /> JSON
                    </button>
                  </div>

                  {/* File input */}
                  <div className="space-y-3">
                    <label className="block">
                      <div className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${!canManage ? 'border-border bg-surface/30 cursor-not-allowed opacity-60' : importFile ? 'border-blue-500/50 bg-primary/5 cursor-pointer' : 'border-border hover:border-gray-500 cursor-pointer'}`}>
                        <input type="file" accept=".csv,.json" className="hidden" disabled={!canManage}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => { if (canManage && e.target.files?.[0]) setImportFile(e.target.files[0]) }} />
                        {importFile ? (
                          <div className="space-y-1">
                            <FileText className="w-8 h-8 text-info mx-auto" />
                            <p className="text-gray-900 font-medium">{importFile.name}</p>
                            <p className="text-muted text-sm">{(importFile.size / 1024).toFixed(1)} KB</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <Upload className="w-8 h-8 text-muted mx-auto" />
                            <p className="text-secondary">Click to select a file</p>
                            <p className="text-muted text-sm">Supports .csv and .json (max 1 MB, 200 services)</p>
                          </div>
                        )}
                      </div>
                    </label>
                  </div>

                  {/* Expected columns help */}
                  <details className="text-sm">
                    <summary className="text-muted cursor-pointer hover:text-secondary">Expected columns &amp; aliases</summary>
                    <div className="mt-2 p-3 bg-background/50 rounded-lg border border-border/50 text-muted text-xs space-y-1">
                      <p><span className="text-secondary">Required:</span> name. <span className="text-secondary">service_type</span> (web_app | rest_api | soap_api | webhook | external_api | database | other | http | postgresql) — defaults to &quot;other&quot; if omitted</p>
                      <p><span className="text-secondary">HTTP:</span> url, method, health_path, auth_type, auth_value</p>
                      <p><span className="text-secondary">PostgreSQL:</span> host, port, database_name, username, password</p>
                      <p><span className="text-secondary">Optional:</span> environment, description, timeout_seconds, check_interval_seconds, enabled, catalog_type, category, tags</p>
                      <p className="pt-1 border-t border-border/30"><span className="text-secondary">Aliases accepted:</span> type or serviceType &rarr; service_type &bull; target or endpoint &rarr; url &bull; catalogType &rarr; catalog_type &bull; timeout &rarr; timeout_seconds &bull; checkInterval &rarr; check_interval_seconds &bull; authType &rarr; auth_type &bull; authValue &rarr; auth_value</p>
                      <p><span className="text-secondary">Delimiters:</span> CSV can use comma, semicolon, or tab as column separator (auto-detected)</p>
                      <p><span className="text-secondary">Tags:</span> comma, semicolon, or pipe separated (e.g. &quot;critical,external,api&quot;)</p>
                      <p><span className="text-secondary">Auth:</span> leave auth_type empty if not needed &mdash; do not use &quot;None&quot;</p>
                    </div>
                  </details>

                  {/* Action */}
                  <div className="flex justify-end gap-3 pt-2">
                    <button onClick={closeImportModal} className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">Cancel</button>
                    <button onClick={canManage ? handleImportValidate : undefined} disabled={!canManage || !importFile || importLoading}
                      title={!canManage ? 'Only administrators can import services' : ''}
                      className="flex items-center gap-2 px-5 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
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
                    <div className="p-4 rounded-lg bg-critical/10 border border-red-500/30 text-critical">
                      <p className="font-medium">Validation failed</p>
                      <p className="text-sm mt-1">{importPreview.error}</p>
                    </div>
                  ) : (
                    <>
                      {/* Summary cards */}
                      <div className="grid grid-cols-4 gap-3">
                        {[
                          { label: 'Total', value: importPreview.total_received, color: 'text-secondary' },
                          { label: 'Valid', value: importPreview.valid_count, color: 'text-success' },
                          { label: 'Invalid', value: importPreview.invalid_count, color: 'text-critical' },
                          { label: 'Duplicates', value: importPreview.duplicate_count, color: 'text-warning' },
                        ].map((c: { label: string; value: number; color: string }) => (
                          <div key={c.label} className="bg-background/50 rounded-lg p-3 border border-border/50 text-center">
                            <p className="text-muted text-xs">{c.label}</p>
                            <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
                          </div>
                        ))}
                      </div>

                      {/* Valid services preview */}
                      {importPreview.valid_preview?.length > 0 && (
                        <div>
                          <p className="text-sm text-muted mb-2">Services to be created:</p>
                          <div className="max-h-40 overflow-y-auto bg-background/50 rounded-lg border border-border/50">
                            <table className="w-full text-sm">
                              <thead><tr className="border-b border-border/50">
                                <th className="text-left p-2 text-muted text-xs">Row</th>
                                <th className="text-left p-2 text-muted text-xs">Name</th>
                                <th className="text-left p-2 text-muted text-xs">Type</th>
                                <th className="text-left p-2 text-muted text-xs">Target</th>
                              </tr></thead>
                              <tbody>
                                {importPreview.valid_preview.map((s: any) => (
                                  <tr key={s.row} className="border-b border-border/30">
                                    <td className="p-2 text-muted">{s.row}</td>
                                    <td className="p-2 text-gray-900">{s.name}</td>
                                    <td className="p-2 text-muted">{s.service_type}</td>
                                    <td className="p-2 text-muted truncate max-w-[200px]">{s.target}</td>
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
                          <p className="text-sm text-muted mb-2">Issues found:</p>
                          <div className="max-h-40 overflow-y-auto space-y-1">
                            {importPreview.errors.map((e: any, i: number) => (
                              <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-warning/10 border border-yellow-500/20 text-warning' : 'bg-critical/10 border border-red-500/20 text-critical'}`}>
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
                      className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">
                      ← Back
                    </button>
                    <div className="flex gap-3">
                      <button onClick={closeImportModal} className="px-4 py-2 rounded-lg text-muted hover:text-gray-900 transition-colors">Cancel</button>
                      {importPreview && !importPreview.error && importPreview.valid_count > 0 && (
                        <button onClick={canManage ? handleImportConfirm : undefined} disabled={!canManage || importLoading}
                          title={!canManage ? 'Only administrators can import services' : ''}
                          className="flex items-center gap-2 px-5 py-2 rounded-lg bg-green-600 text-white hover:bg-success disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors">
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
                    <div className="p-4 rounded-lg bg-critical/10 border border-red-500/30 text-critical">
                      <p className="font-medium">Import failed</p>
                      <p className="text-sm mt-1">{importResult.error}</p>
                    </div>
                  ) : (
                    <>
                      <div className={`p-4 rounded-lg border ${importResult.created_count > 0 ? 'bg-success/10 border-green-500/30' : 'bg-warning/10 border-yellow-500/30'}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className={`w-5 h-5 ${importResult.created_count > 0 ? 'text-success' : 'text-warning'}`} />
                          <span className={`font-medium ${importResult.created_count > 0 ? 'text-success' : 'text-warning'}`}>
                            Import complete
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <div><span className="text-muted">Created:</span> <span className="text-success font-medium">{importResult.created_count}</span></div>
                          <div><span className="text-muted">Skipped:</span> <span className="text-warning font-medium">{importResult.skipped_count}</span></div>
                          <div><span className="text-muted">Invalid:</span> <span className="text-critical font-medium">{importResult.invalid_count}</span></div>
                        </div>
                      </div>

                      {/* Created services list */}
                      {importResult.created_services?.length > 0 && (
                        <div>
                          <p className="text-sm text-muted mb-2">Created services:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {importResult.created_services.map((s: any) => (
                              <div key={s.id} className="flex items-center gap-2 p-2 bg-success/5 rounded text-sm border border-green-500/10">
                                <CheckCircle className="w-3.5 h-3.5 text-success flex-shrink-0" />
                                <span className="text-slate-900">{s.name}</span>
                                <span className="text-muted">({s.service_type})</span>
                                <span className="text-gray-600 ml-auto">id={s.id}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {importResult.errors?.length > 0 && (
                        <div>
                          <p className="text-sm text-muted mb-2">Issues:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {importResult.errors.map((e: any, i: number) => (
                              <div key={i} className={`p-2 rounded text-xs ${e.status === 'skipped' ? 'bg-warning/10 text-warning' : 'bg-critical/10 text-critical'}`}>
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
                      className="px-5 py-2 rounded-lg bg-primary text-gray-900 hover:bg-primary font-medium transition-colors">
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