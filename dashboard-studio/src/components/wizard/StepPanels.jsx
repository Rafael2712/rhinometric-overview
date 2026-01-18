import { Alert, AlertDescription } from '../ui';
import { useDashboardStore } from '../../lib/store';

export default function StepPanels() {
  const { selectedTemplate } = useDashboardStore();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Configure Panels</h2>
      <p className="text-muted-foreground mb-6">
        Panel configuration is automatic for template-based dashboards
      </p>

      <Alert>
        <AlertDescription>
          <div className="space-y-2">
            <p className="font-semibold">Template: {selectedTemplate?.name}</p>
            <p>This template includes {selectedTemplate?.panels} pre-configured panels with optimized queries and visualizations.</p>
            <p className="text-sm text-muted-foreground mt-4">
              💡 Panel customization will be available in future releases. For now, templates provide production-ready configurations.
            </p>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
