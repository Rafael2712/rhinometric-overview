import { Settings as SettingsIcon, Palette, Bell, Globe, Shield, Database, Zap, Link2, FileText, Bot, CheckCircle2, AlertCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function SettingsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Settings'
  }, [])
  const navigate = useNavigate()
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Fetch current settings
  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['settings', token],
    queryFn: async () => {
      const response = await fetch('/api/settings', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Failed to fetch settings')
      return response.json()
    },
    enabled: !!token
  })

  // Update AI alerts mutation
  const updateAIAlertsMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await fetch('/api/settings/ai-alerts', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          enabled,
          description: "Enable or disable AI anomaly alerting to Slack/Alertmanager"
        })
      })
      if (!response.ok) throw new Error('Failed to update settings')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  })

  const aiAlertsEnabled = settingsData?.ai_alerts?.enabled || false

  const handleAIAlertsToggle = (enabled: boolean) => {
    updateAIAlertsMutation.mutate(enabled)
  }
  
  const plannedFeatures = [
    {
      icon: Palette,
      title: 'Theme & Appearance',
      description: 'Customize color scheme, dark/light mode, and layout preferences',
      phase: 'Phase 2'
    },
    {
      icon: Bell,
      title: 'Notification Channels',
      description: 'Configure email, Slack, PagerDuty, and webhook integrations',
      phase: 'Phase 2'
    },
    {
      icon: Globe,
      title: 'Language & Timezone',
      description: 'Set regional preferences and date/time formats',
      phase: 'Phase 2'
    },
    {
      icon: Shield,
      title: 'Security & Access',
      description: 'Manage API keys, SSO configuration, and user permissions',
      phase: 'Phase 3'
    },
    {
      icon: Database,
      title: 'Data Retention',
      description: 'Configure metrics retention policies and backup schedules',
      phase: 'Phase 3'
    },
    {
      icon: Zap,
      title: 'Automation Rules',
      description: 'Set up auto-remediation and custom alert routing',
      phase: 'Phase 3'
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Configure your Rhinometric Console preferences</p>
      </div>

      {/* Save Success Message */}
      {saveSuccess && (
        <div className="card bg-success/10 border-success/30 flex items-center gap-3">
          <CheckCircle2 className="text-success" size={20} />
          <span className="text-success font-medium">Settings saved successfully!</span>
        </div>
      )}

      {/* AI Alerts Configuration */}
      <div className="card">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Bot className="text-primary" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-1">AI Anomaly Alerting</h3>
            <p className="text-sm text-text-muted">
              Control whether AI-detected anomalies generate Slack notifications and Alertmanager alerts.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-surface-light rounded-lg">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-white font-medium">Enable AI Alerting</span>
              {isLoading && <span className="text-xs text-text-muted">(Loading...)</span>}
            </div>
            <p className="text-xs text-text-muted">
              When enabled, high-severity anomalies will trigger notifications. 
              When disabled, anomalies are only visible in the AI Anomalies page.
            </p>
          </div>
          
          <button
            onClick={() => handleAIAlertsToggle(!aiAlertsEnabled)}
            disabled={isLoading || updateAIAlertsMutation.isPending}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
              aiAlertsEnabled ? 'bg-success' : 'bg-gray-600'
            } ${(isLoading || updateAIAlertsMutation.isPending) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                aiAlertsEnabled ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {!aiAlertsEnabled && (
          <div className="mt-4 p-3 bg-warning/10 border border-warning/30 rounded-lg flex items-start gap-2">
            <AlertCircle className="text-warning flex-shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-warning">
              <strong>Alerting Disabled:</strong> AI anomalies will not generate Slack or Alertmanager notifications. 
              Anomalies are still being detected and visible in the dashboard.
            </p>
          </div>
        )}
      </div>

      {/* Status Notice */}
      <div className="card bg-secondary/10 border-secondary/30">
        <div className="flex items-start gap-4">
          <SettingsIcon className="text-secondary mt-1" size={24} />
          <div className="flex-1">
            <h3 className="text-secondary font-semibold mb-2">Additional Settings: In Development</h3>
            <p className="text-gray-300 text-sm">
              Advanced configuration options will be implemented in Phase 2 & 3. 
              Below is a preview of the planned features to give you visibility into the product roadmap.
            </p>
          </div>
        </div>
      </div>

      {/* Planned Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plannedFeatures.map((feature) => {
          const Icon = feature.icon
          return (
            <div 
              key={feature.title}
              className="card hover:border-primary/50 transition-all cursor-not-allowed opacity-70"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 bg-surface-light rounded-lg">
                  <Icon className="text-primary" size={24} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
                    <span className="text-xs px-2 py-1 bg-secondary/20 text-secondary rounded-full">
                      {feature.phase}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">{feature.description}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Roadmap Info */}
      <div className="card bg-blue-500/10 border-blue-500/30">
        <h3 className="text-blue-300 font-semibold mb-3">Development Roadmap</h3>
        <div className="space-y-2 text-sm text-blue-200/80">
          <p><strong>Phase 2 (Weeks 2-6):</strong> Theme customization, notification integrations, regional settings</p>
          <p><strong>Phase 3 (Future):</strong> Advanced security features, data retention policies, automation engine</p>
          <p className="mt-4 text-xs text-blue-300">
            Have feature requests? Contact us at 
            <a href="mailto:support@rhinometric.com" className="text-primary hover:underline ml-1">
              support@rhinometric.com
            </a>
          </p>
        </div>
      </div>

      {/* Coming Soon Modules */}
      <div className="card bg-warning/10 border-warning/30">
        <h3 className="text-warning font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Coming Soon in v1.2
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => navigate('/integrations')}
            className="text-left p-4 bg-surface-light rounded-lg hover:bg-surface-lighter transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-all">
                <Link2 className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-white mb-1 group-hover:text-primary transition-colors">
                  Integrations
                </h4>
                <p className="text-xs text-text-muted">
                  REST APIs, Webhooks, MQTT, Databases, Cloud Providers
                </p>
              </div>
            </div>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="text-left p-4 bg-surface-light rounded-lg hover:bg-surface-lighter transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-all">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-white mb-1 group-hover:text-primary transition-colors">
                  Reports
                </h4>
                <p className="text-xs text-text-muted">
                  Executive & Technical PDF reports, Scheduled exports
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}
