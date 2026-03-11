/**
 * Utilidades para generar enlaces a herramientas externas de observabilidad
 * Grafana (Metrics + Logs). Traces out of scope.
 *
 * ARCHITECTURAL RULE: No hardcoded queries. All queries derived from anomaly metadata.
 */

/**
 * Genera URL de Grafana Explore con query de VictoriaMetrics/Prometheus
 */
export function getGrafanaMetricsUrl(
  metricQuery: string,
  startTime: string,
  endTime: string
): string {
  const from = new Date(startTime).getTime();
  const to = new Date(endTime).getTime();

  const params = new URLSearchParams({
    'orgId': '1',
    'left': JSON.stringify({
      datasource: 'victoriametrics',
      queries: [{
        refId: 'A',
        expr: metricQuery
      }],
      range: {
        from: from.toString(),
        to: to.toString()
      }
    })
  });

  return `/grafana/explore?${params.toString()}`;
}

/**
 * Genera URL de Grafana Explore con query de Loki (logs)
 */
export function getGrafanaLogsUrl(
  logQuery: string,
  startTime: string,
  endTime: string
): string {
  const from = new Date(startTime).getTime();
  const to = new Date(endTime).getTime();

  const params = new URLSearchParams({
    'orgId': '1',
    'left': JSON.stringify({
      datasource: 'loki',
      queries: [{
        refId: 'A',
        expr: logQuery
      }],
      range: {
        from: from.toString(),
        to: to.toString()
      }
    })
  });

  return `/grafana/explore?${params.toString()}`;
}

/**
 * Verifica si el usuario tiene permisos para acceder a herramientas externas
 */
export function canAccessExternalTools(userRoles: string[]): boolean {
  return userRoles.some(role =>
    ['OWNER', 'ADMIN'].includes(role.toUpperCase())
  );
}

/**
 * Dynamic PromQL query builder - derives query from anomaly metadata.
 * Maps anomaly metric_name to real Prometheus expressions.
 * NEVER returns a hardcoded catch-all.
 */
export function buildDynamicPromQL(anomaly: {
  metric_name?: string;
  entity_type?: string;
  entity_name?: string;
  source?: string;
}): string {
  const metricName = anomaly.metric_name || '';
  const entityName = anomaly.entity_name || '';
  const entityType = anomaly.entity_type || '';

  // Strip ::entity_name suffix from grouped metric names
  const baseMetric = metricName.split('::')[0].trim();

  // --- Service metrics ---
  if (entityType === 'service' || metricName.startsWith('external_service_')) {
    const serviceMetrics: Record<string, string> = {
      'external_service_latency_ms': `external_service_latency_ms{service_name="${entityName}"}`,
      'external_service_latency': `external_service_latency_ms{service_name="${entityName}"}`,
      'external_service_health_score': `external_service_health_score{service_name="${entityName}"}`,
      'external_service_health': `external_service_health_score{service_name="${entityName}"}`,
      'external_service_up': `external_service_up{service_name="${entityName}"}`,
      'external_service_availability': `external_service_up{service_name="${entityName}"}`,
    };
    return serviceMetrics[baseMetric] || `${baseMetric}{service_name="${entityName}"}`;
  }

  // --- Infrastructure metrics ---
  if (entityType === 'infrastructure' || metricName.startsWith('node_')) {
    const infraMetrics: Record<string, string> = {
      'node_cpu_usage': '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
      'node_memory_usage': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
      'node_disk_usage': '(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100',
      'node_disk_io': 'rate(node_disk_io_time_seconds_total[5m])',
      'node_network_receive': 'rate(node_network_receive_bytes_total[5m])',
      'node_network_transmit': 'rate(node_network_transmit_bytes_total[5m])',
    };
    return infraMetrics[baseMetric] || baseMetric;
  }

  // --- Website metrics ---
  if (entityType === 'website' || metricName.startsWith('rhinometric_website_')) {
    return baseMetric;
  }

  // Fallback: use the raw metric name as PromQL (no catch-all)
  return baseMetric || metricName;
}

/**
 * Dynamic LogQL query builder - derives query from anomaly metadata.
 * NEVER returns a generic catch-all like {job=~".+"}.
 */
export function buildDynamicLogQL(anomaly: {
  metric_name?: string;
  entity_type?: string;
  entity_name?: string;
  source?: string;
}): string {
  const entityType = anomaly.entity_type || '';
  const entityName = anomaly.entity_name || '';

  if (entityType === 'service' || anomaly.source === 'external_services') {
    return `{job="console-backend"} |= "${entityName}" |~ "(?i)(error|warn|fail|timeout|exception)"`;
  }

  if (entityType === 'infrastructure') {
    return '{job="docker_logs"} |~ "(?i)(error|warn|fail|oom|exception)"';
  }

  if (entityType === 'website') {
    return '{job="console-backend"} |~ "(?i)(website|ssl|dns|response_time)" |~ "(?i)(error|warn|fail)"';
  }

  // Cannot determine entity_type - return scoped query, never catch-all
  if (entityName) {
    return `{job="console-backend"} |= "${entityName}" |~ "(?i)(error|warn|fail)"`;
  }

  return '{job="console-backend"} |~ "(?i)(error|warn|fail)"';
}

/**
 * Abre enlace externo en nueva pestana
 */
export function openExternalLink(url: string): void {
  window.open(url, '_blank', 'noopener,noreferrer');
}
