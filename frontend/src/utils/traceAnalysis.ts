// ─────────────────────────────────────────────────────────
// Trace Intelligence — Client-Side Analysis Utilities
// Pure functions. No backend calls. No side effects.
// ─────────────────────────────────────────────────────────

// ── Jaeger native types ─────────────────────────────────

export interface JaegerTag {
  key: string
  type: string
  value: string | number | boolean
}

export interface JaegerReference {
  refType: 'CHILD_OF' | 'FOLLOWS_FROM'
  traceID: string
  spanID: string
}

export interface JaegerLog {
  timestamp: number
  fields: JaegerTag[]
}

export interface JaegerSpan {
  traceID: string
  spanID: string
  operationName: string
  references: JaegerReference[]
  startTime: number       // microseconds since epoch
  duration: number        // microseconds
  tags: JaegerTag[]
  logs: JaegerLog[]
  processID: string
  warnings: string[] | null
}

export interface JaegerProcess {
  serviceName: string
  tags: JaegerTag[]
}

export interface JaegerTrace {
  traceID: string
  spans: JaegerSpan[]
  processes: Record<string, JaegerProcess>
  warnings?: string[]
}

// ── Classification ──────────────────────────────────────

export type TraceClassificationType = 'collector' | 'platform' | 'customer'

export interface TraceClassification {
  type: TraceClassificationType
  label: string
  description: string
  confidence: 'high' | 'medium' | 'low'
}

/**
 * Classify a trace based on operations, service names, and tags.
 * Current data is exclusively collector traces, but the logic
 * supports future platform and customer traces as well.
 */
export function classifyTrace(trace: JaegerTrace): TraceClassification {
  const { spans, processes } = trace
  if (!spans || spans.length === 0) {
    return {
      type: 'collector',
      label: 'Unknown',
      description: 'Empty trace — no spans available.',
      confidence: 'low',
    }
  }

  const operations = spans.map(s => s.operationName.toLowerCase())
  const serviceNames = new Set<string>()
  for (const s of spans) serviceNames.add(getServiceName(s, processes).toLowerCase())

  // ── Collector traces ──
  const collectorOpPatterns = ['collector.', 'collector_cycle', 'send_metrics', 'send_logs']
  const collectorOps = operations.filter(op =>
    collectorOpPatterns.some(p => op.includes(p))
  )
  const isCollectorService = [...serviceNames].some(s => s.includes('collector'))

  if (collectorOps.length > 0 || isCollectorService) {
    const allCollector = collectorOps.length === operations.length
    return {
      type: 'collector',
      label: 'Collector Trace',
      description: 'This trace represents an internal telemetry collection cycle, not an end-user business transaction.',
      confidence: allCollector ? 'high' : 'medium',
    }
  }

  // ── Platform traces ──
  const platformPatterns = ['api.', 'backend.', 'auth.', 'db.', 'cache.', 'queue.', 'health']
  const isPlatformOp = operations.some(op =>
    platformPatterns.some(p => op.startsWith(p))
  )
  const isPlatformSvc = [...serviceNames].some(s =>
    s.includes('backend') || s.includes('console') || s.includes('api')
  )
  if (isPlatformOp || isPlatformSvc) {
    return {
      type: 'platform',
      label: 'Platform Trace',
      description: 'This trace represents internal platform activity, not a customer business transaction.',
      confidence: 'medium',
    }
  }

  // ── Customer traces ──
  return {
    type: 'customer',
    label: 'Customer Trace',
    description: 'This trace may represent customer-facing application activity.',
    confidence: 'low',
  }
}

// ── Enriched types for the UI ───────────────────────────

export interface SpanNode {
  span: JaegerSpan
  serviceName: string
  children: SpanNode[]
  depth: number
  isBottleneck: boolean
  isError: boolean
  isCriticalPath: boolean
  /** Duration as percentage of total trace duration */
  pctOfTrace: number
}

export interface ServiceBreakdown {
  serviceName: string
  totalDuration: number    // microseconds — wall-clock (merged overlapping spans)
  spanCount: number
  pctOfTrace: number       // wall-clock contribution as % of trace duration (≤100 per service)
  hasErrors: boolean
}

export interface TraceAnalysis {
  traceID: string
  totalDuration: number
  spanCount: number
  serviceCount: number
  errorCount: number
  rootSpan: JaegerSpan | null
  bottleneckSpan: JaegerSpan | null
  bottleneckService: string
  bottleneckPct: number
  criticalPath: string[]       // spanIDs on the critical path
  serviceBreakdown: ServiceBreakdown[]
  dominantService: string
  dominantServicePct: number
  spanTree: SpanNode[]
  flatTree: SpanNode[]         // pre-order traversal for rendering
  insights: string[]
  classification: TraceClassification
}

