import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage } from './pages/Login'
import { ChangePasswordPage } from './pages/ChangePassword'
import { ResetPasswordPage } from './pages/ResetPassword'
import { Layout } from './components/Layout'
import { HomePage } from './pages/Home'
import { DashboardsPage } from './pages/Dashboards'
import { DashboardViewer } from './pages/DashboardViewer'
import { AnomaliesPage } from './pages/Anomalies'
import { CorrelationView } from './pages/CorrelationView'
import { AlertsPage } from './pages/Alerts'
import { AlertHistoryPage } from './pages/AlertHistory'
import { IncidentsPage } from './pages/Incidents'
import { LogsPage } from './pages/Logs'
import { TracesPage } from './pages/Traces'
import { LicensePage } from './pages/License'
import { SettingsPage } from './pages/Settings'
import { IntegrationsPage } from './pages/Integrations'
import { ReportsPage } from './pages/Reports'
import { UsersPage } from './pages/Users'
import ServicesPage from './pages/Services'
import { SystemHealthPage } from './pages/SystemHealth'
import { RoadmapPage } from './pages/Roadmap'
import { AIInsightsPage } from './pages/AIInsights'
import { useAuthStore } from './lib/auth/store'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuthStore()
  return isAdmin() ? <>{children}</> : <Navigate to="/" replace />
}

function App() {
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
          <Route path="system-health" element={<SystemHealthPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="ai-insights" element={<AIInsightsPage />} />
          <Route path="correlations/:id" element={<CorrelationView />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="alert-history" element={<AlertHistoryPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="traces" element={<TracesPage />} />
          <Route path="license" element={<LicensePage />} />
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
