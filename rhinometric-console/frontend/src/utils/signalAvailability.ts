/**
 * Signal availability model for monitored entities.
 *
 * The REAL source of truth for per-service telemetry state is ExternalService
 * from the backend API.  This utility provides:
 *   1. Static defaults by entity type (for pages that don't have per-service data)
 *   2. A helper to derive SignalAvailability from a real service object
 */

export interface SignalAvailability {
  /** Synthetic checks (HTTP pings, DB pings) are running */
  synthetic: boolean;
  /** Real application-level metrics from a collector (e.g. OpenTelemetry) */
  realMetrics: boolean;
  /** Customer application logs are collected (not platform logs) */
  logs: boolean;
  /** Distributed traces are collected */
  traces: boolean;
  /** Human-readable monitoring mode */
  monitoringMode: 'synthetic' | 'full' | 'telemetry_enabled' | 'infrastructure';
  /** Short label for badges */
  monitoringLabel: string;
}

/**
 * Telemetry state from the backend ExternalService model.
 * Pages should use this when they have per-service data.
 */
export interface ServiceTelemetryState {
  monitoring_mode: string;      // "synthetic_only" | "telemetry_enabled"
  synthetic_enabled: boolean;
  metrics_enabled: boolean;
  logs_enabled: boolean;
  traces_enabled: boolean;
  telemetry_attached: boolean;
  telemetry_status: string;     // "not_configured" | "configured" | "connected" | "receiving_data" | "stale" | "error"
  telemetry_service_key?: string | null;
}

/**
 * Derive per-service signal availability from real backend data.
 * This is the PREFERRED way — used when per-service API data is available.
 */
export function getServiceSignalAvailability(svc: ServiceTelemetryState): SignalAvailability {
  const isTelemetry = svc.monitoring_mode === 'telemetry_enabled';
  return {
    synthetic: svc.synthetic_enabled,
    realMetrics: isTelemetry && svc.metrics_enabled,
    logs: isTelemetry && svc.logs_enabled,
    traces: isTelemetry && svc.traces_enabled,
    monitoringMode: isTelemetry ? 'telemetry_enabled' : 'synthetic',
    monitoringLabel: isTelemetry
      ? getTelemetryLabel(svc.telemetry_status)
      : 'Synthetic monitoring only',
  };
}

/**
 * Human-readable label for telemetry status.
 */
export function getTelemetryLabel(status: string): string {
  switch (status) {
    case 'not_configured': return 'Telemetry not configured';
    case 'configured':     return 'Telemetry configured — awaiting data';
    case 'connected':      return 'Telemetry connected';
    case 'receiving_data': return 'Telemetry active';
    case 'stale':          return 'Telemetry stale';
    case 'error':          return 'Telemetry error';
    default:               return 'Unknown telemetry state';
  }
}

/**
 * Telemetry status → color / bg for badges.
 */
export function getTelemetryStatusStyle(status: string): { color: string; bg: string; border: string } {
  switch (status) {
    case 'receiving_data': return { color: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/20' };
    case 'connected':      return { color: 'text-blue-400',   bg: 'bg-blue-500/10',   border: 'border-blue-500/20'  };
    case 'configured':     return { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' };
    case 'stale':          return { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' };
    case 'error':          return { color: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/20'    };
    default:               return { color: 'text-gray-400',   bg: 'bg-gray-500/10',   border: 'border-gray-500/20'   };
  }
}

/**
 * Static fallback — returns defaults by entity type only.
 * Use getServiceSignalAvailability() when you have per-service data.
 */
export function getSignalAvailability(entityType: string): SignalAvailability {
  switch (entityType) {
    case 'service':
      return {
        synthetic: true,
        realMetrics: false,
        logs: false,
        traces: false,
        monitoringMode: 'synthetic',
        monitoringLabel: 'Synthetic monitoring only',
      };
    case 'infrastructure':
      return {
        synthetic: false,
        realMetrics: true,
        logs: true,
        traces: false,
        monitoringMode: 'infrastructure',
        monitoringLabel: 'Infrastructure monitoring',
      };
    case 'website':
      return {
        synthetic: true,
        realMetrics: false,
        logs: false,
        traces: false,
        monitoringMode: 'synthetic',
        monitoringLabel: 'Synthetic monitoring only',
      };
    default:
      return {
        synthetic: true,
        realMetrics: false,
        logs: false,
        traces: false,
        monitoringMode: 'synthetic',
        monitoringLabel: 'Synthetic monitoring only',
      };
  }
}

/**
 * Returns a user-facing reason why a signal is unavailable for a given
 * entity type, or null if the signal IS available.
 *
 * For per-service accuracy, prefer checking svc.logs_enabled / svc.traces_enabled directly.
 */
export function getSignalDisabledReason(
  signal: 'metrics' | 'logs' | 'traces',
  entityType: string,
): string | null {
  const avail = getSignalAvailability(entityType);
  switch (signal) {
    case 'metrics':
      return null;
    case 'logs':
      if (!avail.logs)
        return 'Customer logs are not connected for this service';
      return null;
    case 'traces':
      if (!avail.traces)
        return 'Customer traces are not connected for this service';
      return null;
    default:
      return null;
  }
}
