import { useEffect, useState } from 'react'
import {
  CheckCircle2, Zap, Clock, MapPin, ChevronDown, Shield,
  Activity, Brain, Bell, AlertTriangle, GitBranch, Target,
  Search, Network, BarChart3, FileText, Users, Layers,
  Server, Lock, Gauge, Workflow, Cpu, Database
} from 'lucide-react'

/* ----------------------------------------------------------------
   Roadmap data – static (no backend dependency).
   Structure makes future i18n or API migration trivial.
   ---------------------------------------------------------------- */
interface RoadmapItem {
  title: string
  summary: string
  whatItDoes: string
  whyItMatters: string
  category: 'Backend' | 'Frontend' | 'Docs' | 'Ops' | 'AI' | 'Full-Stack'
  done?: boolean
  icon: typeof Activity
}

interface RoadmapSection {
  key: 'completed' | 'P0' | 'P1' | 'P2'
  label: string
  subtitle: string
  icon: typeof Zap
  accent: string
  badgeBg: string
  badgeText: string
  headerBg: string
  items: RoadmapItem[]
}

const sections: RoadmapSection[] = [
  /* ============================================================
     CORE PLATFORM — COMPLETED
     ============================================================ */
  {
    key: 'completed',
    label: 'Core Platform',
    subtitle: 'Delivered & Production-Ready',
    icon: CheckCircle2,
    accent: 'border-success/50',
    badgeBg: 'bg-success/15',
    badgeText: 'text-success',
    headerBg: 'from-success/5 to-transparent',
    items: [
      {
        title: 'Service Monitoring',
        summary: 'Real-time health tracking for every registered service.',
        whatItDoes: 'Continuously monitors HTTP endpoints, latency, error rates, and availability for all configured services. Displays live health status with color-coded indicators and historical trend data.',
        whyItMatters: 'Provides the foundational visibility layer that every operator needs — knowing which services are healthy and which need attention, at a glance.',
        category: 'Full-Stack',
        done: true,
        icon: Activity,
      },
      {
        title: 'Service Dependency Map',
        summary: 'Visual graph of how services connect and affect each other.',
        whatItDoes: 'Renders an interactive directed graph showing service-to-service dependencies (HTTP, database, cache, queue, external). Supports drag-and-drop layout, hover tooltips, click-to-inspect detail panels, and automatic impact propagation when a service degrades.',
        whyItMatters: 'Operators can instantly understand blast radius — when one service fails, the map shows which downstream services are at risk, enabling faster triage and smarter escalation.',
        category: 'Full-Stack',
        done: true,
        icon: Network,
      },
      {
        title: 'AI-Powered Anomaly Detection',
        summary: 'Automatic detection of unusual metric behavior using statistical analysis.',
        whatItDoes: 'Analyzes service metrics (latency, error rate, availability) using adaptive statistical thresholds. Detects deviations beyond normal baselines, groups related anomalies by service and time window, and tracks anomaly lifecycle (open → acknowledged → resolved).',
        whyItMatters: 'Catches problems that static thresholds miss. Reduces mean-time-to-detect by surfacing metric anomalies before they become user-visible incidents.',
        category: 'AI',
        done: true,
        icon: Brain,
      },
      {
        title: 'AI Insights',
        summary: 'Explainable AI-assisted analysis with risk scoring and recommendations.',
        whatItDoes: 'Analyzes monitored services over time, computes composite risk scores with weighted factors, detects latency and availability trends with statistical regression, identifies anomaly patterns, and generates actionable recommendations. Provides per-service insight cards with expandable trend details and risk breakdowns.',
        whyItMatters: 'Transforms raw monitoring data into operator-friendly intelligence. Instead of reading dashboards, operators receive clear risk assessments and prioritized recommendations — supporting faster, more confident decisions.',
        category: 'AI',
        done: true,
        icon: Zap,
      },
      {
        title: 'Alert Rules Management',
        summary: 'Configurable rules engine for defining alert conditions.',
        whatItDoes: 'Allows operators to create, edit, enable/disable, and delete alert rules with configurable conditions (metric thresholds, comparison operators), severity levels (critical, warning, info), and evaluation intervals. Rules are evaluated automatically against live service metrics.',
        whyItMatters: 'Gives teams precise control over what triggers notifications, reducing alert fatigue while ensuring critical conditions are never missed.',
        category: 'Full-Stack',
        done: true,
        icon: Bell,
      },
      {
        title: 'Alerts & Notifications',
        summary: 'Real-time alert generation and multi-channel delivery.',
        whatItDoes: 'Generates alerts when configured rules are violated, delivers notifications through Slack and email channels, and maintains a live alert feed with severity indicators, timestamps, and acknowledgment controls.',
        whyItMatters: 'Ensures the right people know about problems immediately — through the channels they already use — without requiring constant dashboard monitoring.',
        category: 'Backend',
        done: true,
        icon: AlertTriangle,
      },
      {
        title: 'Alert History',
        summary: 'Searchable archive of all past alerts with filtering and analytics.',
        whatItDoes: 'Stores every alert ever generated with full metadata. Provides a paginated, filterable interface with search by service, severity, status, and date range. Includes resolution tracking and alert frequency analytics.',
        whyItMatters: 'Enables post-incident review and trend analysis — teams can identify recurring alert patterns, measure improvement over time, and demonstrate compliance with audit requirements.',
        category: 'Full-Stack',
        done: true,
        icon: FileText,
      },
      {
        title: 'Incident Management',
        summary: 'Structured incident lifecycle from detection through resolution.',
        whatItDoes: 'Provides a complete incident workflow: creation (manual or from alerts), status progression (open → investigating → mitigating → resolved → closed), severity classification, service association, assignment to team members, and resolution tracking with timestamps.',
        whyItMatters: 'Replaces ad-hoc incident handling with a structured process. Every incident has clear ownership, status, and history — essential for team coordination and post-incident learning.',
        category: 'Full-Stack',
        done: true,
        icon: Shield,
      },
      {
        title: 'Incident Timeline & Collaboration',
        summary: 'Chronological event log with team collaboration tools per incident.',
        whatItDoes: 'Records every incident event (status changes, assignments, comments, linked alerts) on a timestamped timeline. Supports team comments with author attribution, event filtering by type, and a complete audit trail from detection to resolution.',
        whyItMatters: 'Creates institutional memory for every incident. During active response, teams coordinate through comments. After resolution, the timeline provides the foundation for blameless post-mortems.',
        category: 'Full-Stack',
        done: true,
        icon: GitBranch,
      },
      {
        title: 'Root Cause Analysis Engine',
        summary: 'Deterministic analysis that identifies probable incident causes.',
        whatItDoes: 'Examines a ±5-minute window around each incident, correlating four signal sources: metric anomalies, active alerts, anomaly detection results, and log patterns. Scores each signal by relevance and timing proximity, ranks contributing factors, and presents results with confidence levels (high, medium, low).',
        whyItMatters: 'Accelerates post-incident review from hours to seconds. Instead of manually correlating dashboards, operators get a ranked list of probable causes backed by evidence — dramatically reducing mean-time-to-understand.',
        category: 'AI',
        done: true,
        icon: Search,
      },
      {
        title: 'SLO/SLA Tracking',
        summary: 'Objective-based reliability tracking with burn-rate monitoring.',
        whatItDoes: 'Defines Service Level Objectives (availability and latency targets) per service, continuously tracks compliance against targets, calculates remaining error budgets, monitors burn rates, and triggers warnings when error budgets are at risk of exhaustion.',
        whyItMatters: 'Shifts reliability conversations from subjective ("the service feels slow") to objective ("we have consumed 73% of our monthly error budget"). Essential for SLA commitments and data-driven prioritization.',
        category: 'Full-Stack',
        done: true,
        icon: Target,
      },
      {
        title: 'RBAC Access Control',
        summary: 'Role-based permissions controlling who can do what.',
        whatItDoes: 'Implements three access levels (Owner, Admin, Viewer) with enforced permissions across all API endpoints and UI components. Owners manage users and system settings, Admins configure services and rules, Viewers have read-only access.',
        whyItMatters: 'Ensures operational security — the right people have the right access. Prevents accidental misconfiguration by viewers and provides the access control foundation required for enterprise adoption.',
        category: 'Backend',
        done: true,
        icon: Lock,
      },
    ],
  },

  /* ============================================================
     NOW — P0: STABILITY & COMMERCIAL READINESS
     ============================================================ */
  {
    key: 'P0',
    label: 'Now',
    subtitle: 'Stability & Commercial Readiness',
    icon: Zap,
    accent: 'border-primary/40',
    badgeBg: 'bg-primary/15',
    badgeText: 'text-primary',
    headerBg: 'from-primary/5 to-transparent',
    items: [
      {
        title: 'Close Technical Debt',
        summary: 'Resolve accumulated inconsistencies affecting reliability.',
        whatItDoes: 'Addresses critical bugs, timeout handling, license validation edge cases, and code inconsistencies identified during feature development. Includes dependency updates and deprecation fixes.',
        whyItMatters: 'A clean, predictable codebase is the prerequisite for production confidence. Unresolved debt compounds into unpredictable failures under real-world conditions.',
        category: 'Backend',
        icon: Workflow,
      },
      {
        title: 'Test Coverage for Core Modules',
        summary: 'Baseline automated tests for critical paths.',
        whatItDoes: 'Introduces and expands automated test coverage for authentication, license validation, anomaly detection, notification flows, incident management, and alert rule evaluation. Targets regression prevention for the most impactful code paths.',
        whyItMatters: 'Reduces regression risk during future development and maintenance. Automated tests act as a safety net — catching breaks before they reach production.',
        category: 'Backend',
        icon: Shield,
      },
      {
        title: 'Installer Packaging & License Validation',
        summary: 'Clean installation scripts and hardened licensing.',
        whatItDoes: 'Finalizes deployment packaging (Docker Compose configuration, environment templates, migration scripts) and hardens license validation logic to support clean installations, upgrades, and secure commercial distribution.',
        whyItMatters: 'First impressions matter — a smooth installation experience and reliable licensing are table-stakes for commercial software. Eliminates "works on my machine" deployment issues.',
        category: 'Ops',
        icon: Layers,
      },
      {
        title: 'RBAC Hardening & Audit Trail',
        summary: 'Strengthen access controls and log critical actions.',
        whatItDoes: 'Stabilizes role-based access enforcement across all endpoints, implements a basic audit trail for critical operations (user management, settings changes, license updates, rule modifications), and adds session management improvements.',
        whyItMatters: 'Enterprise customers require demonstrable access control and auditability. This work closes the gap between functional RBAC and production-grade security compliance.',
        category: 'Backend',
        icon: Lock,
      },
      {
        title: 'Production Deployment Validation',
        summary: 'End-to-end verification of the full deployment pipeline.',
        whatItDoes: 'Validates the complete deployment cycle: fresh installation, configuration, service registration, monitoring activation, alert generation, incident creation, and notification delivery. Includes smoke tests and health-check verification.',
        whyItMatters: 'Confirms that every feature works together in a production-like environment — not just individually in development. The final gate before commercial release.',
        category: 'Ops',
        icon: Server,
      },
    ],
  },

  /* ============================================================
     NEXT — P1: PLATFORM EXPANSION
     ============================================================ */
  {
    key: 'P1',
    label: 'Next',
    subtitle: 'Platform Expansion',
    icon: Clock,
    accent: 'border-secondary/40',
    badgeBg: 'bg-secondary/15',
    badgeText: 'text-secondary',
    headerBg: 'from-secondary/5 to-transparent',
    items: [
      {
        title: 'Unified Connector Framework',
        summary: 'Standardized ingestion from diverse data sources.',
        whatItDoes: 'Implements a connector architecture supporting HTTP APIs, webhooks, databases, and IoT/MQTT sources under a unified configuration model. Each connector type follows a standard interface for registration, health checking, and data normalization.',
        whyItMatters: 'Unlocks monitoring for environments beyond HTTP services — industrial IoT, database health, third-party API integrations — without custom development for each source.',
        category: 'Backend',
        icon: Cpu,
      },
      {
        title: 'Dashboard Builder v1',
        summary: 'Native UI-based dashboard creation and customization.',
        whatItDoes: 'Enables users to create, arrange, and customize dashboards directly within Rhinometric Console. Supports metric widgets, status panels, chart types, and layout persistence — without relying exclusively on external tools like Grafana.',
        whyItMatters: 'Reduces dependency on external visualization tools for common use cases. Operators can build focused dashboards tailored to their specific monitoring needs within minutes.',
        category: 'Frontend',
        icon: BarChart3,
      },
      {
        title: 'Responsive & Mobile Improvements',
        summary: 'Optimized experience on tablets and mobile devices.',
        whatItDoes: 'Adapts key pages (Services, Alerts, AI Anomalies, Incidents, Dashboards) for mobile and tablet screen sizes. Implements responsive layouts, touch-friendly interactions, and condensed data views without sacrificing information density.',
        whyItMatters: 'On-call engineers need to check system status from their phones. Responsive design makes Rhinometric usable anywhere, not just at a desk.',
        category: 'Frontend',
        icon: Layers,
      },
      {
        title: 'Load & Resilience Testing',
        summary: 'Structured stress testing under production-like conditions.',
        whatItDoes: 'Performs structured load tests simulating high ingestion volumes, concurrent anomaly detection, alert storms, and API throughput limits. Identifies bottlenecks and validates recovery behavior under resource pressure.',
        whyItMatters: 'Monitoring platforms must remain stable when the systems they monitor are failing — the worst time for the monitoring tool to break. Load testing proves resilience when it matters most.',
        category: 'Ops',
        icon: Gauge,
      },
      {
        title: 'Storage Retention Policies',
        summary: 'Configurable data lifecycle management.',
        whatItDoes: 'Introduces configurable retention strategies for metrics, logs, anomalies, alerts, and incident data. Supports time-based expiration, storage quotas, and archival rules with automatic cleanup.',
        whyItMatters: 'Without retention policies, storage grows indefinitely. Configurable retention balances operational history needs with infrastructure cost and database performance.',
        category: 'Ops',
        icon: Database,
      },
      {
        title: 'Meta-Monitoring of Rhinometric Core',
        summary: 'Self-monitoring the monitoring platform itself.',
        whatItDoes: 'Implements internal observability for Rhinometric services: ingestion pipeline health, anomaly engine processing latency, notification dispatcher status, API response times, and database connection pool utilization.',
        whyItMatters: 'A monitoring platform that cannot monitor itself is a blind spot. Meta-monitoring ensures operators are alerted to platform issues before they affect service visibility.',
        category: 'Ops',
        icon: Activity,
      },
      {
        title: 'Unified Event Model',
        summary: 'Cross-source event standardization for intelligent correlation.',
        whatItDoes: 'Standardizes event representation across all data sources (metrics, logs, alerts, anomalies, incidents) into a unified schema. Enables cross-source queries, consistent timestamps, and shared context propagation.',
        whyItMatters: 'The foundation for next-generation intelligence features. Unified events enable correlation queries like "show me everything that happened to Service X in the last hour" across all data types.',
        category: 'Backend',
        icon: Workflow,
      },
      {
        title: 'Operational Reporting',
        summary: 'Scheduled and on-demand operational reports.',
        whatItDoes: 'Generates configurable reports covering SLO compliance, incident frequency, mean-time-to-resolve trends, anomaly patterns, and service health summaries. Supports PDF/CSV export and scheduled email delivery.',
        whyItMatters: 'Transforms operational data into management-ready reports. Essential for SLA reviews, capacity planning discussions, and demonstrating platform value to stakeholders.',
        category: 'Full-Stack',
        icon: FileText,
      },
    ],
  },

  /* ============================================================
     LATER — P2: ADVANCED INTELLIGENCE & SCALE
     ============================================================ */
  {
    key: 'P2',
    label: 'Later',
    subtitle: 'Advanced Intelligence & Scale',
    icon: MapPin,
    accent: 'border-warning/30',
    badgeBg: 'bg-warning/10',
    badgeText: 'text-warning',
    headerBg: 'from-warning/5 to-transparent',
    items: [
      {
        title: 'Full Documentation Pack',
        summary: 'Comprehensive installation, operations, and user documentation.',
        whatItDoes: 'Produces complete documentation including installation guides, operational runbooks, user manuals, API reference, architectural diagrams, and troubleshooting guides. Covers all platform features with examples and best practices.',
        whyItMatters: 'Professional documentation is the difference between a tool and a product. Enables self-service adoption, reduces support burden, and is a hard requirement for enterprise procurement.',
        category: 'Docs',
        icon: FileText,
      },
      {
        title: 'Commercialization Polish',
        summary: 'Onboarding, messaging, and UX refinements for market readiness.',
        whatItDoes: 'Refines the first-run experience (guided onboarding wizard), product messaging and copy across all pages, empty-state illustrations, loading transitions, and micro-interactions. Ensures consistent visual language and professional presentation.',
        whyItMatters: 'Product perception drives adoption. Polish transforms a capable technical tool into a product that feels trustworthy and approachable from the first interaction.',
        category: 'Frontend',
        icon: Users,
      },
      {
        title: 'Multi-Tenant Improvements',
        summary: 'Enhanced isolation for multiple clients or environments.',
        whatItDoes: 'Enhances data isolation, configuration scoping, and resource management to support multiple clients or logical environments within a single platform deployment. Includes per-tenant settings, data segregation, and usage tracking.',
        whyItMatters: 'Enables managed-service and SaaS deployment models. Multi-tenancy multiplies platform value by serving multiple customers from a single infrastructure investment.',
        category: 'Backend',
        icon: Layers,
      },
      {
        title: 'Advanced Correlation Engine',
        summary: 'Intelligent cross-service anomaly correlation and clustering.',
        whatItDoes: 'Develops an intelligent correlation engine capable of detecting causal relationships between anomalies across services, clustering related events, identifying cascade patterns, and reducing alert noise through deduplication and grouping.',
        whyItMatters: 'The ultimate intelligence layer — instead of N separate alerts, operators see one correlated incident with full causality chain. Dramatically reduces cognitive load during complex multi-service failures.',
        category: 'AI',
        icon: Brain,
      },
    ],
  },
]

