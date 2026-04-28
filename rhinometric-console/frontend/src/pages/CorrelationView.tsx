import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { useCorrelation } from '../hooks/useCorrelation';
import { CorrelationTimeline } from '../components/CorrelationTimeline';
import { CorrelationCard } from '../components/CorrelationCard';
import { useAuthStore } from '../lib/auth/store';
import { format } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { getSignalAvailability, getTelemetryLabel, getTelemetryStatusStyle } from '../utils/signalAvailability';
// date-fns locale removed - using English defaults

const CORRELATION_VIEW_BUILD = '2026-02-16T12';

const SEVERITY_SCORE: Record<string, number> = { critical: 50, high: 40, medium: 25, low: 10, info: 5 };
const MAX_RELATED_ANOMALIES = 15;

// Metric family mapping for contextual grouping
const METRIC_FAMILIES: Record<string, string[]> = {
  network:  ['node_network_receive', 'node_network_transmit', 'node_network_errors', 'network'],
  compute:  ['node_cpu_usage', 'node_cpu', 'node_load', 'cpu', 'load'],
  memory:   ['node_memory_usage', 'node_memory_available', 'node_memory', 'memory'],
  storage:  ['node_disk_usage', 'node_disk_io', 'node_disk', 'disk'],
  service:  ['external_service_latency', 'external_service_availability', 'external_service_health',
             'external_service_error', 'external_service_uptime', 'response_time'],
};

function getMetricFamily(metricName: string): string {
  if (!metricName) return '';
  const lower = metricName.toLowerCase();
  for (const [family, keywords] of Object.entries(METRIC_FAMILIES)) {
    if (keywords.some(kw => lower.includes(kw))) return family;
  }
  return '';
}

interface RankContext {
  entityName: string;
  entityType: string;
  metricName: string;
}

function scoreAnomaly(item: any, ctx: RankContext): number {
  let score = 0;
  const currentFamily = getMetricFamily(ctx.metricName);
  const itemFamily = getMetricFamily(item.metric_name || '');

  // 1. Same entity name (exact match) — strongest signal
  if (ctx.entityName && item.entity_name &&
      item.entity_name.toLowerCase() === ctx.entityName.toLowerCase()) {
    score += 1000;
  }

  // 2. Same metric family / domain
  if (currentFamily && itemFamily && currentFamily === itemFamily) {
    score += 500;
  }

  // 3. Same entity_type (infrastructure vs service)
  if (ctx.entityType && item.entity_type &&
      item.entity_type.toLowerCase() === ctx.entityType.toLowerCase()) {
    score += 200;
  }

  // 4. Active anomalies over resolved
  if (item.status !== 'resolved') {
    score += 100;
  }

  // 5. Severity weight
  score += SEVERITY_SCORE[item.severity] ?? 5;

  // 6. Deviation weight (0-80 points, capped)
  const dev = Math.abs(item.deviation_percent ?? 0);
  score += Math.min(dev * 0.8, 80);

  // 7. Recency weight (0-50 points, last 2 hours = max)
  if (item.timestamp) {
    const ageMs = Date.now() - new Date(item.timestamp).getTime();
    const ageHours = ageMs / 3_600_000;
    score += Math.max(0, 50 - ageHours * 10);
  }

  return score;
}

function rankAndLimitAnomalies(anomalies: any[], ctx: RankContext): any[] {
  if (!anomalies || anomalies.length === 0) return [];
  return [...anomalies]
    .map(a => ({ ...a, _score: scoreAnomaly(a, ctx) }))
    .sort((a, b) => b._score - a._score)
    .slice(0, MAX_RELATED_ANOMALIES);
}

