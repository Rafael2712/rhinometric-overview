import React from 'react';
import { format } from 'date-fns';
// date-fns locale removed - using English defaults

interface CorrelationCardProps {
  title: string;
  icon: string;
  data: any[];
  type: 'metrics' | 'logs' | 'traces' | 'anomalies';
  onViewMore?: () => void;
  totalCount?: number;
}

export const CorrelationCard: React.FC<CorrelationCardProps> = ({
  title,
  icon,
  data,
  type,
  onViewMore,
  totalCount,
}) => {
  const renderMetricData = (item: any) => {
    const lastValue = item.values?.[item.values.length - 1];
    if (!lastValue) return null;

    const [timestamp, value] = lastValue;
    const numValue = parseFloat(value);
    
    return (
      <div key={`${item.query_name}-${timestamp}`} className="p-3 bg-gray-800 rounded-lg border border-gray-700 hover:border-purple-500/50 transition-colors">
        <div className="flex justify-between items-start mb-2">
          <span className="text-sm font-medium text-gray-300 capitalize">
            {item.query_name.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-gray-500">
            {item.source === 'victoria-metrics' ? 'VictoriaMetrics' : 'Prometheus'}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">
            {numValue.toFixed(2)}
            <span className="text-sm text-gray-400 ml-1">
              {item.query_name.includes('usage') ? '%' : ''}
            </span>
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {format(new Date(timestamp * 1000), 'dd/MM/yy HH:mm:ss', )}
        </p>
      </div>
    );
  };

  const renderLogData = (item: any) => {
    const timestamp = typeof item.timestamp === 'number' ? item.timestamp : parseFloat(item.timestamp);
    const logText = item.line || item.log || 'No content';
    const isError = /error|fail|exception/i.test(logText);
    const isWarning = /warn|warning/i.test(logText);

    return (
      <div key={timestamp} className={`p-3 rounded-lg border transition-colors ${
        isError ? 'bg-red-900/20 border-red-700/50 hover:border-red-500/50' :
        isWarning ? 'bg-yellow-900/20 border-yellow-700/50 hover:border-yellow-500/50' :
        'bg-gray-800 border-gray-700 hover:border-gray-500/50'
      }`}>
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            {isError && <span className="text-red-400 text-lg">❌</span>}
            {isWarning && <span className="text-yellow-400 text-lg">⚠️</span>}
            {!isError && !isWarning && <span className="text-gray-400 text-lg">ℹ️</span>}
            <span className={`text-xs font-medium px-2 py-1 rounded ${
              isError ? 'bg-red-500/20 text-red-300' :
              isWarning ? 'bg-yellow-500/20 text-yellow-300' :
              'bg-gray-700 text-gray-300'
            }`}>
              {isError ? 'ERROR' : isWarning ? 'WARNING' : 'INFO'}
            </span>
          </div>
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {format(new Date(timestamp * 1000), 'HH:mm:ss', )}
          </span>
        </div>
        <p className="text-sm text-gray-300 font-mono break-all line-clamp-3">
          {logText}
        </p>
        {item.labels && Object.keys(item.labels).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {Object.entries(item.labels).slice(0, 3).map(([key, value]) => (
              <span key={key} className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded">
                {key}:{String(value).slice(0, 20)}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  const severityConfig: Record<string, { bg: string; text: string; border: string; label: string }> = {
    critical: { bg: 'bg-red-500/20', text: 'text-red-300', border: 'border-red-700/50 hover:border-red-500/50', label: 'CRITICAL' },
    high:     { bg: 'bg-orange-500/20', text: 'text-orange-300', border: 'border-orange-700/50 hover:border-orange-500/50', label: 'HIGH' },
    medium:   { bg: 'bg-yellow-500/20', text: 'text-yellow-300', border: 'border-yellow-700/50 hover:border-yellow-500/50', label: 'MEDIUM' },
    low:      { bg: 'bg-blue-500/20', text: 'text-blue-300', border: 'border-blue-700/50 hover:border-blue-500/50', label: 'LOW' },
    info:     { bg: 'bg-gray-500/20', text: 'text-gray-300', border: 'border-gray-700/50 hover:border-gray-500/50', label: 'INFO' },
  };

  const statusConfig: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    active:   { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400', label: 'Active' },
    firing:   { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400', label: 'Firing' },
    resolved: { bg: 'bg-green-500/15', text: 'text-green-400', dot: 'bg-green-400', label: 'Resolved' },
  };

  const renderAnomalyData = (item: any, index: number) => {
    const sev = severityConfig[item.severity] || severityConfig.medium;
    const stat = statusConfig[item.status] || { bg: 'bg-gray-500/15', text: 'text-gray-400', dot: 'bg-gray-400', label: item.status || 'Unknown' };
    const metricLabel = (item.metric_name || 'Unknown metric').replace(/::/g, ' — ').replace(/_/g, ' ');
    const deviation = item.deviation_percent != null ? Math.abs(item.deviation_percent) : null;
    const deviationDir = item.deviation_percent != null ? (item.deviation_percent >= 0 ? '+' : '-') : '';
    const ts = item.timestamp ? (() => { try { return format(new Date(item.timestamp), 'dd/MM HH:mm:ss'); } catch { return '—'; } })() : null;
    const bgClass = item.status !== 'resolved' ? 'bg-red-950/30' : 'bg-gray-800/60';

    return (
      <div key={`anomaly-${index}-${item.timestamp}`} className={`p-3 rounded-lg border ${sev.border} ${bgClass} transition-colors`}>
        {/* Row 1: metric name + severity + status badges */}
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <span className="text-sm font-medium text-gray-200 truncate flex-1" title={item.metric_name}>
            {metricLabel}
          </span>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${sev.bg} ${sev.text}`}>
              {sev.label}
            </span>
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded flex items-center gap-1 ${stat.bg} ${stat.text}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${stat.dot} ${item.status !== 'resolved' ? 'animate-pulse' : ''}`} />
              {stat.label}
            </span>
          </div>
        </div>

        {/* Row 2: entity + source context */}
        {(item.entity_name || item.entity_type) && (
          <div className="flex items-center gap-2 mb-1.5">
            {item.entity_type && (
              <span className="text-[10px] bg-gray-700/60 text-gray-400 px-1.5 py-0.5 rounded capitalize">
                {item.entity_type}
              </span>
            )}
            {item.entity_name && (
              <span className="text-xs text-gray-400 truncate" title={item.entity_name}>
                {item.entity_name}
              </span>
            )}
            {item.source && (
              <span className="text-[10px] text-gray-500 ml-auto flex-shrink-0">
                via {item.source.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        )}

        {/* Row 3: deviation + values + timestamp */}
        <div className="flex items-center gap-3 text-xs">
          {deviation != null && (
            <span className={`font-semibold ${deviation > 50 ? 'text-red-400' : deviation > 20 ? 'text-orange-400' : 'text-yellow-400'}`}>
              {deviationDir}{deviation.toFixed(1)}%
            </span>
          )}
          {item.current_value != null && item.expected_value != null && (
            <span className="text-gray-500">
              {typeof item.current_value === 'number' ? item.current_value.toFixed(1) : item.current_value}
              {' → '}
              <span className="text-gray-600">exp {typeof item.expected_value === 'number' ? item.expected_value.toFixed(1) : item.expected_value}</span>
            </span>
          )}
          {ts && (
            <span className="text-gray-500 ml-auto flex-shrink-0">{ts}</span>
          )}
        </div>

        {/* Row 4: baseline explanation (compact) */}
        {item.baseline_explanation && (
          <p className="text-[11px] text-gray-500 mt-1 truncate" title={item.baseline_explanation}>
            {item.baseline_explanation}
          </p>
        )}
      </div>
    );
  };

  const renderTraceData = (item: any) => {
    return (
      <div key={item.trace_id} className="p-3 bg-blue-900/20 rounded-lg border border-blue-700/50 hover:border-blue-500/50 transition-colors">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 text-lg">🔗</span>
            <span className="text-sm font-medium text-blue-300">
              Trace ID: {item.trace_id?.slice(0, 16)}...
            </span>
          </div>
        </div>
        {item.span_count && (
          <p className="text-xs text-gray-400">
            {item.span_count} spans | Duration: {item.duration}ms
          </p>
        )}
      </div>
    );
  };

  const renderData = () => {
    if (!data || data.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p className="text-4xl mb-2">📭</p>
          <p className="text-sm">No data found in this time window</p>
        </div>
      );
    }

    switch (type) {
      case 'metrics':
        return data.map(renderMetricData);
      case 'logs':
        return data.map(renderLogData);
      case 'anomalies':
        return data.map((item, i) => renderAnomalyData(item, i));
      case 'traces':
        return data.map(renderTraceData);
      default:
        return <p className="text-gray-500">Unsupported data type</p>;
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            <p className="text-xs text-gray-400">
              {totalCount && totalCount > data.length
                ? <>{data.length} of {totalCount} items shown</>
                : <>{data.length} items found</>}
            </p>
          </div>
        </div>
        {onViewMore && data.length > 0 && (
          <button
            onClick={onViewMore}
            className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
          >
            View more →
          </button>
        )}
      </div>

      {/* Content */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {renderData()}
      </div>
    </div>
  );
};