// ── Helpers ─────────────────────────────────────────────

export function getServiceName(span: JaegerSpan, processes: Record<string, JaegerProcess>): string {
  return processes[span.processID]?.serviceName || span.processID || 'unknown'
}

export function getTagValue(tags: JaegerTag[], key: string): string | number | boolean | undefined {
  const tag = tags.find(t => t.key === key)
  return tag?.value
}

export function isErrorSpan(span: JaegerSpan): boolean {
  const statusCode = getTagValue(span.tags, 'otel.status_code')
  if (statusCode && statusCode !== 'OK' && statusCode !== 'UNSET') return true

  const httpStatus = getTagValue(span.tags, 'http.status_code')
  if (typeof httpStatus === 'number' && httpStatus >= 400) return true
  if (typeof httpStatus === 'string' && parseInt(httpStatus, 10) >= 400) return true

  const errorTag = getTagValue(span.tags, 'error')
  if (errorTag === true || errorTag === 'true') return true

  return false
}

export function formatDuration(microseconds: number): string {
  if (microseconds < 1000) return `${Math.round(microseconds)}\u00B5s`
  if (microseconds < 1000000) return `${(microseconds / 1000).toFixed(1)}ms`
  return `${(microseconds / 1000000).toFixed(2)}s`
}

// ── Wall-clock per service (merge overlapping intervals) ─

function computeWallClockPerService(
  spans: JaegerSpan[],
  processes: Record<string, JaegerProcess>,
): Map<string, number> {
  const svcIntervals = new Map<string, { s: number; e: number }[]>()

  for (const span of spans) {
    const svc = getServiceName(span, processes)
    if (!svcIntervals.has(svc)) svcIntervals.set(svc, [])
    svcIntervals.get(svc)!.push({
      s: span.startTime,
      e: span.startTime + span.duration,
    })
  }

  const result = new Map<string, number>()
  for (const [svc, intervals] of svcIntervals) {
    intervals.sort((a, b) => a.s - b.s)
    const merged: { s: number; e: number }[] = []
    for (const iv of intervals) {
      if (merged.length > 0 && iv.s <= merged[merged.length - 1].e) {
        merged[merged.length - 1].e = Math.max(merged[merged.length - 1].e, iv.e)
      } else {
        merged.push({ s: iv.s, e: iv.e })
      }
    }
    result.set(svc, merged.reduce((sum, m) => sum + (m.e - m.s), 0))
  }
  return result
}

// ── Span tree builder ───────────────────────────────────

function buildSpanTree(
  spans: JaegerSpan[],
  processes: Record<string, JaegerProcess>,
  analysis: { bottleneckId: string; errorIds: Set<string>; criticalPathIds: Set<string>; totalDuration: number }
): SpanNode[] {
  const spanMap = new Map<string, JaegerSpan>()
  const childrenMap = new Map<string, JaegerSpan[]>()

  for (const span of spans) {
    spanMap.set(span.spanID, span)
  }

  // Build parent→children mapping
  const roots: JaegerSpan[] = []
  for (const span of spans) {
    const parentRef = span.references.find(r => r.refType === 'CHILD_OF')
    if (parentRef && spanMap.has(parentRef.spanID)) {
      const parentId = parentRef.spanID
      if (!childrenMap.has(parentId)) childrenMap.set(parentId, [])
      childrenMap.get(parentId)!.push(span)
    } else {
      roots.push(span)
    }
  }

  // Sort roots and children by start time
  roots.sort((a, b) => a.startTime - b.startTime)
  for (const [, children] of childrenMap) {
    children.sort((a, b) => a.startTime - b.startTime)
  }

  function buildNode(span: JaegerSpan, depth: number): SpanNode {
    const children = (childrenMap.get(span.spanID) || []).map(c => buildNode(c, depth + 1))
    return {
      span,
      serviceName: getServiceName(span, processes),
      children,
      depth,
      isBottleneck: span.spanID === analysis.bottleneckId,
      isError: analysis.errorIds.has(span.spanID),
      isCriticalPath: analysis.criticalPathIds.has(span.spanID),
      pctOfTrace: analysis.totalDuration > 0 ? (span.duration / analysis.totalDuration) * 100 : 0,
    }
  }

  return roots.map(r => buildNode(r, 0))
}

