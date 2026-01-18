import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, Button, Badge, Alert, AlertTitle, AlertDescription, Spinner } from '../components/ui';
import { TEMPLATES } from '../lib/utils';
import { apiService } from '../lib/api';
import { useDashboardStore, useAuthStore } from '../lib/store';
import { toast } from 'sonner';

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { setTemplate, reset } = useDashboardStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    try {
      const status = await apiService.getStatus();
      setApiStatus(status);
      setLoading(false);
    } catch (err) {
      setError('Cannot connect to Dashboard Builder API. Make sure the service is running on port 8001.');
      setLoading(false);
    }
  };

  const handleQuickCreate = async (templateId) => {
    if (!isAuthenticated) {
      toast.error('Please authenticate first');
      return;
    }

    try {
      setLoading(true);
      const result = await apiService.createDashboard({
        template: templateId,
        title: `${TEMPLATES.find(t => t.id === templateId)?.name} - ${new Date().toLocaleString()}`,
        tags: ['quick-create', 'template'],
      });

      toast.success(`Dashboard created: ${result.uid}`);
      
      const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000';
      window.open(`${grafanaUrl}/d/${result.uid}`, '_blank');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomize = (template) => {
    if (!isAuthenticated) {
      toast.error('Please authenticate first');
      return;
    }
    reset();
    setTemplate(template);
    navigate('/new');
  };

  if (loading && !apiStatus) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dashboard Templates</h1>
          <p className="text-muted-foreground text-lg">
            Create professional Grafana dashboards in seconds without writing PromQL
          </p>
        </div>

        {/* API Status Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Connection Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {apiStatus && (
          <Alert className="mb-6 bg-green-50 border-green-200">
            <AlertTitle>✅ Dashboard Builder API Connected</AlertTitle>
            <AlertDescription>
              Service: {apiStatus.service} - Version: {apiStatus.version} - Status: {apiStatus.status}
            </AlertDescription>
          </Alert>
        )}

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {TEMPLATES.map((template) => (
            <Card key={template.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between mb-2">
                  <div className={`w-12 h-12 rounded-lg ${template.color} flex items-center justify-center text-2xl`}>
                    {template.icon}
                  </div>
                  <Badge variant="secondary">{template.panels} panels</Badge>
                </div>
                <CardTitle className="text-xl">{template.name}</CardTitle>
                <CardDescription>{template.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Badge variant="outline">{template.category}</Badge>
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button
                  onClick={() => handleQuickCreate(template.id)}
                  disabled={!isAuthenticated || loading}
                  size="sm"
                  className="flex-1 gap-2"
                >
                  <Play className="h-4 w-4" />
                  Create Now
                </Button>
                <Button
                  onClick={() => handleCustomize(template)}
                  disabled={!isAuthenticated}
                  variant="outline"
                  size="sm"
                >
                  Customize
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {/* Info Footer */}
        {!isAuthenticated && (
          <Alert className="mt-8">
            <AlertTitle>Authentication Required</AlertTitle>
            <AlertDescription>
              Please add your JWT token in the settings to create dashboards.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}
