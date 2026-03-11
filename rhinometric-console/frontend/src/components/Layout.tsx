import { useState } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { Home, LayoutDashboard, AlertTriangle, Bell, FileText, Network, CreditCard, Settings, LogOut, Menu, X, Users, Map, Globe, Brain, ClipboardList, Flame, Target } from 'lucide-react'
import { useAuthStore } from '../lib/auth/store'

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Services', href: '/services', icon: Globe },
  { name: 'Dashboards', href: '/dashboards', icon: LayoutDashboard },
  { name: 'AI Anomalies', href: '/anomalies', icon: AlertTriangle },
  { name: 'AI Insights', href: '/ai-insights', icon: Brain },
  { name: 'Alerts', href: '/alerts', icon: Bell },
  { name: 'Alert History', href: '/alert-history', icon: ClipboardList },
  { name: 'Incidents', href: '/incidents', icon: Flame },
  { name: 'SLO / SLA', href: '/slo', icon: Target },
  { name: 'Logs', href: '/logs', icon: FileText },
  { name: 'Traces', href: '/traces', icon: Network },
  { name: 'License', href: '/license', icon: CreditCard },
  { name: 'Users', href: '/users', icon: Users, requiresAdmin: true },
  { name: 'Roadmap', href: '/roadmap', icon: Map },
  { name: 'Settings', href: '/settings', icon: Settings, requiresAdmin: true },
]

export function Layout() {
  const location = useLocation()
  const { user, logout, canManageUsers } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Environment detection
  const environment = import.meta.env.MODE === 'production' ? 'Production' :
                      import.meta.env.MODE === 'staging' ? 'Staging' : 'Development'

  // Close sidebar on navigation (mobile UX)
  const closeSidebar = () => setSidebarOpen(false)

  return (
    <div className="min-h-screen flex bg-background">
      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-30 w-64 bg-surface border-r border-gray-700 flex flex-col transform transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        {/* Logo + close button on mobile */}
        <div className="p-4 sm:p-6 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative w-10 h-10 sm:w-14 sm:h-14 flex items-center justify-center">
                <img src="/rhino-logo.jpg" alt="Rhinometric" className="w-10 h-10 sm:w-14 sm:h-14 object-contain" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent leading-tight">
                  Rhinometric
                </span>
                <span className="text-xs text-gray-400 leading-tight">Console</span>
              </div>
            </div>
            {/* Close button - mobile only */}
            <button
              onClick={closeSidebar}
              className="lg:hidden p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-surface-light"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <nav className="flex-1 px-3 sm:px-4 py-4 sm:py-6 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            if (item.requiresAdmin && !canManageUsers()) {
              return null
            }

            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={closeSidebar}
                className={`flex items-center px-3 sm:px-4 py-2.5 sm:py-3 rounded-md transition-colors duration-200 ${isActive ? 'bg-primary text-white' : 'text-gray-400 hover:bg-surface-light hover:text-white'}`}
              >
                <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
                <span className="font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>

        <div className="p-3 sm:p-4 border-t border-gray-700">
          <div className="flex items-center mb-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary flex items-center justify-center text-white font-semibold text-sm sm:text-base flex-shrink-0">
              {user?.username[0].toUpperCase()}
            </div>
            <div className="ml-3 flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.username}</p>
              <p className="text-xs text-gray-400 truncate">{user?.roles?.join(', ')}</p>
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center justify-center px-3 sm:px-4 py-2 bg-surface-light hover:bg-error text-gray-300 hover:text-white rounded-md transition-colors duration-200">
            <LogOut className="w-4 h-4 mr-2 flex-shrink-0" />
            <span className="text-sm font-medium">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 sm:h-16 bg-surface border-b border-gray-700 flex items-center px-3 sm:px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-white hover:bg-surface-light mr-2 sm:mr-4 flex-shrink-0"
          >
            {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>

          <div className="flex-1 flex items-center justify-between min-w-0">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400 hidden sm:inline">Environment:</span>
              <span className={`font-medium ${environment === 'Production' ? 'text-primary' : 'text-warning'}`}>
                {environment}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse flex-shrink-0" />
              <span className="text-xs sm:text-sm text-gray-400 hidden sm:inline">All Systems Operational</span>
              <span className="text-xs text-gray-400 sm:hidden">OK</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-3 sm:p-4 md:p-6 lg:p-8">
          <Outlet />

          <footer className="mt-12 sm:mt-16 pt-6 sm:pt-8 border-t border-gray-700 text-center text-xs sm:text-sm text-gray-400">
            <p>Rhinometric Console v2.6.0</p>
            <p className="mt-1 text-xs">&copy; {new Date().getFullYear()} Rhinometric. Enterprise Observability Platform.</p>
          </footer>
        </main>
      </div>
    </div>
  )
}
