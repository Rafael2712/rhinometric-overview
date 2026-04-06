/**
 * Dashboard Library — catalog of available dashboards.
 * Phase 1: frontend-only state with localStorage persistence.
 *
 * Tiers:
 *   1 = Core      — essential dashboards for daily monitoring
 *   2 = Extended   — additional views for deeper operational insight
 *   3 = Advanced   — specialized dashboards for incident response & analysis
 */

export interface DashboardEntry {
  uid: string;
  name: string;
  description: string;
  tier: number;       // 1 = Core, 2 = Extended, 3 = Advanced
  icon: string;       // lucide icon name hint (used for UI label)
}

export const DASHBOARD_LIBRARY: DashboardEntry[] = [
  // ── Core (Tier 1) ──────────────────────────────────────────────
  {
    uid: 'ext-svc-overview',
    name: 'Fleet Overview',
    description: 'Aggregated health, latency, uptime and incident counts across all monitored services.',
    tier: 1,
    icon: 'globe',
  },
  {
    uid: 'ext-svc-detail',
    name: 'Service Detail',
    description: 'Deep-dive into a single service: status, latency trends, health timeline, SLA and check history.',
    tier: 1,
    icon: 'activity',
  },
  {
    uid: 'ext-svc-sla',
    name: 'SLA & Reliability',
    description: 'Fleet and per-service SLA tracking, incident volume, SSL certificate health and uptime distribution.',
    tier: 1,
    icon: 'shield',
  },
  // ── Extended (Tier 2) ──────────────────────────────────────────
  {
    uid: 'ext-svc-group',
    name: 'Group View',
    description: 'Filter and compare services within a group or service type — health, latency and failures at a glance.',
    tier: 2,
    icon: 'layers',
  },
  {
    uid: 'ext-svc-ranking',
    name: 'Performance Ranking',
    description: 'Composite ranking by health, uptime, latency and failures — top and bottom performers.',
    tier: 2,
    icon: 'trophy',
  },
  // ── Advanced (Tier 3) ──────────────────────────────────────────
  {
    uid: 'ext-svc-incidents',
    name: 'Alerts & Incidents',
    description: 'Active failures, degraded services, stale checks, incident volume and worst-health services.',
    tier: 3,
    icon: 'alert-triangle',
  },
  {
    uid: 'ext-svc-failures',
    name: 'Failure Analysis',
    description: 'Top failing services, failure rates, consecutive failure trends and incident spike detection.',
    tier: 3,
    icon: 'x-circle',
  },
  {
    uid: 'ext-svc-latency',
    name: 'Latency Deep Dive',
    description: 'P50/P95/P99 percentiles, latency distribution, spike detection and per-service comparison.',
    tier: 3,
    icon: 'timer',
  },
];

const STORAGE_KEY = 'dashboard_selection';

const DEFAULT_SELECTION: string[] = [
  'ext-svc-overview',
  'ext-svc-detail',
  'ext-svc-sla',
];

/** Load user\u2019s dashboard selection from localStorage (or defaults). */
export function loadSelection(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed: string[] = JSON.parse(raw);
      // Validate entries exist in library
      const valid = parsed.filter(uid =>
        DASHBOARD_LIBRARY.some(d => d.uid === uid)
      );
      return valid.length > 0 ? valid : DEFAULT_SELECTION;
    }
  } catch {
    // corrupted — fall back
  }
  return [...DEFAULT_SELECTION];
}

/** Persist user\u2019s dashboard selection. */
export function saveSelection(uids: string[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(uids));
}

/** Get tier label for display. */
export function tierLabel(tier: number): string {
  switch (tier) {
    case 1: return 'Core';
    case 2: return 'Extended';
    case 3: return 'Advanced';
    default: return 'Other';
  }
}
