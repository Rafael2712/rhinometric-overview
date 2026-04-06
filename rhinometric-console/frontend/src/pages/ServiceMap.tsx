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
import { RefreshCw, Network, AlertTriangle, ArrowRight } from 'lucide-react'
import { buildServiceGraph } from '../utils/serviceGraph'
import type { GraphEdge, GraphNode as GNode } from '../utils/serviceGraph'
import type { JaegerTrace } from '../utils/traceAnalysis'
import Dagre from '@dagrejs/dagre'

/* ================================================================
   VISUALIZATION CONSTANTS
   ================================================================ */

const EDGE_THRESHOLDS = { fast: 100, medium: 300 } as const
const ERROR_THRESHOLD = 0.05

const COLORS = {
  healthy:  '#10b981',
  degraded: '#f59e0b',
  error:    '#ef4444',
  muted:    '#6b7280',
  accent:   '#06b6d4',
  surface:  '#111827',
  border:   '#374151',
} as const

/* ================================================================
   EDGE HELPERS
   ================================================================ */

function edgeColor(edge: GraphEdge): string {
  if (edge.errorRate > ERROR_THRESHOLD) return COLORS.error
  if (edge.avgLatency > EDGE_THRESHOLDS.medium) return COLORS.error
  if (edge.avgLatency > EDGE_THRESHOLDS.fast) return COLORS.degraded
  return COLORS.healthy
}

function edgeWidth(count: number, maxCount: number): number {
  if (maxCount <= 1) return 2
  return 2 + (count / maxCount) * 6
}

/** Derive edge stroke dash array based on error state */
function edgeStrokeDash(edge: GraphEdge): string | undefined {
  if (edge.errorRate > ERROR_THRESHOLD) return undefined // animated handles >5%
  if (edge.errorCount > 0) return '8 4' // dashed for any errors < 5%
  return undefined
}

/* ================================================================
   NODE STATUS — uses both latency AND error thresholds
   ================================================================ */

type NodeStatus = 'healthy' | 'degraded' | 'critical'

function computeNodeStatus(errorCount: number, callCount: number, avgLatency: number): NodeStatus {
  const errorRate = callCount > 0 ? errorCount / callCount : 0
  // Critical: high errors OR high latency
  if (errorRate >= ERROR_THRESHOLD || avgLatency > EDGE_THRESHOLDS.medium) return 'critical'
  // Degraded: any errors OR medium latency
  if (errorCount > 0 || avgLatency > EDGE_THRESHOLDS.fast) return 'degraded'
  // Healthy
  return 'healthy'
}

const STATUS_STYLES: Record<NodeStatus, {
  ring: string; glow: string; dot: string; glowActive: string; badge: string; badgeText: string
}> = {
  healthy:  {
    ring: COLORS.healthy, glow: '', dot: 'bg-emerald-500',
    glowActive: 'shadow-[0_0_20px_rgba(16,185,129,0.25)]',
    badge: 'bg-emerald-500/20 border-emerald-500/40', badgeText: 'text-emerald-400'
  },
  degraded: {
    ring: COLORS.degraded, glow: '', dot: 'bg-amber-500',
    glowActive: 'shadow-[0_0_20px_rgba(245,158,11,0.3)]',
    badge: 'bg-amber-500/20 border-amber-500/40', badgeText: 'text-amber-400'
  },
  critical: {
    ring: COLORS.error, glow: 'shadow-[0_0_16px_rgba(239,68,68,0.2)]', dot: 'bg-red-500',
    glowActive: 'shadow-[0_0_24px_rgba(239,68,68,0.4)]',
    badge: 'bg-red-500/20 border-red-500/40', badgeText: 'text-red-400'
  },
}

/** Quick insight line for node tooltip */
function nodeInsight(status: NodeStatus, errorRate: number, avgLatency: number): string {
  if (status === 'critical') {
    if (errorRate >= ERROR_THRESHOLD) return `${(errorRate * 100).toFixed(1)}% error rate — investigate`
    return `High latency ${avgLatency}ms — investigate`
  }
  if (status === 'degraded') {
    if (errorRate > 0) return `Low error rate detected`
    return `Moderate latency ${avgLatency}ms`
  }
  return 'No issues detected'
}

