import { Bot, CheckCircle2, AlertCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useAuthStore } from '../lib/auth/store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function SettingsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Settings'
  }, [])
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


      {/* Error Message */}
      {updateAIAlertsMutation.isError && (
        <div className="card bg-error/10 border-error/30 flex items-center gap-3">
          <AlertCircle className="text-error" size={20} />
          <span className="text-error font-medium">Failed to update setting. Please try again.</span>
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
              Control whether AI-detected anomalies generate Slack and email notifications.
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
              <strong>Alerting Disabled:</strong> AI anomalies are still detected and visible in Rhinometric, but no Slack or email notifications will be sent. 
            </p>
          </div>
        )}

        {aiAlertsEnabled && (
          <div className="mt-4 p-3 bg-success/10 border border-success/30 rounded-lg flex items-start gap-2">
            <CheckCircle2 className="text-success flex-shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-success">
              <strong>Alerting Enabled:</strong> Critical AI anomalies will send Slack and email notifications.
              Lower severities remain visible only in the console.
            </p>
          </div>
        )}
      </div>


    </div>
  )
}
