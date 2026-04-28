import { Bot, CheckCircle2, AlertCircle, MessageSquare, Mail, Send, Save, Eye, EyeOff, Loader2, Hash, Server } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useAuthStore } from '../lib/auth/store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function SettingsPage() {
  useEffect(() => { document.title = 'Rhinometric - Settings' }, [])
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()

  const [saveSuccess, setSaveSuccess] = useState(false)
  const [channelsSaveSuccess, setChannelsSaveSuccess] = useState(false)
  const [slackTestResult, setSlackTestResult] = useState<{status: string, message: string} | null>(null)
  const [emailTestResult, setEmailTestResult] = useState<{status: string, message: string} | null>(null)
  const [showSmtpPassword, setShowSmtpPassword] = useState(false)

  // --- Notification channels form state ---
  const [slackEnabled, setSlackEnabled] = useState(false)
  const [slackWebhook, setSlackWebhook] = useState('')
  const [slackChannel, setSlackChannel] = useState('#rhinometric-alerts')
  const [emailEnabled, setEmailEnabled] = useState(false)
  const [smtpHost, setSmtpHost] = useState('smtp.zoho.eu')
  const [smtpPort, setSmtpPort] = useState('587')
  const [smtpUsername, setSmtpUsername] = useState('')
  const [smtpPassword, setSmtpPassword] = useState('')
  const [smtpTls, setSmtpTls] = useState(true)
  const [fromEmail, setFromEmail] = useState('')
  const [toEmails, setToEmails] = useState('')

  // ---- Fetch AI alerts settings ----
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

  // ---- Fetch notification channels ----
  const { data: channelsData, isLoading: channelsLoading } = useQuery({
    queryKey: ['notification-channels', token],
    queryFn: async () => {
      const response = await fetch('/api/settings/notification-channels', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Failed to fetch channels')
      return response.json()
    },
    enabled: !!token
  })

  // Populate form when channels loaded
  useEffect(() => {
    if (channelsData) {
      const s = channelsData.slack || {}
      const e = channelsData.email || {}
      setSlackEnabled(s.enabled || false)
      setSlackWebhook(s.webhook_url || '')
      setSlackChannel(s.channel || '#rhinometric-alerts')
      setEmailEnabled(e.enabled || false)
      setSmtpHost(e.smtp_host || 'smtp.zoho.eu')
      setSmtpPort(String(e.smtp_port || 587))
      setSmtpUsername(e.smtp_username || '')
      setSmtpPassword(e.smtp_password || '')
      setSmtpTls(e.smtp_require_tls !== false)
      setFromEmail(e.from_email || '')
      setToEmails((e.to_emails || []).join(', '))
    }
  }, [channelsData])

  // ---- AI Alerts toggle mutation ----
  const updateAIAlertsMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await fetch('/api/settings/ai-alerts', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ enabled, description: "Toggle AI alerting" })
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

  // ---- Save channels mutation ----
  const saveChannelsMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        slack: {
          enabled: slackEnabled,
          webhook_url: slackWebhook,
          channel: slackChannel,
        },
        email: {
          enabled: emailEnabled,
          smtp_host: smtpHost,
          smtp_port: parseInt(smtpPort) || 587,
          smtp_username: smtpUsername,
          smtp_password: smtpPassword,
          smtp_require_tls: smtpTls,
          from_email: fromEmail,
          to_emails: toEmails.split(',').map(e => e.trim()).filter(Boolean),
        }
      }
      const response = await fetch('/api/settings/notification-channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      })
      if (!response.ok) throw new Error('Failed to save channels')
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] })
      setChannelsSaveSuccess(true)
      setTimeout(() => setChannelsSaveSuccess(false), 4000)
    }
  })

  // ---- Test Slack mutation (auto-saves first) ----
  const testSlackMutation = useMutation({
    mutationFn: async () => {
      // Auto-save current form values before testing
      const payload = {
        slack: { enabled: slackEnabled, webhook_url: slackWebhook, channel: slackChannel },
        email: { enabled: emailEnabled, smtp_host: smtpHost, smtp_port: parseInt(smtpPort) || 587, smtp_username: smtpUsername, smtp_password: smtpPassword, smtp_require_tls: smtpTls, from_email: fromEmail, to_emails: toEmails.split(',').map(e => e.trim()).filter(Boolean) }
      }
      const saveResp = await fetch('/api/settings/notification-channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      })
      if (!saveResp.ok) throw new Error('Failed to save channels before test')
      // Now run the actual test
      const response = await fetch('/api/settings/notification-channels/test/slack', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] })
      setSlackTestResult(data); setTimeout(() => setSlackTestResult(null), 5000)
    },
    onError: (e: any) => { setSlackTestResult({ status: 'error', message: e.message }); setTimeout(() => setSlackTestResult(null), 5000) }
  })

  // ---- Test Email mutation (auto-saves first) ----
  const testEmailMutation = useMutation({
    mutationFn: async () => {
      // Auto-save current form values before testing
      const payload = {
        slack: { enabled: slackEnabled, webhook_url: slackWebhook, channel: slackChannel },
        email: { enabled: emailEnabled, smtp_host: smtpHost, smtp_port: parseInt(smtpPort) || 587, smtp_username: smtpUsername, smtp_password: smtpPassword, smtp_require_tls: smtpTls, from_email: fromEmail, to_emails: toEmails.split(',').map(e => e.trim()).filter(Boolean) }
      }
      const saveResp = await fetch('/api/settings/notification-channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload)
      })
      if (!saveResp.ok) throw new Error('Failed to save channels before test')
      // Now run the actual test
      const response = await fetch('/api/settings/notification-channels/test/email', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] })
      setEmailTestResult(data); setTimeout(() => setEmailTestResult(null), 5000)
    },
    onError: (e: any) => { setEmailTestResult({ status: 'error', message: e.message }); setTimeout(() => setEmailTestResult(null), 5000) }
  })

  const aiAlertsEnabled = settingsData?.ai_alerts?.enabled || false
  const slackStatus = channelsData?.slack_status || 'not_configured'
  const emailStatus = channelsData?.email_status || 'not_configured'

  const inputClass = "w-full bg-surface-dark border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent placeholder-gray-500"
  const labelClass = "block text-sm font-medium text-gray-300 mb-1"

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Configure your Rhinometric Console preferences and notification channels</p>
      </div>

      {/* Save Success Messages */}
      {saveSuccess && (
        <div className="card bg-success/10 border-success/30 flex items-center gap-3">
          <CheckCircle2 className="text-success" size={20} />
          <span className="text-success font-medium">AI alerting setting saved!</span>
        </div>
      )}
      {channelsSaveSuccess && (
        <div className="card bg-success/10 border-success/30 flex items-center gap-3">
          <CheckCircle2 className="text-success" size={20} />
          <span className="text-success font-medium">Notification channels saved & Alertmanager reloaded!</span>
        </div>
      )}
      {(updateAIAlertsMutation.isError || saveChannelsMutation.isError) && (
        <div className="card bg-error/10 border-error/30 flex items-center gap-3">
          <AlertCircle className="text-error" size={20} />
          <span className="text-error font-medium">Failed to update setting. Please try again.</span>
        </div>
      )}

      {/* ================================================================ */}
      {/* Section 1: AI Alerting Toggle */}
      {/* ================================================================ */}
      <div className="card">
        <div className="flex items-start gap-4 mb-4">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Bot className="text-primary" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-1">AI Anomaly Alerting</h3>
            <p className="text-sm text-text-muted">
              Control whether AI-detected anomalies generate Slack and email notifications.
              <br /><span className="text-xs">Prometheus generic alerts are <strong>not</strong> affected by this toggle.</span>
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
            onClick={() => updateAIAlertsMutation.mutate(!aiAlertsEnabled)}
            disabled={isLoading || updateAIAlertsMutation.isPending}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
              aiAlertsEnabled ? 'bg-success' : 'bg-gray-600'
            } ${(isLoading || updateAIAlertsMutation.isPending) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
              aiAlertsEnabled ? 'translate-x-7' : 'translate-x-1'
            }`} />
          </button>
        </div>

        {!aiAlertsEnabled && (
          <div className="mt-4 p-3 bg-warning/10 border border-warning/30 rounded-lg flex items-start gap-2">
            <AlertCircle className="text-warning flex-shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-warning">
              <strong>Alerting Disabled:</strong> AI anomalies are still detected and visible, but no Slack or email notifications will be sent.
            </p>
          </div>
        )}
        {aiAlertsEnabled && (
          <div className="mt-4 p-3 bg-success/10 border border-success/30 rounded-lg flex items-start gap-2">
            <CheckCircle2 className="text-success flex-shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-success">
              <strong>Alerting Enabled:</strong> Critical AI anomalies will send Slack and email notifications.
            </p>
          </div>
        )}
      </div>

      {/* ================================================================ */}
      {/* Section 2: Notification Channels */}
      {/* ================================================================ */}
      <div className="card">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-blue-500/10 rounded-lg">
            <Send className="text-blue-400" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white mb-1">Notification Channels</h3>
            <p className="text-sm text-text-muted">
              Configure where alert notifications are delivered. Changes apply to both AI anomalies and standard Prometheus alerts.
            </p>
          </div>
          {channelsLoading && <Loader2 className="animate-spin text-gray-500" size={20} />}
        </div>

        {/* ---- SLACK ---- */}
        <div className="mb-8 p-5 bg-surface-light rounded-lg border border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <MessageSquare className="text-purple-400" size={20} />
              <h4 className="text-white font-semibold">Slack</h4>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                slackStatus === 'configured' ? 'bg-success/20 text-success' : 'bg-gray-600/40 text-gray-400'
              }`}>
                {slackStatus === 'configured' ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <button
              onClick={() => setSlackEnabled(!slackEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                slackEnabled ? 'bg-purple-500' : 'bg-gray-600'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                slackEnabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>

          {slackEnabled && (
            <div className="space-y-3">
              <div>
                <label className={labelClass}>Webhook URL <span className="text-red-400">*</span></label>
                <input
                  type="text"
                  value={slackWebhook}
                  onChange={e => setSlackWebhook(e.target.value)}
                  placeholder="https://hooks.slack.com/services/T.../B.../..."
                  className={inputClass}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Create a webhook at <a href="https://api.slack.com/messaging/webhooks" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">api.slack.com/messaging/webhooks</a>
                </p>
              </div>
              <div>
                <label className={labelClass}>Channel</label>
                <div className="relative">
                  <Hash className="absolute left-3 top-2.5 text-gray-500" size={14} />
                  <input
                    type="text"
                    value={slackChannel.replace('#', '')}
                    onChange={e => setSlackChannel('#' + e.target.value.replace('#', ''))}
                    placeholder="rhinometric-alerts"
                    className={`${inputClass} pl-8`}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">Leave default if your webhook is configured for a specific channel.</p>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => testSlackMutation.mutate()}
                  disabled={testSlackMutation.isPending || !slackWebhook}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                >
                  {testSlackMutation.isPending ? <Loader2 className="animate-spin" size={14} /> : <Send size={14} />}
                  Send Test Message
                </button>
              </div>

              {slackTestResult && (
                <div className={`p-2 rounded-lg text-xs flex items-center gap-2 ${
                  slackTestResult.status === 'ok' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                }`}>
                  {slackTestResult.status === 'ok' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                  {slackTestResult.message}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ---- EMAIL (SMTP) ---- */}
        <div className="mb-6 p-5 bg-surface-light rounded-lg border border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Mail className="text-cyan-400" size={20} />
              <h4 className="text-white font-semibold">Email (SMTP)</h4>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                emailStatus === 'configured' ? 'bg-success/20 text-success' : 'bg-gray-600/40 text-gray-400'
              }`}>
                {emailStatus === 'configured' ? 'Configured' : 'Not Configured'}
              </span>
            </div>
            <button
              onClick={() => setEmailEnabled(!emailEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                emailEnabled ? 'bg-cyan-500' : 'bg-gray-600'
              }`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                emailEnabled ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>

          {emailEnabled && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>SMTP Host <span className="text-red-400">*</span></label>
                  <div className="relative">
                    <Server className="absolute left-3 top-2.5 text-gray-500" size={14} />
                    <input type="text" value={smtpHost} onChange={e => setSmtpHost(e.target.value)} placeholder="smtp.zoho.eu" className={`${inputClass} pl-8`} />
                  </div>
                </div>
                <div>
                  <label className={labelClass}>Port</label>
                  <input type="number" value={smtpPort} onChange={e => setSmtpPort(e.target.value)} placeholder="587" className={inputClass} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>Username <span className="text-red-400">*</span></label>
                  <input type="text" value={smtpUsername} onChange={e => setSmtpUsername(e.target.value)} placeholder="user@company.com" className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Password <span className="text-red-400">*</span></label>
                  <div className="relative">
                    <input
                      type={showSmtpPassword ? 'text' : 'password'}
                      value={smtpPassword}
                      onChange={e => setSmtpPassword(e.target.value)}
                      placeholder="••••••••"
                      className={`${inputClass} pr-10`}
                    />
                    <button onClick={() => setShowSmtpPassword(!showSmtpPassword)} className="absolute right-3 top-2.5 text-gray-500 hover:text-gray-300">
                      {showSmtpPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className={labelClass}>From Email</label>
                <input type="email" value={fromEmail} onChange={e => setFromEmail(e.target.value)} placeholder="alerts@company.com" className={inputClass} />
                <p className="text-xs text-gray-500 mt-1">Defaults to SMTP username if empty.</p>
              </div>
              <div>
                <label className={labelClass}>To Email(s) <span className="text-red-400">*</span></label>
                <input type="text" value={toEmails} onChange={e => setToEmails(e.target.value)} placeholder="admin@company.com, team@company.com" className={inputClass} />
                <p className="text-xs text-gray-500 mt-1">Comma-separated list of recipient email addresses.</p>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={smtpTls} onChange={e => setSmtpTls(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary bg-surface-dark" />
                  <span className="text-sm text-gray-300">Require STARTTLS</span>
                </label>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => testEmailMutation.mutate()}
                  disabled={testEmailMutation.isPending || !smtpUsername || !toEmails}
                  className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                >
                  {testEmailMutation.isPending ? <Loader2 className="animate-spin" size={14} /> : <Mail size={14} />}
                  Send Test Email
                </button>
              </div>

              {emailTestResult && (
                <div className={`p-2 rounded-lg text-xs flex items-center gap-2 ${
                  emailTestResult.status === 'ok' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                }`}>
                  {emailTestResult.status === 'ok' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                  {emailTestResult.message}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Save Channels Button */}
        <div className="flex justify-end">
          <button
            onClick={() => saveChannelsMutation.mutate()}
            disabled={saveChannelsMutation.isPending}
            className="flex items-center gap-2 px-6 py-2.5 bg-primary hover:bg-primary/90 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {saveChannelsMutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
            Save Notification Channels
          </button>
        </div>
      </div>
    </div>
  )
}
