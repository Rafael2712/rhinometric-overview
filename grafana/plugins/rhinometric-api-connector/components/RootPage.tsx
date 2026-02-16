import React, { useState } from 'react';
import { AppRootProps } from '@grafana/data';
import { Button, useStyles2, Field, Input, Select, TextArea } from '@grafana/ui';
import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';

const API_BASE = 'http://localhost:8000';

const CONNECTOR_TYPES = [
  { label: '🐘 PostgreSQL', value: 'postgresql', icon: '🐘' },
  { label: '📮 Redis', value: 'redis', icon: '📮' },
  { label: '📨 Apache Kafka', value: 'kafka', icon: '📨' },
  { label: '🐰 RabbitMQ', value: 'rabbitmq', icon: '🐰' },
  { label: '📡 MQTT (IoT)', value: 'mqtt', icon: '📡' },
  { label: '☁️ AWS CloudWatch', value: 'aws', icon: '☁️' },
  { label: '🌐 Azure Monitor', value: 'azure', icon: '🌐' },
  { label: '🔥 Prometheus', value: 'prometheus', icon: '🔥' }
];

interface ConnectorConfig {
  [key: string]: any;
}

export const RootPage: React.FC<AppRootProps> = () => {
  const styles = useStyles2(getStyles);
  const [selectedType, setSelectedType] = useState<string>('');
  const [config, setConfig] = useState<ConnectorConfig>({});
  const [connectionName, setConnectionName] = useState('');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const updateConfig = (key: string, value: any) => {
    setConfig({ ...config, [key]: value });
  };

  const testConnection = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      
      const response = await fetch(`${API_BASE}/api/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: selectedType, config })
      });

      const result = await response.json();
      setTestResult({
        success: response.ok,
        message: result.message || (response.ok ? 'Connection successful!' : 'Connection failed')
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Error testing connection: ' + (error as Error).message
      });
    } finally {
      setTesting(false);
    }
  };

  const saveConnection = async () => {
    try {
      setSaving(true);
      
      const response = await fetch(`${API_BASE}/api/datasources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: connectionName,
          type: selectedType,
          config,
          enabled: true
        })
      });

      if (response.ok) {
        alert('Connection saved successfully!');
        setConnectionName('');
        setConfig({});
        setSelectedType('');
      } else {
        alert('Error saving connection');
      }
    } catch (error) {
      alert('Error saving connection');
    } finally {
      setSaving(false);
    }
  };

  const renderConfigForm = () => {
    switch (selectedType) {
      case 'postgresql':
        return (
          <>
            <Field label="Host">
              <Input value={config.host || ''} onChange={(e) => updateConfig('host', e.currentTarget.value)} placeholder="localhost" />
            </Field>
            <Field label="Port">
              <Input type="number" value={config.port || 5432} onChange={(e) => updateConfig('port', parseInt(e.currentTarget.value))} />
            </Field>
            <Field label="Database">
              <Input value={config.database || ''} onChange={(e) => updateConfig('database', e.currentTarget.value)} />
            </Field>
            <Field label="Username">
              <Input value={config.username || ''} onChange={(e) => updateConfig('username', e.currentTarget.value)} />
            </Field>
            <Field label="Password">
              <Input type="password" value={config.password || ''} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
          </>
        );
      
      case 'redis':
        return (
          <>
            <Field label="Host">
              <Input value={config.host || ''} onChange={(e) => updateConfig('host', e.currentTarget.value)} placeholder="localhost" />
            </Field>
            <Field label="Port">
              <Input type="number" value={config.port || 6379} onChange={(e) => updateConfig('port', parseInt(e.currentTarget.value))} />
            </Field>
            <Field label="Password">
              <Input type="password" value={config.password || ''} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
            <Field label="Database">
              <Input type="number" value={config.database || 0} onChange={(e) => updateConfig('database', parseInt(e.currentTarget.value))} />
            </Field>
          </>
        );

      case 'kafka':
        return (
          <>
            <Field label="Bootstrap Servers">
              <Input value={config.bootstrap_servers || ''} onChange={(e) => updateConfig('bootstrap_servers', e.currentTarget.value)} placeholder="localhost:9092" />
            </Field>
            <Field label="Security Protocol">
              <Select
                options={[
                  { label: 'PLAINTEXT', value: 'PLAINTEXT' },
                  { label: 'SSL', value: 'SSL' },
                  { label: 'SASL_PLAINTEXT', value: 'SASL_PLAINTEXT' },
                  { label: 'SASL_SSL', value: 'SASL_SSL' }
                ]}
                value={config.security_protocol}
                onChange={(option) => updateConfig('security_protocol', option.value)}
              />
            </Field>
            <Field label="SASL Mechanism">
              <Select
                options={[
                  { label: 'PLAIN', value: 'PLAIN' },
                  { label: 'SCRAM-SHA-256', value: 'SCRAM-SHA-256' },
                  { label: 'SCRAM-SHA-512', value: 'SCRAM-SHA-512' }
                ]}
                value={config.sasl_mechanism}
                onChange={(option) => updateConfig('sasl_mechanism', option.value)}
              />
            </Field>
            <Field label="Username">
              <Input value={config.username || ''} onChange={(e) => updateConfig('username', e.currentTarget.value)} />
            </Field>
            <Field label="Password">
              <Input type="password" value={config.password || ''} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
          </>
        );

      case 'rabbitmq':
        return (
          <>
            <Field label="Host">
              <Input value={config.host || ''} onChange={(e) => updateConfig('host', e.currentTarget.value)} placeholder="localhost" />
            </Field>
            <Field label="Port">
              <Input type="number" value={config.port || 5672} onChange={(e) => updateConfig('port', parseInt(e.currentTarget.value))} />
            </Field>
            <Field label="Username">
              <Input value={config.username || 'guest'} onChange={(e) => updateConfig('username', e.currentTarget.value)} />
            </Field>
            <Field label="Password">
              <Input type="password" value={config.password || 'guest'} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
            <Field label="Virtual Host">
              <Input value={config.vhost || '/'} onChange={(e) => updateConfig('vhost', e.currentTarget.value)} />
            </Field>
          </>
        );

      case 'mqtt':
        return (
          <>
            <Field label="Broker Host">
              <Input value={config.host || ''} onChange={(e) => updateConfig('host', e.currentTarget.value)} placeholder="broker.hivemq.com" />
            </Field>
            <Field label="Port">
              <Input type="number" value={config.port || 1883} onChange={(e) => updateConfig('port', parseInt(e.currentTarget.value))} />
            </Field>
            <Field label="Client ID">
              <Input value={config.client_id || ''} onChange={(e) => updateConfig('client_id', e.currentTarget.value)} placeholder="rhinometric-client" />
            </Field>
            <Field label="Username">
              <Input value={config.username || ''} onChange={(e) => updateConfig('username', e.currentTarget.value)} />
            </Field>
            <Field label="Password">
              <Input type="password" value={config.password || ''} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
            <Field label="Test Topic">
              <Input value={config.test_topic || ''} onChange={(e) => updateConfig('test_topic', e.currentTarget.value)} placeholder="test/topic" />
            </Field>
          </>
        );

      case 'aws':
        return (
          <>
            <Field label="Region">
              <Select
                options={[
                  { label: 'us-east-1', value: 'us-east-1' },
                  { label: 'us-west-2', value: 'us-west-2' },
                  { label: 'eu-west-1', value: 'eu-west-1' },
                  { label: 'eu-central-1', value: 'eu-central-1' }
                ]}
                value={config.region}
                onChange={(option) => updateConfig('region', option.value)}
              />
            </Field>
            <Field label="Access Key">
              <Input value={config.access_key || ''} onChange={(e) => updateConfig('access_key', e.currentTarget.value)} />
            </Field>
            <Field label="Secret Key">
              <Input type="password" value={config.secret_key || ''} onChange={(e) => updateConfig('secret_key', e.currentTarget.value)} />
            </Field>
          </>
        );

      case 'azure':
        return (
          <>
            <Field label="Subscription ID">
              <Input value={config.subscription_id || ''} onChange={(e) => updateConfig('subscription_id', e.currentTarget.value)} />
            </Field>
            <Field label="Tenant ID">
              <Input value={config.tenant_id || ''} onChange={(e) => updateConfig('tenant_id', e.currentTarget.value)} />
            </Field>
            <Field label="Client ID">
              <Input value={config.client_id || ''} onChange={(e) => updateConfig('client_id', e.currentTarget.value)} />
            </Field>
            <Field label="Client Secret">
              <Input type="password" value={config.client_secret || ''} onChange={(e) => updateConfig('client_secret', e.currentTarget.value)} />
            </Field>
          </>
        );

      case 'prometheus':
        return (
          <>
            <Field label="URL">
              <Input value={config.url || ''} onChange={(e) => updateConfig('url', e.currentTarget.value)} placeholder="http://localhost:9090" />
            </Field>
            <Field label="Username (optional)">
              <Input value={config.username || ''} onChange={(e) => updateConfig('username', e.currentTarget.value)} />
            </Field>
            <Field label="Password (optional)">
              <Input type="password" value={config.password || ''} onChange={(e) => updateConfig('password', e.currentTarget.value)} />
            </Field>
          </>
        );

      default:
        return <p className={styles.hint}>Select a connector type to configure</p>;
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🔌 API Connector</h1>
        <p>Connect external systems, databases, message queues, and IoT devices</p>
      </div>

      <div className={styles.content}>
        <div className={styles.typeSelector}>
          <h3>Select Connector Type</h3>
          <div className={styles.typeGrid}>
            {CONNECTOR_TYPES.map(type => (
              <button
                key={type.value}
                className={`${styles.typeCard} ${selectedType === type.value ? styles.typeCardActive : ''}`}
                onClick={() => setSelectedType(type.value)}
              >
                <span className={styles.typeIcon}>{type.icon}</span>
                <span className={styles.typeName}>{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {selectedType && (
          <div className={styles.configPanel}>
            <h3>Configure {CONNECTOR_TYPES.find(t => t.value === selectedType)?.label}</h3>
            
            <Field label="Connection Name">
              <Input
                value={connectionName}
                onChange={(e) => setConnectionName(e.currentTarget.value)}
                placeholder="My Connection"
              />
            </Field>

            {renderConfigForm()}

            <div className={styles.actions}>
              <Button onClick={testConnection} variant="secondary" disabled={testing || !selectedType}>
                {testing ? '⏳ Testing...' : '🧪 Test Connection'}
              </Button>
              <Button onClick={saveConnection} variant="primary" disabled={saving || !connectionName || !selectedType}>
                {saving ? '⏳ Saving...' : '💾 Save Connection'}
              </Button>
            </div>

            {testResult && (
              <div className={testResult.success ? styles.successMessage : styles.errorMessage}>
                {testResult.message}
              </div>
            )}
          </div>
        )}
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
    flex-direction: column;
    gap: ${theme.spacing(3)};
  `,
  typeSelector: css`
    h3 {
      margin-bottom: ${theme.spacing(2)};
      color: ${theme.colors.text.primary};
    }
  `,
  typeGrid: css`
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: ${theme.spacing(2)};
  `,
  typeCard: css`
    background: ${theme.colors.background.secondary};
    border: 2px solid ${theme.colors.border.weak};
    border-radius: ${theme.shape.borderRadius()};
    padding: ${theme.spacing(2)};
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: ${theme.spacing(1)};
    &:hover {
      border-color: ${theme.colors.primary.border};
      background: ${theme.colors.background.canvas};
    }
  `,
  typeCardActive: css`
    border-color: ${theme.colors.primary.main};
    background: ${theme.colors.action.selected};
  `,
  typeIcon: css`
    font-size: 32px;
  `,
  typeName: css`
    font-size: ${theme.typography.bodySmall.fontSize};
    text-align: center;
    color: ${theme.colors.text.primary};
  `,
  configPanel: css`
    background: ${theme.colors.background.secondary};
    padding: ${theme.spacing(3)};
    border-radius: ${theme.shape.borderRadius()};
    h3 {
      margin-bottom: ${theme.spacing(2)};
      color: ${theme.colors.text.primary};
    }
  `,
  actions: css`
    margin-top: ${theme.spacing(3)};
    display: flex;
    gap: ${theme.spacing(2)};
  `,
  hint: css`
    color: ${theme.colors.text.secondary};
    text-align: center;
    padding: ${theme.spacing(4)};
  `,
  successMessage: css`
    margin-top: ${theme.spacing(2)};
    padding: ${theme.spacing(2)};
    background: ${theme.colors.success.transparent};
    border: 1px solid ${theme.colors.success.border};
    border-radius: ${theme.shape.borderRadius()};
    color: ${theme.colors.success.text};
  `,
  errorMessage: css`
    margin-top: ${theme.spacing(2)};
    padding: ${theme.spacing(2)};
    background: ${theme.colors.error.transparent};
    border: 1px solid ${theme.colors.error.border};
    border-radius: ${theme.shape.borderRadius()};
    color: ${theme.colors.error.text};
  `
});
