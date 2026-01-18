/**
 * RHINOMETRIC v2.4.0 - API Connector Plugin
 * ==========================================
 * 
 * Grafana plugin for visual datasource configuration.
 */

import { PanelPlugin } from '@grafana/data';
import { APIConnectorPanel } from './components/APIConnectorPanel';
import { APIConnectorOptions } from './types';

export const plugin = new PanelPlugin<APIConnectorOptions>(APIConnectorPanel).setPanelOptions((builder) => {
  return builder
    .addTextInput({
      path: 'apiUrl',
      name: 'API Connector URL',
      description: 'URL of the RHINOMETRIC API Connector backend',
      defaultValue: 'http://localhost:8000',
    })
    .addBooleanSwitch({
      path: 'autoRefresh',
      name: 'Auto-refresh datasources',
      description: 'Automatically refresh datasource list',
      defaultValue: true,
    })
    .addNumberInput({
      path: 'refreshInterval',
      name: 'Refresh interval (seconds)',
      description: 'Interval to refresh datasource list',
      defaultValue: 30,
    });
});
