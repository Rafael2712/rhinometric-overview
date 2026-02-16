import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronLeft, Check } from 'lucide-react';
import { Button, Card, CardContent, Spinner } from '../components/ui';
import { useDashboardStore } from '../lib/store';
import { apiService } from '../lib/api';
import { toast } from 'sonner';

// Steps components
import StepTemplate from '../components/wizard/StepTemplate';
import StepDatasource from '../components/wizard/StepDatasource';
import StepPanels from '../components/wizard/StepPanels';
import StepLayout from '../components/wizard/StepLayout';
import StepPreview from '../components/wizard/StepPreview';

const STEPS = [
  { id: 1, name: 'Template', component: StepTemplate },
  { id: 2, name: 'Datasource', component: StepDatasource },
  { id: 3, name: 'Panels', component: StepPanels },
  { id: 4, name: 'Layout', component: StepLayout },
  { id: 5, name: 'Preview', component: StepPreview },
];

export default function NewDashboardPage() {
  const navigate = useNavigate();
  const { currentStep, setStep, selectedTemplate, dashboardConfig, reset } = useDashboardStore();
  const [loading, setLoading] = useState(false);
  const [createdDashboard, setCreatedDashboard] = useState(null);

  const CurrentStepComponent = STEPS[currentStep - 1]?.component;

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setStep(currentStep - 1);
    }
  };

  const handleCreate = async () => {
    try {
      setLoading(true);
      
      const payload = {
        template: selectedTemplate?.id,
        title: dashboardConfig.title || `${selectedTemplate?.name} - ${new Date().toLocaleString()}`,
        description: dashboardConfig.description,
        tags: dashboardConfig.tags,
        refresh: dashboardConfig.refresh,
      };

      const result = await apiService.createDashboard(payload);
      
      setCreatedDashboard(result);
      toast.success(`Dashboard created successfully: ${result.uid}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenGrafana = () => {
    if (createdDashboard) {
      const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000';
      window.open(`${grafanaUrl}/d/${createdDashboard.uid}`, '_blank');
    }
  };

  const handleReset = () => {
    reset();
    setCreatedDashboard(null);
    navigate('/');
  };

  // Success view after creation
  if (createdDashboard) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="mb-6">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Dashboard Created!</h2>
                <p className="text-muted-foreground">Your dashboard is ready to view in Grafana</p>
              </div>

              <div className="bg-muted p-4 rounded-lg mb-6 text-left">
                <div className="grid gap-2">
                  <div>
                    <span className="text-sm text-muted-foreground">UID:</span>
                    <p className="font-mono font-semibold">{createdDashboard.uid}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Title:</span>
                    <p className="font-semibold">{createdDashboard.title}</p>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">URL:</span>
                    <p className="font-mono text-sm break-all">{createdDashboard.url}</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 justify-center">
                <Button onClick={handleOpenGrafana} size="lg">
                  Open in Grafana
                </Button>
                <Button onClick={handleReset} variant="outline" size="lg">
                  Create Another
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      currentStep >= step.id
                        ? 'bg-primary text-white'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {step.id}
                  </div>
                  <span
                    className={`ml-2 text-sm font-medium ${
                      currentStep >= step.id ? 'text-foreground' : 'text-muted-foreground'
                    }`}
                  >
                    {step.name}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-4 ${
                      currentStep > step.id ? 'bg-primary' : 'bg-muted'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Current Step Content */}
        <Card className="mb-6">
          <CardContent className="p-8">
            {CurrentStepComponent && <CurrentStepComponent />}
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            onClick={handlePrevious}
            variant="outline"
            disabled={currentStep === 1 || loading}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>

          {currentStep < STEPS.length ? (
            <Button onClick={handleNext} disabled={!selectedTemplate || loading}>
              Next
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleCreate} disabled={loading || !dashboardConfig.title}>
              {loading ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Creating...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Create Dashboard
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
