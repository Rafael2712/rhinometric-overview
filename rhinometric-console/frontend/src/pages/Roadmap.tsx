import { useEffect, useState } from 'react'
import { MapPin, Zap, Clock, ChevronDown } from 'lucide-react'

/* ----------------------------------------------------------------
   Roadmap data – static for now (no backend dependency).
   Structure makes future i18n or API migration trivial.
   ---------------------------------------------------------------- */
interface RoadmapItem {
  title: string
  description: string
  category: 'Backend' | 'Frontend' | 'Docs' | 'Ops'
  done?: boolean
}

interface RoadmapColumn {
  key: 'P0' | 'P1' | 'P2'
  label: string
  subtitle: string
  icon: typeof Zap
  accent: string
  badgeBg: string
  badgeText: string
  items: RoadmapItem[]
}

const columns: RoadmapColumn[] = [
  {
    key: 'P0',
    label: 'Now',
    subtitle: 'Stability & Commercial Readiness',
    icon: Zap,
    accent: 'border-primary/40',
    badgeBg: 'bg-primary/15',
    badgeText: 'text-primary',
    items: [
      {
        title: 'Close technical debt (licenses, timeouts, critical bugs)',
        description: 'Resolve accumulated technical inconsistencies affecting reliability, including license validation stability, timeout handling, and critical production bugs. This ensures predictable behavior before commercial rollout.',
        category: 'Backend',
      },
      {
        title: 'Minimum test coverage for core modules',
        description: 'Introduce baseline automated test coverage for authentication, license validation, anomaly detection, and notification flows to reduce regression risk during future development.',
        category: 'Backend',
      },
      {
        title: 'Installer packaging + license validation',
        description: 'Finalize deployment packaging and harden license validation logic to support clean installations and secure commercial distribution.',
        category: 'Ops',
      },
      {
        title: 'RBAC hardening + basic audit trail',
        description: 'Stabilize role-based access control (Owner/Admin/Viewer) and implement a basic audit trail for critical actions (settings changes, user modifications, license updates).',
        category: 'Backend',
      },
      {
        title: 'Notifications pipeline validation (Slack + Email)',
        description: 'Ensure end-to-end reliability of notification channels, including configuration persistence, fallback handling, and successful dispatch of critical anomaly alerts.',
        category: 'Backend',
        done: true,
      },
    ],
  },
  {
    key: 'P1',
    label: 'Next',
    subtitle: 'Platform Expansion',
    icon: Clock,
    accent: 'border-secondary/40',
    badgeBg: 'bg-secondary/15',
    badgeText: 'text-secondary',
    items: [
      {
        title: 'Unified Connector Framework (API / Webhook / DB / MQTT)',
        description: 'Design and implement a standardized connector architecture enabling ingestion from HTTP APIs, webhooks, databases, and IoT/MQTT sources under a unified configuration model.',
        category: 'Backend',
      },
      {
        title: 'Dashboard Builder v1 (native UI-based dashboards)',
        description: 'Enable users to create and customize dashboards directly within Rhinometric Console without relying exclusively on external visualization tools.',
        category: 'Frontend',
      },
      {
        title: 'Responsive & mobile improvements',
        description: 'Optimize key pages (License, Alerts, AI Anomalies, Dashboards) for mobile and tablet usability without increasing visual complexity.',
        category: 'Frontend',
      },
      {
        title: 'Load & resilience tests',
        description: 'Perform structured stress and resilience testing to validate system behavior under high ingestion and anomaly detection loads.',
        category: 'Ops',
      },
      {
        title: 'Storage retention policies',
        description: 'Introduce configurable data retention strategies for metrics, logs, and anomalies to support scalability and storage efficiency.',
        category: 'Ops',
      },
      {
        title: 'Meta-monitoring of Rhinometric core',
        description: 'Implement internal monitoring of Rhinometric services themselves (ingestion health, anomaly engine status, dispatcher health) to ensure platform observability.',
        category: 'Ops',
      },
      {
        title: 'Unified event model (cross-source intelligence foundation)',
        description: 'Standardize event representation across data sources to prepare the platform for future cross-service correlation and intelligent clustering capabilities.',
        category: 'Backend',
      },
    ],
  },
  {
    key: 'P2',
    label: 'Later',
    subtitle: 'Advanced Intelligence & Scale',
    icon: MapPin,
    accent: 'border-warning/30',
    badgeBg: 'bg-warning/10',
    badgeText: 'text-warning',
    items: [
      {
        title: 'Full documentation pack (install, ops, user manuals)',
        description: 'Produce comprehensive installation, operational, and user documentation including architectural diagrams and troubleshooting guides.',
        category: 'Docs',
      },
      {
        title: 'Commercialization polish (onboarding, copy, UX)',
        description: 'Refine onboarding flows, product messaging, and user experience details to support commercial positioning and client adoption.',
        category: 'Frontend',
      },
      {
        title: 'Multi-tenant improvements',
        description: 'Enhance isolation and configuration management to better support multiple clients or logical environments within the same platform.',
        category: 'Backend',
      },
      {
        title: 'Advanced correlation & anomaly clustering engine',
        description: 'Develop an intelligent correlation engine capable of detecting relationships between anomalies across services and data sources to reduce alert noise and improve root cause analysis.',
        category: 'Backend',
      },
    ],
  },
]

