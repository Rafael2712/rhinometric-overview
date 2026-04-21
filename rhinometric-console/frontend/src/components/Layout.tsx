import { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Home, LayoutDashboard, AlertTriangle, Bell, CreditCard, Settings,
  LogOut, Menu, X, Users, Globe, ClipboardList, Flame, Shield,
  HardDrive, Map, Zap, Search, Sun, Moon, ChevronDown,
} from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'
import { useTheme } from '../contexts/ThemeContext'

// ── Nav structure (grouped) ──────────────────────────────────────
const NAV_GROUPS = [
  {
    key: 'overview',
    label: null, // no label for the first single item
    items: [
      { name: 'Overview', href: '/', icon: Home },
    ],
  },
  {
    key: 'operate',
    label: 'OPERAR',
    items: [
      { name: 'Incidentes', href: '/incidents', icon: Flame },
      { name: 'Atención', href: '/alerts', icon: Bell },
      { name: 'Investigar', href: '/ai-anomalies-v2', icon: Search },
    ],
  },
  {
    key: 'manage',
    label: 'GESTIONAR',
    items: [
      { name: 'Servicios', href: '/services', icon: Globe },
      { name: 'Políticas de Alerta', href: '/alert-rules', icon: Shield, requiredRoles: ['OWNER', 'ADMIN'] },
    ],
  },
  {
    key: 'config',
    label: 'CONFIGURACIÓN',
    items: [
      { name: 'Integraciones', href: '/integrations', icon: Zap },
      { name: 'Usuarios', href: '/users', icon: Users, requiredRoles: ['OWNER', 'ADMIN'] },
      { name: 'Ajustes', href: '/settings', icon: Settings, requiredRoles: ['OWNER', 'ADMIN'] },
    ],
  },
  {
    key: 'secondary',
    label: 'MÁS',
    items: [
      { name: 'Historial de Alertas', href: '/alert-history', icon: ClipboardList },
      { name: 'Dashboards', href: '/dashboards', icon: LayoutDashboard },
      { name: 'Informes', href: '/reports', icon: Map },
      { name: 'Licencia', href: '/license', icon: CreditCard, requiredRoles: ['OWNER'] },
      { name: 'Backup', href: '/backup-recovery', icon: HardDrive, requiredRoles: ['OWNER', 'ADMIN'] },
      { name: 'Roadmap', href: '/roadmap', icon: AlertTriangle },
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

  const toggleGroup = (key: string) => {
    setExpandedGroups(prev => ({ ...prev, [key]: !prev[key] }))
  }

  // Global operational status
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

  // Unread alert count for badge
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

  // Incident count badge
  const { data: incCountData } = useQuery({
    queryKey: ['incidents-count-badge', token],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const r = await fetch('/api/incidents', { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) return null
      const d = await r.json()
      const active = (d?.incidents ?? []).filter((i: any) =>
        ['open','investigating','triggered'].includes(i.status))
      return active.length
    },
    enabled: !!token,
    refetchInterval: 15000,
  })

  const downCount = summaryData?.monitored_services?.down ?? 0
  const degradedCount = summaryData?.monitored_services?.degraded ?? 0
  const globalStatus: 'CRITICAL' | 'WARNING' | 'HEALTHY' =
    downCount > 0 ? 'CRITICAL' : degradedCount > 0 ? 'WARNING' : 'HEALTHY'

  const alertBadge = alertCountData ? Number(alertCountData) : 0
  const incBadge = incCountData ? Number(incCountData) : 0

  // Badge count per nav item
  const badges: Record<string, number> = {
    '/incidents': incBadge,
    '/alerts': alertBadge,
  }

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--c-bg)' }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-20 lg:hidden" onClick={closeSidebar} />
      )}

      {/* ── Sidebar ───────────────────────────────────────────── */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-60 flex flex-col transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
        style={{ backgroundColor: 'var(--c-sidebar-bg)', borderRight: '1px solid var(--c-sidebar-border)' }}
      >
        {/* Logo */}
        <div className="px-5 py-5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--c-sidebar-border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/rhino-logo.jpg" alt="Rhinometric" className="w-full h-full object-contain" />
            </div>
            <div>
              <span className="text-sm font-bold text-white leading-tight block">Rhinometric</span>
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
                      <span className="section-heading" style={{ margin: 0, padding: 0 }}>
                        {group.label}
                      </span>
                      <ChevronDown
                        size={12}
                        style={{ color: 'var(--c-sidebar-section)', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 200ms' }}
                      />
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
                          className="flex items-center justify-between px-3 py-2.5 rounded-md transition-colors duration-150 group"
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
                            <span className="ml-2 flex-shrink-0 min-w-[20px] h-5 flex items-center justify-center rounded-full text-xs font-bold px-1.5"
                              style={{
                                backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : 'var(--c-critical)',
                                color: '#fff',
                              }}>
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
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-semibold text-xs flex-shrink-0">
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.username}</p>
              <p className="text-xs truncate" style={{ color: 'var(--c-sidebar-section)' }}>
                {user?.roles?.join(', ')}
              </p>
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
            <span className="font-medium">Cerrar sesión</span>
          </button>
        </div>
      </aside>

      {/* ── Main area ─────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header
          className="h-14 flex items-center px-4 lg:px-6 gap-4 flex-shrink-0"
          style={{ backgroundColor: 'var(--c-header-bg)', borderBottom: '1px solid var(--c-header-border)' }}
        >
          {/* Mobile menu trigger */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-1.5 rounded-md transition-colors"
            style={{ color: 'var(--c-text-muted)' }}
          >
            {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>

          {/* Environment tag */}
          <div className="flex items-center gap-2 text-sm">
            <span className="hidden sm:inline" style={{ color: 'var(--c-text-muted)' }}>Entorno:</span>
            <span className={`font-medium text-xs px-2 py-0.5 rounded-full ${
              environment === 'Production'
                ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300'
                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
            }`}>
              {environment}
            </span>
          </div>

          <div className="flex-1" />

          {/* Global status indicator */}
          <div className="hidden sm:flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full animate-pulse ${
              globalStatus === 'CRITICAL' ? 'bg-red-500' :
              globalStatus === 'WARNING' ? 'bg-amber-500' : 'bg-green-500'
            }`} />
            <span className="text-sm font-medium" style={{ color: 'var(--c-text-secondary)' }}>
              {globalStatus === 'CRITICAL' ? 'Problemas críticos' :
               globalStatus === 'WARNING' ? 'Operación degradada' : 'Todos los sistemas OK'}
            </span>
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md transition-colors duration-150"
            style={{ backgroundColor: 'var(--c-surface-dark)', color: 'var(--c-text-secondary)' }}
            title={theme === 'light' ? 'Cambiar a tema oscuro' : 'Cambiar a tema claro'}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </header>

        {/* Page content */}
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
