/**
 * Dashboard Library — hardcoded catalog of available dashboards.
 * Phase 1: frontend-only state with localStorage persistence.
 */

export interface DashboardEntry {
  uid: string;
  name: string;
  description: string;
  tier: number;       // 1 = core, 2 = extended, 3 = advanced
  icon: string;       // lucide icon name hint (used for UI label)
}

export const DASHBOARD_LIBRARY: DashboardEntry[] = [
  {
    uid: 'ext-svc-overview',
    name: 'Fleet Overview',
    description: 'Aggregated health, latency and uptime across all monitored services.',
    tier: 1,
    icon: 'globe',
  },
  {
    uid: 'ext-svc-detail',
    name: 'Service Detail',
    description: 'Deep-dive into a single service: status, latency trend, SLA and checks.',
    tier: 1,
    icon: 'activity',
  },
  {
    uid: 'ext-svc-sla',
    name: 'SLA & Reliability',
    description: '30-day SLA tracking, incident counts and SSL certificate health.',
    tier: 1,
    icon: 'shield',
  },
  {
    uid: 'ext-svc-group',
    name: 'Group View',
    description: 'Filter and compare services within a group or service type.',
    tier: 2,
    icon: 'layers',
  },
  {
    uid: 'ext-svc-incidents',
    name: 'Alerts & Incidents',
    description: 'Active failures, degraded services and incident volume over time.',
    tier: 3,
    icon: 'alert-triangle',
  },
  {
    uid: 'ext-svc-failures',
    name: 'Failure Analysis',
    description: 'Top failing services, failure rates, spike detection and consecutive failure trends.',
    tier: 2,
    icon: 'x-circle',
  },
  {
    uid: 'ext-svc-latency',
    name: 'Latency Deep Dive',
    description: 'P50/P95/P99 percentiles, latency distribution, spike detection and service comparison.',
    tier: 2,
    icon: 'timer',
  },
  {
    uid: 'ext-svc-ranking',
    name: 'Performance Ranking',
    description: 'Composite ranking by health, uptime, latency and failures — top and bottom performers.',
    tier: 2,
    icon: 'trophy',
  },
];

const STORAGE_KEY = 'dashboard_selection';

const DEFAULT_SELECTION: string[] = [
  'ext-svc-overview',
  'ext-svc-detail',
  'ext-svc-sla',
];

/** Load user's dashboard selection from localStorage (or defaults). */
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

/** Persist user's dashboard selection. */
export function saveSelection(uids: string[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(uids));
}

/** Get tier label for display. */
export function tierLabel(tier: number): string {
  switch (tier) {
    case 1: return 'Core';
    case 2: return 'Extended';
    case 3: return 'Advanced';
    default: return '';
  }
}
