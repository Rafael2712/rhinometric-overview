import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { PanelRenderer } from '../components/PanelRenderer';
import { useAuthStore } from '../lib/auth/store';

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

const TIME_RANGES: TimeRange[] = [
  { label: 'Last 1 hour', from: 'now-1h', to: 'now' },
  { label: 'Last 6 hours', from: 'now-6h', to: 'now' },
  { label: 'Last 24 hours', from: 'now-24h', to: 'now' },
  { label: 'Last 7 days', from: 'now-7d', to: 'now' },
  { label: 'Last 30 days', from: 'now-30d', to: 'now' },
];

export const DashboardViewer: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRange, setSelectedRange] = useState<TimeRange>(TIME_RANGES[1]); // Default: 6h
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
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to load dashboard');
      }
      
      const data = await response.json();
      // Grafana API returns { dashboard: {...}, meta: {...} }
      const dashboardData = data.dashboard || data;
      setDashboard(dashboardData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleTimeRangeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const range = TIME_RANGES.find(r => r.label === event.target.value);
    if (range) {
      setSelectedRange(range);
    }
  };

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

  if (!dashboard) {
    return null;
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">{dashboard.title}</h1>
        
        <select
          value={selectedRange.label}
          onChange={handleTimeRangeChange}
          className="input w-auto min-w-[200px]"
        >
          {TIME_RANGES.map(range => (
            <option key={range.label} value={range.label}>
              {range.label}
            </option>
          ))}
        </select>
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
            />
          </div>
        ))}
      </div>
    </div>
  );
};
