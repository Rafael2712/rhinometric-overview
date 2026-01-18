import { TEMPLATES } from '../../lib/utils';
import { Card, CardHeader, CardTitle, CardDescription, Badge } from '../ui';
import { useDashboardStore } from '../../lib/store';

export default function StepTemplate() {
  const { selectedTemplate, setTemplate } = useDashboardStore();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Choose a Template</h2>
      <p className="text-muted-foreground mb-6">
        Select a pre-built dashboard template that matches your monitoring needs
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TEMPLATES.map((template) => (
          <Card
            key={template.id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedTemplate?.id === template.id
                ? 'ring-2 ring-primary'
                : ''
            }`}
            onClick={() => setTemplate(template)}
          >
            <CardHeader>
              <div className="flex items-start justify-between mb-2">
                <div className={`w-12 h-12 rounded-lg ${template.color} flex items-center justify-center text-2xl`}>
                  {template.icon}
                </div>
                <Badge variant="secondary">{template.panels} panels</Badge>
              </div>
              <CardTitle className="text-lg">{template.name}</CardTitle>
              <CardDescription>{template.description}</CardDescription>
              <div className="pt-2">
                <Badge variant="outline">{template.category}</Badge>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
