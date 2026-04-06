/* eslint-disable */
import { useState, useMemo, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
  Handle,
  Position,
} from '@xyflow/react'
import type { Node, Edge, EdgeMouseHandler } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { RefreshCw, Network, AlertTriangle, ArrowRight, Activity } from 'lucide-react'
import { buildServiceGraph } from '../utils/serviceGraph'
import type { GraphEdge } from '../utils/serviceGraph'
import type { JaegerTrace } from '../utils/traceAnalysis'

/* ── Edge color helpers ─────────────────────────────────────── */

function edgeColor(edge: GraphEdge): string {
  if (edge.errorRate > 0.1) return '#ef4444'   // red: >10% errors
  if (edge.avgLatency > 500) return '#ef4444'   // red: >500ms
  if (edge.avgLatency > 200) return '#eab308'   // yellow: >200ms
  return '#22c55e'                               // green: healthy
}

function edgeWidth(count: number, maxCount: number): number {
  if (maxCount <= 1) return 2
  return 2 + (count / maxCount) * 6  // 2..8
}

/* ── Node health color ──────────────────────────────────────── */

function nodeColor(errorCount: number, callCount: number): { bg: string; border: string; text: string } {
  const rate = callCount > 0 ? errorCount / callCount : 0
  if (rate > 0.1) return { bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-400' }
  if (rate > 0.02) return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/50', text: 'text-yellow-400' }
  return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/50', text: 'text-emerald-400' }
}

/* ── Custom Node ────────────────────────────────────────────── */

interface ServiceNodeData {
  label: string
  callCount: number
  errorCount: number
  onSelect: (id: string) => void
  [key: string]: unknown
}

function ServiceNode({ data }: { data: ServiceNodeData }) {
  const nc = nodeColor(data.errorCount, data.callCount)
  const [hovered, setHovered] = useState(false)
  const errorRate = data.callCount > 0 ? ((data.errorCount / data.callCount) * 100).toFixed(1) : '0'

  return (
    <div
      className={`relative rounded-xl border-2 ${nc.border} ${nc.bg} px-4 py-3 min-w-[150px] cursor-pointer transition-all duration-200 hover:scale-105`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => data.onSelect(data.label)}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-500 !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500 !w-2 !h-2" />

      <div className="flex items-center gap-2 mb-1">
        <Activity size={14} className={nc.text} />
        <span className="text-sm font-semibold text-gray-200 truncate max-w-[130px]">{data.label}</span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-gray-500">{data.callCount} spans</span>
        {data.errorCount > 0 && (
          <span className="text-red-400">{data.errorCount} err</span>
        )}
      </div>

      {hovered && (
        <div className="absolute z-50 left-full ml-3 top-0 bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl min-w-[170px] pointer-events-none">
          <p className="text-xs font-semibold text-gray-200 mb-1">{data.label}</p>
          <p className="text-xs text-gray-400">Spans: <span className="text-gray-200 font-mono">{data.callCount}</span></p>
          <p className="text-xs text-gray-400">Errors: <span className="text-red-400 font-mono">{data.errorCount}</span></p>
          <p className="text-xs text-gray-400">Error rate: <span className="text-gray-200 font-mono">{errorRate}%</span></p>
        </div>
      )}
    </div>
  )
}

const nodeTypes = { service: ServiceNode }

/* ── Auto-layout (topological) ──────────────────────────────── */

function autoLayout(
  graphNodes: { id: string; callCount: number; errorCount: number }[],
  graphEdges: GraphEdge[],
  onSelect: (id: string) => void
): { nodes: Node[]; edges: Edge[] } {
  // Compute depth via topological sort
  const inDegree = new Map<string, number>()
  const children = new Map<string, string[]>()
  graphNodes.forEach(n => { inDegree.set(n.id, 0); children.set(n.id, []) })
  graphEdges.forEach(e => {
    inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1)
    const ch = children.get(e.source) || []
    ch.push(e.target)
    children.set(e.source, ch)
  })

  const depth = new Map<string, number>()
  const queue: string[] = []
  graphNodes.forEach(n => {
    if ((inDegree.get(n.id) || 0) === 0) {
      queue.push(n.id)
      depth.set(n.id, 0)
    }
  })

  while (queue.length > 0) {
    const cur = queue.shift()!
    const curDepth = depth.get(cur) || 0
    for (const c of (children.get(cur) || [])) {
      const newDepth = curDepth + 1
      if (!depth.has(c) || newDepth > depth.get(c)!) {
        depth.set(c, newDepth)
      }
      const deg = (inDegree.get(c) || 1) - 1
      inDegree.set(c, deg)
      if (deg <= 0) queue.push(c)
    }
  }
  // Assign unvisited
  graphNodes.forEach(n => { if (!depth.has(n.id)) depth.set(n.id, 0) })

  // Group by level
  const levels = new Map<number, string[]>()
  depth.forEach((d, id) => {
    const list = levels.get(d) || []
    list.push(id)
    levels.set(d, list)
  })

  const nodeById = new Map(graphNodes.map(n => [n.id, n]))
  const X_GAP = 280
  const Y_GAP = 180
  const nodes: Node[] = []

  levels.forEach((ids, level) => {
    const startX = -(ids.length - 1) * X_GAP / 2
    ids.forEach((id, idx) => {
      const gn = nodeById.get(id)
      if (!gn) return
      nodes.push({
        id,
        type: 'service',
        position: { x: startX + idx * X_GAP, y: level * Y_GAP },
        data: {
          label: gn.id,
          callCount: gn.callCount,
          errorCount: gn.errorCount,
          onSelect,
        } as ServiceNodeData,
      })
    })
  })

  const maxCount = Math.max(1, ...graphEdges.map(e => e.count))

  const edges: Edge[] = graphEdges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    animated: e.errorRate > 0.05,
    style: {
      stroke: edgeColor(e),
      strokeWidth: edgeWidth(e.count, maxCount),
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: edgeColor(e),
    },
    data: { ...e },
  }))

  return { nodes, edges }
}

