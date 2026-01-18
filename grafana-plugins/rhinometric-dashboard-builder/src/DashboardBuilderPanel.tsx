/**
 * RHINOMETRIC v2.4.0 - Dashboard Builder Panel
 * ==============================================
 * 
 * Visual dashboard creator embedded in Grafana.
 * 
 * Features:
 * - Drag-and-drop grid layout
 * - Template library (Infrastructure, API, Messaging, ESG)
 * - Real-time preview
 * - Save to backend (PostgreSQL)
 * - Export to Grafana JSON
 * 
 * Security:
 * - License validation required
 * - JWT authentication
 * - 100% on-premise
 */

import React, { useState, useEffect } from 'react';
import { PanelProps } from '@grafana/data';
import { Button, useStyles2, Alert, Input, Field, Select, TagsInput, Modal } from '@grafana/ui';
import { css } from '@emotion/css';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

// ============================================================================
// TYPES
// ============================================================================

interface DashboardPanel {
  id: number;
  type: string; // graph, gauge, table, stat, heatmap
  title: string;
  datasource?: string;
  query?: string;
  x: number;
  y: number;
  width: number; // Grid width (1-24)
  height: number; // Grid height
  options: Record<string, any>;
}

interface DashboardConfig {
  title: string;
  description?: string;
  tags: string[];
  template?: string;
  panels: DashboardPanel[];
  time_range: { from: string; to: string };
  refresh: string;
  variables: any[];
}

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  panels: DashboardPanel[];
}

