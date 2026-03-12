/* eslint-disable */
import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import type { Node, Edge } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  Globe, Database, Server, Wifi, Box, X, Plus,
  RefreshCw, AlertTriangle, Trash2, ArrowRight, Zap,
} from 'lucide-react'

/* ── Types ──────────────────────────────────────────────────────── */

interface MapNode {
  id: number
  name: string
  type: string
  status: string
  incident_id?: string | null
  service_type?: string | null
  environment?: string | null
  last_response_time_ms?: number | null
  last_check_at?: string | null
}

interface MapEdge {
  id: string
  source: number
  target: number
  type: string
  description?: string | null
}

interface GraphData {
  nodes: MapNode[]
  edges: MapEdge[]
}

interface ServiceItem {
  id: number
  name: string
  service_type: string
  status: string
  environment?: string | null
}

/* ── Style helpers ──────────────────────────────────────────────── */

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  healthy:  { bg: 'bg-green-500/10',  border: 'border-green-500/50',  text: 'text-green-400',  glow: '' },
  degraded: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/50', text: 'text-yellow-400', glow: '' },
  incident: { bg: 'bg-red-500/10',    border: 'border-red-500/50',    text: 'text-red-400',    glow: 'animate-pulse shadow-lg shadow-red-500/30' },
  impacted: { bg: 'bg-orange-500/10', border: 'border-orange-500/50', text: 'text-orange-400', glow: 'shadow-md shadow-orange-500/20' },
}

const EDGE_COLORS: Record<string, string> = {
  http: '#3b82f6',
  database: '#a855f7',
  cache: '#f97316',
  queue: '#eab308',
  external: '#6b7280',
}

const TYPE_ICONS: Record<string, typeof Globe> = {
  http: Globe,
  postgresql: Database,
  database: Database,
  cache: Zap,
  queue: Box,
  external: Wifi,
}

