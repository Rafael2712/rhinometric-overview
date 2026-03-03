/**
 * Utilidades para generar enlaces a herramientas externas de observabilidad
 * Grafana, Loki, Jaeger con parámetros de tiempo dinámicos
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

  // Formato simplificado para Grafana Explore
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

  // Formato simplificado para Grafana Explore con Loki
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
 * Genera URL de Jaeger con filtro de tiempo
 * NOTA: Jaeger UI requiere puerto directo o QUERY_BASE_PATH configurado
 */
export function getJaegerTracesUrl(
  startTime: string,
  endTime: string,
  service?: string
): string {
  const start = new Date(startTime).getTime() * 1000; // microseconds
  const end = new Date(endTime).getTime() * 1000;

  const params = new URLSearchParams({
    start: start.toString(),
    end: end.toString(),
    limit: '50',
    lookback: 'custom',
    maxDuration: '',
    minDuration: ''
  });

  if (service) {
    params.append('service', service);
  }

  // Usar puerto directo de Jaeger (16686) hasta configurar QUERY_BASE_PATH
  // Alternativa: return `/jaeger` para usar redirect de nginx
  return `http://46.225.231.117:16686/search?${params.toString()}`;
}

/**
 * Genera URL de Loki directo (API)
 */
export function getLokiApiUrl(
  query: string,
  startTime: string,
  endTime: string
): string {
  const start = new Date(startTime).getTime() * 1000000; // nanoseconds
  const end = new Date(endTime).getTime() * 1000000;

  const params = new URLSearchParams({
    query,
    start: start.toString(),
    end: end.toString(),
    limit: '100'
  });

  return `/api/loki/query_range?${params.toString()}`;
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
 * Genera query de Loki para logs de un host específico
 */
export function buildLokiQuery(host?: string, level?: string): string {
  const labels: string[] = [];

  if (host) {
    labels.push(`host="${host}"`);
  }

  if (level) {
    labels.push(`level="${level}"`);
  }

  return labels.length > 0
    ? `{${labels.join(',')}}`
    : '{job=~".+"}'; // Query general si no hay filtros
}

/**
 * Abre enlace externo en nueva pestaña
 */
export function openExternalLink(url: string): void {
  window.open(url, '_blank', 'noopener,noreferrer');
}