interface BackendResponse {
  success: boolean;
  message: string;
  dashboard_id?: string;
  metadata?: any;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const BACKEND_URL = 'http://localhost:8001/api';

const PANEL_TYPES = [
  { label: '📊 Graph', value: 'graph' },
  { label: '🎯 Gauge', value: 'gauge' },
  { label: '📋 Table', value: 'table' },
  { label: '🔢 Stat', value: 'stat' },
  { label: '🌡️ Heatmap', value: 'heatmap' },
  { label: '📈 Bar Chart', value: 'barchart' },
  { label: '🥧 Pie Chart', value: 'piechart' },
  { label: '📝 Text', value: 'text' },
];

const DATASOURCES = [
  { label: 'Prometheus', value: 'Prometheus' },
  { label: 'Loki', value: 'Loki' },
  { label: 'Tempo', value: 'Tempo' },
  { label: 'PostgreSQL', value: 'PostgreSQL' },
  { label: 'Redis', value: 'Redis' },
];

const TIME_RANGES = [
  { label: 'Last 5 minutes', value: 'now-5m' },
  { label: 'Last 15 minutes', value: 'now-15m' },
  { label: 'Last 30 minutes', value: 'now-30m' },
  { label: 'Last 1 hour', value: 'now-1h' },
  { label: 'Last 6 hours', value: 'now-6h' },
  { label: 'Last 12 hours', value: 'now-12h' },
  { label: 'Last 24 hours', value: 'now-24h' },
  { label: 'Last 7 days', value: 'now-7d' },
];

const REFRESH_INTERVALS = [
  { label: 'No refresh', value: '' },
  { label: '10s', value: '10s' },
  { label: '30s', value: '30s' },
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
];

// ============================================================================
// STYLES
// ============================================================================

const getStyles = () => ({
  container: css`
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 600px;
    border-radius: 8px;
  `,
  header: css`
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    backdrop-filter: blur(10px);
  `,
  title: css`
    font-size: 24px;
    font-weight: bold;
    color: white;
    display: flex;
    align-items: center;
    gap: 10px;
  `,
  logo: css`
    font-size: 32px;
  `,
  buttonGroup: css`
    display: flex;
    gap: 10px;
  `,
  content: css`
    display: flex;
    gap: 20px;
  `,
  sidebar: css`
    width: 300px;
    background: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    max-height: 800px;
    overflow-y: auto;
  `,
  canvas: css`
    flex: 1;
    background: white;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    min-height: 600px;
  `,
  section: css`
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e0e0e0;
  `,
  sectionTitle: css`
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #333;
  `,
  templateGrid: css`
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
  `,
  templateCard: css`
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      border-color: #667eea;
      background: #f5f5ff;
      transform: translateY(-2px);
    }
  `,
  templateIcon: css`
    font-size: 24px;
    margin-bottom: 5px;
  `,
  templateName: css`
    font-weight: 600;
    color: #333;
    margin-bottom: 3px;
  `,
  templateDesc: css`
    font-size: 12px;
    color: #666;
  `,
  gridContainer: css`
    border: 2px dashed #e0e0e0;
    border-radius: 8px;
    min-height: 500px;
    background: #fafafa;
    position: relative;
  `,
  gridItem: css`
    background: white;
    border: 2px solid #667eea;
    border-radius: 6px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    cursor: move;
    display: flex;
    flex-direction: column;
    
    &:hover {
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
  `,
  panelHeader: css`
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e0e0e0;
  `,
  panelTitle: css`
    font-weight: 600;
    color: #333;
    font-size: 14px;
  `,
  panelType: css`
    font-size: 18px;
  `,
  panelContent: css`
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 12px;
  `,
  deleteButton: css`
    padding: 2px 8px;
    font-size: 12px;
    background: #ff4444;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    
    &:hover {
      background: #cc0000;
    }
  `,
  emptyState: css`
    text-align: center;
    padding: 60px 20px;
    color: #999;
  `,
  emptyIcon: css`
    font-size: 64px;
    margin-bottom: 15px;
  `,
  alert: css`
    margin-bottom: 15px;
  `,
});

// ============================================================================
// COMPONENT
// ============================================================================

export const DashboardBuilderPanel: React.FC<PanelProps> = ({ width, height, data }) => {
  const styles = useStyles2(getStyles);
  
  // State
  const [templates, setTemplates] = useState<Record<string, Template>>({});
  const [dashboard, setDashboard] = useState<DashboardConfig>({
    title: 'New Dashboard',
    description: '',
    tags: [],
    panels: [],
    time_range: { from: 'now-6h', to: 'now' },
    refresh: '30s',
    variables: [],
  });
  const [selectedPanel, setSelectedPanel] = useState<DashboardPanel | null>(null);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // ========================================================================
  // EFFECTS
  // ========================================================================

  useEffect(() => {
    loadTemplates();
  }, []);

  // ========================================================================
  // API CALLS
  // ========================================================================

  const loadTemplates = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/templates`);
      const data = await response.json();
      setTemplates(data.templates);
      setAlert({ type: 'success', message: `Loaded ${data.count} templates` });
    } catch (error) {
      console.error('Error loading templates:', error);
      setAlert({ type: 'error', message: 'Failed to load templates' });
    }
  };

  const saveDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/dashboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add real JWT token
          'Authorization': 'Bearer mock-token',
        },
        body: JSON.stringify({
          dashboard: dashboard,
          overwrite: false,
        }),
      });

      const result: BackendResponse = await response.json();

      if (result.success) {
        setAlert({ type: 'success', message: result.message });
        setShowSaveModal(false);
      } else {
        setAlert({ type: 'error', message: result.message });
      }
    } catch (error) {
      console.error('Error saving dashboard:', error);
      setAlert({ type: 'error', message: 'Failed to save dashboard' });
    } finally {
      setLoading(false);
    }
  };

  const exportDashboard = () => {
    const json = JSON.stringify(dashboard, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${dashboard.title.toLowerCase().replace(/ /g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setAlert({ type: 'success', message: 'Dashboard exported successfully' });
  };

  // ========================================================================
  // DASHBOARD OPERATIONS
  // ========================================================================

  const loadTemplate = (templateId: string) => {
    const template = templates[templateId];
    if (!template) return;

    setDashboard({
      ...dashboard,
      title: template.name,
      description: template.description,
      tags: [template.category],
      template: templateId,
      panels: [...template.panels],
    });

    setAlert({ type: 'success', message: `Template "${template.name}" loaded` });
  };

  const addPanel = () => {
    const newPanel: DashboardPanel = {
      id: dashboard.panels.length + 1,
      type: 'graph',
      title: `Panel ${dashboard.panels.length + 1}`,
      datasource: 'Prometheus',
      query: '',
      x: 0,
      y: dashboard.panels.length * 8,
      width: 12,
      height: 8,
      options: {},
    };

    setDashboard({
      ...dashboard,
      panels: [...dashboard.panels, newPanel],
    });
  };

  const updatePanel = (panelId: number, updates: Partial<DashboardPanel>) => {
    setDashboard({
      ...dashboard,
      panels: dashboard.panels.map(p => p.id === panelId ? { ...p, ...updates } : p),
    });
  };

  const deletePanel = (panelId: number) => {
    setDashboard({
      ...dashboard,
      panels: dashboard.panels.filter(p => p.id !== panelId),
    });
    setSelectedPanel(null);
  };

  const clearDashboard = () => {
    setDashboard({
      title: 'New Dashboard',
      description: '',
      tags: [],
      panels: [],
      time_range: { from: 'now-6h', to: 'now' },
      refresh: '30s',
      variables: [],
    });
    setAlert({ type: 'info', message: 'Dashboard cleared' });
  };

  // ========================================================================
  // GRID LAYOUT
  // ========================================================================

  const onLayoutChange = (layout: any[]) => {
    setDashboard({
      ...dashboard,
      panels: dashboard.panels.map(panel => {
        const item = layout.find(l => l.i === String(panel.id));
        if (item) {
          return { ...panel, x: item.x, y: item.y, width: item.w, height: item.h };
        }
        return panel;
      }),
    });
  };

  // ========================================================================
  // RENDER HELPERS
  // ========================================================================

  const getPanelIcon = (type: string) => {
    const icons: Record<string, string> = {
      graph: '📊',
      gauge: '🎯',
      table: '📋',
      stat: '🔢',
      heatmap: '🌡️',
      barchart: '📈',
      piechart: '🥧',
      text: '📝',
    };
    return icons[type] || '📊';
  };

  // ========================================================================
  // RENDER
  // ========================================================================

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.title}>
          <span className={styles.logo}>🎨</span>
          <span>RHINOMETRIC Dashboard Builder</span>
        </div>
        <div className={styles.buttonGroup}>
          <Button onClick={addPanel} variant="primary">+ Add Panel</Button>
          <Button onClick={clearDashboard} variant="secondary">Clear</Button>
          <Button onClick={exportDashboard} variant="secondary">Export JSON</Button>
          <Button onClick={() => setShowSaveModal(true)} variant="primary">💾 Save</Button>
        </div>
      </div>

      {/* Alert */}
      {alert && (
        <Alert title={alert.message} severity={alert.type} className={styles.alert} onRemove={() => setAlert(null)} />
      )}

      {/* Main Content */}
      <div className={styles.content}>
        {/* Sidebar */}
        <div className={styles.sidebar}>
          {/* Dashboard Settings */}
          <div className={styles.section}>
            <div className={styles.sectionTitle}>⚙️ Dashboard Settings</div>
            <Field label="Title">
              <Input
                value={dashboard.title}
                onChange={(e) => setDashboard({ ...dashboard, title: e.currentTarget.value })}
                placeholder="Dashboard title"
              />
            </Field>
            <Field label="Description">
              <Input
                value={dashboard.description}
                onChange={(e) => setDashboard({ ...dashboard, description: e.currentTarget.value })}
                placeholder="Optional description"
              />
            </Field>
            <Field label="Tags">
              <TagsInput
                tags={dashboard.tags}
                onChange={(tags) => setDashboard({ ...dashboard, tags })}
                placeholder="Add tags"
              />
            </Field>
          </div>

          {/* Templates */}
          <div className={styles.section}>
            <div className={styles.sectionTitle}>📋 Templates</div>
            <div className={styles.templateGrid}>
              {Object.values(templates).map((template) => (
                <div
                  key={template.id}
                  className={styles.templateCard}
                  onClick={() => loadTemplate(template.id)}
                >
                  <div className={styles.templateIcon}>{template.icon}</div>
                  <div className={styles.templateName}>{template.name}</div>
                  <div className={styles.templateDesc}>{template.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Panel Editor (if selected) */}
          {selectedPanel && (
            <div className={styles.section}>
              <div className={styles.sectionTitle}>✏️ Edit Panel</div>
              <Field label="Title">
                <Input
                  value={selectedPanel.title}
                  onChange={(e) => updatePanel(selectedPanel.id, { title: e.currentTarget.value })}
                />
              </Field>
              <Field label="Type">
                <Select
                  options={PANEL_TYPES}
                  value={selectedPanel.type}
                  onChange={(v) => updatePanel(selectedPanel.id, { type: v.value! })}
                />
              </Field>
              <Field label="Datasource">
                <Select
                  options={DATASOURCES}
                  value={selectedPanel.datasource}
                  onChange={(v) => updatePanel(selectedPanel.id, { datasource: v.value! })}
                />
              </Field>
              <Field label="Query">
                <Input
                  value={selectedPanel.query}
                  onChange={(e) => updatePanel(selectedPanel.id, { query: e.currentTarget.value })}
                  placeholder="PromQL, LogQL, SQL..."
                />
              </Field>
              <Button onClick={() => deletePanel(selectedPanel.id)} variant="destructive" size="sm" fullWidth>
                🗑️ Delete Panel
              </Button>
            </div>
          )}
        </div>

        {/* Canvas */}
        <div className={styles.canvas}>
          <div className={styles.sectionTitle}>
            🖼️ Canvas ({dashboard.panels.length} panels)
          </div>
          {dashboard.panels.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>📭</div>
              <div>No panels yet. Click "Add Panel" or load a template to get started.</div>
            </div>
          ) : (
            <GridLayout
              className={styles.gridContainer}
              layout={dashboard.panels.map(p => ({
                i: String(p.id),
                x: p.x,
                y: p.y,
                w: p.width,
                h: p.height,
              }))}
              cols={24}
              rowHeight={30}
              width={width - 350}
              onLayoutChange={onLayoutChange}
              draggableCancel=".no-drag"
            >
              {dashboard.panels.map((panel) => (
                <div key={panel.id} className={styles.gridItem} onClick={() => setSelectedPanel(panel)}>
                  <div className={styles.panelHeader}>
                    <span className={styles.panelTitle}>{panel.title}</span>
                    <span className={styles.panelType}>{getPanelIcon(panel.type)}</span>
                  </div>
                  <div className={styles.panelContent}>
                    <div>
                      <div>{panel.type} panel</div>
                      <div style={{ fontSize: '10px', marginTop: '4px' }}>
                        {panel.datasource} • {panel.query ? panel.query.substring(0, 30) + '...' : 'No query'}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </GridLayout>
          )}
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <Modal title="💾 Save Dashboard" isOpen={showSaveModal} onDismiss={() => setShowSaveModal(false)}>
          <p>Save dashboard "{dashboard.title}" to backend storage?</p>
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <Button onClick={saveDashboard} variant="primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save'}
            </Button>
            <Button onClick={() => setShowSaveModal(false)} variant="secondary">
              Cancel
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};
