/**
 * RHINOMETRIC v2.4.0 - API Service
 * =================================
 * 
 * Service for communicating with FastAPI backend.
 */

import axios, { AxiosInstance } from 'axios';
import { ConnectionTestRequest, TestResult, DatasourceTemplate, Datasource } from '../types';

export class APIService {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Get available datasource templates
   */
  async getTemplates(): Promise<{ templates: Record<string, DatasourceTemplate>; count: number }> {
    const response = await this.client.get('/api/templates');
    return response.data;
  }

  /**
   * Get specific template
   */
  async getTemplate(templateId: string): Promise<{ template_id: string; template: DatasourceTemplate }> {
    const response = await this.client.get(`/api/templates/${templateId}`);
    return response.data;
  }

  /**
   * Test connection to datasource
   */
  async testConnection(request: ConnectionTestRequest): Promise<TestResult> {
    const response = await this.client.post('/api/test-connection', request);
    return response.data;
  }

  /**
   * Create new datasource
   */
  async createDatasource(datasource: Partial<Datasource>): Promise<{ success: boolean; datasource_id: string }> {
    const response = await this.client.post('/api/datasources', datasource);
    return response.data;
  }

  /**
   * List all datasources
   */
  async listDatasources(): Promise<{ datasources: Datasource[]; count: number }> {
    const response = await this.client.get('/api/datasources');
    return response.data;
  }

  /**
   * Get specific datasource
   */
  async getDatasource(datasourceId: string): Promise<Datasource> {
    const response = await this.client.get(`/api/datasources/${datasourceId}`);
    return response.data;
  }

  /**
   * Update datasource
   */
  async updateDatasource(datasourceId: string, datasource: Partial<Datasource>): Promise<{ success: boolean }> {
    const response = await this.client.put(`/api/datasources/${datasourceId}`, datasource);
    return response.data;
  }

  /**
   * Delete datasource
   */
  async deleteDatasource(datasourceId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/api/datasources/${datasourceId}`);
    return response.data;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/');
    return response.data;
  }
}
