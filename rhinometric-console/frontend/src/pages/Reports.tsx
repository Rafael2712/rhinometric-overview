import { useEffect } from 'react'
import { FileText, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function ReportsPage() {
  useEffect(() => {
    document.title = 'Reports - Coming Soon - Rhinometric'
  }, [])

  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="btn btn-secondary"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-white">Reports</h1>
          <p className="text-text-muted mt-2">Generate executive and technical reports</p>
        </div>
      </div>

      {/* Coming Soon Card */}
      <div className="card max-w-3xl mx-auto text-center py-12">
        <div className="bg-primary/10 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
          <FileText className="w-10 h-10 text-primary" />
        </div>

        <span className="inline-block px-4 py-1.5 bg-warning/10 text-warning rounded-full text-sm font-medium mb-4">
          Coming in v1.2
        </span>

        <h2 className="text-2xl font-bold text-white mb-4">
          Advanced Reporting System In Development
        </h2>

        <p className="text-text-muted max-w-xl mx-auto mb-8">
          We're crafting a powerful reporting engine to help you communicate insights to stakeholders
          with beautiful, automated reports.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Executive Reports</h3>
            <p className="text-sm text-text-muted">
              High-level KPI summaries, trends, and insights for C-level stakeholders in PDF format
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Technical Reports</h3>
            <p className="text-sm text-text-muted">
              Detailed performance metrics, anomaly analysis, and incident reports for technical teams
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Scheduled Reports</h3>
            <p className="text-sm text-text-muted">
              Automated daily, weekly, or monthly reports delivered via email or Slack
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Custom Templates</h3>
            <p className="text-sm text-text-muted">
              Design your own report templates with drag-and-drop dashboard widgets
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Export Formats</h3>
            <p className="text-sm text-text-muted">
              PDF, Excel, CSV, and interactive HTML reports with embedded charts
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Report History</h3>
            <p className="text-sm text-text-muted">
              Archive and compare historical reports to track progress over time
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-surface-light">
          <p className="text-sm text-text-muted">
            Need specific report types?{' '}
            <a href="mailto:support@rhinometric.com" className="text-primary hover:underline">
              Share your requirements
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