const categoryColors: Record<string, string> = {
  Backend:  'bg-primary/10 text-primary',
  Frontend: 'bg-secondary/10 text-secondary',
  Docs:     'bg-warning/10 text-warning',
  Ops:      'bg-success/10 text-success',
}

/* ----------------------------------------------------------------
   Component
   ---------------------------------------------------------------- */
export function RoadmapPage() {
  useEffect(() => { document.title = 'Rhinometric - Roadmap' }, [])

  // Track one expanded item globally: "P0-2" means column P0, item index 2
  const [expanded, setExpanded] = useState<string | null>(null)

  const toggle = (key: string) =>
    setExpanded(prev => (prev === key ? null : key))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">Roadmap</h1>
        <p className="text-text-muted text-sm sm:text-base">
          Product priorities for Rhinometric Console v2.6
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(categoryColors).map(([cat, cls]) => (
          <span key={cat} className={`text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
            {cat}
          </span>
        ))}
        <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-success/20 text-success font-medium">
          ✓ Done
        </span>
      </div>

      {/* Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        {columns.map((col) => {
          const Icon = col.icon
          return (
            <div
              key={col.key}
              className={`rounded-xl bg-surface border ${col.accent} p-4 sm:p-5 flex flex-col`}
            >
              {/* Column header */}
              <div className="flex items-center gap-2 mb-1">
                <div className={`p-1.5 rounded-lg ${col.badgeBg}`}>
                  <Icon className={`w-4 h-4 ${col.badgeText}`} />
                </div>
                <div className="flex items-baseline gap-2">
                  <h2 className="text-base sm:text-lg font-semibold text-white">{col.label}</h2>
                  <span className={`text-[10px] sm:text-xs font-medium px-1.5 py-0.5 rounded ${col.badgeBg} ${col.badgeText}`}>
                    {col.key}
                  </span>
                </div>
              </div>
              <p className="text-[10px] sm:text-xs text-text-muted mb-3 ml-9">{col.subtitle}</p>

              {/* Items */}
              <ul className="space-y-2 flex-1">
                {col.items.map((item, idx) => {
                  const itemKey = `${col.key}-${idx}`
                  const isOpen = expanded === itemKey
                  return (
                    <li
                      key={idx}
                      className={`rounded-lg bg-surface-dark border border-gray-700/50 transition-colors hover:border-gray-600 ${item.done ? 'opacity-70' : ''}`}
                    >
                      <button
                        type="button"
                        onClick={() => toggle(itemKey)}
                        className="w-full flex items-start gap-2 px-3 py-2.5 text-left"
                      >
                        <ChevronDown
                          className={`w-3.5 h-3.5 mt-0.5 text-gray-500 flex-shrink-0 transition-transform duration-150 ${isOpen ? 'rotate-0' : '-rotate-90'}`}
                        />
                        <div className="min-w-0 flex-1">
                          <p className={`text-sm text-text-secondary leading-snug ${item.done ? 'line-through' : ''}`}>
                            {item.title}
                          </p>
                          <div className="flex items-center gap-1.5 mt-1.5">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${categoryColors[item.category]}`}>
                              {item.category}
                            </span>
                            {item.done && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-success/20 text-success font-medium">
                                ✓ Done
                              </span>
                            )}
                          </div>
                        </div>
                      </button>

                      {/* Collapsible description */}
                      {isOpen && (
                        <div className="px-3 pb-3 pl-9">
                          <p className="text-xs text-text-muted leading-relaxed">
                            {item.description}
                          </p>
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>

              {/* Item count */}
              <p className="text-[10px] text-text-muted mt-3 pt-2 border-t border-gray-700/50">
                {col.items.length} items · {col.items.filter(i => i.done).length} completed
              </p>
            </div>
          )
        })}
      </div>

      {/* Footer note */}
      <p className="text-xs text-text-muted text-center">
        Last updated: March 2026 · Priorities may shift based on customer feedback.
      </p>
    </div>
  )
}
