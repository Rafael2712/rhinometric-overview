import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search, SlidersHorizontal, RefreshCw, X, FileText,
  Copy, Download, Bug, Info, AlertTriangle, Flame, XCircle,
  Clock, Server,
} from 'lucide-react';
import { useAuthStore } from '../lib/auth/store';

/* ============================================================== *
 *  TYPES
 * ============================================================== */

interface LogEntry {
  timestamp: string;
  message: string;
  level: string;
  source_type: string;
  service_type: string;
  fields: Record<string, any>;
  stream: Record<string, string>;
}

interface FiltersData {
  levels: string[];
  source_types: string[];
  services: string[];
  service_types: string[];
  methods: string[];
  status_codes: string[];
}

interface EnrichedResponse {
  status: string;
  data: {
    entries: LogEntry[];
    total: number;
    total_before_filters: number;
    filters: FiltersData;
  };
}

/* ============================================================== *
 *  CONSTANTS
 * ============================================================== */

const TIME_RANGES = [
  { label: '15 min', value: 15 * 60 },
  { label: '1 hora', value: 60 * 60 },
  { label: '6 horas', value: 6 * 60 * 60 },
  { label: '24 horas', value: 24 * 60 * 60 },
  { label: '7 dias', value: 7 * 24 * 60 * 60 },
];

type LevelCfg = { icon: any; color: string; bg: string; label: string };

const LEVEL_CONFIG: Record<string, LevelCfg> = {
  debug: { icon: Bug, color: 'text-gray-400', bg: 'bg-gray-500/20', label: 'DEBUG' },
  info:  { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'INFO' },
  warn:  { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'WARN' },
  error: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20', label: 'ERROR' },
  fatal: { icon: Flame, color: 'text-red-300', bg: 'bg-red-700/30', label: 'FATAL' },
  unknown: { icon: Info, color: 'text-gray-500', bg: 'bg-gray-600/20', label: 'UNKNOWN' },
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  access_log: 'HTTP Access',
  error_log: 'Error Log',
  collector_cycle: 'Collector Cycle',
  collector_signal: 'Collector Signal',
  application: 'Application',
};

const SERVICE_TYPE_LABELS: Record<string, string> = {
  http_api: 'HTTP API',
  web_app: 'Web App',
  database_postgres: 'PostgreSQL',
  collector: 'Collector',
  unknown: 'Unknown',
};

const SERVICE_TYPE_COLORS: Record<string, string> = {
  http_api: 'text-cyan-400 bg-cyan-500/20',
  web_app: 'text-green-400 bg-green-500/20',
  database_postgres: 'text-purple-400 bg-purple-500/20',
  collector: 'text-orange-400 bg-orange-500/20',
  unknown: 'text-gray-400 bg-gray-500/20',
};

const STATUS_CODE_GROUPS = [
  { label: '2xx OK', value: '2xx' },
  { label: '3xx Redirect', value: '3xx' },
  { label: '4xx Client Err', value: '4xx' },
  { label: '5xx Server Err', value: '5xx' },
];

const LIMIT_OPTIONS = [50, 100, 250];

const SEVERITY_OPTIONS = [
  { value: 'fatal', label: 'Fatal' },
  { value: 'error', label: 'Error' },
  { value: 'warn', label: 'Warn' },
  { value: 'info', label: 'Info' },
  { value: 'debug', label: 'Debug' },
  { value: 'unknown', label: 'Unknown' },
];

/* ============================================================== *
 *  HELPERS
 * ============================================================== */

