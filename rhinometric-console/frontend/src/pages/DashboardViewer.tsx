import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, CircularProgress, Alert, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { apiClient } from '../services/api';
import { PanelRenderer } from '../components/PanelRenderer';

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

  useEffect(() => {
    if (uid) {
      loadDashboard();
    }
  }, [uid]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/api/dashboards/${uid}`);
      setDashboard(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleTimeRangeChange = (event: any) => {
    const range = TIME_RANGES.find(r => r.label === event.target.value);
    if (range) {
      setSelectedRange(range);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{dashboard.title}</Typography>
        
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel id="timerange-label">Time Range</InputLabel>
          <Select
            labelId="timerange-label"
            value={selectedRange.label}
            label="Time Range"
            onChange={handleTimeRangeChange}
          >
            {TIME_RANGES.map(range => (
              <MenuItem key={range.label} value={range.label}>
                {range.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Panels Grid */}
      <Box
        display="grid"
        gridTemplateColumns="repeat(24, 1fr)"
        gap={2}
        sx={{
          '& > div': {
            backgroundColor: 'background.paper',
            borderRadius: 1,
            overflow: 'hidden',
            boxShadow: 1,
          }
        }}
      >
        {dashboard.panels.map(panel => (
          <Box
            key={panel.id}
            sx={{
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
          </Box>
        ))}
      </Box>
    </Box>
  );
};
