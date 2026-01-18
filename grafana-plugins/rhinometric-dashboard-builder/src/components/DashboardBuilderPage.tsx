import React, { useState } from 'react';
import { css } from 'emotion';
import { Button, Input, Select, Field, FieldSet, Card, Icon, useStyles2 } from '@grafana/ui';
import { GrafanaTheme2 } from '@grafana/data';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';

const getStyles = (theme: GrafanaTheme2) => ({
  container: css`
    padding: ${theme.spacing(3)};
    background: ${theme.colors.background.primary};
  `,
  header: css`
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: ${theme.spacing(3)};
    padding-bottom: ${theme.spacing(2)};
    border-bottom: 1px solid ${theme.colors.border.weak};
  `,
  title: css`
    font-size: ${theme.typography.h2.fontSize};
    font-weight: ${theme.typography.h2.fontWeight};
    color: #00d4aa;
    display: flex;
    align-items: center;
    gap: ${theme.spacing(1)};
  `,
  logo: css`
    font-weight: 700;
    color: #00d4aa;
  `,
  sidebar: css`
    width: 300px;
    padding: ${theme.spacing(2)};
    background: ${theme.colors.background.secondary};
    border-radius: ${theme.shape.borderRadius(1)};
  `,
  canvas: css`
    flex: 1;
    margin-left: ${theme.spacing(3)};
    padding: ${theme.spacing(2)};
    background: ${theme.colors.background.canvas};
    border: 2px dashed ${theme.colors.border.weak};
    border-radius: ${theme.shape.borderRadius(1)};
    min-height: 600px;
  `,
  mainContent: css`
    display: flex;
  `,
  panelCard: css`
    cursor: pointer;
    margin-bottom: ${theme.spacing(2)};
    transition: all 0.2s;
    &:hover {
      border-color: #00d4aa;
      box-shadow: 0 0 10px rgba(0, 212, 170, 0.3);
    }
  `,
  panel: css`
    background: ${theme.colors.background.secondary};
    border: 1px solid ${theme.colors.border.medium};
    border-radius: ${theme.shape.borderRadius(1)};
    padding: ${theme.spacing(2)};
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
  `,
  buttonGroup: css`
    display: flex;
    gap: ${theme.spacing(1)};
  `,
});

interface Panel {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
  type: string;
  title: string;
}

export const DashboardBuilderPage: React.FC = () => {
  const styles = useStyles2(getStyles);
  const [dashboardName, setDashboardName] = useState('New Dashboard');
  const [panels, setPanels] = useState<Panel[]>([]);
  const [nextId, setNextId] = useState(1);

  const panelTypes = [
    { label: 'Time Series', value: 'timeseries', icon: 'graph-bar' },
    { label: 'Stat', value: 'stat', icon: 'calculator-alt' },
    { label: 'Table', value: 'table', icon: 'table' },
    { label: 'Gauge', value: 'gauge', icon: 'circle' },
    { label: 'Bar Chart', value: 'barchart', icon: 'chart-line' },
    { label: 'Pie Chart', value: 'piechart', icon: 'circle-slice-8' },
  ];

  const addPanel = (type: string) => {
    const newPanel: Panel = {
      i: `panel-${nextId}`,
      x: (panels.length * 2) % 12,
      y: Math.floor(panels.length / 6) * 4,
      w: 4,
      h: 4,
      type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Panel ${nextId}`,
    };
    setPanels([...panels, newPanel]);
    setNextId(nextId + 1);
  };

  const removePanel = (id: string) => {
    setPanels(panels.filter((p) => p.i !== id));
  };

  const saveDashboard = async () => {
    const dashboard = {
      title: dashboardName,
      panels: panels.map((panel, idx) => ({
        id: idx + 1,
        type: panel.type,
        title: panel.title,
        gridPos: {
          x: panel.x,
          y: panel.y,
          w: panel.w,
          h: panel.h,
        },
      })),
    };

    try {
      const response = await fetch('http://localhost:8001/api/dashboards/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dashboard),
      });
      
      if (response.ok) {
        alert('✅ Dashboard saved successfully!');
      }
    } catch (error) {
      alert('❌ Error saving dashboard');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          <span className={styles.logo}>RHINOMETRIC</span>
          <Icon name="apps" size="xl" />
          Dashboard Builder
        </div>
        <div className={styles.buttonGroup}>
          <Button variant="secondary" icon="eye">
            Preview
          </Button>
          <Button variant="primary" icon="save" onClick={saveDashboard}>
            Save Dashboard
          </Button>
        </div>
      </div>

      <FieldSet>
        <Field label="Dashboard Name">
          <Input
            value={dashboardName}
            onChange={(e) => setDashboardName(e.currentTarget.value)}
            placeholder="Enter dashboard name..."
          />
        </Field>
      </FieldSet>

      <div className={styles.mainContent}>
        <div className={styles.sidebar}>
          <h3>Panel Types</h3>
          {panelTypes.map((type) => (
            <Card
              key={type.value}
              className={styles.panelCard}
              onClick={() => addPanel(type.value)}
            >
              <Card.Heading>
                <Icon name={type.icon as any} /> {type.label}
              </Card.Heading>
              <Card.Description>Click to add to dashboard</Card.Description>
            </Card>
          ))}
        </div>

        <div className={styles.canvas}>
          <h3>Dashboard Canvas ({panels.length} panels)</h3>
          <GridLayout
            className="layout"
            cols={12}
            rowHeight={30}
            width={1200}
            onLayoutChange={(layout) => {
              const updatedPanels = panels.map((panel) => {
                const layoutItem = layout.find((l) => l.i === panel.i);
                return layoutItem
                  ? { ...panel, x: layoutItem.x, y: layoutItem.y, w: layoutItem.w, h: layoutItem.h }
                  : panel;
              });
              setPanels(updatedPanels);
            }}
          >
            {panels.map((panel) => (
              <div key={panel.i} data-grid={panel} className={styles.panel}>
                <strong>{panel.title}</strong>
                <p>{panel.type}</p>
                <Button
                  variant="destructive"
                  size="sm"
                  icon="trash-alt"
                  onClick={() => removePanel(panel.i)}
                >
                  Remove
                </Button>
              </div>
            ))}
          </GridLayout>
        </div>
      </div>
    </div>
  );
};