function formatTimestamp(nanos: string): string {
  try {
    const ms = parseInt(nanos) / 1e6;
    const d = new Date(ms);
    return d.toLocaleString('es-ES', {
      day: '2-digit', month: '2-digit', year: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return nanos;
  }
}

function formatTimestampShort(nanos: string): string {
  try {
    const ms = parseInt(nanos) / 1e6;
    const d = new Date(ms);
    return d.toLocaleTimeString('es-ES', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return nanos;
  }
}

function statusCodeClass(code: number): string {
  if (code >= 500) return 'text-red-400';
  if (code >= 400) return 'text-yellow-400';
  if (code >= 300) return 'text-cyan-400';
  if (code >= 200) return 'text-green-400';
  return 'text-gray-400';
}

/* ============================================================== *
 *  FILTER BAR COMPONENT
 * ============================================================== */

function FilterBar({
  search, setSearch, serviceType, setServiceType, service, setService, level, setLevel,
  sourceType, setSourceType, method, setMethod, statusCode, setStatusCode,
  pathContains, setPathContains, timeRange, setTimeRange, limit, setLimit,
  availableFilters, activeFilterCount, onClearAll, onRefresh, isLoading,
}: {
  search: string; setSearch: (v: string) => void;
  serviceType: string; setServiceType: (v: string) => void;
  service: string; setService: (v: string) => void;
  level: string; setLevel: (v: string) => void;
  sourceType: string; setSourceType: (v: string) => void;
  method: string; setMethod: (v: string) => void;
  statusCode: string; setStatusCode: (v: string) => void;
  pathContains: string; setPathContains: (v: string) => void;
  timeRange: number; setTimeRange: (v: number) => void;
  limit: number; setLimit: (v: number) => void;
  availableFilters: FiltersData | null;
  activeFilterCount: number;
  onClearAll: () => void;
  onRefresh: () => void;
  isLoading: boolean;
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <div className="space-y-3">
      {/* Row 1: Search + Time + Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar en logs..."
            className="input pl-10 w-full"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-4 h-4 text-gray-400 hover:text-white" />
            </button>
          )}
        </div>

        {/* Time range */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="input w-36"
        >
          {TIME_RANGES.map(t => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>

        {/* Limit */}
        <select
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          className="input w-28"
        >
          {LIMIT_OPTIONS.map(l => (
            <option key={l} value={l}>{l} lineas</option>
          ))}
        </select>

        {/* Toggle filters */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`btn ${showAdvanced ? 'btn-primary' : 'btn-secondary'} flex items-center gap-1.5 relative`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span className="hidden sm:inline">Filtros</span>
          {activeFilterCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-primary rounded-full text-[10px] font-bold text-white flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>

        {/* Clear all */}
        {activeFilterCount > 0 && (
          <button onClick={onClearAll} className="btn btn-secondary text-red-400 hover:text-red-300 flex items-center gap-1.5">
            <X className="w-4 h-4" />
            <span className="hidden sm:inline">Limpiar</span>
          </button>
        )}

        {/* Refresh */}
        <button onClick={onRefresh} className="btn btn-secondary flex items-center gap-1.5" disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Row 2: Quick filters — always visible when panel is open */}
      {showAdvanced && (
        <>
          <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-surface-light/30 border border-white/5">
            {/* Service Type */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Tipo servicio</label>
              <select value={serviceType} onChange={(e) => setServiceType(e.target.value)} className="input w-full text-sm">
                <option value="">Todos</option>
                {(availableFilters?.service_types ?? []).map(st => (
                  <option key={st} value={st}>{SERVICE_TYPE_LABELS[st] ?? st}</option>
                ))}
              </select>
            </div>

            {/* Service */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Servicio</label>
              <select value={service} onChange={(e) => setService(e.target.value)} className="input w-full text-sm">
                <option value="">Todos</option>
                {(availableFilters?.services ?? []).map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Severity — canonical list */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Severidad</label>
              <select value={level} onChange={(e) => setLevel(e.target.value)} className="input w-full text-sm">
                <option value="">Todas</option>
                {SEVERITY_OPTIONS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 3: Advanced filters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 rounded-lg bg-surface-light/20 border border-white/5">
            {/* Source type */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Tipo evento</label>
              <select value={sourceType} onChange={(e) => setSourceType(e.target.value)} className="input w-full text-sm">
                <option value="">Todos</option>
                {(availableFilters?.source_types ?? []).map(t => (
                  <option key={t} value={t}>{SOURCE_TYPE_LABELS[t] ?? t}</option>
                ))}
              </select>
            </div>

            {/* HTTP Status */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">HTTP status</label>
              <select value={statusCode} onChange={(e) => setStatusCode(e.target.value)} className="input w-full text-sm">
                <option value="">Todos</option>
                {STATUS_CODE_GROUPS.map(g => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
                {(availableFilters?.status_codes ?? []).map(sc => (
                  <option key={sc} value={sc}>{sc}</option>
                ))}
              </select>
            </div>

            {/* HTTP Method */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Metodo HTTP</label>
              <select value={method} onChange={(e) => setMethod(e.target.value)} className="input w-full text-sm">
                <option value="">Todos</option>
                {(availableFilters?.methods ?? []).map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {/* Path contains */}
            <div>
              <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 block">Path</label>
              <input
                type="text"
                value={pathContains}
                onChange={(e) => setPathContains(e.target.value)}
                placeholder="/api/..."
                className="input w-full text-sm"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* ============================================================== *
 *  LOG ROW COMPONENT
 * ============================================================== */

function LogRow({ entry, isSelected, onClick, searchTerm }: {
  entry: LogEntry; isSelected: boolean; onClick: () => void; searchTerm: string;
}) {
  const lc = LEVEL_CONFIG[entry.level] ?? LEVEL_CONFIG.info;
  const LevelIcon = lc.icon;
  const { fields, stream } = entry;

  const serviceName = stream.service_name ?? stream.job ?? stream.service ?? '—';
  const hasHttp = fields.method && fields.status_code;

  const renderMessage = useCallback((msg: string) => {
    if (!searchTerm) return msg;
    try {
      const re = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      const parts = msg.split(re);
      return parts.map((part: string, i: number) =>
        re.test(part) ? <mark key={i} className="bg-yellow-500/40 text-yellow-200 rounded px-0.5">{part}</mark> : part
      );
    } catch {
      return msg;
    }
  }, [searchTerm]);

  return (
    <div
      onClick={onClick}
      className={`group flex items-start gap-2 px-3 py-2 cursor-pointer border-l-2 transition-all duration-100 hover:bg-white/[0.03] ${
        isSelected
          ? 'border-l-primary bg-primary/5'
          : 'border-l-transparent'
      }`}
    >
      {/* Timestamp */}
      <span className="text-[11px] text-gray-500 font-mono whitespace-nowrap mt-0.5 min-w-[70px]">
        {formatTimestampShort(entry.timestamp)}
      </span>

      {/* Level badge */}
      <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wide ${lc.color} ${lc.bg} min-w-[52px] justify-center`}>
        <LevelIcon className="w-3 h-3" />
        {lc.label}
      </span>

      {/* Source type */}
      <span className="text-[10px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded min-w-[80px] text-center truncate hidden lg:inline-block">
        {SOURCE_TYPE_LABELS[entry.source_type] ?? entry.source_type}
      </span>

      {/* Service type */}
      {entry.service_type && entry.service_type !== 'unknown' && (
        <span className={`text-[10px] px-1.5 py-0.5 rounded min-w-[60px] text-center truncate hidden lg:inline-block ${SERVICE_TYPE_COLORS[entry.service_type] || 'text-gray-400 bg-gray-500/20'}`}>
          {SERVICE_TYPE_LABELS[entry.service_type] || entry.service_type}
        </span>
      )}

      {/* Service */}
      <span className="text-[11px] text-cyan-400 truncate min-w-[100px] max-w-[160px] hidden md:inline-block" title={serviceName}>
        {serviceName}
      </span>

      {/* HTTP info (if access log) */}
      {hasHttp ? (
        <span className="flex items-center gap-1.5 min-w-[180px] max-w-[260px] shrink-0 hidden xl:flex">
          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1 rounded">
            {fields.method}
          </span>
          <span className={`text-[10px] font-mono ${statusCodeClass(Number(fields.status_code))}`}>
            {fields.status_code}
          </span>
          <span className="text-[11px] text-gray-400 truncate font-mono" title={fields.full_path ?? fields.path}>
            {fields.path}
          </span>
        </span>
      ) : (
        <span className="min-w-[180px] hidden xl:block" />
      )}

      {/* Message */}
      <span className="text-[11px] text-gray-300 truncate flex-1 min-w-0 font-mono leading-5">
        {renderMessage(entry.message.substring(0, 300))}
      </span>
    </div>
  );
}

/* ============================================================== *
 *  DETAIL PANEL COMPONENT
 * ============================================================== */

function DetailPanel({ entry, onClose }: { entry: LogEntry; onClose: () => void }) {
  const [tab, setTab] = useState<'parsed' | 'raw' | 'stream'>('parsed');
  const lc = LEVEL_CONFIG[entry.level] ?? LEVEL_CONFIG.info;
  const LevelIcon = lc.icon;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const tabs = [
    { id: 'parsed' as const, label: 'Campos' },
    { id: 'raw' as const, label: 'Mensaje raw' },
    { id: 'stream' as const, label: 'Stream labels' },
  ];

  return (
    <div className="card p-0 overflow-hidden border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/5 bg-surface-light/30">
        <div className="flex items-center gap-3 min-w-0">
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${lc.color} ${lc.bg}`}>
            <LevelIcon className="w-4 h-4" />
            {lc.label}
          </span>
          <span className="text-xs text-gray-400 font-mono">
            {formatTimestamp(entry.timestamp)}
          </span>
          <span className="text-xs text-cyan-400">
            {entry.stream.service_name ?? entry.stream.job ?? '—'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => copyToClipboard(JSON.stringify(entry, null, 2))}
            className="btn btn-secondary p-1.5"
            title="Copiar JSON"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button onClick={onClose} className="btn btn-secondary p-1.5">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-xs font-medium transition-colors ${
              tab === t.id ? 'text-primary border-b-2 border-primary' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 max-h-[50vh] overflow-y-auto">
        {tab === 'parsed' && (
          <div className="space-y-3">
            {/* Summary cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <FieldCard label="Tipo" value={SOURCE_TYPE_LABELS[entry.source_type] ?? entry.source_type} />
              <FieldCard label="Tipo Servicio" value={SERVICE_TYPE_LABELS[entry.service_type] || entry.service_type || 'unknown'} />
              <FieldCard label="Level" value={entry.level.toUpperCase()} color={lc.color} />
              {entry.fields.method && <FieldCard label="Metodo" value={entry.fields.method} color="text-emerald-400" />}
              {entry.fields.status_code != null && <FieldCard label="Status" value={String(entry.fields.status_code)} color={statusCodeClass(Number(entry.fields.status_code))} />}
              {entry.fields.path && <FieldCard label="Path" value={entry.fields.path} mono />}
              {entry.fields.full_path && entry.fields.full_path !== entry.fields.path && <FieldCard label="Full path" value={entry.fields.full_path} mono />}
              {entry.fields.client_ip && <FieldCard label="IP" value={entry.fields.client_ip} mono />}
              {entry.fields.response_bytes && <FieldCard label="Bytes" value={entry.fields.response_bytes} />}
              {entry.fields.duration_ms != null && <FieldCard label="Duracion" value={`${entry.fields.duration_ms}ms`} />}
              {entry.fields.signal && <FieldCard label="Signal" value={entry.fields.signal} />}
              {entry.fields.cycle_num != null && <FieldCard label="Cycle" value={`#${entry.fields.cycle_num}`} />}
              {entry.fields.ok_count != null && <FieldCard label="OK/Total" value={`${entry.fields.ok_count}/${entry.fields.total_signals}`} />}
              {entry.fields.module && <FieldCard label="Module" value={entry.fields.module} />}
              {entry.fields.error_message && <FieldCard label="Error" value={entry.fields.error_message} color="text-red-400" />}
              {entry.fields.access_time && <FieldCard label="Timestamp" value={entry.fields.access_time} mono />}
            </div>

            {/* All fields JSON */}
            <div className="mt-4">
              <h4 className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Todos los campos parseados</h4>
              <pre className="text-xs text-gray-300 bg-black/30 rounded-lg p-3 overflow-x-auto font-mono">
                {JSON.stringify(entry.fields, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {tab === 'raw' && (
          <div>
            <div className="flex justify-end mb-2">
              <button
                onClick={() => copyToClipboard(entry.message)}
                className="btn btn-secondary text-xs flex items-center gap-1"
              >
                <Copy className="w-3.5 h-3.5" />
                Copiar
              </button>
            </div>
            <pre className="text-xs text-gray-200 bg-black/30 rounded-lg p-4 overflow-x-auto font-mono whitespace-pre-wrap break-all leading-5">
              {entry.message}
            </pre>
          </div>
        )}

        {tab === 'stream' && (
          <div className="space-y-1">
            {Object.entries(entry.stream).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 py-1.5 border-b border-white/5 last:border-0">
                <span className="text-[11px] text-gray-500 font-mono min-w-[120px]">{k}</span>
                <span className="text-[11px] text-gray-200 font-mono break-all">{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function FieldCard({ label, value, color, mono }: { label: string; value: string; color?: string; mono?: boolean }) {
  return (
    <div className="bg-black/20 rounded-lg px-3 py-2">
      <div className="text-[9px] uppercase tracking-wider text-gray-500">{label}</div>
      <div className={`text-sm truncate ${color ?? 'text-gray-200'} ${mono ? 'font-mono text-xs' : ''}`} title={value}>
        {value}
      </div>
    </div>
  );
}

/* ============================================================== *
 *  STATS BAR COMPONENT
 * ============================================================== */

function StatsBar({ total, totalBeforeFilters, filters, isLoading, lastRefresh }: {
  total: number; totalBeforeFilters: number; filters: FiltersData | null; isLoading: boolean; lastRefresh: Date | null;
}) {
  return (
    <div className="flex items-center justify-between px-1 py-1.5">
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-400">
          <span className="text-gray-200 font-semibold">{total}</span>
          {totalBeforeFilters > 0 && totalBeforeFilters !== total && (
            <span> de {totalBeforeFilters}</span>
          )}
          {' '}lineas
        </span>

        {filters && (
          <div className="flex items-center gap-1.5">
            {filters.levels.map(l => {
              const cfg = LEVEL_CONFIG[l];
              return cfg ? (
                <span key={l} className={`text-[10px] px-1.5 py-0.5 rounded ${cfg.bg} ${cfg.color}`}>
                  {cfg.label}
                </span>
              ) : null;
            })}
          </div>
        )}

        {filters && filters.services.length > 0 && (
          <div className="flex items-center gap-1 text-[10px] text-gray-400">
            <Server className="w-3 h-3" />
            <span>{filters.services.length} servicio{filters.services.length > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 text-[10px] text-gray-500">
        {isLoading && <span className="text-primary animate-pulse">Cargando...</span>}
        {lastRefresh && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {lastRefresh.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        )}
      </div>
    </div>
  );
}

/* ============================================================== *
 *  EMPTY STATE COMPONENT
 * ============================================================== */

function EmptyState({ hasFilters, isError }: { hasFilters: boolean; isError?: boolean }) {
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <XCircle className="w-12 h-12 text-red-400/50 mb-4" />
        <h3 className="text-lg font-medium text-gray-200 mb-1">Error al consultar logs</h3>
        <p className="text-sm text-gray-400">No se pudo conectar con el servicio de logs. Verifica la conexion.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <FileText className="w-12 h-12 text-gray-600 mb-4" />
      <h3 className="text-lg font-medium text-gray-200 mb-1">
        {hasFilters ? 'Sin resultados para estos filtros' : 'No hay logs en este periodo'}
      </h3>
      <p className="text-sm text-gray-400 max-w-md">
        {hasFilters
          ? 'Intenta ampliar el rango de tiempo o ajustar los filtros aplicados.'
          : 'No se encontraron logs de servicios del cliente en el periodo seleccionado. Verifica que los servicios esten enviando datos.'}
      </p>
    </div>
  );
}

/* ============================================================== *
 *  MAIN LOGS PAGE
 * ============================================================== */

export function LogsPage() {
  const token = useAuthStore((state) => state.token);

  /* --- Filters state --- */
  const [search, setSearch] = useState('');
  const [service, setService] = useState('');
  const [level, setLevel] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [method, setMethod] = useState('');
  const [statusCode, setStatusCode] = useState('');
  const [pathContains, setPathContains] = useState('');
  const [serviceType, setServiceType] = useState('');
  const [timeRange, setTimeRange] = useState(60 * 60);
  const [limit, setLimit] = useState(100);

  /* --- UI state --- */
  const [selectedEntry, setSelectedEntry] = useState<LogEntry | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  /* --- Debounced search --- */
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  const [debouncedPath, setDebouncedPath] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedPath(pathContains), 400);
    return () => clearTimeout(t);
  }, [pathContains]);

  /* --- Active filter count --- */
  const activeFilterCount = useMemo(() => {
    let n = 0;
    if (serviceType) n++;
    if (service) n++;
    if (level) n++;
    if (sourceType) n++;
    if (method) n++;
    if (statusCode) n++;
    if (debouncedPath) n++;
    if (debouncedSearch) n++;
    return n;
  }, [serviceType, service, level, sourceType, method, statusCode, debouncedPath, debouncedSearch]);

  const clearAllFilters = useCallback(() => {
    setSearch('');
    setServiceType('');
    setService('');
    setLevel('');
    setSourceType('');
    setMethod('');
    setStatusCode('');
    setPathContains('');
  }, []);

  /* --- Query params --- */
  const queryParams = useMemo(() => {
    const now = Date.now() * 1e6;
    const start = (Date.now() - timeRange * 1000) * 1e6;
    const params: Record<string, string> = {
      query: '{}',
      start: String(Math.floor(start)),
      end: String(Math.floor(now)),
      limit: String(limit),
      direction: 'backward',
    };
    if (serviceType) params.service_type = serviceType;
    if (service) params.service = service;
    if (level) params.level = level;
    if (sourceType) params.source_type = sourceType;
    if (method) params.method = method;
    if (statusCode) params.status_code = statusCode;
    if (debouncedPath) params.path_contains = debouncedPath;
    if (debouncedSearch) params.search = debouncedSearch;
    return params;
  }, [timeRange, limit, serviceType, service, level, sourceType, method, statusCode, debouncedPath, debouncedSearch]);

  /* --- Data fetching --- */
  const { data, isLoading, isError, refetch } = useQuery<EnrichedResponse>({
    queryKey: ['logs-enriched', queryParams],
    queryFn: async () => {
      const qs = new URLSearchParams(queryParams).toString();
      const res = await fetch(`/api/logs/enriched?${qs}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setLastRefresh(new Date());
      return res.json();
    },
    refetchInterval: autoRefresh ? 10000 : false,
    staleTime: 5000,
    retry: 1,
  });

  const entries = data?.data?.entries ?? [];
  const total = data?.data?.total ?? 0;
  const totalBeforeFilters = data?.data?.total_before_filters ?? 0;
  const availableFilters = data?.data?.filters ?? null;

  /* --- Hierarchical: reset service when type changes --- */
  useEffect(() => {
    if (service && availableFilters?.services && !availableFilters.services.includes(service)) {
      setService('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serviceType, availableFilters?.services]);

  /* --- Keyboard navigation --- */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedEntry(null);
        return;
      }
      if (!selectedEntry || entries.length === 0) return;
      const idx = entries.findIndex(en => en.timestamp === selectedEntry.timestamp && en.message === selectedEntry.message);
      if (e.key === 'ArrowDown' && idx < entries.length - 1) {
        e.preventDefault();
        setSelectedEntry(entries[idx + 1]);
      } else if (e.key === 'ArrowUp' && idx > 0) {
        e.preventDefault();
        setSelectedEntry(entries[idx - 1]);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedEntry, entries]);

  /* --- Export --- */
  const handleExport = useCallback(() => {
    const blob = new Blob([JSON.stringify(entries, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-export-${new Date().toISOString().slice(0, 19)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [entries]);

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Log Explorer</h1>
          <p className="text-sm text-gray-400 mt-0.5">Consulta y analiza logs de tus servicios</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn ${autoRefresh ? 'btn-primary' : 'btn-secondary'} text-xs flex items-center gap-1.5`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto ON' : 'Auto OFF'}
          </button>

          {/* Export */}
          <button
            onClick={handleExport}
            disabled={entries.length === 0}
            className="btn btn-secondary text-xs flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Exportar
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="card p-4">
        <FilterBar
          search={search} setSearch={setSearch}
          serviceType={serviceType} setServiceType={setServiceType}
          service={service} setService={setService}
          level={level} setLevel={setLevel}
          sourceType={sourceType} setSourceType={setSourceType}
          method={method} setMethod={setMethod}
          statusCode={statusCode} setStatusCode={setStatusCode}
          pathContains={pathContains} setPathContains={setPathContains}
          timeRange={timeRange} setTimeRange={setTimeRange}
          limit={limit} setLimit={setLimit}
          availableFilters={availableFilters}
          activeFilterCount={activeFilterCount}
          onClearAll={clearAllFilters}
          onRefresh={() => refetch()}
          isLoading={isLoading}
        />
      </div>

      {/* Stats bar */}
      <StatsBar
        total={total}
        totalBeforeFilters={totalBeforeFilters}
        filters={availableFilters}
        isLoading={isLoading}
        lastRefresh={lastRefresh}
      />

      {/* Results */}
      <div className="flex gap-4">
        {/* Log list */}
        <div className={`card p-0 overflow-hidden flex-1 min-w-0 ${selectedEntry ? 'max-w-[60%]' : ''}`}>
          {/* Column headers */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-surface-light/20 text-[10px] uppercase tracking-wider text-gray-500">
            <span className="min-w-[70px]">Hora</span>
            <span className="min-w-[52px] text-center">Level</span>
            <span className="min-w-[80px] text-center hidden lg:inline-block">Tipo</span>
            <span className="min-w-[100px] hidden md:inline-block">Servicio</span>
            <span className="min-w-[180px] hidden xl:block">HTTP</span>
            <span className="flex-1">Mensaje</span>
          </div>

          {/* Log entries */}
          <div ref={listRef} className="max-h-[calc(100vh-340px)] overflow-y-auto divide-y divide-white/[0.03]">
            {isLoading && entries.length === 0 ? (
              <div className="flex items-center justify-center py-16">
                <RefreshCw className="w-6 h-6 text-primary animate-spin" />
              </div>
            ) : isError ? (
              <EmptyState hasFilters={false} isError />
            ) : entries.length === 0 ? (
              <EmptyState hasFilters={activeFilterCount > 0} />
            ) : (
              entries.map((entry, i) => (
                <LogRow
                  key={`${entry.timestamp}-${i}`}
                  entry={entry}
                  isSelected={selectedEntry?.timestamp === entry.timestamp && selectedEntry?.message === entry.message}
                  onClick={() => setSelectedEntry(
                    selectedEntry?.timestamp === entry.timestamp && selectedEntry?.message === entry.message
                      ? null
                      : entry
                  )}
                  searchTerm={debouncedSearch}
                />
              ))
            )}
          </div>
        </div>

        {/* Detail panel */}
        {selectedEntry && (
          <div className="w-[40%] min-w-[350px] max-w-[500px]">
            <DetailPanel entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
          </div>
        )}
      </div>
    </div>
  );
}