/* ── Edge Tooltip ───────────────────────────────────────────── */

function EdgeTooltip({ edge, position }: { edge: GraphEdge | null; position: { x: number; y: number } }) {
  if (!edge) return null
  return (
    <div
      className="fixed z-[9999] bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl pointer-events-none"
      style={{ left: position.x + 12, top: position.y - 10 }}
    >
      <p className="text-xs font-semibold text-gray-200 mb-1.5">
        {edge.source} <span className="text-gray-500">&rarr;</span> {edge.target}
      </p>
      <div className="space-y-0.5">
        <p className="text-xs text-gray-400">Calls: <span className="text-gray-200 font-mono">{edge.count}</span></p>
        <p className="text-xs text-gray-400">Avg latency: <span className="text-gray-200 font-mono">{edge.avgLatency} ms</span></p>
        <p className="text-xs text-gray-400">Error rate: <span className={`font-mono ${edge.errorRate > 0.05 ? 'text-red-400' : 'text-gray-200'}`}>{(edge.errorRate * 100).toFixed(1)}%</span></p>
      </div>
    </div>
  )
}

/* ── Main Page ──────────────────────────────────────────────── */

export function ServiceMapPage() {
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  

  // Fetch traces ONCE on load (manual refresh via refetch)
  const { data: tracesData, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['service-map-traces'],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({ limit: '100', lookback: '15m' })
      const res = await fetch(`/api/traces?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch traces')
      return res.json()
    },
    enabled: !!token,
    staleTime: Infinity,  // never auto-refetch
    refetchOnWindowFocus: false,
  })

  const traces: JaegerTrace[] = tracesData?.traces || []

  // Build graph (memoized — only recomputes when traces change)
  const graph = useMemo(() => buildServiceGraph(traces), [traces])

  // Node click → navigate to dashboard
  const handleNodeSelect = useCallback((_serviceId: string) => {
    navigate('/dashboards/ext-svc-detail/view')
  }, [navigate])

  // Layout (memoized)
  const { layoutNodes, layoutEdges } = useMemo(() => {
    if (graph.nodes.length === 0) return { layoutNodes: [], layoutEdges: [] }
    const layout = autoLayout(graph.nodes, graph.edges, handleNodeSelect)
    return { layoutNodes: layout.nodes, layoutEdges: layout.edges }
  }, [graph, handleNodeSelect])

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutEdges)

  // Sync when layout changes
  useEffect(() => {
    if (layoutNodes.length > 0) setNodes(layoutNodes)
    if (layoutEdges.length > 0) setEdges(layoutEdges)
  }, [layoutNodes, layoutEdges, setNodes, setEdges])

  // Edge hover handlers
  const onEdgeMouseEnter: EdgeMouseHandler = useCallback((_event, edge) => {
    if (edge.data) setHoveredEdge(edge.data as unknown as GraphEdge)
  }, [])

  const onEdgeMouseLeave: EdgeMouseHandler = useCallback(() => {
    setHoveredEdge(null)
  }, [])

  // Edge click → filter traces
  const onEdgeClick: EdgeMouseHandler = useCallback((_event, edge) => {
    const d = edge.data as unknown as GraphEdge | undefined
    if (d) {
      navigate('/traces', { state: { filterServices: [d.source, d.target] } })
    }
  }, [navigate])

  // Track mouse position for tooltip
  useEffect(() => {
    const handler = (e: MouseEvent) => setMousePos({ x: e.clientX, y: e.clientY })
    window.addEventListener('mousemove', handler)
    return () => window.removeEventListener('mousemove', handler)
  }, [])

  // Stats (memoized)
  const stats = useMemo(() => ({
    services: graph.nodes.length,
    edges: graph.edges.length,
    traces: traces.length,
    totalCalls: graph.edges.reduce((s, e) => s + e.count, 0),
    avgLatency: graph.edges.length > 0
      ? Math.round(graph.edges.reduce((s, e) => s + e.avgLatency, 0) / graph.edges.length)
      : 0,
    errorEdges: graph.edges.filter(e => e.errorRate > 0.05).length,
  }), [graph, traces])

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Service Map</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Trace-based dependency graph — built from {traces.length} traces
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs transition-colors disabled:opacity-50"
        >
          <RefreshCw size={12} className={isFetching ? 'animate-spin' : ''} />
          {isFetching ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {[
          { label: 'Services', value: stats.services, color: 'text-cyan-400' },
          { label: 'Dependencies', value: stats.edges, color: 'text-purple-400' },
          { label: 'Traces', value: stats.traces, color: 'text-gray-200' },
          { label: 'Total Calls', value: stats.totalCalls, color: 'text-blue-400' },
          { label: 'Avg Latency', value: `${stats.avgLatency}ms`, color: 'text-yellow-400' },
          { label: 'Error Edges', value: stats.errorEdges, color: stats.errorEdges > 0 ? 'text-red-400' : 'text-green-400' },
        ].map(s => (
          <div key={s.label} className="bg-surface rounded-lg border border-gray-700/50 p-2 sm:p-3 text-center">
            <p className={`text-lg sm:text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertTriangle size={16} />
          Failed to load traces: {(error as Error).message}
        </div>
      )}

      {/* Map */}
      <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden" style={{ height: 'calc(100vh - 340px)', minHeight: '400px' }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
            <span className="ml-3 text-gray-400">Building service map from traces...</span>
          </div>
        ) : graph.nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Network size={48} className="mb-4 opacity-30" />
            <p className="text-lg font-medium">No services found</p>
            <p className="text-sm mt-1">No traces available in the last 15 minutes</p>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onEdgeMouseEnter={onEdgeMouseEnter}
            onEdgeMouseLeave={onEdgeMouseLeave}
            onEdgeClick={onEdgeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            minZoom={0.2}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
            className="bg-gray-900"
          >
            <Background color="#374151" gap={20} size={1} />
            <Controls
              className="!bg-gray-800 !border-gray-700 !shadow-xl"
              showInteractive={false}
            />
            <MiniMap
              nodeColor={(n) => {
                const d = n.data as ServiceNodeData | undefined
                if (!d) return '#22c55e'
                const rate = d.callCount > 0 ? d.errorCount / d.callCount : 0
                if (rate > 0.1) return '#ef4444'
                if (rate > 0.02) return '#eab308'
                return '#22c55e'
              }}
              maskColor="rgba(0,0,0,0.7)"
              className="!bg-gray-800 !border-gray-700"
            />

            {/* Legend */}
            <Panel position="top-right">
              <div className="bg-gray-800/90 backdrop-blur border border-gray-700 rounded-lg p-3 text-xs space-y-1.5">
                <p className="font-semibold text-gray-300 mb-2">Legend</p>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-gray-400">Healthy</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <span className="text-gray-400">Degraded</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-gray-400">Errors</span>
                </div>
                <div className="border-t border-gray-700 pt-1.5 mt-1.5">
                  <p className="text-gray-500 mb-1">Edges</p>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-0.5 rounded bg-emerald-500" />
                    <span className="text-gray-400">&lt;200ms</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-6 h-0.5 rounded bg-yellow-500" />
                    <span className="text-gray-400">200-500ms</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-6 h-0.5 rounded bg-red-500" />
                    <span className="text-gray-400">&gt;500ms / errors</span>
                  </div>
                </div>
              </div>
            </Panel>
          </ReactFlow>
        )}
      </div>

      {/* Edge tooltip overlay */}
      <EdgeTooltip edge={hoveredEdge} position={mousePos} />

      {/* Dependencies table */}
      {graph.edges.length > 0 && (
        <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-200">Dependencies ({graph.edges.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-800/30 text-gray-400 uppercase tracking-wider">
                  <th className="px-4 py-2 text-left">Source</th>
                  <th className="px-4 py-2 text-left">Target</th>
                  <th className="px-4 py-2 text-right">Calls</th>
                  <th className="px-4 py-2 text-right">Avg Latency</th>
                  <th className="px-4 py-2 text-right">Error Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {graph.edges
                  .sort((a, b) => b.count - a.count)
                  .map((edge, i) => (
                  <tr
                    key={i}
                    className="hover:bg-gray-800/20 cursor-pointer"
                    onClick={() => navigate('/traces', { state: { filterServices: [edge.source, edge.target] } })}
                  >
                    <td className="px-4 py-2.5 text-gray-300 font-medium">{edge.source}</td>
                    <td className="px-4 py-2.5 text-gray-300 font-medium">
                      <span className="flex items-center gap-1.5">
                        <ArrowRight size={10} className="text-gray-600" />
                        {edge.target}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-gray-200 font-mono">{edge.count}</td>
                    <td className="px-4 py-2.5 text-right font-mono">
                      <span className={edge.avgLatency > 500 ? 'text-red-400' : edge.avgLatency > 200 ? 'text-yellow-400' : 'text-gray-200'}>
                        {edge.avgLatency} ms
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono">
                      <span className={edge.errorRate > 0.05 ? 'text-red-400' : 'text-gray-200'}>
                        {(edge.errorRate * 100).toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