function getIcon(type: string) {
  return TYPE_ICONS[type] || Server
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return 'N/A'
  const d = new Date(iso)
  const s = Math.floor((Date.now() - d.getTime()) / 1000)
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

/* ── Custom Node ────────────────────────────────────────────────── */

function ServiceNode({ data }: { data: Record<string, unknown> }) {
  const node = data as unknown as MapNode & { onSelect: (n: MapNode) => void }
  const st = STATUS_COLORS[node.status] || STATUS_COLORS.healthy
  const Icon = getIcon(node.service_type || node.type || 'http')
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className={`relative rounded-xl border-2 ${st.border} ${st.bg} ${st.glow} px-4 py-3 min-w-[160px] cursor-pointer transition-all duration-200 hover:scale-105`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => node.onSelect(node)}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-500 !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500 !w-2 !h-2" />

      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className={st.text} />
        <span className="text-sm font-semibold text-gray-200 truncate max-w-[120px]">{node.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-xs px-1.5 py-0.5 rounded ${st.bg} ${st.text} font-medium uppercase`}>
          {node.status}
        </span>
        <span className="text-xs text-gray-500">{node.service_type || node.type}</span>
      </div>

      {/* Hover tooltip */}
      {hovered && (
        <div className="absolute z-50 left-full ml-3 top-0 bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl min-w-[180px] pointer-events-none">
          <p className="text-xs text-gray-400 mb-1">Latency: <span className="text-gray-200 font-mono">{node.last_response_time_ms ? `${node.last_response_time_ms.toFixed(1)}ms` : 'N/A'}</span></p>
          <p className="text-xs text-gray-400 mb-1">Last check: <span className="text-gray-200">{timeAgo(node.last_check_at)}</span></p>
          {node.environment && <p className="text-xs text-gray-400">Env: <span className="text-gray-200">{node.environment}</span></p>}
        </div>
      )}
    </div>
  )
}

const nodeTypes = { service: ServiceNode }

/* ── Auto layout ────────────────────────────────────────────────── */

function autoLayout(mapNodes: MapNode[], mapEdges: MapEdge[]): { nodes: Node[]; edges: Edge[] } {
  // Simple grid layout with dependency hierarchy
  const nodeMap = new Map<number, MapNode>()
  mapNodes.forEach(n => nodeMap.set(n.id, n))

  // Calculate depths using topological sort
  const inDegree = new Map<number, number>()
  const children = new Map<number, number[]>()
  mapNodes.forEach(n => { inDegree.set(n.id, 0); children.set(n.id, []) })
  mapEdges.forEach(e => {
    inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1)
    const ch = children.get(e.source) || []
    ch.push(e.target)
    children.set(e.source, ch)
  })

  const depth = new Map<number, number>()
  const queue: number[] = []
  mapNodes.forEach(n => { if ((inDegree.get(n.id) || 0) === 0) { queue.push(n.id); depth.set(n.id, 0) } })

  while (queue.length > 0) {
    const cur = queue.shift()!
    const ch = children.get(cur) || []
    for (const c of ch) {
      const newDepth = (depth.get(cur) || 0) + 1
      if (!depth.has(c) || newDepth > depth.get(c)!) {
        depth.set(c, newDepth)
      }
      const deg = (inDegree.get(c) || 1) - 1
      inDegree.set(c, deg)
      if (deg <= 0) queue.push(c)
    }
  }

  // Assign unvisited nodes
  mapNodes.forEach(n => { if (!depth.has(n.id)) depth.set(n.id, 0) })

  // Group by depth level
  const levels = new Map<number, number[]>()
  depth.forEach((d, id) => {
    const list = levels.get(d) || []
    list.push(id)
    levels.set(d, list)
  })

  const X_GAP = 280
  const Y_GAP = 160
  const nodes: Node[] = []

  levels.forEach((ids, level) => {
    const startX = -(ids.length - 1) * X_GAP / 2
    ids.forEach((id, idx) => {
      const mn = nodeMap.get(id)
      if (!mn) return
      nodes.push({
        id: String(id),
        type: 'service',
        position: { x: startX + idx * X_GAP, y: level * Y_GAP },
        data: { ...mn } as Record<string, unknown>,
      })
    })
  })

  const edges: Edge[] = mapEdges.map(e => ({
    id: e.id,
    source: String(e.source),
    target: String(e.target),
    type: 'smoothstep',
    animated: true,
    style: { stroke: EDGE_COLORS[e.type] || '#6b7280', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: EDGE_COLORS[e.type] || '#6b7280' },
    label: e.type,
    labelStyle: { fill: '#9ca3af', fontSize: 10 },
    labelBgStyle: { fill: '#1f2937', fillOpacity: 0.8 },
    labelBgPadding: [4, 2] as [number, number],
  }))

  return { nodes, edges }
}

/* ── Main Page Component ────────────────────────────────────────── */

export function ServiceMapPage() {
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` }

  const [selectedNode, setSelectedNode] = useState<MapNode | null>(null)
  const [showAddDep, setShowAddDep] = useState(false)

  // Graph query
  const { data: graphData, isLoading, refetch } = useQuery({
    queryKey: ['service-map'],
    queryFn: async () => {
      const res = await fetch('/api/service-map', { headers })
      if (!res.ok) throw new Error('Failed to load service map')
      return res.json() as Promise<GraphData>
    },
    refetchInterval: 30000,
  })

  // Services list for dependency creation
  const { data: servicesList } = useQuery({
    queryKey: ['service-map-services'],
    queryFn: async () => {
      const res = await fetch('/api/service-map/services/list', { headers })
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<ServiceItem[]>
    },
    enabled: showAddDep,
  })

  // Delete dependency mutation
  const deleteMutation = useMutation({
    mutationFn: async (depId: string) => {
      const res = await fetch(`/api/service-map/dependencies/${depId}`, { method: 'DELETE', headers })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['service-map'] }),
  })

  // Build React Flow nodes/edges
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graphData) return { flowNodes: [], flowEdges: [] }
    const onSelect = (n: MapNode) => setSelectedNode(n)
    const layout = autoLayout(graphData.nodes, graphData.edges)
    // Inject onSelect into node data
    const nodesWithHandler = layout.nodes.map(n => ({
      ...n,
      data: { ...n.data, onSelect } as Record<string, unknown>,
    }))
    return { flowNodes: nodesWithHandler, flowEdges: layout.edges }
  }, [graphData])

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges)

  // Sync when data changes
  useEffect(() => {
    if (flowNodes.length > 0) setNodes(flowNodes)
    if (flowEdges.length > 0) setEdges(flowEdges)
  }, [flowNodes, flowEdges])

  // Stats
  const stats = useMemo(() => {
    if (!graphData) return { total: 0, healthy: 0, degraded: 0, incident: 0, impacted: 0, deps: 0 }
    return {
      total: graphData.nodes.length,
      healthy: graphData.nodes.filter(n => n.status === 'healthy').length,
      degraded: graphData.nodes.filter(n => n.status === 'degraded').length,
      incident: graphData.nodes.filter(n => n.status === 'incident').length,
      impacted: graphData.nodes.filter(n => n.status === 'impacted').length,
      deps: graphData.edges.length,
    }
  }, [graphData])

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Service Map</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">Service dependency topology with live status</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs transition-colors"
          >
            <RefreshCw size={12} /> Refresh
          </button>
          <button
            onClick={() => setShowAddDep(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-xs transition-colors"
          >
            <Plus size={12} /> Add Dependency
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {[
          { label: 'Services', value: stats.total, color: 'text-gray-200' },
          { label: 'Healthy', value: stats.healthy, color: 'text-green-400' },
          { label: 'Degraded', value: stats.degraded, color: 'text-yellow-400' },
          { label: 'Incident', value: stats.incident, color: 'text-red-400' },
          { label: 'Impacted', value: stats.impacted, color: 'text-orange-400' },
          { label: 'Dependencies', value: stats.deps, color: 'text-purple-400' },
        ].map(s => (
          <div key={s.label} className="bg-surface rounded-lg border border-gray-700/50 p-2 sm:p-3 text-center">
            <p className={`text-lg sm:text-xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Map */}
      <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden" style={{ height: 'calc(100vh - 340px)', minHeight: '400px' }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
            <span className="ml-3 text-gray-400">Loading service map...</span>
          </div>
        ) : graphData && graphData.nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Globe size={48} className="mb-4 opacity-30" />
            <p className="text-lg font-medium">No services configured</p>
            <p className="text-sm mt-1">Add services in the Services page to see them here</p>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
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
                const st = (n.data as any)?.status || 'healthy'
                if (st === 'incident') return '#ef4444'
                if (st === 'degraded') return '#eab308'
                if (st === 'impacted') return '#f97316'
                return '#22c55e'
              }}
              maskColor="rgba(0,0,0,0.7)"
              className="!bg-gray-800 !border-gray-700"
            />

            {/* Legend */}
            <Panel position="top-right">
              <div className="bg-gray-800/90 backdrop-blur border border-gray-700 rounded-lg p-3 text-xs space-y-1.5">
                <p className="font-semibold text-gray-300 mb-2">Legend</p>
                {[
                  { color: 'bg-green-500', label: 'Healthy' },
                  { color: 'bg-yellow-500', label: 'Degraded' },
                  { color: 'bg-red-500', label: 'Incident' },
                  { color: 'bg-orange-500', label: 'Impacted' },
                ].map(l => (
                  <div key={l.label} className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${l.color}`} />
                    <span className="text-gray-400">{l.label}</span>
                  </div>
                ))}
                <div className="border-t border-gray-700 pt-1.5 mt-1.5">
                  {Object.entries(EDGE_COLORS).map(([type, color]) => (
                    <div key={type} className="flex items-center gap-2 mt-1">
                      <div className="w-6 h-0.5 rounded" style={{ backgroundColor: color }} />
                      <span className="text-gray-400 capitalize">{type}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          </ReactFlow>
        )}
      </div>

      {/* Dependencies table */}
      {graphData && graphData.edges.length > 0 && (
        <div className="bg-surface rounded-xl border border-gray-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-200">Dependencies ({graphData.edges.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-800/30 text-gray-400 uppercase tracking-wider">
                  <th className="px-4 py-2 text-left">Source</th>
                  <th className="px-4 py-2 text-left">Target</th>
                  <th className="px-4 py-2 text-left">Type</th>
                  <th className="px-4 py-2 text-left">Description</th>
                  <th className="px-4 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {graphData.edges.map(edge => {
                  const srcNode = graphData.nodes.find(n => n.id === edge.source)
                  const tgtNode = graphData.nodes.find(n => n.id === edge.target)
                  return (
                    <tr key={edge.id} className="hover:bg-gray-800/20">
                      <td className="px-4 py-2.5 text-gray-300 font-medium">{srcNode?.name || edge.source}</td>
                      <td className="px-4 py-2.5 text-gray-300 font-medium">{tgtNode?.name || edge.target}</td>
                      <td className="px-4 py-2.5">
                        <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ backgroundColor: (EDGE_COLORS[edge.type] || '#6b7280') + '30', color: EDGE_COLORS[edge.type] || '#6b7280' }}>
                          {edge.type}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-gray-500">{edge.description || '—'}</td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={() => { if (confirm('Delete this dependency?')) deleteMutation.mutate(edge.id) }}
                          className="text-gray-500 hover:text-red-400 transition-colors"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Service detail panel */}
      {selectedNode && (
        <div className="fixed inset-y-0 right-0 w-80 md:w-96 bg-surface border-l border-gray-700 shadow-2xl z-50 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-200">Service Details</h3>
            <button onClick={() => setSelectedNode(null)} className="text-gray-500 hover:text-gray-300">
              <X size={16} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex items-center gap-3">
              {(() => { const Icon = getIcon(selectedNode.service_type || selectedNode.type || 'http'); return <Icon size={24} className={STATUS_COLORS[selectedNode.status]?.text || 'text-gray-400'} /> })()}
              <div>
                <p className="text-base font-semibold text-gray-200">{selectedNode.name}</p>
                <p className="text-xs text-gray-500">{selectedNode.service_type || selectedNode.type}</p>
              </div>
            </div>
            <div className={`px-3 py-2 rounded-lg border ${STATUS_COLORS[selectedNode.status]?.border || 'border-gray-700'} ${STATUS_COLORS[selectedNode.status]?.bg || 'bg-gray-800/40'}`}>
              <span className={`text-xs font-semibold uppercase ${STATUS_COLORS[selectedNode.status]?.text || 'text-gray-400'}`}>
                {selectedNode.status}
              </span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Latency</span>
                <span className="text-gray-200 font-mono">{selectedNode.last_response_time_ms ? `${selectedNode.last_response_time_ms.toFixed(1)} ms` : 'N/A'}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Last Check</span>
                <span className="text-gray-200">{timeAgo(selectedNode.last_check_at)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Environment</span>
                <span className="text-gray-200">{selectedNode.environment || 'default'}</span>
              </div>
              {selectedNode.incident_id && (
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Incident</span>
                  <span className="text-red-400 font-mono text-xs">{selectedNode.incident_id.slice(0, 8)}...</span>
                </div>
              )}
            </div>
            {/* Connected services */}
            {graphData && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Dependencies</p>
                <div className="space-y-1">
                  {graphData.edges.filter(e => e.source === selectedNode.id).map(e => {
                    const tgt = graphData.nodes.find(n => n.id === e.target)
                    return (
                      <div key={e.id} className="flex items-center gap-2 text-xs bg-gray-800/30 rounded px-2 py-1.5">
                        <ArrowRight size={10} className="text-gray-600" />
                        <span className="text-gray-300">{tgt?.name || e.target}</span>
                        <span className="text-gray-600 ml-auto">{e.type}</span>
                      </div>
                    )
                  })}
                  {graphData.edges.filter(e => e.target === selectedNode.id).map(e => {
                    const src = graphData.nodes.find(n => n.id === e.source)
                    return (
                      <div key={e.id} className="flex items-center gap-2 text-xs bg-gray-800/30 rounded px-2 py-1.5">
                        <span className="text-gray-300">{src?.name || e.source}</span>
                        <ArrowRight size={10} className="text-gray-600" />
                        <span className="text-blue-400 font-medium">{selectedNode.name}</span>
                        <span className="text-gray-600 ml-auto">{e.type}</span>
                      </div>
                    )
                  })}
                  {graphData.edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).length === 0 && (
                    <p className="text-xs text-gray-600 italic">No dependencies</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Dependency Modal */}
      {showAddDep && (
        <AddDependencyModal
          services={servicesList || []}
          headers={headers}
          onClose={() => setShowAddDep(false)}
          onCreated={() => { setShowAddDep(false); queryClient.invalidateQueries({ queryKey: ['service-map'] }) }}
        />
      )}
    </div>
  )
}

/* ── Add Dependency Modal ───────────────────────────────────────── */

function AddDependencyModal({ services, headers, onClose, onCreated }: {
  services: ServiceItem[]
  headers: Record<string, string>
  onClose: () => void
  onCreated: () => void
}) {
  const [sourceId, setSourceId] = useState<number | ''>('')
  const [targetId, setTargetId] = useState<number | ''>('')
  const [depType, setDepType] = useState('http')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sourceId || !targetId) { setError('Select both services'); return }
    if (sourceId === targetId) { setError('Source and target must differ'); return }
    setError('')
    setSaving(true)

    try {
      const res = await fetch('/api/service-map/dependencies', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_service_id: sourceId,
          target_service_id: targetId,
          dependency_type: depType,
          description: description || null,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Failed to create dependency')
        return
      }
      onCreated()
    } catch {
      setError('Network error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-surface rounded-xl border border-gray-700 shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-sm font-semibold text-gray-200">Add Dependency</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300"><X size={16} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2 text-xs text-red-400 flex items-center gap-2">
              <AlertTriangle size={12} /> {error}
            </div>
          )}

          <div>
            <label className="block text-xs text-gray-400 mb-1">Source Service (depends on target)</label>
            <select
              value={sourceId}
              onChange={e => setSourceId(e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">Select source...</option>
              {services.map(s => <option key={s.id} value={s.id}>{s.name} ({s.service_type})</option>)}
            </select>
          </div>

          <div className="flex justify-center">
            <ArrowRight size={16} className="text-gray-600" />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Target Service (depended upon)</label>
            <select
              value={targetId}
              onChange={e => setTargetId(e.target.value ? Number(e.target.value) : '')}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">Select target...</option>
              {services.map(s => <option key={s.id} value={s.id}>{s.name} ({s.service_type})</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Dependency Type</label>
            <select
              value={depType}
              onChange={e => setDepType(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            >
              {['http', 'database', 'cache', 'queue', 'external'].map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="e.g. API uses PostgreSQL for auth"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg bg-gray-800 text-gray-400 hover:text-gray-200 text-sm">
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-sm disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Dependency'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