/** Node width scales with call count */
function nodeWidth(callCount: number, maxCalls: number): number {
  const MIN = 160, MAX = 240
  if (maxCalls <= 1) return MIN
  return MIN + ((callCount / maxCalls) * (MAX - MIN))
}

/* ================================================================
   NODE METADATA — incoming/outgoing counts + avgLatency per node
   ================================================================ */

interface NodeMeta {
  incoming: Map<string, number>
  outgoing: Map<string, number>
  avgLatency: Map<string, number>  // weighted avg across all edges touching node
  totalEdgeCalls: Map<string, number>
  totalEdgeErrors: Map<string, number>
}

function computeNodeMeta(edges: GraphEdge[]): NodeMeta {
  const incoming = new Map<string, number>()
  const outgoing = new Map<string, number>()
  const latSum = new Map<string, number>()
  const latWeight = new Map<string, number>()
  const totalEdgeCalls = new Map<string, number>()
  const totalEdgeErrors = new Map<string, number>()

  edges.forEach(e => {
    incoming.set(e.target, (incoming.get(e.target) || 0) + 1)
    outgoing.set(e.source, (outgoing.get(e.source) || 0) + 1)

    // Accumulate latency for both source and target
    for (const nodeId of [e.source, e.target]) {
      latSum.set(nodeId, (latSum.get(nodeId) || 0) + e.avgLatency * e.count)
      latWeight.set(nodeId, (latWeight.get(nodeId) || 0) + e.count)
      totalEdgeCalls.set(nodeId, (totalEdgeCalls.get(nodeId) || 0) + e.count)
      totalEdgeErrors.set(nodeId, (totalEdgeErrors.get(nodeId) || 0) + e.errorCount)
    }
  })

  const avgLatency = new Map<string, number>()
  latSum.forEach((sum, id) => {
    const w = latWeight.get(id) || 1
    avgLatency.set(id, Math.round(sum / w))
  })

  return { incoming, outgoing, avgLatency, totalEdgeCalls, totalEdgeErrors }
}

/* ================================================================
   DAGRE LAYOUT
   ================================================================ */

function dagreLayout(
  graphNodes: GNode[],
  graphEdges: GraphEdge[],
  meta: NodeMeta,
  onSelect: (id: string) => void,
): { nodes: Node[]; edges: Edge[] } {
  const g = new Dagre.graphlib.Graph({ directed: true })
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 120, marginx: 40, marginy: 40 })

  const maxCalls = Math.max(1, ...graphNodes.map(n => n.callCount))

  graphNodes.forEach(n => {
    const w = nodeWidth(n.callCount, maxCalls)
    g.setNode(n.id, { label: n.id, width: w, height: 80 })
  })

  graphEdges.forEach(e => { g.setEdge(e.source, e.target) })
  Dagre.layout(g)

  const nodes: Node[] = graphNodes.map(n => {
    const pos = g.node(n.id)
    const w = nodeWidth(n.callCount, maxCalls)
    const avgLat = meta.avgLatency.get(n.id) || 0
    const status = computeNodeStatus(n.errorCount, n.callCount, avgLat)
    return {
      id: n.id,
      type: 'service',
      position: { x: pos.x - w / 2, y: pos.y - 40 },
      data: {
        label: n.id,
        callCount: n.callCount,
        errorCount: n.errorCount,
        nodeWidth: w,
        incoming: meta.incoming.get(n.id) || 0,
        outgoing: meta.outgoing.get(n.id) || 0,
        avgLatency: avgLat,
        status,
        onSelect,
      } as ServiceNodeData,
    }
  })

  const maxCount = Math.max(1, ...graphEdges.map(e => e.count))
  const edges: Edge[] = graphEdges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    animated: e.errorRate > ERROR_THRESHOLD,
    label: `${e.avgLatency}ms`,
    labelStyle: {
      fill: '#9ca3af',
      fontSize: 10,
      fontWeight: 500,
      fontFamily: 'ui-monospace, monospace',
    },
    labelBgStyle: { fill: '#1f2937', fillOpacity: 0.85 },
    labelBgPadding: [6, 3] as [number, number],
    labelBgBorderRadius: 4,
    style: {
      stroke: edgeColor(e),
      strokeWidth: edgeWidth(e.count, maxCount),
      strokeDasharray: edgeStrokeDash(e),
      opacity: e.errorRate > ERROR_THRESHOLD ? 1 : 0.85,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: edgeColor(e),
      width: 16,
      height: 16,
    },
    data: { ...e },
  }))

  return { nodes, edges }
}

