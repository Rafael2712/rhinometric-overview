/**
 * Grafana Integration Utilities
 * 
 * v2.6.0-SECURITY:
 * - Anonymous access disabled in Grafana
 * - Using console-viewer user (Viewer role) for read-only access
 * - Kiosk mode enabled to hide Grafana UI chrome
 * - Auth handled via Basic Auth in URL (temporary - will move to backend proxy in v2.7)
 */

const GRAFANA_PUBLIC_URL =
  import.meta.env.VITE_GRAFANA_PUBLIC_URL || "http://89.167.22.228/grafana";

/**
 * Build Grafana URL without credentials (relies on session/cookies)
 * Credentials in URL cause CORS errors in modern browsers
 */
function buildAuthenticatedUrl(path: string, params: Record<string, string> = {}): string {
  // Add theme parameter
  const defaultParams = {
    theme: 'dark',
    ...params
  };
  
  const queryString = new URLSearchParams(defaultParams).toString();
  const url = `${GRAFANA_PUBLIC_URL}${path}?${queryString}`;
  
  return url;
}

/**
 * Abre un dashboard de Grafana en nueva pestaña con autenticación
 * @param uid - UID del dashboard en Grafana
 * @param params - Query params adicionales
 */
export function openGrafanaDashboard(uid: string, params?: Record<string, string>) {
  const url = buildAuthenticatedUrl(`/d/${uid}`, params);
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Abre Grafana Explore en nueva pestaña con autenticación
 * @param extraPath - Path después de /explore (ej: "?orgId=1&left=...")
 */
export function openGrafanaExplore(extraPath: string) {
  // Parse existing params from extraPath
  const [basePath, existingParams] = extraPath.split('?');
  const params: Record<string, string> = {};
  
  if (existingParams) {
    new URLSearchParams(existingParams).forEach((value, key) => {
      params[key] = value;
    });
  }
  
  const url = buildAuthenticatedUrl(`/explore${basePath}`, params);
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Genera URL completa para un dashboard (con autenticación y kiosk)
 * Útil para mostrar en tooltips o copiar al clipboard
 */
export function getGrafanaDashboardUrl(uid: string, params?: Record<string, string>): string {
  return buildAuthenticatedUrl(`/d/${uid}`, params);
}

/**
 * Genera URL para Grafana Explore (con autenticación y kiosk)
 */
export function getGrafanaExploreUrl(extraPath: string): string {
  const [basePath, existingParams] = extraPath.split('?');
  const params: Record<string, string> = {};
  
  if (existingParams) {
    new URLSearchParams(existingParams).forEach((value, key) => {
      params[key] = value;
    });
  }
  
  return buildAuthenticatedUrl(`/explore${basePath}`, params);
}