interface TimelineEvent {
  timestamp: string;
  type: 'anomaly' | 'metric' | 'log' | 'alert';
  label: string;
  value?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

export function CorrelationView() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Parse anomaly entity data from URL search params
  const entityType = searchParams.get('entity_type') || '';
  const entityName = searchParams.get('entity_name') || '';
  const metricName = searchParams.get('metric_name') || '';
  const source = searchParams.get('source') || '';
  const { loading, error, data, correlate } = useCorrelation();
  const { token } = useAuthStore();
  const [isRefreshing, setIsRefreshing] = useState(false);
  // Signal availability — what telemetry actually exists for this entity type
  const currentEntityType = entityType || data?.metadata?.entity_type || '';
  const staticSignals = getSignalAvailability(currentEntityType);

  // Fetch service telemetry state for per-service override
  const currentEntityName = entityName || data?.metadata?.entity_name || '';
  const { data: servicesListData } = useQuery({
    queryKey: ['services-for-correlation'],
    queryFn: async () => {
      if (!token) return [];
      const res = await fetch('/api/external-services', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) return [];
      const json = await res.json();
      return json.services || json || [];
    },
    staleTime: 30000,
    enabled: !!token,
  });

  // Find the matching service telemetry state
  const matchedSvc = Array.isArray(servicesListData)
    ? servicesListData.find((s: any) => (s.name || '').toLowerCase() === currentEntityName.toLowerCase())
    : null;

  const signals = matchedSvc && matchedSvc.monitoring_mode === 'telemetry_enabled'
    ? {
        ...staticSignals,
        realMetrics: matchedSvc.metrics_enabled || false,
        logs: matchedSvc.logs_enabled || false,
        traces: matchedSvc.traces_enabled || false,
        monitoringMode: 'telemetry_enabled' as const,
        monitoringLabel: getTelemetryLabel(matchedSvc.telemetry_status || 'not_configured'),
      }
    : staticSignals;

  useEffect(() => {
    document.title = 'Event Correlation - Rhinometric';
  }, []);

  useEffect(() => {
    if (id) {
      loadCorrelation();
    }
  }, [id]);

  const loadCorrelation = async () => {
    if (!id) return;

    // id is the anomaly timestamp from URL — use it as the event timestamp
    // so the correlation window centers on when the anomaly actually occurred
    const eventTimestamp = (() => {
      try {
        const d = new Date(decodeURIComponent(id));
        return isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString();
      } catch {
        return new Date().toISOString();
      }
    })();

    await correlate({
      event_id: id,
      event_timestamp: eventTimestamp,
      event_type: 'anomaly',
      event_metadata: {
        entity_type: entityType,
        entity_name: entityName,
        metric_name: metricName,
        source: source
      }
    });
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadCorrelation();
    setIsRefreshing(false);
  };

  // Construir eventos para el timeline
  const buildTimelineEvents = (): TimelineEvent[] => {
    if (!data) return [];

    const events: TimelineEvent[] = [];

    // Agregar métricas al timeline
    data.metrics.forEach((metric: any) => {
      if (metric.values && metric.values.length > 0) {
        const [timestamp, value] = metric.values[metric.values.length - 1];
        events.push({
          timestamp: new Date(timestamp * 1000).toISOString(),
          type: 'metric',
          label: metric.query_name.replace(/_/g, ' '),
          value: parseFloat(value).toFixed(2)
        });
      }
    });

    // Agregar logs al timeline
    data.logs.forEach((log: any) => {
      const isError = /error|fail|exception/i.test(log.line);
      const isWarning = /warn|warning/i.test(log.line);
      
      events.push({
        timestamp: new Date(log.timestamp * 1000).toISOString(),
        type: 'log',
        label: log.line.substring(0, 50) + (log.line.length > 50 ? '...' : ''),
        severity: isError ? 'high' : isWarning ? 'medium' : 'low'
      });
    });

    // Agregar anomalías relacionadas al timeline
    data.related_anomalies.forEach((anomaly: any) => {
      events.push({
        timestamp: anomaly.timestamp || data.timestamp,
        type: 'anomaly',
        label: anomaly.metric_name || 'Anomaly detected',
        severity: anomaly.severity || 'medium'
      });
    });

    return events.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  };

