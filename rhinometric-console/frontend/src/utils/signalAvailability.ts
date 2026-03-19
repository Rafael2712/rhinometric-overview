/**
 * Signal availability model for monitored entities.
 *
 * Current state (2025):
 *   - External services → synthetic monitoring only (HTTP / PostgreSQL checks).
 *     No real customer application logs, traces, or app-level metrics.
 *   - Infrastructure → real metrics from node-exporter, docker logs available.
 *   - Websites → synthetic HTTP checks only.
 *
 * This module is the single source of truth for what signals exist
 * so the UI can honestly label deep-analysis actions.
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
  monitoringMode: 'synthetic' | 'full' | 'infrastructure';
  /** Short label for badges */
  monitoringLabel: string;
}

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
 */
export function getSignalDisabledReason(
  signal: 'metrics' | 'logs' | 'traces',
  entityType: string,
): string | null {
  const avail = getSignalAvailability(entityType);
  switch (signal) {
    case 'metrics':
      // Synthetic check metrics (latency, availability) always exist in Prometheus
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
