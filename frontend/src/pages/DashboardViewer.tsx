import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { PanelRenderer } from '../components/PanelRenderer';
import { useAuthStore } from '../lib/auth/store';
import { RefreshCw } from 'lucide-react';

interface Panel {
  id: number;
  title: string;
  type: string;
  gridPos: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
}

interface Dashboard {
  uid: string;
  title: string;
  slug: string;
  tags: string[];
  panels: Panel[];
}

type TimeRange = {
  label: string;
  from: string;
  to: string;
};

type RefreshInterval = {
  label: string;
  value: number; // milliseconds, 0 = off
};

const TIME_RANGES: TimeRange[] = [
  { label: 'Last 1 hour', from: 'now-1h', to: 'now' },
  { label: 'Last 6 hours', from: 'now-6h', to: 'now' },
  { label: 'Last 24 hours', from: 'now-24h', to: 'now' },
  { label: 'Last 7 days', from: 'now-7d', to: 'now' },
  { label: 'Last 30 days', from: 'now-30d', to: 'now' },
];

const REFRESH_INTERVALS: RefreshInterval[] = [
  { label: 'Off', value: 0 },
  { label: '5s', value: 5000 },
  { label: '10s', value: 10000 },
  { label: '15s', value: 15000 },
  { label: '30s', value: 30000 },
  { label: '1m', value: 60000 },
  { label: '5m', value: 300000 },
  { label: '10m', value: 600000 },
  { label: '15m', value: 900000 },
  { label: '30m', value: 1800000 },
];

// Default: 30s auto-refresh (ensures Grafana template vars reload on open)
const DEFAULT_REFRESH = REFRESH_INTERVALS[4]; // 30s — ensure fresh data on load

// Strip leading numbering like "01 - "
const cleanTitle = (title: string) => title.replace(/^\d+\s*-\s*/, '');

export const DashboardViewer: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRange, setSelectedRange] = useState<TimeRange>(TIME_RANGES[1]);
  const [refreshInterval, setRefreshInterval] = useState<RefreshInterval>(DEFAULT_REFRESH);
  const [refreshKey, setRefreshKey] = useState(0);
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (uid) {
      loadDashboard();
    }
  }, [uid]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/dashboards/${uid}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to load dashboard');
      const data = await response.json();
      const dashboardData = data.dashboard || data;
      setDashboard(dashboardData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh: increment refreshKey to force iframe reload
  useEffect(() => {
    if (refreshInterval.value === 0) return;
    const timer = setInterval(() => {
      setRefreshKey(prev => prev + 1);
      
    }, refreshInterval.value);
    return () => clearInterval(timer);
  }, [refreshInterval]);

  const handleTimeRangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const range = TIME_RANGES.find(r => r.label === event.target.value);
    if (range) setSelectedRange(range);
  };

  const handleRefreshChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const interval = REFRESH_INTERVALS.find(r => r.label === event.target.value);
    if (interval) setRefreshInterval(interval);
  };

  const handleManualRefresh = useCallback(() => {
    setRefreshKey(prev => prev + 1);
    
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="card bg-error/10 border-error">
          <p className="text-error">{error}</p>
        </div>
      </div>
    );
  }

  if (!dashboard) return null;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-3xl font-bold text-white">{cleanTitle(dashboard.title)}</h1>

        <div className="flex items-center gap-3">
          {/* Manual refresh button */}
          <button
            onClick={handleManualRefresh}
            className="btn-outline px-3 py-2 flex items-center gap-2 text-sm"
            title="Refresh now"
          >
            <RefreshCw className={`w-4 h-4 ${refreshInterval.value > 0 ? 'animate-spin-slow' : ''}`} />
          </button>

          {/* Auto-refresh interval selector */}
          <div className="flex items-center gap-2">
            <select
              value={refreshInterval.label}
              onChange={handleRefreshChange}
              className="input w-auto min-w-[100px] text-sm"
              title="Auto-refresh interval"
            >
              {REFRESH_INTERVALS.map(interval => (
                <option key={interval.label} value={interval.label}>
                  {interval.label === 'Off' ? 'Auto: Off' : `Auto: ${interval.label}`}
                </option>
              ))}
            </select>
          </div>

          {/* Time range selector */}
          <select
            value={selectedRange.label}
            onChange={handleTimeRangeChange}
            className="input w-auto min-w-[180px] text-sm"
          >
            {TIME_RANGES.map(range => (
              <option key={range.label} value={range.label}>
                {range.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Panels Grid */}
      <div className="grid grid-cols-24 gap-4">
        {dashboard.panels.map(panel => (
          <div
            key={panel.id}
            style={{
              gridColumn: `span ${panel.gridPos.w}`,
              gridRow: `span ${Math.ceil(panel.gridPos.h / 2)}`,
            }}
          >
            <PanelRenderer
              uid={dashboard.uid}
              panelId={panel.id}
              title={panel.title}
              from={selectedRange.from}
              to={selectedRange.to}
              refresh={refreshInterval.value > 0 ? refreshInterval.label : undefined}
              refreshKey={refreshKey}
            />
          </div>
        ))}
      </div>
    </div>
  );
};