import { useState, useEffect } from 'react';
import { ExternalLink, Trash2, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Input, Button, Badge, Alert, AlertDescription } from '../components/ui';
import { useHistoryStore } from '../lib/store';

export default function DashboardsPage() {
  const { dashboards } = useHistoryStore();
  const [search, setSearch] = useState('');
  const [filtered, setFiltered] = useState(dashboards);

  useEffect(() => {
    if (search) {
      setFiltered(
        dashboards.filter(
          (d) =>
            d.title?.toLowerCase().includes(search.toLowerCase()) ||
            d.uid?.toLowerCase().includes(search.toLowerCase())
        )
      );
    } else {
      setFiltered(dashboards);
    }
  }, [search, dashboards]);

  const handleOpen = (dashboard) => {
    const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000';
    window.open(`${grafanaUrl}/d/${dashboard.uid}`, '_blank');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dashboard History</h1>
          <p className="text-muted-foreground">Recently created dashboards</p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Search by title or UID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Dashboard List */}
        {filtered.length === 0 ? (
          <Alert>
            <AlertDescription>
              {dashboards.length === 0
                ? 'No dashboards created yet. Start by creating one from templates.'
                : 'No dashboards found matching your search.'}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-4">
            {filtered.map((dashboard) => (
              <Card key={dashboard.uid}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-2">{dashboard.title}</h3>
                      <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        <span className="font-mono">{dashboard.uid}</span>
                        {dashboard.tags?.map((tag) => (
                          <Badge key={tag} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      {dashboard.created_at && (
                        <p className="text-sm text-muted-foreground mt-2">
                          Created: {new Date(dashboard.created_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleOpen(dashboard)}
                        variant="outline"
                        size="sm"
                        className="gap-2"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Open
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
