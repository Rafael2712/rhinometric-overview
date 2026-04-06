/* eslint-disable */
import { create } from 'zustand'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/auth/store'
import type { JaegerTrace } from '../utils/traceAnalysis'

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

export const TIME_RANGE_OPTIONS = [
  { value: '15m', label: 'Last 15m' },
  { value: '30m', label: 'Last 30m' },
  { value: '1h',  label: 'Last 1h' },
  { value: '6h',  label: 'Last 6h' },
  { value: '24h', label: 'Last 24h' },
  { value: '3d',  label: 'Last 3d' },
] as const

/* ──────────────────────────────────────────────────────────────────
   SHARED TRACES HOOK

   queryKey: ['traces-shared', timeRange]

   All trace-related pages use this queryKey for the base (unfiltered)
   dataset. React Query deduplicates requests and shares cache entries
   with the same queryKey, so navigating between pages is instant
   when staleTime (30 s) hasn't expired.
   ────────────────────────────────────────────────────────────────── */

export function useTracesData() {
  const token  = useAuthStore((s) => s.token)
  const timeRange = useTimeRangeStore((s) => s.timeRange)

  const query = useQuery({
    queryKey: ['traces-shared', timeRange],
    queryFn: async () => {
      if (!token) throw new Error('No token')
      const params = new URLSearchParams({ limit: '100', lookback: timeRange })
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