/** Pre-order traversal (DFS) to flatten tree for rendering */
function flattenTree(nodes: SpanNode[]): SpanNode[] {
  const result: SpanNode[] = []
  function walk(node: SpanNode) {
    result.push(node)
    for (const child of node.children) walk(child)
  }
  for (const n of nodes) walk(n)
  return result
}

// ── Critical path ───────────────────────────────────────

function computeCriticalPath(spans: JaegerSpan[]): Set<string> {
  const spanMap = new Map<string, JaegerSpan>()
  const childrenMap = new Map<string, JaegerSpan[]>()

  for (const span of spans) spanMap.set(span.spanID, span)

  const roots: JaegerSpan[] = []
  for (const span of spans) {
    const parentRef = span.references.find(r => r.refType === 'CHILD_OF')
    if (parentRef && spanMap.has(parentRef.spanID)) {
      const pid = parentRef.spanID
      if (!childrenMap.has(pid)) childrenMap.set(pid, [])
      childrenMap.get(pid)!.push(span)
    } else {
      roots.push(span)
    }
  }

  const pathIds = new Set<string>()

  function findLongest(spanId: string): number {
    const span = spanMap.get(spanId)
    if (!span) return 0
    const children = childrenMap.get(spanId) || []
    if (children.length === 0) return span.duration

    let maxChildDur = 0
    let maxChildId = ''
    for (const child of children) {
      const childDur = findLongest(child.spanID)
      if (childDur > maxChildDur) {
        maxChildDur = childDur
        maxChildId = child.spanID
      }
    }
    if (maxChildId) pathIds.add(maxChildId)
    return span.duration
  }

  if (roots.length > 0) {
    const mainRoot = roots.reduce((a, b) => a.duration >= b.duration ? a : b)
    pathIds.add(mainRoot.spanID)
    findLongest(mainRoot.spanID)
  }

  return pathIds
}

// ── Main analysis function ──────────────────────────────

export function analyzeTrace(trace: JaegerTrace): TraceAnalysis {
  const { spans, processes, traceID } = trace
  const classification = classifyTrace(trace)

  if (!spans || spans.length === 0) {
    return emptyAnalysis(traceID, classification)
  }

  const minStart = Math.min(...spans.map(s => s.startTime))
  const maxEnd = Math.max(...spans.map(s => s.startTime + s.duration))
  const totalDuration = maxEnd - minStart

  // Root span = span with no CHILD_OF reference in trace
  const spanIdSet = new Set(spans.map(s => s.spanID))
  const rootSpan = spans.find(s => {
    const parentRef = s.references.find(r => r.refType === 'CHILD_OF')
    return !parentRef || !spanIdSet.has(parentRef.spanID)
  }) || spans[0]

  // Bottleneck = span with highest duration
  const bottleneckSpan = spans.reduce((a, b) => a.duration >= b.duration ? a : b)
  const bottleneckService = getServiceName(bottleneckSpan, processes)
  const bottleneckPct = totalDuration > 0 ? (bottleneckSpan.duration / totalDuration) * 100 : 0

  // Errors
  const errorIds = new Set<string>()
  for (const span of spans) {
    if (isErrorSpan(span)) errorIds.add(span.spanID)
  }

  // Service breakdown — wall-clock merged per service
  const wallClockMap = computeWallClockPerService(spans, processes)
  const svcSpanCount = new Map<string, { count: number; hasErrors: boolean }>()
  for (const span of spans) {
    const svc = getServiceName(span, processes)
    const entry = svcSpanCount.get(svc) || { count: 0, hasErrors: false }
    entry.count++
    if (errorIds.has(span.spanID)) entry.hasErrors = true
    svcSpanCount.set(svc, entry)
  }

  const serviceBreakdown: ServiceBreakdown[] = Array.from(wallClockMap.entries())
    .map(([name, wallClock]) => ({
      serviceName: name,
      totalDuration: wallClock,
      spanCount: svcSpanCount.get(name)?.count || 0,
      pctOfTrace: totalDuration > 0 ? (wallClock / totalDuration) * 100 : 0,
      hasErrors: svcSpanCount.get(name)?.hasErrors || false,
    }))
    .sort((a, b) => b.totalDuration - a.totalDuration)

  const dominantService = serviceBreakdown[0]?.serviceName || 'unknown'
  const dominantServicePct = serviceBreakdown[0]?.pctOfTrace || 0

  // Services
  const serviceSet = new Set<string>()
  for (const span of spans) serviceSet.add(getServiceName(span, processes))

  // Critical path
  const criticalPathIds = computeCriticalPath(spans)

  // Build span tree
  const spanTree = buildSpanTree(spans, processes, {
    bottleneckId: bottleneckSpan.spanID,
    errorIds,
    criticalPathIds,
    totalDuration,
  })
  const flatTree = flattenTree(spanTree)

  // ── Insights (classification-aware, trustworthy) ──
  const insights: string[] = []

  // Classification context
  if (classification.type === 'collector') {
    insights.push('Internal collector flow detected')
  }

  // Bottleneck
  if (bottleneckPct >= 50) {
    insights.push(
      `Bottleneck span accounts for ${bottleneckPct.toFixed(0)}% of total trace duration (${formatDuration(bottleneckSpan.duration)})`
    )
  } else if (bottleneckPct >= 30) {
    insights.push(
      `Slowest span: "${bottleneckSpan.operationName}" \u2014 ${bottleneckPct.toFixed(0)}% of total (${formatDuration(bottleneckSpan.duration)})`
    )
  }

  // Errors
  if (errorIds.size > 0) {
    const errorServices = new Set<string>()
    for (const sid of errorIds) {
      const s = spans.find(sp => sp.spanID === sid)
      if (s) errorServices.add(getServiceName(s, processes))
    }
    insights.push(
      `${errorIds.size} error span${errorIds.size > 1 ? 's' : ''} detected` +
      (errorServices.size > 0 ? ` in ${Array.from(errorServices).join(', ')}` : '')
    )
  } else {
    insights.push('No errors detected in this trace')
  }

  // Duration summary
  insights.push(
    `Trace completed in ${formatDuration(totalDuration)} across ${spans.length} span${spans.length > 1 ? 's' : ''} and ${serviceSet.size} service${serviceSet.size > 1 ? 's' : ''}`
  )

  return {
    traceID,
    totalDuration,
    spanCount: spans.length,
    serviceCount: serviceSet.size,
    errorCount: errorIds.size,
    rootSpan,
    bottleneckSpan,
    bottleneckService,
    bottleneckPct,
    criticalPath: Array.from(criticalPathIds),
    serviceBreakdown,
    dominantService,
    dominantServicePct,
    spanTree,
    flatTree,
    insights,
    classification,
  }
}

