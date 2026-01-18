/**
 * RHINOMETRIC v2.4.0 - Type Definitions
 * ======================================
 */

export interface APIConnectorOptions {
  apiUrl: string;
  autoRefresh: boolean;
  refreshInterval: number;
}

export type ConnectorCategory = 'database' | 'messaging' | 'industrial' | 'cloud' | 'api' | 'custom';

export interface DatasourceTemplate {
  name: string;
  description: string;
  icon: string;
  category?: ConnectorCategory;
  color?: string;
  tooltip?: string;
  fields: TemplateField[];
}

export interface TemplateField {
  name: string;
  type: 'text' | 'password' | 'number' | 'boolean' | 'select';
  required: boolean;
  default?: any;
  options?: string[];
  placeholder?: string;
}

export interface ConnectionTestRequest {
  datasource_type: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  region?: string;
  access_key?: string;
  secret_key?: string;
  subscription_id?: string;
  tenant_id?: string;
  client_id?: string;
  client_secret?: string;
  url?: string;
  ssl?: boolean;
  timeout?: number;
  
  // RabbitMQ
  vhost?: string;
  
  // Kafka
  bootstrap_servers?: string;
  security_protocol?: string;
  sasl_mechanism?: string;
  ssl_check_hostname?: boolean;
  
  // MQTT
  use_tls?: boolean;
  keepalive?: number;
  clean_session?: boolean;
  test_topic?: string;
}

export interface TestResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
  duration_ms: number;
}

export interface Datasource {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  config: Record<string, any>;
  tags: string[];
  created_at?: string;
  updated_at?: string;
}
