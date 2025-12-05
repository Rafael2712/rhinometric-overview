import { Settings as SettingsIcon, Palette, Bell, Globe, Shield, Database, Zap } from 'lucide-react'
import { useEffect } from 'react'

export function SettingsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Settings'
  }, [])
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

      {/* Status Notice */}
      <div className="card bg-secondary/10 border-secondary/30">
        <div className="flex items-start gap-4">
          <SettingsIcon className="text-secondary mt-1" size={24} />
          <div className="flex-1">
            <h3 className="text-secondary font-semibold mb-2">Settings Module: In Development</h3>
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
    </div>
  )
}