  const timelineEvents = buildTimelineEvents();

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 text-primary animate-spin" size={48} />
          <p className="text-gray-500">Correlating events...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="card bg-error/10 border-error/30">
          <div className="flex items-start gap-4">
            <AlertCircle className="text-error mt-1" size={24} />
            <div className="flex-1">
              <h3 className="text-error font-semibold mb-2">Error Loading Correlation</h3>
              <p className="text-error/80 text-sm mb-4">{error}</p>
              <button
                onClick={loadCorrelation}
                className="btn btn-secondary"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="card text-center py-16">
          <AlertCircle className="mx-auto mb-4 text-gray-500" size={48} />
          <p className="text-gray-500">No correlation information found</p>
        </div>
      </div>
    );
  }

  return (
    <div data-build={CORRELATION_VIEW_BUILD}>
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Correlation Analysis
            </h1>
            <p className="text-gray-500">
              Event detected on {format(new Date(data.timestamp), "MMMM dd, yyyy 'at' HH:mm:ss")}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="card bg-purple-500/10 border-purple-500/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl">📊</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.summary.metrics_count}</div>
              <div className="text-sm text-gray-500">Metrics</div>
            </div>
          </div>
        </div>

        <div className="card bg-gray-100/30 border-gray-200/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl">📝</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.summary.logs_count}</div>
              <div className="text-sm text-gray-500">Logs</div>
            </div>
          </div>
        </div>

        <div className="card bg-gray-100/20 border-gray-200/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl opacity-50">🔗</div>
            <div>
              <div className="text-2xl font-bold text-gray-500">N/A</div>
              <div className="text-sm text-gray-500">{signals.traces ? 'Traces' : 'Traces — not connected'}</div>
            </div>
          </div>
        </div>

        <div className="card bg-orange-500/10 border-orange-500/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl">⚠️</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{data.summary.anomalies_count}</div>
              <div className="text-sm text-gray-500">Anomalies</div>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {timelineEvents.length > 0 && (
        <div className="mb-8">
          <CorrelationTimeline
            events={timelineEvents}
            centralTimestamp={data.timestamp}
            windowStart={data.correlation_window.start}
            windowEnd={data.correlation_window.end}
          />
        </div>
      )}

      {/* Correlation Window Info */}
      <div className="card mb-8 bg-blue-500/5 border-blue-500/20">
        <div className="flex items-start gap-3">
          <div className="text-2xl">🕐</div>
          <div className="flex-1">
            <h3 className="text-gray-900 font-semibold mb-2">Correlation Window</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Start:</span>
                <span className="ml-2 text-gray-900 font-medium">
                  {format(new Date(data.correlation_window.start), 'HH:mm:ss')}
                </span>
              </div>
              <div>
                <span className="text-gray-500">End:</span>
                <span className="ml-2 text-gray-900 font-medium">
                  {format(new Date(data.correlation_window.end), 'HH:mm:ss')}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Duration:</span>
                <span className="ml-2 text-gray-900 font-medium">
                  {data.correlation_window.duration_seconds} seconds
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Monitoring Mode Banner */}
      {signals.monitoringMode === 'telemetry_enabled' && matchedSvc && (
        <div className={`card mb-8 ${getTelemetryStatusStyle(matchedSvc.telemetry_status || 'configured').bg} border ${getTelemetryStatusStyle(matchedSvc.telemetry_status || 'configured').border}`}>
          <div className="flex items-start gap-3">
            <div className="text-2xl">📡</div>
            <div className="flex-1">
              <h3 className={`font-semibold mb-1 ${getTelemetryStatusStyle(matchedSvc.telemetry_status || 'configured').color}`}>
                {getTelemetryLabel(matchedSvc.telemetry_status || 'configured')}
              </h3>
              <p className="text-sm text-gray-500">
                This service has telemetry enabled.
                {matchedSvc.metrics_enabled && ' Metrics'}{matchedSvc.logs_enabled && ' Logs'}{matchedSvc.traces_enabled && ' Traces'} signals are configured.
              </p>
            </div>
          </div>
        </div>
      )}

      {signals.monitoringMode === 'synthetic' && (
        <div className="card mb-8 bg-amber-500/5 border-amber-500/20">
          <div className="flex items-start gap-3">
            <div className="text-2xl">📡</div>
            <div className="flex-1">
              <h3 className="text-amber-400 font-semibold mb-1">Monitoring Mode: Synthetic Only</h3>
              <p className="text-sm text-gray-500">
                This service is monitored via automated synthetic checks (HTTP / PostgreSQL).
                Telemetry is not configured for this service.
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Enable telemetry and deploy a collector to correlate with application logs, traces, and real metrics.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card mb-8 bg-gray-50/50 border-gray-200">
        <div className="flex items-start gap-3 mb-4">
          <div className="text-2xl">🔗</div>
          <div className="flex-1">
            <h3 className="text-gray-900 font-semibold mb-1">Quick Actions</h3>
            <p className="text-sm text-gray-500">
              Navigate to related views
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* View Logs */}
          <button
            onClick={() => navigate('/logs')}
            className="p-4 rounded-lg border transition-all flex items-center gap-3 bg-green-500/10 border-green-500/30 hover:bg-green-500/20 hover:border-green-500/50 cursor-pointer"
            title="View system logs"
          >
            <div className="text-3xl">📝</div>
            <div className="flex-1 text-left">
              <div className="text-gray-900 font-medium">View Logs</div>
              <div className="text-xs text-gray-500">Explore full logs</div>
            </div>
          </button>

          {/* Service Dashboard */}
          <button
            onClick={() => navigate('/dashboards/ext-svc-detail/view')}
            className="p-4 rounded-lg border transition-all flex items-center gap-3 bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20 hover:border-blue-500/50 cursor-pointer"
            title="View service dashboard"
          >
            <div className="text-3xl">📊</div>
            <div className="flex-1 text-left">
              <div className="text-gray-900 font-medium">Service Dashboard</div>
              <div className="text-xs text-gray-500">View detailed metrics</div>
            </div>
          </button>

          {/* Latency Dashboard */}
          <button
            onClick={() => navigate('/dashboards/ext-svc-latency/view')}
            className="p-4 rounded-lg border transition-all flex items-center gap-3 bg-purple-500/10 border-purple-500/30 hover:bg-purple-500/20 hover:border-purple-500/50 cursor-pointer"
            title="View latency dashboard"
          >
            <div className="text-3xl">⏱️</div>
            <div className="flex-1 text-left">
              <div className="text-gray-900 font-medium">Latency Dashboard</div>
              <div className="text-xs text-gray-500">Analyze service latency</div>
            </div>
          </button>
        </div>
      </div>

      {/* Data Cards Grid */}
      <div className="space-y-6">
        {/* Metrics */}
        {data.metrics.length > 0 && (
          <CorrelationCard
            title="Correlated Metrics"
            icon="📊"
            data={data.metrics}
            type="metrics"
          />
        )}

        {/* Logs */}
        {data.logs.length > 0 && (
          <CorrelationCard
            title="Related Logs"
            icon="📝"
            data={data.logs}
            type="logs"
          />
        )}

        {/* Anomalies */}
        {data.related_anomalies.length > 0 && (() => {
          const ranked = rankAndLimitAnomalies(data.related_anomalies, {
            entityName: entityName || data.metadata?.entity_name || '',
            entityType: entityType || data.metadata?.entity_type || '',
            metricName: metricName || data.metadata?.metric_name || '',
          });
          return (
            <CorrelationCard
              title="Related Anomalies"
              icon="🔍"
              data={ranked}
              type="anomalies"
              totalCount={data.related_anomalies.length}
            />
          );
        })()}

        {/* Traces - out of scope, hidden */}
      </div>

      {/* Empty State */}
      {data.metrics.length === 0 && 
       data.logs.length === 0 && 
        
       data.related_anomalies.length === 0 && (
        <div className="card text-center py-16">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Correlated Data Found
          </h3>
          <p className="text-gray-500 mb-6">
            No related events detected in the specified time window.
          </p>
          <button onClick={handleRefresh} className="btn btn-primary">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
