import { useState } from 'react';
import { useAuthStore } from '../lib/auth/store';

export interface CorrelationMetadata {
  host?: string;
  service?: string;
  metric_name?: string;
  instance?: string;
  level?: string;
  [key: string]: any;
}

export interface CorrelationRequest {
  event_id: string;
  event_timestamp: string; // ISO format
  event_type: 'anomaly' | 'alert' | 'log' | 'trace';
  event_metadata?: CorrelationMetadata;
}

export interface MetricResult {
  query_name: string;
  metric: Record<string, string>;
  values: [number, string][];
  source: 'victoria-metrics' | 'prometheus';
}

export interface LogResult {
  timestamp: number;
  labels: Record<string, string>;
  line: string;
}

export interface CorrelationResponse {
  event_id: string;
  timestamp: string;
  event_type: string;
  correlation_window: {
    start: string;
    end: string;
    duration_seconds: number;
  };
  metadata: CorrelationMetadata;
  metrics: MetricResult[];
  logs: LogResult[];
  traces: any[];
  related_anomalies: any[];
  summary: {
    metrics_count: number;
    logs_count: number;
    traces_count: number;
    anomalies_count: number;
  };
}

export interface CorrelationConfig {
  correlation_window_seconds: number;
  correlation_window_minutes: number;
  use_victoria_metrics: boolean;
  tsdb_primary: string;
  backends: {
    victoria_metrics: string;
    prometheus: string;
    loki: string;
    jaeger: string;
    ai_anomaly: string;
  };
}

export const useCorrelation = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CorrelationResponse | null>(null);
  const [config, setConfig] = useState<CorrelationConfig | null>(null);
  
  const { token } = useAuthStore();

  /**
   * Correlaciona un evento con datos de observabilidad
   */
  const correlate = async (request: CorrelationRequest): Promise<CorrelationResponse | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/correlation/correlate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('No autorizado. Por favor, inicia sesión nuevamente.');
        }
        if (response.status === 403) {
          throw new Error('No tienes permisos para realizar esta operación.');
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      const result: CorrelationResponse = await response.json();
      setData(result);
      return result;
    } catch (err: any) {
      const errorMessage = err.message || 'Error al correlacionar evento';
      setError(errorMessage);
      console.error('[useCorrelation] Error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Obtiene la configuración del motor de correlación
   */
  const getConfig = async (): Promise<CorrelationConfig | null> => {
    try {
      const response = await fetch(`/api/correlation/config`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const result: CorrelationConfig = await response.json();
      setConfig(result);
      return result;
    } catch (err: any) {
      console.error('[useCorrelation] Error getting config:', err);
      return null;
    }
  };

  /**
   * Verifica el estado del motor de correlación
   */
  const checkHealth = async (): Promise<boolean> => {
    try {
      const response = await fetch(`/api/correlation/health`);
      if (!response.ok) return false;
      
      const result = await response.json();
      return result.status === 'healthy';
    } catch (err) {
      console.error('[useCorrelation] Health check failed:', err);
      return false;
    }
  };

  return {
    loading,
    error,
    data,
    config,
    correlate,
    getConfig,
    checkHealth,
  };
};
