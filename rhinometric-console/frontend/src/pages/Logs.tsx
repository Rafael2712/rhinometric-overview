import { FileText, Search, Download, RefreshCw, Filter, Clock } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import { openGrafanaExplore } from '../utils/grafana'

interface LogEntry {
  timestamp: string
  level: string
  message: string
  labels: Record<string, string>
  stream: Record<string, string>
}

export function LogsPage() {
  useEffect(() => {
    document.title = 'Rhinometric - Logs'
  }, [])

  const token = useAuthStore((state) => state.token)
  const [searchQuery, setSearchQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [timeRange, setTimeRange] = useState<string>('15m')  // Changed from 1h to 15min for performance
  const [autoRefresh, setAutoRefresh] = useState(false)

  const { data: logsData, isLoading, error, refetch } = useQuery({
    queryKey: ['logs', token, searchQuery, levelFilter, timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token available')
      
      // Build LogQL query - optimized for speed
      let logql = '{job=~".+"}'
      if (levelFilter !== 'all') {
        logql = `{job=~".+"} |= "${levelFilter}"`  // Use exact match for speed
      }
      if (searchQuery) {
        logql += ` |= "${searchQuery}"`  // Use exact match instead of regex
      }

      const params = new URLSearchParams({
        query: logql,
        limit: '50',  // Reduced limit for faster response
        start: `${Date.now() - parseTimeRange(timeRange)}000000`, // nanoseconds
        end: `${Date.now()}000000`,
        direction: 'backward'
      })

      const response = await fetch(`/api/logs?${params}`)
      
      if (!response.ok) throw new Error('Failed to fetch logs')
      return response.json()
    },
    enabled: true, // Temporarily changed from !!token
    refetchInterval: autoRefresh ? 5000 : false,
    refetchOnMount: true,
    staleTime: 0,
  })

  const parseTimeRange = (range: string): number => {
    const value = parseInt(range.slice(0, -1))
    const unit = range.slice(-1)
    const multipliers: Record<string, number> = { 'h': 3600000, 'm': 60000, 'd': 86400000 }
    return value * (multipliers[unit] || 3600000)
  }

  const logs: LogEntry[] = logsData?.data?.result?.flatMap((stream: any) => 
    stream.values?.map(([timestamp, message]: [string, string]) => ({
      timestamp: new Date(parseInt(timestamp) / 1000000).toISOString(),
      message,
      level: detectLogLevel(message),
      labels: stream.stream || {},
      stream: stream.stream || {}
    })) || []
  ) || []

  function detectLogLevel(message: string): string {
    const msg = message.toLowerCase()
    if (msg.includes('error') || msg.includes('fatal')) return 'error'
    if (msg.includes('warn')) return 'warning'
    if (msg.includes('info')) return 'info'
    if (msg.includes('debug')) return 'debug'
    return 'info'
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-error bg-error/10 border-error/30'
      case 'warning': return 'text-warning bg-warning/10 border-warning/30'
      case 'info': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'debug': return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
      default: return 'text-gray-300 bg-gray-500/10 border-gray-500/30'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Log Explorer</h1>
          <p className="text-text-muted">Query and analyze logs from Loki</p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn btn-secondary flex items-center gap-2 ${autoRefresh ? 'bg-primary/20 text-primary' : ''}`}
          >
            <RefreshCw size={16} className={autoRefresh ? 'animate-spin' : ''} />
            Auto-refresh
          </button>
          <button 
            onClick={() => {
              const dataStr = JSON.stringify(logs, null, 2)
              const dataBlob = new Blob([dataStr], { type: 'application/json' })
              const url = URL.createObjectURL(dataBlob)
              const link = document.createElement('a')
              link.href = url
              link.download = `logs-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`
              link.click()
              URL.revokeObjectURL(url)
            }}
            disabled={logs.length === 0}
            className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card space-y-4">
        {/* Search Bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search logs... (press Enter to search)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && refetch()}
              className="w-full bg-surface-light border border-gray-700 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-primary"
            />
          </div>
          <button 
            onClick={() => refetch()}
            className="btn flex items-center gap-2"
          >
            <Search size={16} />
            Search
          </button>
          <button
            onClick={() => {
              // Build LogQL query
              let logql = '{job=~".+"}'
              if (levelFilter !== 'all') {
                logql = `{job=~".+"} |= "${levelFilter}"`
              }
              if (searchQuery) {
                logql += ` |= "${searchQuery}"`
              }

              // Open Grafana Explore directly (v2.5.1 - direct links strategy)
              const exploreUrl = `?orgId=1&left=${encodeURIComponent(JSON.stringify({
                datasource: 'loki',
                queries: [{ refId: 'A', expr: logql }],
                range: { from: `now-${timeRange}`, to: 'now' }
              }))}`
              openGrafanaExplore(exploreUrl)
            }}
            className="btn btn-secondary flex items-center gap-2"
          >
            <Download size={16} />
            View in Grafana
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <span className="text-sm text-gray-400">Level:</span>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400" />
            <span className="text-sm text-gray-400">Time:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-surface-light border border-gray-700 text-white rounded px-3 py-1.5 text-sm"
            >
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="30m">Last 30 minutes</option>
              <option value="1h">Last 1 hour</option>
            </select>
          </div>

          <div className="text-sm text-gray-400">
            {logs.length} log entries (max 50)
          </div>
        </div>
      </div>

      {/* Logs Display */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-gray-400 mt-4">Loading logs...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <FileText className="text-error mx-auto mb-4" size={48} />
            <p className="text-error">Failed to load logs</p>
            <p className="text-sm text-gray-400 mt-2">{(error as Error).message}</p>
            <button onClick={() => refetch()} className="btn btn-secondary mt-4">
              Retry
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="text-gray-400 mx-auto mb-4" size={48} />
            <p className="text-white text-lg font-semibold">No Logs Found</p>
            <p className="text-gray-400 mt-2">Try adjusting your search filters or time range</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {logs.map((log, index) => (
              <div 
                key={index}
                className="flex items-start gap-3 p-3 hover:bg-surface-light rounded-lg transition-colors border-l-2 border-transparent hover:border-primary"
              >
                {/* Timestamp */}
                <div className="text-xs text-gray-500 font-mono whitespace-nowrap pt-1">
                  {new Date(log.timestamp).toLocaleTimeString('en-US', { 
                    hour12: false, 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                  })}
                </div>

                {/* Level Badge */}
                <div className={`text-xs font-medium px-2 py-0.5 rounded border whitespace-nowrap ${getLevelColor(log.level)}`}>
                  {log.level.toUpperCase()}
                </div>

                {/* Labels */}
                {log.stream.job && (
                  <code className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded whitespace-nowrap">
                    {log.stream.job}
                  </code>
                )}

                {/* Message */}
                <div className="flex-1 text-sm text-gray-300 font-mono break-all">
                  {log.message}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Banner */}
      <div className="card bg-primary/5 border-primary/20">
        <div className="flex items-start gap-3">
          <FileText className="text-primary mt-1" size={20} />
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">LogQL Queries</h3>
            <p className="text-xs text-gray-400">
              Use LogQL syntax for advanced queries. Examples: <code className="text-primary mx-1">{'{job="varlogs"}'}</code> 
              or <code className="text-primary mx-1">{'|~ "error"'}</code> for regex matching.
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Connected to Loki on port 3100 • {autoRefresh ? 'Auto-refreshing every 5s' : 'Manual refresh'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
