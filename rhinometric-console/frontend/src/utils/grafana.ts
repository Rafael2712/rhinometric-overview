/**
 * Grafana Integration Utilities
 * 
 * En v2.5.1 usamos links directos a Grafana en lugar de proxy embebido.
 * Los dashboards, logs y traces se abren en nuevas pestañas apuntando
 * directamente al puerto 3000 de Grafana.
 * 
 * El proxy /api/grafana/ queda reservado para una futura integración
 * con RBAC completo en v2.6.x
 */

const GRAFANA_PUBLIC_URL =
  import.meta.env.VITE_GRAFANA_PUBLIC_URL || "http://89.167.15.73:3000";

/**
 * Abre un dashboard de Grafana en nueva pestaña
 * @param uid - UID del dashboard en Grafana
 * @param params - Query params adicionales (ej: "kiosk=tv&from=now-1h")
 */
export function openGrafanaDashboard(uid: string, params?: string) {
  const queryString = params ? `?${params}` : "";
  const url = `${GRAFANA_PUBLIC_URL}/d/${uid}${queryString}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Abre Grafana Explore en nueva pestaña
 * @param extraPath - Path después de /explore (ej: "?orgId=1&left=...")
 */
export function openGrafanaExplore(extraPath: string) {
  const url = `${GRAFANA_PUBLIC_URL}/explore${extraPath}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Genera URL completa para un dashboard
 * Útil para mostrar en tooltips o copiar al clipboard
 */
export function getGrafanaDashboardUrl(uid: string, params?: string): string {
  const queryString = params ? `?${params}` : "";
  return `${GRAFANA_PUBLIC_URL}/d/${uid}${queryString}`;
}

/**
 * Genera URL para Grafana Explore
 */
export function getGrafanaExploreUrl(extraPath: string): string {
  return `${GRAFANA_PUBLIC_URL}/explore${extraPath}`;
}