/* ================================================================
   CUSTOM SERVICE NODE
   ================================================================ */

interface ServiceNodeData {
  label: string
  callCount: number
  errorCount: number
  nodeWidth: number
  incoming: number
  outgoing: number
  avgLatency: number
  status: NodeStatus
  onSelect: (id: string) => void
  [key: string]: unknown
}

function ServiceNode({ data }: { data: ServiceNodeData }) {
  const ss = STATUS_STYLES[data.status]
  const [hovered, setHovered] = useState(false)
  const errorRate = data.callCount > 0 ? data.errorCount / data.callCount : 0
  const errorRateStr = (errorRate * 100).toFixed(1)
  const insight = nodeInsight(data.status, errorRate, data.avgLatency)

  return (
    <div
      className="relative group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => data.onSelect(data.label)}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !w-2.5 !h-2.5 !border-2 !border-gray-800 !-top-1" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !w-2.5 !h-2.5 !border-2 !border-gray-800 !-bottom-1" />

      {/* Node card */}
      <div
        className={`rounded-xl border-2 px-4 py-3 cursor-pointer transition-all duration-200 backdrop-blur-sm
          hover:scale-[1.03] ${hovered ? ss.glowActive : ss.glow}`}
        style={{
          width: data.nodeWidth,
          borderColor: ss.ring,
          backgroundColor: 'rgba(17, 24, 39, 0.92)',
        }}
      >
        {/* Status badge — top right */}
        <div className={`absolute -top-2 -right-2 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider border ${ss.badge} ${ss.badgeText}`}>
          {data.status === 'critical' ? 'ERR' : data.status === 'degraded' ? 'WARN' : 'OK'}
        </div>

        {/* Header row */}
        <div className="flex items-center gap-2 mb-1.5">
          <div className={`w-2.5 h-2.5 rounded-full ${ss.dot} flex-shrink-0`} />
          <span className="text-sm font-semibold text-gray-100 truncate" title={data.label}>
            {data.label}
          </span>
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-3 text-[11px]">
          <span className="text-gray-400">
            <span className="text-gray-200 font-mono font-medium">{data.callCount}</span> spans
          </span>
          <span className="text-gray-400">
            <span className="text-gray-200 font-mono font-medium">{data.avgLatency}</span>ms
          </span>
          {data.errorCount > 0 && (
            <span className="text-red-400">
              <span className="font-mono font-medium">{data.errorCount}</span> err
            </span>
          )}
        </div>
      </div>

      {/* Hover tooltip */}
      {hovered && (
        <div
          className="absolute z-50 left-full ml-3 top-0 rounded-lg p-3 min-w-[210px] pointer-events-none border"
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.96)',
            borderColor: COLORS.border,
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}
        >
          <p className="text-xs font-bold text-gray-100 mb-2 truncate">{data.label}</p>

          {/* Quick insight */}
          <p className={`text-[10px] mb-2 px-2 py-1 rounded ${ss.badge} ${ss.badgeText}`}>
            {insight}
          </p>

          <div className="space-y-1">
            <Row label="Total spans" value={String(data.callCount)} />
            <Row label="Avg latency" value={`${data.avgLatency} ms`}
              color={data.avgLatency > EDGE_THRESHOLDS.medium ? 'text-red-400' : data.avgLatency > EDGE_THRESHOLDS.fast ? 'text-amber-400' : undefined} />
            <Row label="Errors" value={String(data.errorCount)} color={data.errorCount > 0 ? 'text-red-400' : undefined} />
            <Row label="Error rate" value={`${errorRateStr}%`}
              color={errorRate > ERROR_THRESHOLD ? 'text-red-400' : errorRate > 0 ? 'text-amber-400' : undefined} />
            <div className="border-t border-gray-700/50 my-1.5" />
            <Row label="Incoming deps" value={String(data.incoming)} color="text-cyan-400" />
            <Row label="Outgoing deps" value={String(data.outgoing)} color="text-purple-400" />
          </div>

          <p className="text-[10px] text-gray-600 mt-2 italic">Click to view traces</p>
        </div>
      )}
    </div>
  )
}