const categoryColors: Record<string, string> = {
  'Full-Stack': 'bg-primary/10 text-primary',
  Backend:      'bg-blue-500/10 text-blue-400',
  Frontend:     'bg-secondary/10 text-secondary',
  AI:           'bg-purple-500/10 text-purple-400',
  Docs:         'bg-warning/10 text-warning',
  Ops:          'bg-success/10 text-success',
}

/* ----------------------------------------------------------------
   Component
   ---------------------------------------------------------------- */
export function RoadmapPage() {
  useEffect(() => { document.title = 'Rhinometric \u2014 Roadmap' }, [])

  const [expanded, setExpanded] = useState<string | null>(null)
  const toggle = (key: string) =>
    setExpanded(prev => (prev === key ? null : key))

  const totalItems = sections.reduce((s, c) => s + c.items.length, 0)
  const doneItems  = sections.reduce((s, c) => s + c.items.filter(i => i.done).length, 0)
  const pct = Math.round((doneItems / totalItems) * 100)

  return (
    <div className="space-y-6">
      {/* ---- Header ---- */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">Product Roadmap</h1>
        <p className="text-text-muted text-sm sm:text-base">
          Rhinometric Console — feature delivery tracker and product vision
        </p>
      </div>

      {/* ---- Progress bar ---- */}
      <div className="bg-surface rounded-xl border border-gray-700/50 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-text-secondary font-medium">Overall Progress</span>
          <span className="text-sm text-white font-semibold">{doneItems} / {totalItems} features ({pct}%)</span>
        </div>
        <div className="h-2.5 bg-surface-dark rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-success to-primary rounded-full transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex gap-4 mt-3 text-xs text-text-muted">
          {sections.map(s => (
            <span key={s.key} className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${s.badgeBg} ${s.badgeText} inline-block ring-1 ring-current`} />
              {s.label}: {s.items.length} items
            </span>
          ))}
        </div>
      </div>

      {/* ---- Legend ---- */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(categoryColors).map(([cat, cls]) => (
          <span key={cat} className={`text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
            {cat}
          </span>
        ))}
        <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-success/20 text-success font-medium ml-2">
          ✓ Delivered
        </span>
      </div>

      {/* ---- Sections ---- */}
      <div className="space-y-6">
        {sections.map((sec) => {
          const Icon = sec.icon
          const sectionDone = sec.items.filter(i => i.done).length
          return (
            <div
              key={sec.key}
              className={`rounded-xl bg-surface border ${sec.accent} overflow-hidden`}
            >
              {/* Section header */}
              <div className={`bg-gradient-to-r ${sec.headerBg} px-4 sm:px-5 py-4 border-b border-gray-700/30`}>
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${sec.badgeBg}`}>
                    <Icon className={`w-5 h-5 ${sec.badgeText}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-lg sm:text-xl font-semibold text-white">{sec.label}</h2>
                      <span className={`text-[10px] sm:text-xs font-bold px-2 py-0.5 rounded ${sec.badgeBg} ${sec.badgeText} uppercase tracking-wide`}>
                        {sec.key}
                      </span>
                      {sec.key === 'completed' && (
                        <span className="text-[10px] sm:text-xs px-2 py-0.5 rounded bg-success/20 text-success font-medium">
                          All delivered
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-muted mt-0.5">{sec.subtitle}</p>
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap">
                    {sectionDone}/{sec.items.length}
                  </span>
                </div>
              </div>

              {/* Items grid */}
              <div className="p-4 sm:p-5">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {sec.items.map((item, idx) => {
                    const itemKey = `${sec.key}-${idx}`
                    const isOpen = expanded === itemKey
                    const ItemIcon = item.icon
                    return (
                      <div
                        key={idx}
                        className={`rounded-lg bg-surface-dark border transition-all duration-200 ${
                          isOpen ? 'border-gray-600 ring-1 ring-gray-600/50' : 'border-gray-700/50 hover:border-gray-600'
                        } ${item.done ? '' : 'opacity-90'}`}
                      >
                        <button
                          type="button"
                          onClick={() => toggle(itemKey)}
                          className="w-full flex items-start gap-3 px-3.5 py-3 text-left"
                        >
                          <div className={`p-1.5 rounded-md mt-0.5 flex-shrink-0 ${item.done ? 'bg-success/15' : sec.badgeBg}`}>
                            <ItemIcon className={`w-3.5 h-3.5 ${item.done ? 'text-success' : sec.badgeText}`} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className={`text-sm font-medium leading-snug ${item.done ? 'text-success' : 'text-text-secondary'}`}>
                                {item.title}
                              </p>
                              {item.done && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-success/20 text-success font-bold uppercase tracking-wide">
                                  Delivered
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-text-muted mt-1 leading-relaxed">{item.summary}</p>
                            <div className="flex items-center gap-1.5 mt-2">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${categoryColors[item.category]}`}>
                                {item.category}
                              </span>
                            </div>
                          </div>
                          <ChevronDown
                            className={`w-4 h-4 mt-1 text-gray-500 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-0' : '-rotate-90'}`}
                          />
                        </button>

                        {/* Expanded detail */}
                        {isOpen && (
                          <div className="px-3.5 pb-3.5 pl-12 space-y-2.5 border-t border-gray-700/30 pt-2.5 mx-3.5 mb-1">
                            <div>
                              <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-1">What it does</p>
                              <p className="text-xs text-text-secondary leading-relaxed">{item.whatItDoes}</p>
                            </div>
                            <div>
                              <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wide mb-1">Why it matters</p>
                              <p className="text-xs text-text-secondary leading-relaxed">{item.whyItMatters}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* ---- Footer ---- */}
      <div className="text-center space-y-1 pt-2">
        <p className="text-xs text-text-muted">
          Last updated: June 2025 · Priorities may shift based on customer feedback and operational needs.
        </p>
        <p className="text-[10px] text-text-muted/60">
          Rhinometric Console · Product Roadmap · {doneItems} features delivered · {totalItems - doneItems} planned
        </p>
      </div>
    </div>
  )
}
