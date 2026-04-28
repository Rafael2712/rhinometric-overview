import { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Home, Bell, CreditCard, Settings, LayoutDashboard, HardDrive,
  LogOut, Menu, X, Users, Globe, ClipboardList, Flame, Shield,
  Map, Zap, Search, Sun, Moon, ChevronDown, BarChart2,
} from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { useTheme } from '../contexts/ThemeContext'

const NAV_GROUPS = [
  {
    key: 'overview',
    label: null,
    items: [
      { name: 'Overview', href: '/', icon: Home },
    ],
  },
  {
    key: 'operate',
    label: 'OPERATE',
    items: [
      { name: 'Incidents', href: '/incidents', icon: Flame },
      { name: 'Alerts', href: '/alerts', icon: Bell },
      { name: 'Investigate', href: '/ai-anomalies-v2', icon: Search },
    ],
  },
  {
    key: 'observe',
    label: 'OBSERVE',
    items: [
      { name: 'Dashboards', href: '/dashboards', icon: LayoutDashboard },
    ],
  },
  {
    key: 'manage',
    label: 'MANAGE',
    items: [
      { name: 'Services', href: '/services', icon: Globe },
      { name: 'Alert Policies', href: '/alert-rules', icon: Shield, requiredRoles: ['OWNER', 'ADMIN'] },
      { name: 'SLO', href: '/slo', icon: BarChart2 },
    ],
  },
  {
    key: 'config',
    label: 'CONFIGURATION',
    items: [
      { name: 'Integrations', href: '/integrations', icon: Zap },
      { name: 'Users', href: '/users', icon: Users, requiredRoles: ['OWNER', 'ADMIN'] },
      { name: 'Settings', href: '/settings', icon: Settings, requiredRoles: ['OWNER', 'ADMIN'] },
    ],
  },
  {
    key: 'resilience',
    label: 'RESILIENCE',
    items: [
      { name: 'Backup & Recovery', href: '/backup-recovery', icon: HardDrive },
    ],
  },
  {
    key: 'secondary',
    label: 'MORE',
    items: [
      { name: 'Alert History', href: '/alert-history', icon: ClipboardList },
      { name: 'Reports', href: '/reports', icon: Map },
      { name: 'License', href: '/license', icon: CreditCard, requiredRoles: ['OWNER'] },
    ],
  },
]

