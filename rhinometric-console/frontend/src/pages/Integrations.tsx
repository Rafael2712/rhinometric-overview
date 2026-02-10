import { useEffect } from 'react'
import { Link2, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export function IntegrationsPage() {
  useEffect(() => {
    document.title = 'Integrations - Coming Soon - Rhinometric'
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
          <h1 className="text-3xl font-bold text-white">Integrations</h1>
          <p className="text-text-muted mt-2">Connect your data sources and services</p>
        </div>
      </div>

      {/* Coming Soon Card */}
      <div className="card max-w-3xl mx-auto text-center py-12">
        <div className="bg-primary/10 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
          <Link2 className="w-10 h-10 text-primary" />
        </div>

        <span className="inline-block px-4 py-1.5 bg-warning/10 text-warning rounded-full text-sm font-medium mb-4">
          Coming in v1.2
        </span>

        <h2 className="text-2xl font-bold text-white mb-4">
          Integrations Module Under Development
        </h2>

        <p className="text-text-muted max-w-xl mx-auto mb-8">
          We're building a comprehensive integrations platform to connect all your data sources seamlessly.
          Stay tuned for the next release!
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">REST APIs</h3>
            <p className="text-sm text-text-muted">
              Configure custom REST API endpoints with authentication, headers, and polling intervals
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Webhooks</h3>
            <p className="text-sm text-text-muted">
              Receive real-time events from GitHub, GitLab, Stripe, and custom webhook sources
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">MQTT Brokers</h3>
            <p className="text-sm text-text-muted">
              Connect to MQTT brokers for IoT device monitoring and real-time telemetry
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Databases</h3>
            <p className="text-sm text-text-muted">
              Monitor PostgreSQL, MySQL, MongoDB, and other databases with custom queries
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Cloud Providers</h3>
            <p className="text-sm text-text-muted">
              AWS, Azure, GCP metrics collection and monitoring integration
            </p>
          </div>

          <div className="bg-surface-light rounded-lg p-4">
            <h3 className="font-semibold text-white mb-2">Custom Collectors</h3>
            <p className="text-sm text-text-muted">
              Build and deploy your own data collectors with our SDK
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-surface-light">
          <p className="text-sm text-text-muted">
            Want early access or have integration requests?{' '}
            <a href="mailto:support@rhinometric.com" className="text-primary hover:underline">
              Contact our team
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
