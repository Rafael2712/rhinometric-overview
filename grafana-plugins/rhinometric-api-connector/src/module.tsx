import React from 'react';
import { AppRootProps } from '@grafana/data';
import { APIConnectorPage } from './components/APIConnectorPage';

export class App extends React.PureComponent<AppRootProps> {
  render() {
    return <APIConnectorPage />;
  }
}
