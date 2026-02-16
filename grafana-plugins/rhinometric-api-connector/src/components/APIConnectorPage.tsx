import React, { useState, useEffect } from 'react';
import { css } from 'emotion';
import {
  Button,
  Input,
  Select,
  Field,
  FieldSet,
  Card,
  Icon,
  useStyles2,
  Alert,
  Switch,
  TextArea,
} from '@grafana/ui';
import { GrafanaTheme2, SelectableValue } from '@grafana/data';

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
  grid: css`
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: ${theme.spacing(2)};
    margin-bottom: ${theme.spacing(3)};
  `,
  connectorCard: css`
    cursor: pointer;
    transition: all 0.2s;
    &:hover {
      border-color: #00d4aa;
      box-shadow: 0 0 10px rgba(0, 212, 170, 0.3);
    }
  `,
  form: css`
    max-width: 800px;
    margin: 0 auto;
  `,
  buttonGroup: css`
    display: flex;
    gap: ${theme.spacing(1)};
    justify-content: flex-end;
    margin-top: ${theme.spacing(3)};
  `,
  connectionsList: css`
    margin-top: ${theme.spacing(3)};
  `,
  connectionItem: css`
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: ${theme.spacing(2)};
    background: ${theme.colors.background.secondary};
    border-radius: ${theme.shape.borderRadius(1)};
    margin-bottom: ${theme.spacing(1)};
  `,
});

