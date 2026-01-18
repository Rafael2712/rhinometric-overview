import { Alert, AlertDescription } from '../ui';
import { useDashboardStore } from '../../lib/store';

export default function StepLayout() {
  const { selectedTemplate } = useDashboardStore();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Dashboard Layout</h2>
      <p className="text-muted-foreground mb-6">
        Layout is optimized automatically based on your template
      </p>

      <Alert>
        <AlertDescription>
          <div className="space-y-2">
            <p className="font-semibold">Auto-Layout Enabled</p>
            <p>The template "{selectedTemplate?.name}" uses an optimized grid layout with:</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>Responsive panel sizing (24-column grid)</li>
              <li>Logical grouping of related metrics</li>
              <li>Mobile-friendly breakpoints</li>
            </ul>
            <p className="text-sm text-muted-foreground mt-4">
              💡 Drag-and-drop layout editor coming soon!
            </p>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
