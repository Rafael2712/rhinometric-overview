/**
 * Grafana utilities — DEPRECATED.
 * All observability links now use internal navigation.
 * This file is kept as an empty stub so existing imports don't break at build time.
 */

/** @deprecated No-op stub. Use internal navigation instead. */
export function openGrafanaDashboard(_uid: string, _params?: Record<string, string>) {
  // No-op: Grafana integration removed
}

/** @deprecated No-op stub. Use internal navigation instead. */
export function openGrafanaExplore(_extraPath: string) {
  // No-op: Grafana integration removed
}

/** @deprecated No-op stub. */
export function getGrafanaDashboardUrl(_uid: string, _params?: Record<string, string>): string {
  return ''
}

/** @deprecated No-op stub. */
export function getGrafanaExploreUrl(_extraPath: string): string {
  return ''
}