/** Quick summary for trace list items (lightweight, no tree) */
export function summarizeTrace(trace: JaegerTrace): {
  totalDuration: number
  spanCount: number
  serviceCount: number
  errorCount: number
  rootOperation: string
  rootService: string
  startTime: number
  classificationType: TraceClassificationType
  classificationLabel: string
} {
  const { spans, processes } = trace
  if (!spans || spans.length === 0) {
    return { totalDuration: 0, spanCount: 0, serviceCount: 0, errorCount: 0, rootOperation: 'Unknown', rootService: 'unknown', startTime: 0, classificationType: 'collector', classificationLabel: 'Unknown' }
  }

  const minStart = Math.min(...spans.map(s => s.startTime))
  const maxEnd = Math.max(...spans.map(s => s.startTime + s.duration))
  const totalDuration = maxEnd - minStart

  const spanIdSet = new Set(spans.map(s => s.spanID))
  const rootSpan = spans.find(s => {
    const parentRef = s.references.find(r => r.refType === 'CHILD_OF')
    return !parentRef || !spanIdSet.has(parentRef.spanID)
  }) || spans[0]

  const services = new Set<string>()
  let errorCount = 0
  for (const span of spans) {
    services.add(getServiceName(span, processes))
    if (isErrorSpan(span)) errorCount++
  }

  const classification = classifyTrace(trace)

  return {
    totalDuration,
    spanCount: spans.length,
    serviceCount: services.size,
    errorCount,
    rootOperation: rootSpan.operationName,
    rootService: getServiceName(rootSpan, processes),
    startTime: rootSpan.startTime,
    classificationType: classification.type,
    classificationLabel: classification.label,
  }
}

function emptyAnalysis(traceID: string, classification: TraceClassification): TraceAnalysis {
  return {
    traceID,
    totalDuration: 0,
    spanCount: 0,
    serviceCount: 0,
    errorCount: 0,
    rootSpan: null,
    bottleneckSpan: null,
    bottleneckService: '',
    bottleneckPct: 0,
    criticalPath: [],
    serviceBreakdown: [],
    dominantService: '',
    dominantServicePct: 0,
    spanTree: [],
    flatTree: [],
    insights: ['No spans in this trace'],
    classification,
  }
}