export function Layout() {
  const location = useLocation()
  const { user, logout, hasRole } = useAuthStore()
  const { theme, toggleTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    secondary: false,
  })

  const environment = import.meta.env.MODE === 'production' ? 'Production'
    : import.meta.env.MODE === 'staging' ? 'Staging' : 'Development'

  const closeSidebar = () => setSidebarOpen(false)
  const toggleGroup = (key: string) =>
    setExpandedGroups(prev => ({ ...prev, [key]: !prev[key] }))

  const token = useAuthStore((s) => s.token)

  const { data: summaryData } = useQuery({
    queryKey: ['services-summary', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/services/summary', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return null
      return r.json()
    },
    enabled: !!token,
    refetchInterval: 5000,
  })

  const { data: alertCountData } = useQuery({
    queryKey: ['alerts-count-badge', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/alerts', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return null
      const d = await r.json()
      return d?.total ?? (Array.isArray(d?.alerts) ? d.alerts.length : 0)
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const { data: incCountData } = useQuery({
    queryKey: ['incidents-count-badge', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/incidents', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return null
      const d = await r.json()
      const active = (d?.incidents ?? []).filter((i: any) =>
        ['open', 'investigating', 'triggered'].includes(i.status))
      return active.length
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const { data: anomalyCountData } = useQuery({
    queryKey: ['anomalies-count-badge', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/v2/anomalies/active', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return 0
      const d = await r.json()
      return d?.count ?? 0
    },
    enabled: !!token,
    refetchInterval: 30000,
  })

  const downCount = summaryData?.monitored_services?.down ?? 0
  const degradedCount = summaryData?.monitored_services?.degraded ?? 0
  const alertBadge = alertCountData ? Number(alertCountData) : 0
  const incBadge = incCountData ? Number(incCountData) : 0
  const anomalyBadge = anomalyCountData ? Number(anomalyCountData) : 0
  // Unified global status — single source of truth
  const globalStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY' =
    downCount > 0 ? 'CRITICAL'
    : degradedCount > 0 || alertBadge > 0 || incBadge > 0 || anomalyBadge > 0 ? 'WARNING'
    : 'HEALTHY'
  const badges: Record<string, number> = { '/incidents': incBadge, '/alerts': alertBadge, '/ai-anomalies-v2': anomalyBadge }
  // Per-item badge colors: incidents=critical-red, alerts=amber-warning, investigate=indigo-ai
  const badgeColors: Record<string, string> = {
    '/incidents':       '#b91c1c',
    '/alerts':          '#b45309',
    '/ai-anomalies-v2': '#4f46e5',
  }

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--c-bg)' }}>
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-20 lg:hidden" onClick={closeSidebar} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-60 flex flex-col transform transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
        style={{ backgroundColor: 'var(--c-sidebar-bg)', borderRight: '1px solid var(--c-sidebar-border)' }}
      >
        {/* Logo */}
        <div className="px-5 py-5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--c-sidebar-border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/rhino-logo.jpg" alt="Rhinometric" className="w-full h-full object-contain" />
            </div>
            <div>
              <span className="text-sm font-bold leading-tight block" style={{ color: 'var(--c-sidebar-text-hover)' }}>Rhinometric</span>
              <span className="text-xs leading-tight block" style={{ color: 'var(--c-sidebar-section)' }}>Console</span>
            </div>
          </div>
          <button onClick={closeSidebar} className="lg:hidden p-1 rounded" style={{ color: 'var(--c-sidebar-text)' }}>
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3">
          {NAV_GROUPS.map((group) => {
            const visibleItems = group.items.filter(item =>
              !(item as any).requiredRoles ||
              (item as any).requiredRoles.some((r: string) => hasRole(r))
            )
            if (visibleItems.length === 0) return null
            const isCollapsible = group.key === 'secondary'
            const isExpanded = isCollapsible ? expandedGroups[group.key] : true
            return (
              <div key={group.key} className="mb-1">
                {group.label && (
                  isCollapsible ? (
                    <button
                      onClick={() => toggleGroup(group.key)}
                      className="w-full flex items-center justify-between px-4 py-1.5 text-left"
                    >
                      <span className="section-heading" style={{ margin: 0, padding: 0 }}>{group.label}</span>
                      <ChevronDown size={12} style={{ color: 'var(--c-sidebar-section)', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 200ms' }} />
                    </button>
                  ) : (
                    <div className="section-heading">{group.label}</div>
                  )
                )}
                {isExpanded && (
                  <div className="space-y-0.5 px-3">
                    {visibleItems.map((item) => {
                      const Icon = item.icon
                      const isActive = location.pathname === item.href
                      const badge = badges[item.href] ?? 0
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          onClick={closeSidebar}
                          className="flex items-center justify-between px-3 py-2.5 rounded-md transition-colors duration-150"
                          style={{
                            backgroundColor: isActive ? 'var(--c-sidebar-active-bg)' : 'transparent',
                            color: isActive ? 'var(--c-sidebar-active-text)' : 'var(--c-sidebar-text)',
                          }}
                          onMouseEnter={e => {
                            if (!isActive) {
                              (e.currentTarget as HTMLElement).style.backgroundColor = 'var(--c-sidebar-hover-bg)'
                              ;(e.currentTarget as HTMLElement).style.color = 'var(--c-sidebar-text-hover)'
                            }
                          }}
                          onMouseLeave={e => {
                            if (!isActive) {
                              (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent'
                              ;(e.currentTarget as HTMLElement).style.color = 'var(--c-sidebar-text)'
                            }
                          }}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <Icon className="w-4 h-4 flex-shrink-0" />
                            <span className="text-sm font-medium truncate">{item.name}</span>
                          </div>
                          {badge > 0 && (
                            <span
                              className="ml-2 flex-shrink-0 min-w-[20px] h-5 flex items-center justify-center rounded-full text-xs font-bold px-1.5"
                              style={{ backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : (badgeColors[item.href] ?? 'var(--c-critical)'), color: '#fff' }}
                            >
                              {badge > 99 ? '99+' : badge}
                            </span>
                          )}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4" style={{ borderTop: '1px solid var(--c-sidebar-border)' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-gray-900 font-semibold text-xs flex-shrink-0">
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--c-sidebar-text-hover)' }}>{user?.username}</p>
              <p className="text-xs truncate" style={{ color: 'var(--c-sidebar-section)' }}>{user?.roles?.join(', ')}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm transition-colors duration-150"
            style={{ backgroundColor: 'var(--c-sidebar-hover-bg)', color: 'var(--c-sidebar-text)' }}
            onMouseEnter={e => {
              ;(e.currentTarget as HTMLElement).style.backgroundColor = '#ef4444'
              ;(e.currentTarget as HTMLElement).style.color = '#fff'
            }}
            onMouseLeave={e => {
              ;(e.currentTarget as HTMLElement).style.backgroundColor = 'var(--c-sidebar-hover-bg)'
              ;(e.currentTarget as HTMLElement).style.color = 'var(--c-sidebar-text)'
            }}
          >
            <LogOut className="w-4 h-4" />
            <span className="font-medium">Log out</span>
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header
          className="h-14 flex items-center px-4 lg:px-6 gap-4 flex-shrink-0"
          style={{ backgroundColor: 'var(--c-header-bg)', borderBottom: '1px solid var(--c-header-border)' }}
        >
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-1.5 rounded-md transition-colors"
            style={{ color: 'var(--c-text-muted)' }}
          >
            {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>

          <div className="flex items-center gap-2 text-sm">
            <span className="hidden sm:inline" style={{ color: 'var(--c-text-muted)' }}>Environment:</span>
            <span
              className={`font-medium text-xs px-2 py-0.5 rounded-full ${
                environment === 'Production'
                  ? 'bg-sky-100 text-sky-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {environment}
            </span>
          </div>

          <div className="flex-1" />

          <div className="hidden sm:flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full animate-pulse ${
              globalStatus === 'CRITICAL' ? 'bg-red-500' :
              globalStatus === 'WARNING' ? 'bg-amber-500' : 'bg-green-500'
            }`} />
            <span className="text-sm font-medium" style={{ color: 'var(--c-text-secondary)' }}>
              {globalStatus === 'CRITICAL' ? 'Critical issues detected' :
               globalStatus === 'WARNING' ? 'Degraded operation' : 'All systems OK'}
            </span>
          </div>

          <button
            onClick={toggleTheme}
            className="p-2 rounded-md transition-colors duration-150"
            style={{ backgroundColor: 'var(--c-surface-dark)', color: 'var(--c-text-secondary)' }}
            title={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </header>

        <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
          <Outlet />
          <footer className="mt-12 pt-6 border-t text-center text-xs" style={{ borderColor: 'var(--c-border)', color: 'var(--c-text-muted)' }}>
            <p>Rhinometric Console v2.6.0 · © {new Date().getFullYear()} Rhinometric</p>
          </footer>
        </main>
      </div>
    </div>
  )
}
