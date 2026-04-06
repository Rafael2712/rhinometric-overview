// ─────────────────────────────────────────────────────────
// Service Graph — Build dependency graph from trace data
// Pure functions. No backend calls. No side effects.
// ─────────────────────────────────────────────────────────

import type { JaegerTrace, JaegerSpan } from './traceAnalysis'
import { getServiceName, isErrorSpan } from './traceAnalysis'

// ── Types ───────────────────────────────────────────────

export interface GraphNode {
  id: string            // serviceName
  callCount: number     // total spans for this service
  errorCount: number    // spans with error status
}

export interface GraphEdge {
  source: string        // parent service
  target: string        // child service
  count: number         // how many times this relationship appears
  totalLatency: number  // sum of child span durations (µs)
  avgLatency: number    // totalLatency / count (ms)
  errorCount: number    // errors on the child spans of this edge
  errorRate: number     // errorCount / count (0..1)
}

export interface ServiceGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ── Step 1: Build span tree per trace ───────────────────

interface SpanWithService {
  span: JaegerSpan
  serviceName: string
  parentSpanID: string | null
}

function getParentSpanID(span: JaegerSpan): string | null {
  if (!span.references || span.references.length === 0) return null
  const childOf = span.references.find(r => r.refType === 'CHILD_OF')
  return childOf?.spanID || span.references[0]?.spanID || null
}

// ── Step 2 & 3: Extract and aggregate relationships ─────

export function buildServiceGraph(traces: JaegerTrace[]): ServiceGraph {
  // Edge accumulator: key = "source→target"
  const edgeMap = new Map<string, {
    source: string
    target: string
    count: number
    totalLatency: number
    errorCount: number
  }>()

  // Node accumulator
  const nodeMap = new Map<string, { callCount: number; errorCount: number }>()

  for (const trace of traces) {
    const { spans, processes } = trace
    if (!spans || spans.length === 0) continue

    // Build spanID → span+service lookup
    const spanLookup = new Map<string, SpanWithService>()
    for (const span of spans) {
      const serviceName = getServiceName(span, processes)
      spanLookup.set(span.spanID, {
        span,
        serviceName,
        parentSpanID: getParentSpanID(span),
      })

      // Count node appearances
      const node = nodeMap.get(serviceName) || { callCount: 0, errorCount: 0 }
      node.callCount++
      if (isErrorSpan(span)) node.errorCount++
      nodeMap.set(serviceName, node)
    }

    // For each span, find parent → extract cross-service edges
    for (const [, entry] of spanLookup) {
      if (!entry.parentSpanID) continue
      const parent = spanLookup.get(entry.parentSpanID)
      if (!parent) continue

      // Only create edge when services differ
      if (parent.serviceName === entry.serviceName) continue

      const key = `${parent.serviceName}\u2192${entry.serviceName}`
      const edge = edgeMap.get(key) || {
        source: parent.serviceName,
        target: entry.serviceName,
        count: 0,
        totalLatency: 0,
        errorCount: 0,
      }
      edge.count++
      edge.totalLatency += entry.span.duration  // µs
      if (isErrorSpan(entry.span)) edge.errorCount++
      edgeMap.set(key, edge)
    }
  }

  // Build final structures
  const nodes: GraphNode[] = Array.from(nodeMap.entries()).map(([id, data]) => ({
    id,
    callCount: data.callCount,
    errorCount: data.errorCount,
  }))

  const edges: GraphEdge[] = Array.from(edgeMap.values()).map(e => ({
    source: e.source,
    target: e.target,
    count: e.count,
    totalLatency: e.totalLatency,
    avgLatency: Math.round(e.totalLatency / e.count / 1000),  // µs → ms
    errorCount: e.errorCount,
    errorRate: e.count > 0 ? e.errorCount / e.count : 0,
  }))

  return { nodes, edges }
}
