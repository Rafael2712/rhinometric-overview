import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, Spinner, Alert, AlertTitle, AlertDescription, Badge } from '../ui';
import { useDashboardStore } from '../../lib/store';
import { apiService } from '../../lib/api';
import { toast } from 'sonner';

export default function StepDatasource() {
  const { selectedDatasource, setDatasource } = useDashboardStore();
  const [datasources, setDatasources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDatasources();
  }, []);

  const loadDatasources = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDatasources();
      setDatasources(Array.isArray(data) ? data : []);
      
      // Auto-select Prometheus if available
      const prometheus = data.find(ds => ds.type === 'prometheus');
      if (prometheus && !selectedDatasource) {
        setDatasource(prometheus);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load datasources from Grafana');
      toast.error('Could not load datasources');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Datasources</AlertTitle>
        <AlertDescription>
          {error}. Make sure Grafana is running and accessible.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Select Datasource</h2>
      <p className="text-muted-foreground mb-6">
        Choose the datasource for your dashboard metrics
      </p>

      {datasources.filter(ds => ds.type === 'prometheus').length === 0 && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>No Prometheus Datasource Found</AlertTitle>
          <AlertDescription>
            Please configure a Prometheus datasource in Grafana before creating dashboards.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-4">
        {datasources.map((ds) => (
          <Card
            key={ds.uid}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedDatasource?.uid === ds.uid
                ? 'ring-2 ring-primary'
                : ''
            }`}
            onClick={() => setDatasource(ds)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg flex items-center gap-2">
                    {ds.name}
                    {ds.isDefault && <Badge variant="secondary">Default</Badge>}
                    {selectedDatasource?.uid === ds.uid && (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    )}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    <span className="font-mono text-xs">{ds.uid}</span>
                    <span className="mx-2">•</span>
                    <Badge variant="outline">{ds.type}</Badge>
                  </CardDescription>
                  <p className="text-sm text-muted-foreground mt-2">{ds.url}</p>
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