function Row({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <p className="text-[11px] text-gray-400 flex justify-between gap-4">
      <span>{label}</span>
      <span className={`font-mono font-medium ${color || 'text-gray-200'}`}>{value}</span>
    </p>
  )
}

const nodeTypes = { service: ServiceNode }

/* ================================================================
   EDGE TOOLTIP (follows cursor)
   ================================================================ */

function EdgeTooltip({ edge, position }: { edge: GraphEdge | null; position: { x: number; y: number } }) {
  if (!edge) return null

  const hasErrors = edge.errorCount > 0
  const isCritical = edge.errorRate > ERROR_THRESHOLD
  const isSlowEdge = edge.avgLatency > EDGE_THRESHOLDS.medium
  const insight = isCritical
    ? `${(edge.errorRate * 100).toFixed(1)}% error rate`
    : isSlowEdge
      ? `High latency ${edge.avgLatency}ms`
      : hasErrors
        ? `${edge.errorCount} error${edge.errorCount > 1 ? 's' : ''} detected`
        : 'No issues detected'

  const insightStyle = isCritical || isSlowEdge
    ? 'bg-red-500/20 border-red-500/40 text-red-400'
    : hasErrors
      ? 'bg-amber-500/20 border-amber-500/40 text-amber-400'
      : 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'

  return (
    <div
      className="fixed z-[9999] pointer-events-none rounded-lg p-3 border"
      style={{
        left: position.x + 14,
        top: position.y - 12,
        backgroundColor: 'rgba(17, 24, 39, 0.96)',
        borderColor: COLORS.border,
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
      }}
    >
      <p className="text-xs font-bold text-gray-100 mb-2">
        {edge.source}
        <span className="text-gray-500 mx-1.5">&rarr;</span>
        {edge.target}
      </p>

      {/* Quick insight */}
      <p className={`text-[10px] mb-2 px-2 py-1 rounded border ${insightStyle}`}>
        {insight}
      </p>

      <div className="space-y-1">
        <Row label="Calls" value={String(edge.count)} />
        <Row label="Avg latency" value={`${edge.avgLatency} ms`}
          color={edge.avgLatency > EDGE_THRESHOLDS.medium ? 'text-red-400' : edge.avgLatency > EDGE_THRESHOLDS.fast ? 'text-amber-400' : 'text-gray-200'} />
        <Row label="Error rate" value={`${(edge.errorRate * 100).toFixed(1)}%`}
          color={edge.errorRate > ERROR_THRESHOLD ? 'text-red-400' : 'text-gray-200'} />
      </div>

      <p className="text-[10px] text-gray-600 mt-2 italic">Click to investigate</p>
    </div>
  )
}

/* ================================================================
   LEGEND
   ================================================================ */

function Legend() {
  return (
    <div
      className="rounded-lg p-3 text-[11px] space-y-2 border backdrop-blur-sm"
      style={{
        backgroundColor: 'rgba(31, 41, 55, 0.92)',
        borderColor: COLORS.border,
        minWidth: 175,
      }}
    >
      <p className="font-bold text-gray-200 text-xs mb-2">Legend</p>

      <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold">Node status</p>
      <LegendRow dot="bg-emerald-500" text="Healthy — no issues" />
      <LegendRow dot="bg-amber-500" text="Degraded — latency/errors" />
      <LegendRow dot="bg-red-500" text="Critical — high errors/latency" />

      <div className="border-t border-gray-700/50 !my-2" />

      <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold">Edge color</p>
      <LegendLine color={COLORS.healthy} text="< 100ms" />
      <LegendLine color={COLORS.degraded} text="100–300ms" />
      <LegendLine color={COLORS.error} text="> 300ms / errors" />

      <div className="border-t border-gray-700/50 !my-2" />

      <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold">Edge thickness</p>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <div className="w-5 rounded-full" style={{ height: 2, backgroundColor: '#6b7280' }} />
          <span className="text-gray-500 text-[10px]">to</span>
          <div className="w-5 rounded-full" style={{ height: 7, backgroundColor: '#6b7280' }} />
        </div>
        <span className="text-gray-400">Call volume</span>
      </div>

      <div className="border-t border-gray-700/50 !my-2" />

      <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold">Edge pattern</p>
      <div className="flex items-center gap-2">
        <div className="w-5 border-t-2 border-dashed border-gray-400" />
        <span className="text-gray-400">Errors present</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-5 border-t-2 border-dotted border-red-400" />
        <span className="text-gray-400">&gt; 5% errors (animated)</span>
      </div>

      <div className="border-t border-gray-700/50 !my-2" />

      <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold">Interactions</p>
      <p className="text-gray-400">Click node → view traces</p>
      <p className="text-gray-400">Click edge → investigate relation</p>
    </div>
  )
}

