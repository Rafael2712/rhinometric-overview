import React, { useState, useEffect } from 'react';
import { AppRootProps } from '@grafana/data';
import { Button, useStyles2, Field, Input, Select } from '@grafana/ui';
import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

const API_BASE = 'http://localhost:8001';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  panels: any[];
}

interface DashboardPanel {
  id: string;
  title: string;
  type: string;
  datasource: string;
  targets: any[];
  gridPos: { x: number; y: number; w: number; h: number };
}

export const RootPage: React.FC<AppRootProps> = () => {
  const styles = useStyles2(getStyles);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [panels, setPanels] = useState<DashboardPanel[]>([]);
  const [dashboardName, setDashboardName] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/templates`);
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  const loadTemplate = async (templateId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/templates/${templateId}`);
      const template = await response.json();
      setPanels(template.panels || []);
      setDashboardName(template.name);
    } catch (error) {
      console.error('Error loading template:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveDashboard = async () => {
    try {
      setLoading(true);
      const payload = {
        name: dashboardName,
        panels: panels,
        tags: ['rhinometric', 'custom']
      };
      
      const response = await fetch(`${API_BASE}/api/dashboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('rhinometric-token') || ''}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert('Dashboard saved successfully!');
      } else {
        alert('Error saving dashboard');
      }
    } catch (error) {
      console.error('Error saving dashboard:', error);
      alert('Error saving dashboard');
    } finally {
      setLoading(false);
    }
  };

  const addPanel = () => {
    const newPanel: DashboardPanel = {
      id: `panel-${Date.now()}`,
      title: 'New Panel',
      type: 'graph',
      datasource: 'Prometheus',
      targets: [],
      gridPos: { x: 0, y: panels.length * 8, w: 12, h: 8 }
    };
    setPanels([...panels, newPanel]);
  };

  const removePanel = (panelId: string) => {
    setPanels(panels.filter(p => p.id !== panelId));
  };

  const templateOptions = templates.map(t => ({
    label: t.name,
    value: t.id,
    description: t.description
  }));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🏗️ Dashboard Builder</h1>
        <p>Create custom dashboards visually</p>
      </div>

      <div className={styles.content}>
        <div className={styles.sidebar}>
          <Field label="Select Template">
            <Select
              options={templateOptions}
              value={selectedTemplate}
              onChange={(option) => {
                setSelectedTemplate(option.value || '');
                if (option.value) {
                  loadTemplate(option.value);
                }
              }}
              placeholder="Choose a template..."
            />
          </Field>

          <Field label="Dashboard Name">
            <Input
              value={dashboardName}
              onChange={(e) => setDashboardName(e.currentTarget.value)}
              placeholder="My Dashboard"
            />
          </Field>

          <div className={styles.actions}>
            <Button onClick={addPanel} variant="secondary" fullWidth>
              ➕ Add Panel
            </Button>
            <Button onClick={saveDashboard} variant="primary" fullWidth disabled={loading || !dashboardName}>
              💾 Save Dashboard
            </Button>
          </div>
        </div>

        <div className={styles.canvas}>
          <h3>Dashboard Preview</h3>
          {panels.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No panels yet. Select a template or add panels manually.</p>
            </div>
          ) : (
            <div className={styles.panelGrid}>
              {panels.map(panel => (
                <div key={panel.id} className={styles.panel}>
                  <div className={styles.panelHeader}>
                    <span>{panel.title}</span>
                    <button onClick={() => removePanel(panel.id)} className={styles.removeBtn}>
                      ❌
                    </button>
                  </div>
                  <div className={styles.panelBody}>
                    <p>Type: {panel.type}</p>
                    <p>Datasource: {panel.datasource}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const getStyles = (theme: GrafanaTheme2) => ({
  container: css`
    padding: ${theme.spacing(2)};
    background: ${theme.colors.background.primary};
    min-height: 100vh;
  `,
  header: css`
    margin-bottom: ${theme.spacing(3)};
    h1 {
      color: ${theme.colors.text.primary};
      margin-bottom: ${theme.spacing(1)};
    }
    p {
      color: ${theme.colors.text.secondary};
    }
  `,
  content: css`
    display: flex;
    gap: ${theme.spacing(2)};
  `,
  sidebar: css`
    width: 300px;
    background: ${theme.colors.background.secondary};
    padding: ${theme.spacing(2)};
    border-radius: ${theme.shape.borderRadius()};
  `,
  actions: css`
    margin-top: ${theme.spacing(3)};
    display: flex;
    flex-direction: column;
    gap: ${theme.spacing(1)};
  `,
  canvas: css`
    flex: 1;
    background: ${theme.colors.background.secondary};
    padding: ${theme.spacing(2)};
    border-radius: ${theme.shape.borderRadius()};
    h3 {
      margin-bottom: ${theme.spacing(2)};
      color: ${theme.colors.text.primary};
    }
  `,
  emptyState: css`
    text-align: center;
    padding: ${theme.spacing(4)};
    color: ${theme.colors.text.secondary};
  `,
  panelGrid: css`
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: ${theme.spacing(2)};
  `,
  panel: css`
    background: ${theme.colors.background.primary};
    border: 1px solid ${theme.colors.border.weak};
    border-radius: ${theme.shape.borderRadius()};
    overflow: hidden;
  `,
  panelHeader: css`
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: ${theme.spacing(1.5)};
    background: ${theme.colors.background.canvas};
    border-bottom: 1px solid ${theme.colors.border.weak};
    font-weight: bold;
  `,
  panelBody: css`
    padding: ${theme.spacing(1.5)};
    p {
      margin: ${theme.spacing(0.5)} 0;
      color: ${theme.colors.text.secondary};
      font-size: ${theme.typography.bodySmall.fontSize};
    }
  `,
  removeBtn: css`
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    opacity: 0.7;
    &:hover {
      opacity: 1;
    }
  `
});