interface Connector {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface Connection {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
}

const connectors: Connector[] = [
  { id: 'aws', name: 'AWS CloudWatch', icon: 'cloud', description: 'Connect to AWS services' },
  { id: 'azure', name: 'Azure Monitor', icon: 'cloud-upload', description: 'Connect to Azure resources' },
  { id: 'kafka', name: 'Apache Kafka', icon: 'exchange-alt', description: 'Stream data from Kafka' },
  { id: 'mqtt', name: 'MQTT', icon: 'rss', description: 'IoT data via MQTT protocol' },
  { id: 'rabbitmq', name: 'RabbitMQ', icon: 'rabbit', description: 'Message queue integration' },
  { id: 'postgres', name: 'PostgreSQL', icon: 'database', description: 'Direct database connection' },
  { id: 'mongodb', name: 'MongoDB', icon: 'layer-group', description: 'NoSQL database connector' },
  { id: 'rest', name: 'REST API', icon: 'plug', description: 'Generic REST API endpoint' },
];

export const APIConnectorPage: React.FC = () => {
  const styles = useStyles2(getStyles);
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/connections');
      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
      }
    } catch (error) {
      console.error('Error loading connections:', error);
    }
  };

  const handleConnectorSelect = (connector: Connector) => {
    setSelectedConnector(connector);
    setFormData({});
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: selectedConnector?.id,
          config: formData,
        }),
      });

      const result = await response.json();
      setTestResult({
        success: response.ok,
        message: result.message || (response.ok ? 'Connection successful!' : 'Connection failed'),
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Error testing connection',
      });
    }
  };

  const handleSaveConnection = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          type: selectedConnector?.id,
          config: formData,
          enabled: true,
        }),
      });

      if (response.ok) {
        alert('✅ Connection saved successfully!');
        setSelectedConnector(null);
        loadConnections();
      }
    } catch (error) {
      alert('❌ Error saving connection');
    }
  };

  const handleDeleteConnection = async (id: string) => {
    if (confirm('Delete this connection?')) {
      try {
        await fetch(`http://localhost:8000/api/connections/${id}`, { method: 'DELETE' });
        loadConnections();
      } catch (error) {
        alert('Error deleting connection');
      }
    }
  };

  const renderForm = () => {
    if (!selectedConnector) return null;

    const commonFields = (
      <>
        <Field label="Connection Name" required>
          <Input
            placeholder="My AWS Connection"
            value={formData.name || ''}
            onChange={(e) => setFormData({ ...formData, name: e.currentTarget.value })}
          />
        </Field>
      </>
    );

    switch (selectedConnector.id) {
      case 'aws':
        return (
          <FieldSet>
            {commonFields}
            <Field label="AWS Region" required>
              <Select
                options={[
                  { label: 'us-east-1', value: 'us-east-1' },
                  { label: 'us-west-2', value: 'us-west-2' },
                  { label: 'eu-west-1', value: 'eu-west-1' },
                ]}
                value={formData.region}
                onChange={(v) => setFormData({ ...formData, region: v.value })}
              />
            </Field>
            <Field label="Access Key ID" required>
              <Input
                type="password"
                value={formData.accessKeyId || ''}
                onChange={(e) => setFormData({ ...formData, accessKeyId: e.currentTarget.value })}
              />
            </Field>
            <Field label="Secret Access Key" required>
              <Input
                type="password"
                value={formData.secretAccessKey || ''}
                onChange={(e) => setFormData({ ...formData, secretAccessKey: e.currentTarget.value })}
              />
            </Field>
          </FieldSet>
        );

      case 'postgres':
        return (
          <FieldSet>
            {commonFields}
            <Field label="Host" required>
              <Input
                placeholder="localhost"
                value={formData.host || ''}
                onChange={(e) => setFormData({ ...formData, host: e.currentTarget.value })}
              />
            </Field>
            <Field label="Port" required>
              <Input
                type="number"
                placeholder="5432"
                value={formData.port || ''}
                onChange={(e) => setFormData({ ...formData, port: e.currentTarget.value })}
              />
            </Field>
            <Field label="Database" required>
              <Input
                value={formData.database || ''}
                onChange={(e) => setFormData({ ...formData, database: e.currentTarget.value })}
              />
            </Field>
            <Field label="Username" required>
              <Input
                value={formData.username || ''}
                onChange={(e) => setFormData({ ...formData, username: e.currentTarget.value })}
              />
            </Field>
            <Field label="Password" required>
              <Input
                type="password"
                value={formData.password || ''}
                onChange={(e) => setFormData({ ...formData, password: e.currentTarget.value })}
              />
            </Field>
          </FieldSet>
        );

      case 'rest':
        return (
          <FieldSet>
            {commonFields}
            <Field label="API Endpoint URL" required>
              <Input
                placeholder="https://api.example.com"
                value={formData.url || ''}
                onChange={(e) => setFormData({ ...formData, url: e.currentTarget.value })}
              />
            </Field>
            <Field label="Authentication Type">
              <Select
                options={[
                  { label: 'None', value: 'none' },
                  { label: 'API Key', value: 'apikey' },
                  { label: 'Bearer Token', value: 'bearer' },
                  { label: 'Basic Auth', value: 'basic' },
                ]}
                value={formData.authType}
                onChange={(v) => setFormData({ ...formData, authType: v.value })}
              />
            </Field>
            <Field label="API Key / Token">
              <Input
                type="password"
                value={formData.apiKey || ''}
                onChange={(e) => setFormData({ ...formData, apiKey: e.currentTarget.value })}
              />
            </Field>
            <Field label="Custom Headers (JSON)">
              <TextArea
                placeholder='{"Content-Type": "application/json"}'
                value={formData.headers || ''}
                onChange={(e) => setFormData({ ...formData, headers: e.currentTarget.value })}
              />
            </Field>
          </FieldSet>
        );

      default:
        return (
          <FieldSet>
            {commonFields}
            <Alert title="Configuration" severity="info">
              Configuration form for {selectedConnector.name} will be displayed here.
            </Alert>
          </FieldSet>
        );
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          <span className={styles.logo}>RHINOMETRIC</span>
          <Icon name="plug" size="xl" />
          API Connector
        </div>
      </div>

      {!selectedConnector ? (
        <>
          <h3>Select a Connector Type</h3>
          <div className={styles.grid}>
            {connectors.map((connector) => (
              <Card
                key={connector.id}
                className={styles.connectorCard}
                onClick={() => handleConnectorSelect(connector)}
              >
                <Card.Heading>
                  <Icon name={connector.icon as any} size="xl" /> {connector.name}
                </Card.Heading>
                <Card.Description>{connector.description}</Card.Description>
              </Card>
            ))}
          </div>

          <div className={styles.connectionsList}>
            <h3>Active Connections ({connections.length})</h3>
            {connections.map((conn) => (
              <div key={conn.id} className={styles.connectionItem}>
                <div>
                  <strong>{conn.name}</strong> - {conn.type}
                  <Switch value={conn.enabled} />
                </div>
                <div>
                  <Button variant="secondary" size="sm" icon="edit">
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    icon="trash-alt"
                    onClick={() => handleDeleteConnection(conn.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className={styles.form}>
          <Button variant="secondary" icon="arrow-left" onClick={() => setSelectedConnector(null)}>
            Back to Connectors
          </Button>

          <h2>
            <Icon name={selectedConnector.icon as any} /> Configure {selectedConnector.name}
          </h2>

          {renderForm()}

          {testResult && (
            <Alert title={testResult.success ? 'Success' : 'Error'} severity={testResult.success ? 'success' : 'error'}>
              {testResult.message}
            </Alert>
          )}

          <div className={styles.buttonGroup}>
            <Button variant="secondary" icon="check" onClick={handleTestConnection}>
              Test Connection
            </Button>
            <Button variant="primary" icon="save" onClick={handleSaveConnection}>
              Save Connection
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