function LegendRow({ dot, text }: { dot: string; text: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2.5 h-2.5 rounded-full ${dot} flex-shrink-0`} />
      <span className="text-gray-400">{text}</span>
    </div>
  )
}

function LegendLine({ color, text }: { color: string; text: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-5 h-[3px] rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="text-gray-400">{text}</span>
    </div>
  )
}

/* ================================================================
   MAIN PAGE
   ================================================================ */

export function ServiceMapPage() {
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

  /* ── Fetch traces (manual refresh) ─────────────────────────── */
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
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  const traces: JaegerTrace[] = tracesData?.traces || []

  /* ── Build graph (memoized) ────────────────────────────────── */
  const graph = useMemo(() => buildServiceGraph(traces), [traces])
  const meta = useMemo(() => computeNodeMeta(graph.edges), [graph.edges])

  /* ── Node click → navigate to traces filtered by service ───── */
  const handleNodeSelect = useCallback((serviceId: string) => {
    navigate('/traces', { state: { prefillService: serviceId } })
  }, [navigate])

  /* ── Layout (dagre, memoized) ──────────────────────────────── */
  const { layoutNodes, layoutEdges } = useMemo(() => {
    if (graph.nodes.length === 0) return { layoutNodes: [], layoutEdges: [] }
    const layout = dagreLayout(graph.nodes, graph.edges, meta, handleNodeSelect)
    return { layoutNodes: layout.nodes, layoutEdges: layout.edges }
  }, [graph, meta, handleNodeSelect])

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutEdges)

  useEffect(() => {
    if (layoutNodes.length > 0) setNodes(layoutNodes)
    if (layoutEdges.length > 0) setEdges(layoutEdges)
  }, [layoutNodes, layoutEdges, setNodes, setEdges])

  /* ── Edge interaction ──────────────────────────────────────── */
  const onEdgeMouseEnter: EdgeMouseHandler = useCallback((_event, edge) => {
    if (edge.data) setHoveredEdge(edge.data as unknown as GraphEdge)
  }, [])

  const onEdgeMouseLeave: EdgeMouseHandler = useCallback(() => {
    setHoveredEdge(null)
  }, [])

  /** Edge click → navigate to traces with source + target context */
  const onEdgeClick: EdgeMouseHandler = useCallback((_event, edge) => {
    const d = edge.data as unknown as GraphEdge | undefined
    if (d) {
      navigate('/traces', { state: { sourceService: d.source, targetService: d.target } })
    }
  }, [navigate])

  useEffect(() => {
    const handler = (e: MouseEvent) => setMousePos({ x: e.clientX, y: e.clientY })
    window.addEventListener('mousemove', handler)
    return () => window.removeEventListener('mousemove', handler)
  }, [])

  /* ── Stats ─────────────────────────────────────────────────── */
  const stats = useMemo(() => ({
    services: graph.nodes.length,
    edges: graph.edges.length,
    traces: traces.length,
    totalCalls: graph.edges.reduce((s, e) => s + e.count, 0),
    avgLatency: graph.edges.length > 0
      ? Math.round(graph.edges.reduce((s, e) => s + e.avgLatency, 0) / graph.edges.length)
      : 0,
    errorEdges: graph.edges.filter(e => e.errorRate > ERROR_THRESHOLD).length,
  }), [graph, traces])

  /* ── Render ────────────────────────────────────────────────── */
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Service Map</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Trace-based dependency graph &mdash; built from {traces.length} traces
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs
            transition-colors disabled:opacity-50 border border-gray-700"
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
          { label: 'Avg Latency', value: `${stats.avgLatency}ms`, color: 'text-amber-400' },
          { label: 'Error Edges', value: stats.errorEdges,
            color: stats.errorEdges > 0 ? 'text-red-400' : 'text-emerald-400' },
        ].map(s => (
          <div key={s.label} className="bg-surface rounded-lg border border-gray-700/50 p-2 sm:p-3 text-center">
            <p className={`text-lg sm:text-xl font-bold font-mono ${s.color}`}>{s.value}</p>
            <p className="text-[10px] sm:text-xs text-gray-500 font-medium uppercase tracking-wide">{s.label}</p>
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

      {/* Graph container */}
      <div
        className="bg-surface rounded-xl border border-gray-700 overflow-hidden"
        style={{ height: 'calc(100vh - 340px)', minHeight: '420px' }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full gap-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
            <span className="text-gray-400 text-sm">Building service map from traces&hellip;</span>
          </div>
        ) : graph.nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Network size={56} className="mb-4 opacity-20" />
            <p className="text-lg font-semibold text-gray-400">No services detected</p>
            <p className="text-sm mt-1 text-gray-600">
              No cross-service traces found in the last 15 minutes.
            </p>
            <button
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs
                transition-colors border border-gray-700 flex items-center gap-1.5"
            >
              <RefreshCw size={12} />
              Try again
            </button>
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
            fitViewOptions={{ padding: 0.35 }}
            minZoom={0.15}
            maxZoom={2.5}
            proOptions={{ hideAttribution: true }}
            className="bg-gray-900"
          >
            <Background color="#1f2937" gap={24} size={1} />
            <Controls
              className="!bg-gray-800/90 !border-gray-700 !shadow-xl !rounded-lg"
              showInteractive={false}
            />
            <MiniMap
              nodeColor={(n) => {
                const d = n.data as ServiceNodeData | undefined
                if (!d) return COLORS.healthy
                return STATUS_STYLES[d.status]?.ring || COLORS.healthy
              }}
              maskColor="rgba(0,0,0,0.7)"
              className="!bg-gray-800/90 !border-gray-700 !rounded-lg"
              pannable
              zoomable
            />
            <Panel position="top-right">
              <Legend />
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
            <h3 className="text-sm font-bold text-gray-200">
              Dependencies
              <span className="ml-2 text-gray-500 font-normal">({graph.edges.length})</span>
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-800/40 text-gray-400 uppercase tracking-wider text-[10px]">
                  <th className="px-4 py-2.5 text-left font-semibold">Source</th>
                  <th className="px-4 py-2.5 text-left font-semibold">Target</th>
                  <th className="px-4 py-2.5 text-right font-semibold">Calls</th>
                  <th className="px-4 py-2.5 text-right font-semibold">Avg Latency</th>
                  <th className="px-4 py-2.5 text-right font-semibold">Error Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {graph.edges
                  .sort((a, b) => b.count - a.count)
                  .map((edge, i) => {
                    const latColor = edge.avgLatency > EDGE_THRESHOLDS.medium
                      ? 'text-red-400'
                      : edge.avgLatency > EDGE_THRESHOLDS.fast
                        ? 'text-amber-400'
                        : 'text-gray-200'
                    return (
                      <tr
                        key={i}
                        className="hover:bg-gray-800/30 cursor-pointer transition-colors"
                        onClick={() => navigate('/traces', { state: { sourceService: edge.source, targetService: edge.target } })}
                      >
                        <td className="px-4 py-2.5 text-gray-300 font-medium">{edge.source}</td>
                        <td className="px-4 py-2.5 text-gray-300 font-medium">
                          <span className="flex items-center gap-1.5">
                            <ArrowRight size={10} className="text-gray-600 flex-shrink-0" />
                            {edge.target}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-right text-gray-200 font-mono">{edge.count}</td>
                        <td className={`px-4 py-2.5 text-right font-mono ${latColor}`}>{edge.avgLatency} ms</td>
                        <td className="px-4 py-2.5 text-right font-mono">
                          <span className={edge.errorRate > ERROR_THRESHOLD ? 'text-red-400' : edge.errorCount > 0 ? 'text-amber-400' : 'text-gray-200'}>
                            {(edge.errorRate * 100).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
