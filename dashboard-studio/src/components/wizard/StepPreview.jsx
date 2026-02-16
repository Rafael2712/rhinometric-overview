import { Input, Label, Badge } from '../ui';
import { useDashboardStore } from '../../lib/store';
import { REFRESH_INTERVALS, TIME_RANGES } from '../../lib/utils';

export default function StepPreview() {
  const { selectedTemplate, selectedDatasource, dashboardConfig, setConfig } = useDashboardStore();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Review & Create</h2>
      <p className="text-muted-foreground mb-6">
        Configure final settings and create your dashboard
      </p>

      <div className="space-y-6">
        {/* Dashboard Title */}
        <div>
          <Label htmlFor="title">Dashboard Title *</Label>
          <Input
            id="title"
            placeholder={`${selectedTemplate?.name} - ${new Date().toLocaleDateString()}`}
            value={dashboardConfig.title}
            onChange={(e) => setConfig({ title: e.target.value })}
            className="mt-1"
          />
        </div>

        {/* Description */}
        <div>
          <Label htmlFor="description">Description</Label>
          <Input
            id="description"
            placeholder="Optional description for your dashboard"
            value={dashboardConfig.description}
            onChange={(e) => setConfig({ description: e.target.value })}
            className="mt-1"
          />
        </div>

        {/* Tags */}
        <div>
          <Label htmlFor="tags">Tags (comma-separated)</Label>
          <Input
            id="tags"
            placeholder="monitoring, production, system"
            value={dashboardConfig.tags?.join(', ') || ''}
            onChange={(e) =>
              setConfig({ tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean) })
            }
            className="mt-1"
          />
        </div>

        {/* Refresh Interval */}
        <div>
          <Label htmlFor="refresh">Refresh Interval</Label>
          <select
            id="refresh"
            value={dashboardConfig.refresh}
            onChange={(e) => setConfig({ refresh: e.target.value })}
            className="mt-1 w-full h-10 rounded-md border border-input bg-background px-3 py-2"
          >
            {REFRESH_INTERVALS.map((interval) => (
              <option key={interval.value} value={interval.value}>
                {interval.label}
              </option>
            ))}
          </select>
        </div>

        {/* Summary */}
        <div className="border-t pt-6">
          <h3 className="font-semibold mb-4">Dashboard Summary</h3>
          <div className="space-y-3 bg-muted p-4 rounded-lg">
            <div>
              <span className="text-sm text-muted-foreground">Template:</span>
              <p className="font-medium">{selectedTemplate?.name}</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Datasource:</span>
              <p className="font-medium">{selectedDatasource?.name || 'Not selected'}</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Panels:</span>
              <p className="font-medium">{selectedTemplate?.panels} panels</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Category:</span>
              <Badge>{selectedTemplate?.category}</Badge>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
