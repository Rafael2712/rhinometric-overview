/* eslint-disable */
import { create } from 'zustand'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import type { JaegerTrace } from '../utils/traceAnalysis'

/* ──────────────────────────────────────────────────────────────────
   TIME RANGE OPTIONS
   ────────────────────────────────────────────────────────────────── */

export interface TimeRangeOption {
  value: string
  label: string
  kind: 'lookback' | 'day'
}

export const TIME_RANGE_OPTIONS: TimeRangeOption[] = [
  { value: '15m', label: 'Last 15m', kind: 'lookback' },
  { value: '30m', label: 'Last 30m', kind: 'lookback' },
  { value: '1h',  label: 'Last 1h',  kind: 'lookback' },
  { value: '6h',  label: 'Last 6h',  kind: 'lookback' },
  { value: 'today',     label: 'Today',               kind: 'day' },
  { value: 'yesterday', label: 'Yesterday',            kind: 'day' },
  { value: 'day-2',     label: 'Day before yesterday', kind: 'day' },
]

/* ──────────────────────────────────────────────────────────────────
   HELPERS — resolve a range value to API params
   ────────────────────────────────────────────────────────────────── */

function startOfDay(daysAgo: number): Date {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfDay(daysAgo: number): Date {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  d.setHours(23, 59, 59, 999)
  return d
}

/**
 * Convert a time range value into URLSearchParams for /api/traces.
 *
 * - Lookback ranges (15m, 30m, 1h, 6h): use `lookback` param.
 * - Day ranges (today, yesterday, day-2): use absolute `start` & `end`
 *   in microseconds so the backend queries Jaeger with exact boundaries.
 */
export function resolveTimeParams(value: string): URLSearchParams {
  const params = new URLSearchParams({ limit: '100' })

  switch (value) {
    case 'today': {
      const s = startOfDay(0)
      const e = new Date() // now
      params.set('start', String(Math.floor(s.getTime() * 1000)))
      params.set('end',   String(Math.floor(e.getTime() * 1000)))
      break
    }
    case 'yesterday': {
      const s = startOfDay(1)
      const e = endOfDay(1)
      params.set('start', String(Math.floor(s.getTime() * 1000)))
      params.set('end',   String(Math.floor(e.getTime() * 1000)))
      break
    }
    case 'day-2': {
      const s = startOfDay(2)
      const e = endOfDay(2)
      params.set('start', String(Math.floor(s.getTime() * 1000)))
      params.set('end',   String(Math.floor(e.getTime() * 1000)))
      break
    }
    default:
      // lookback (15m, 30m, 1h, 6h)
      params.set('lookback', value)
      break
  }

  return params
}

/** Human-readable label for the currently selected range. */
export function rangeLabel(value: string): string {
  return TIME_RANGE_OPTIONS.find(o => o.value === value)?.label ?? value
}

/* ──────────────────────────────────────────────────────────────────
   TIME RANGE STORE — shared across Traces, TraceAnalytics, ServiceMap
   ────────────────────────────────────────────────────────────────── */

interface TimeRangeState {
  timeRange: string
  setTimeRange: (tr: string) => void
}

export const useTimeRangeStore = create<TimeRangeState>((set) => ({
  timeRange: '1h',
  setTimeRange: (timeRange) => set({ timeRange }),
}))

/* ──────────────────────────────────────────────────────────────────
   SHARED TRACES HOOK

   queryKey: ['traces-shared', timeRange]

   All trace-related pages share this queryKey.
   React Query deduplicates requests with the same key so
   navigating between Traces → Analytics → ServiceMap is instant.
   ────────────────────────────────────────────────────────────────── */

export function useTracesData() {
  const token     = useAuthStore((s) => s.token)
  const timeRange = useTimeRangeStore((s) => s.timeRange)

  const query = useQuery({
    queryKey: ['traces-shared', timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = resolveTimeParams(timeRange)
      const res = await fetch(`/api/traces?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to fetch traces')
      return res.json() as Promise<{ traces: JaegerTrace[] }>
    },
    enabled: !!token,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  })

  return {
    traces: (query.data?.traces || []) as JaegerTrace[],
    timeRange,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
    refetch: query.refetch,
  }
}
