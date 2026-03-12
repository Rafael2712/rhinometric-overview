import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Loader2, RefreshCw, ExternalLink, Lock } from 'lucide-react';
import { useCorrelation } from '../hooks/useCorrelation';
import { CorrelationTimeline } from '../components/CorrelationTimeline';
import { CorrelationCard } from '../components/CorrelationCard';
import { useAuthStore } from '../lib/auth/store';
import { 
  getGrafanaMetricsUrl, 
  getGrafanaLogsUrl, 
  canAccessExternalTools,
  openExternalLink 
} from '../utils/externalLinks';
import { format } from 'date-fns';
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
  const { user } = useAuthStore();
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const hasExternalAccess = user ? canAccessExternalTools(user.roles) : false;

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
    data.metrics.forEach((metric) => {
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
    data.logs.forEach((log) => {
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
          <p className="text-gray-400">Correlating events...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
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
          className="mb-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="card text-center py-16">
          <AlertCircle className="mx-auto mb-4 text-gray-500" size={48} />
          <p className="text-gray-400">No correlation information found</p>
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
          className="mb-4 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Correlation Analysis
            </h1>
            <p className="text-gray-400">
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
              <div className="text-2xl font-bold text-white">{data.summary.metrics_count}</div>
              <div className="text-sm text-gray-400">Metrics</div>
            </div>
          </div>
        </div>

        <div className="card bg-gray-700/30 border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl">📝</div>
            <div>
              <div className="text-2xl font-bold text-white">{data.summary.logs_count}</div>
              <div className="text-sm text-gray-400">Logs</div>
            </div>
          </div>
        </div>

        <div className="card bg-gray-700/20 border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl opacity-50">🔗</div>
            <div>
              <div className="text-2xl font-bold text-gray-500">N/A</div>
              <div className="text-sm text-gray-500">Traces (coming soon)</div>
            </div>
          </div>
        </div>

        <div className="card bg-orange-500/10 border-orange-500/30">
          <div className="flex items-center gap-3">
            <div className="text-3xl">⚠️</div>
            <div>
              <div className="text-2xl font-bold text-white">{data.summary.anomalies_count}</div>
              <div className="text-sm text-gray-400">Anomalies</div>
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
            <h3 className="text-white font-semibold mb-2">Correlation Window</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Start:</span>
                <span className="ml-2 text-white font-medium">
                  {format(new Date(data.correlation_window.start), 'HH:mm:ss')}
                </span>
              </div>
              <div>
                <span className="text-gray-400">End:</span>
                <span className="ml-2 text-white font-medium">
                  {format(new Date(data.correlation_window.end), 'HH:mm:ss')}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Duration:</span>
                <span className="ml-2 text-white font-medium">
                  {data.correlation_window.duration_seconds} seconds
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions - External Tools */}
      {hasExternalAccess && (
      <div className="card mb-8 bg-gray-800/50 border-gray-700">
        <div className="flex items-start gap-3 mb-4">
          <div className="text-2xl">🔗</div>
          <div className="flex-1">
            <h3 className="text-white font-semibold mb-1">Deep Analysis</h3>
            <p className="text-sm text-gray-400">
              Explore data in native observability tools
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Grafana Metrics */}
          <button
            onClick={() => {
              if (hasExternalAccess) {
                // Build the proper PromQL query using entity context
                // data.metrics[0].query_name is a key name, not a valid PromQL expression
                const et = data.metadata?.entity_type || entityType;
                const en = data.metadata?.entity_name || entityName;
                const mn = data.metadata?.metric_name || metricName;
                let metricQuery: string;

                if (et === 'service' || mn?.startsWith('external_service_')) {
                  // Service metrics have service_name label
                  const baseMetric = mn?.split('::')[0]?.trim() || '';
                  const svcMetrics: Record<string, string> = {
                    'external_service_latency_ms': `external_service_latency_ms{service_name="${en}"}`,
                    'external_service_latency': `external_service_latency_ms{service_name="${en}"}`,
                    'external_service_health_score': `external_service_health_score{service_name="${en}"}`,
                    'external_service_health': `external_service_health_score{service_name="${en}"}`,
                    'external_service_up': `external_service_up{service_name="${en}"}`,
                    'external_service_availability': `external_service_up{service_name="${en}"}`,
                  };
                  metricQuery = svcMetrics[baseMetric] || `${baseMetric}{service_name="${en}"}`;
                } else if (et === 'infrastructure' || mn?.startsWith('node_')) {
                  // Infrastructure metrics - use proper PromQL with labels
                  const baseMetric = mn?.split('::')[0]?.trim() || '';
                  const infraMetrics: Record<string, string> = {
                    'node_cpu_usage': '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle",job="node-exporter"}[5m])) * 100)',
                    'node_memory_usage': '(1 - (node_memory_MemAvailable_bytes{job="node-exporter"} / node_memory_MemTotal_bytes{job="node-exporter"})) * 100',
                    'node_disk_usage': '(node_filesystem_size_bytes{job="node-exporter"} - node_filesystem_avail_bytes{job="node-exporter"}) / node_filesystem_size_bytes{job="node-exporter"} * 100',
                    'node_disk_io': 'rate(node_disk_io_time_seconds_total{job="node-exporter"}[5m])',
                    'node_network_receive': 'rate(node_network_receive_bytes_total{job="node-exporter"}[5m])',
                    'node_network_transmit': 'rate(node_network_transmit_bytes_total{job="node-exporter"}[5m])',
                  };
                  metricQuery = infraMetrics[baseMetric] || baseMetric;
                } else {
                  metricQuery = mn || data.metrics[0]?.query_name || 'up';
                }

                const url = getGrafanaMetricsUrl(
                  metricQuery,
                  data.correlation_window.start,
                  data.correlation_window.end
                );
                openExternalLink(url);
              }
            }}
            disabled={!hasExternalAccess}
            className={`p-4 rounded-lg border transition-all flex items-center gap-3 ${
              hasExternalAccess
                ? 'bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20 hover:border-blue-500/50 cursor-pointer'
                : 'bg-gray-800 border-gray-700 opacity-50 cursor-not-allowed'
            }`}
            title={hasExternalAccess ? 'Open metrics in Grafana' : 'Only available for Administrators'}
          >
            <div className="text-3xl">📊</div>
            <div className="flex-1 text-left">
              <div className="text-white font-medium flex items-center gap-2">
                Grafana Metrics
                {hasExternalAccess ? (
                  <ExternalLink size={14} className="text-blue-400" />
                ) : (
                  <Lock size={14} className="text-gray-500" />
                )}
              </div>
              <div className="text-xs text-gray-400">
                {hasExternalAccess ? 'View detailed metrics' : 'Restricted access'}
              </div>
            </div>
          </button>

          {/* Loki Logs */}
          <button
            onClick={() => {
              if (hasExternalAccess) {
                // Dynamic LogQL based on entity context
                const et = data.metadata?.entity_type || entityType;
                let logQuery: string;
                if (et === 'service') {
                  const en = data.metadata?.entity_name || entityName;
                  logQuery = `{job="console-backend"} |= "${en}" |~ "(?i)(error|warn|fail|timeout)"`;
                } else if (et === 'infrastructure') {
                  logQuery = '{job="docker_logs"} |~ "(?i)(error|warn|fail|oom)"';
                } else if (et === 'website') {
                  logQuery = '{job="console-backend"} |~ "(?i)(website|ssl|dns)" |~ "(?i)(error|warn)"';
                } else {
                  logQuery = '{job="console-backend"} |~ "(?i)(error|warn)"';
                }
                const url = getGrafanaLogsUrl(
                  logQuery,
                  data.correlation_window.start,
                  data.correlation_window.end
                );
                openExternalLink(url);
              }
            }}
            disabled={!hasExternalAccess}
            className={`p-4 rounded-lg border transition-all flex items-center gap-3 ${
              hasExternalAccess
                ? 'bg-green-500/10 border-green-500/30 hover:bg-green-500/20 hover:border-green-500/50 cursor-pointer'
                : 'bg-gray-800 border-gray-700 opacity-50 cursor-not-allowed'
            }`}
            title={hasExternalAccess ? 'Open logs in Grafana (Loki)' : 'Only available for Administrators'}
          >
            <div className="text-3xl">📝</div>
            <div className="flex-1 text-left">
              <div className="text-white font-medium flex items-center gap-2">
                Loki Logs
                {hasExternalAccess ? (
                  <ExternalLink size={14} className="text-green-400" />
                ) : (
                  <Lock size={14} className="text-gray-500" />
                )}
              </div>
              <div className="text-xs text-gray-400">
                {hasExternalAccess ? 'Explore full logs' : 'Restricted access'}
              </div>
            </div>
          </button>

          {/* Jaeger Traces – disabled until integration is ready */}
          <button
            disabled
            className="p-4 rounded-lg border transition-all flex items-center gap-3 bg-gray-800 border-gray-700 opacity-50 cursor-not-allowed"
            title="Coming soon"
          >
            <div className="text-3xl">🔗</div>
            <div className="flex-1 text-left">
              <div className="text-white font-medium flex items-center gap-2">
                Jaeger Traces
                <Lock size={14} className="text-gray-500" />
              </div>
              <div className="text-xs text-gray-400">Coming soon</div>
            </div>
          </button>
        </div>

      </div>
      )}

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
          <h3 className="text-xl font-semibold text-white mb-2">
            No Correlated Data Found
          </h3>
          <p className="text-gray-400 mb-6">
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
