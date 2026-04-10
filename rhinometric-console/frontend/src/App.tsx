import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { LoginPage } from './pages/Login'
import { ChangePasswordPage } from './pages/ChangePassword'
import { ResetPasswordPage } from './pages/ResetPassword'
import { Layout } from './components/Layout'
import { HomePage } from './pages/Home'
import { DashboardsPage } from './pages/Dashboards'
import { DashboardViewer } from './pages/DashboardViewer'
import { CorrelationView } from './pages/CorrelationView'
import { AlertsPage } from './pages/Alerts'
import { AlertHistoryPage } from './pages/AlertHistory'
import { IncidentsPage } from './pages/Incidents'
import { SLOPage } from './pages/SLO'
import { AlertRulesPage } from './pages/AlertRules'
import { LogsPage } from './pages/Logs'
import { TracesPage } from './pages/Traces'
import { TraceDetailPage } from './pages/TraceDetail'
import { LicensePage } from './pages/License'
import { SettingsPage } from './pages/Settings'
import { IntegrationsPage } from './pages/Integrations'
import { ReportsPage } from './pages/Reports'
import { UsersPage } from './pages/Users'
import ServicesPage from './pages/Services'
import { ServiceMapPage } from './pages/ServiceMap'
import { SystemHealthPage } from './pages/SystemHealth'
import { RoadmapPage } from './pages/Roadmap'
import { BackupRecoveryPage } from './pages/BackupRecovery'
import { TraceAnalyticsPage } from './pages/TraceAnalytics'
import { AiAnomaliesV2Page } from './pages/AiAnomaliesV2'
import { useAuthStore, useHasHydrated } from './lib/auth/store'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuthStore()
  return isAdmin() ? <>{children}</> : <Navigate to="/" replace />
}

function App() {
  const hasHydrated = useHasHydrated()
  const { initOidc } = useAuthStore()
  const [oidcReady, setOidcReady] = useState(false)

  // Block all rendering until Zustand persist has restored auth state
  // and OIDC initialization is complete
  useEffect(() => {
    if (hasHydrated && !oidcReady) {
      initOidc().finally(() => setOidcReady(true))
    }
  }, [hasHydrated])

  if (!hasHydrated || !oidcReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-gray-400 text-sm">Loading session…</div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/change-password" element={<ProtectedRoute><ChangePasswordPage /></ProtectedRoute>} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<HomePage />} />
          <Route path="dashboards" element={<DashboardsPage />} />
          <Route path="dashboards/:uid/view" element={<DashboardViewer />} />
          <Route path="services" element={<ServicesPage />} />
          <Route path="service-map" element={<ServiceMapPage />} />
          <Route path="system-health" element={<SystemHealthPage />} />
          <Route path="correlations/:id" element={<CorrelationView />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="alert-history" element={<AlertHistoryPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="slo" element={<SLOPage />} />
          <Route path="alert-rules" element={<AlertRulesPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="traces" element={<TracesPage />} />
          <Route path="traces/:traceId" element={<TraceDetailPage />} />
          <Route path="trace-analytics" element={<TraceAnalyticsPage />} />
          <Route path="ai-anomalies-v2" element={<AiAnomaliesV2Page />} />
          <Route path="license" element={<LicensePage />} />
          <Route path="backup-recovery" element={<BackupRecoveryPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<AdminRoute><SettingsPage /></AdminRoute>} />
          <Route path="roadmap" element={<RoadmapPage />} />
          <Route path="integrations" element={<IntegrationsPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
