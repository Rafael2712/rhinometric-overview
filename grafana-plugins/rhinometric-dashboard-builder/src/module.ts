/**
 * RHINOMETRIC v2.4.0 - Dashboard Builder Plugin
 * Plugin entry point for Grafana
 */

import { PanelPlugin } from '@grafana/data';
import { DashboardBuilderPanel } from './DashboardBuilderPanel';

export const plugin = new PanelPlugin(DashboardBuilderPanel).setPanelOptions(builder => {
  return builder
    .addTextInput({
      path: 'backendUrl',
      name: 'Backend URL',
      description: 'Dashboard Builder backend URL',
      defaultValue: 'http://localhost:8001/api',
    })
    .addBooleanSwitch({
      path: 'enableAutoSave',
      name: 'Enable Auto-Save',
      description: 'Automatically save dashboard changes',
      defaultValue: false,
    });
});
