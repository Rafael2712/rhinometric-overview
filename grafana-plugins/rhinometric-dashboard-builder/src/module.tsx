import React from 'react';
import { AppRootProps } from '@grafana/data';
import { DashboardBuilderPage } from './components/DashboardBuilderPage';

export class App extends React.PureComponent<AppRootProps> {
  render() {
    return <DashboardBuilderPage />;
  }
}
