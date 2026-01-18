/**
 * RHINOMETRIC v2.4.0 - API Connector Panel Component
 * ===================================================
 * 
 * Main React component for visual datasource configuration.
 */

import React, { useState, useEffect } from 'react';
import { PanelProps } from '@grafana/data';
import { Button, Select, Input, Alert, Spinner, Card } from '@grafana/ui';
import { APIConnectorOptions, DatasourceTemplate, ConnectionTestRequest, TestResult } from '../types';
import { APIService } from '../services/api';
import './APIConnectorPanel.css';

interface Props extends PanelProps<APIConnectorOptions> {}

export const APIConnectorPanel: React.FC<Props> = ({ options }) => {
  const [templates, setTemplates] = useState<Record<string, DatasourceTemplate>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);

  const apiService = new APIService(options.apiUrl);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const data = await apiService.getTemplates();
      setTemplates(data.templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    setTestResult(null);
    
    // Initialize form with default values
    const template = templates[templateId];
    if (template) {
      const defaults: Record<string, any> = {};
      template.fields.forEach(field => {
        if (field.default !== undefined) {
          defaults[field.name] = field.default;
        }
      });
      setFormData(defaults);
    }
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleTestConnection = async () => {
    setIsLoading(true);
    setTestResult(null);

    try {
      const request: ConnectionTestRequest = {
        datasource_type: selectedTemplate,
        ...formData,
      };

      const result = await apiService.testConnection(request);
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        message: `Test failed: ${error.message}`,
        duration_ms: 0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveDatasource = async () => {
    // TODO: Implement save datasource
    alert('Save datasource functionality coming soon!');
  };

  // Group templates by category
  const categorizedTemplates = () => {
    const categories: Record<string, { icon: string; color: string; label: string; templates: [string, DatasourceTemplate][] }> = {
      database: { icon: '🗄️', color: '#4CAF50', label: 'Databases', templates: [] },
      messaging: { icon: '💬', color: '#2196F3', label: 'Messaging', templates: [] },
      cloud: { icon: '☁️', color: '#9C27B0', label: 'Cloud', templates: [] },
      api: { icon: '🌐', color: '#00BCD4', label: 'APIs', templates: [] },
      industrial: { icon: '⚙️', color: '#FF9800', label: 'Industrial/IoT', templates: [] },
      custom: { icon: '🧩', color: '#607D8B', label: 'Custom', templates: [] },
    };

    Object.entries(templates).forEach(([id, template]) => {
      const category = template.category || 'custom';
      if (categories[category]) {
        categories[category].templates.push([id, template]);
      }
    });

    return categories;
  };

  const filteredTemplates = () => {
    if (selectedCategory === 'all') {
      return Object.entries(templates);
    }
    const cats = categorizedTemplates();
    return cats[selectedCategory]?.templates || [];
  };

  const renderField = (field: any) => {
    switch (field.type) {
      case 'password':
        return (
          <Input
            type="password"
            placeholder={field.name}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, e.currentTarget.value)}
            required={field.required}
          />
        );
      
      case 'number':
        return (
          <Input
            type="number"
            placeholder={field.name}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, parseInt(e.currentTarget.value))}
            required={field.required}
          />
        );
      
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={formData[field.name] || false}
            onChange={(e) => handleFieldChange(field.name, e.target.checked)}
          />
        );
      
      case 'select':
        return (
          <Select
            options={field.options?.map((opt: string) => ({ label: opt, value: opt }))}
            value={formData[field.name]}
            onChange={(e) => handleFieldChange(field.name, e.value)}
          />
        );
      
      default:
        return (
          <Input
            type="text"
            placeholder={field.name}
            value={formData[field.name] || ''}
            onChange={(e) => handleFieldChange(field.name, e.currentTarget.value)}
            required={field.required}
          />
        );
    }
  };

  if (loadingTemplates) {
    return (
      <div className="rhinometric-connector-loading">
        <Spinner size="lg" />
        <p>Loading datasource templates...</p>
      </div>
    );
  }

  return (
    <div className="rhinometric-connector-panel">
      <div className="rhinometric-header">
        <h2>🔌 RHINOMETRIC API Connector</h2>
        <p>Connect external datasources without YAML configuration</p>
      </div>

      {/* Category Filter */}
      <Card className="rhinometric-card">
        <Card.Heading>1. Select Category</Card.Heading>
        <Card.Description>
          <div className="category-tabs">
            <button
              className={`category-tab ${selectedCategory === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('all')}
            >
              <span className="category-icon">📚</span>
              <span className="category-label">All</span>
            </button>
            {Object.entries(categorizedTemplates()).map(([category, data]) => (
              data.templates.length > 0 && (
                <button
                  key={category}
                  className={`category-tab ${selectedCategory === category ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(category)}
                  style={{ borderLeftColor: data.color }}
                >
                  <span className="category-icon">{data.icon}</span>
                  <span className="category-label">{data.label}</span>
                  <span className="category-count">{data.templates.length}</span>
                </button>
              )
            ))}
          </div>
        </Card.Description>
      </Card>

      {/* Template Selection */}
      <Card className="rhinometric-card">
        <Card.Heading>2. Select Datasource Type</Card.Heading>
        <Card.Description>
          <div className="template-grid">
            {filteredTemplates().map(([id, template]) => (
              <div
                key={id}
                className={`template-card ${selectedTemplate === id ? 'selected' : ''}`}
                onClick={() => handleTemplateSelect(id)}
                style={{ borderTopColor: template.color || '#1a73e8' }}
                title={template.tooltip || template.description}
              >
                <div className="template-icon" style={{ color: template.color || '#1a73e8' }}>
                  {template.icon}
                </div>
                <h4>{template.name}</h4>
                <p>{template.description}</p>
                {template.category === 'messaging' && (
                  <div className="on-premise-badge">🏠 On-Premise Only</div>
                )}
              </div>
            ))}
          </div>
        </Card.Description>
      </Card>

      {/* Configuration Form */}
      {selectedTemplate && (
        <Card className="rhinometric-card">
          <Card.Heading>3. Configure Connection</Card.Heading>
          <Card.Description>
            <div className="config-form">
              {templates[selectedTemplate]?.fields.map((field) => (
                <div key={field.name} className="form-field">
                  <label>
                    {field.name}
                    {field.required && <span className="required">*</span>}
                  </label>
                  {renderField(field)}
                </div>
              ))}
            </div>
          </Card.Description>
        </Card>
      )}

      {/* Test Connection */}
      {selectedTemplate && (
        <Card className="rhinometric-card">
          <Card.Heading>4. Test Connection</Card.Heading>
          <Card.Description>
            <div className="test-section">
              <Button
                variant="primary"
                onClick={handleTestConnection}
                disabled={isLoading}
                icon={isLoading ? 'spinner' : 'play'}
              >
                {isLoading ? 'Testing...' : 'Test Connection'}
              </Button>

              {testResult && (
                <Alert
                  title={testResult.success ? 'Connection Successful' : 'Connection Failed'}
                  severity={testResult.success ? 'success' : 'error'}
                >
                  <p>{testResult.message}</p>
                  <p className="test-duration">Duration: {testResult.duration_ms.toFixed(2)}ms</p>
                  
                  {testResult.details && (
                    <pre className="test-details">
                      {JSON.stringify(testResult.details, null, 2)}
                    </pre>
                  )}
                </Alert>
              )}
            </div>
          </Card.Description>
        </Card>
      )}

      {/* Save Datasource */}
      {testResult?.success && (
        <Card className="rhinometric-card">
          <Card.Heading>5. Save Datasource</Card.Heading>
          <Card.Description>
            <div className="save-section">
              <Input
                placeholder="Datasource name (e.g., 'Production DB')"
                onChange={(e) => handleFieldChange('datasource_name', e.currentTarget.value)}
              />
              <Button variant="success" onClick={handleSaveDatasource} icon="save">
                Save to Grafana
              </Button>
            </div>
          </Card.Description>
        </Card>
      )}
    </div>
  );
};
