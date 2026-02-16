import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export const TEMPLATES = [
  {
    id: 'system-overview',
    name: 'System Overview',
    description: 'Complete system monitoring with CPU, Memory, Disk, Network',
    panels: 9,
    category: 'Infrastructure',
    icon: '🖥️',
    color: 'bg-blue-500',
  },
  {
    id: 'application-performance',
    name: 'Application Performance',
    description: 'Monitor API performance, request rates, errors, latency',
    panels: 7,
    category: 'Application',
    icon: '⚡',
    color: 'bg-purple-500',
  },
  {
    id: 'database-monitoring',
    name: 'Database Monitoring',
    description: 'PostgreSQL monitoring with connections, queries, performance',
    panels: 6,
    category: 'Database',
    icon: '🗄️',
    color: 'bg-green-500',
  },
  {
    id: 'network-traffic',
    name: 'Network Traffic',
    description: 'Network monitoring with bandwidth, errors, packets',
    panels: 6,
    category: 'Network',
    icon: '🌐',
    color: 'bg-cyan-500',
  },
  {
    id: 'container-monitoring',
    name: 'Container Monitoring',
    description: 'Docker/K8s monitoring with resource usage per container',
    panels: 8,
    category: 'Containers',
    icon: '🐳',
    color: 'bg-indigo-500',
  },
  {
    id: 'anomaly-detection',
    name: 'AI Anomaly Detection',
    description: 'View anomalies detected by ML models',
    panels: 5,
    category: 'AI/ML',
    icon: '🤖',
    color: 'bg-pink-500',
  },
];

export const PANEL_TYPES = [
  { value: 'stat', label: 'Stat', icon: '📊' },
  { value: 'graph', label: 'Graph', icon: '📈' },
  { value: 'gauge', label: 'Gauge', icon: '🎯' },
  { value: 'table', label: 'Table', icon: '📋' },
  { value: 'pie_chart', label: 'Pie Chart', icon: '🥧' },
  { value: 'heatmap', label: 'Heatmap', icon: '🗺️' },
];

export const REFRESH_INTERVALS = [
  { value: '5s', label: '5 seconds' },
  { value: '10s', label: '10 seconds' },
  { value: '30s', label: '30 seconds' },
  { value: '1m', label: '1 minute' },
  { value: '5m', label: '5 minutes' },
  { value: '15m', label: '15 minutes' },
  { value: '30m', label: '30 minutes' },
  { value: '1h', label: '1 hour' },
];

export const TIME_RANGES = [
  { value: { from: 'now-5m', to: 'now' }, label: 'Last 5 minutes' },
  { value: { from: 'now-15m', to: 'now' }, label: 'Last 15 minutes' },
  { value: { from: 'now-30m', to: 'now' }, label: 'Last 30 minutes' },
  { value: { from: 'now-1h', to: 'now' }, label: 'Last 1 hour' },
  { value: { from: 'now-3h', to: 'now' }, label: 'Last 3 hours' },
  { value: { from: 'now-6h', to: 'now' }, label: 'Last 6 hours' },
  { value: { from: 'now-12h', to: 'now' }, label: 'Last 12 hours' },
  { value: { from: 'now-24h', to: 'now' }, label: 'Last 24 hours' },
  { value: { from: 'now-7d', to: 'now' }, label: 'Last 7 days' },
  { value: { from: 'now-30d', to: 'now' }, label: 'Last 30 days' },
];
