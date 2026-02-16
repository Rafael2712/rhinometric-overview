import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { useState, useEffect } from 'react';
import { Key, X } from 'lucide-react';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import NewDashboardPage from './pages/NewDashboardPage';
import DashboardsPage from './pages/DashboardsPage';
import { Button, Input, Label, Alert, AlertDescription } from './components/ui';
import { useAuthStore } from './lib/store';

function App() {
  const { isAuthenticated, setToken, clearToken } = useAuthStore();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [tokenInput, setTokenInput] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
      setShowAuthModal(true);
    }
  }, []);

  const handleSaveToken = () => {
    if (tokenInput.trim()) {
      setToken(tokenInput.trim());
      setShowAuthModal(false);
      setTokenInput('');
    }
  };

  const handleSkip = () => {
    setShowAuthModal(false);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/new" element={<NewDashboardPage />} />
          <Route path="/dashboards" element={<DashboardsPage />} />
        </Routes>
      </main>

      <Toaster position="top-right" richColors />

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Key className="h-5 w-5 text-primary" />
                <h2 className="text-xl font-bold">JWT Authentication</h2>
              </div>
              <Button variant="ghost" size="icon" onClick={handleSkip}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <Alert className="mb-4">
              <AlertDescription>
                <p className="text-sm">
                  Enter your JWT token to authenticate with the Dashboard Builder API.
                  You can generate a token using the backend service.
                </p>
              </AlertDescription>
            </Alert>

            <div className="space-y-4">
              <div>
                <Label htmlFor="token">JWT Token</Label>
                <Input
                  id="token"
                  type="password"
                  placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  className="mt-1 font-mono text-xs"
                />
              </div>

              <div className="flex gap-2">
                <Button onClick={handleSaveToken} className="flex-1" disabled={!tokenInput.trim()}>
                  Save Token
                </Button>
                <Button onClick={handleSkip} variant="outline">
                  Skip for Now
                </Button>
              </div>

              <div className="text-xs text-muted-foreground">
                <p className="font-semibold mb-1">How to generate a token:</p>
                <code className="block bg-muted p-2 rounded text-xs overflow-x-auto">
                  docker exec rhinometric-dashboard-builder python -c "import jwt; from datetime import datetime, timedelta, timezone; print(jwt.encode({{'user_id': 'admin', 'exp': datetime.now(timezone.utc) + timedelta(days=365)}}, 'your_jwt_secret_for_license_system_change_this', algorithm='HS256'))"
                </code>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Auth Status Banner */}
      {!isAuthenticated && !showAuthModal && (
        <div className="fixed bottom-4 right-4 z-40">
          <Alert className="shadow-lg">
            <AlertDescription className="flex items-center gap-2">
              <span className="text-sm">Not authenticated</span>
              <Button size="sm" onClick={() => setShowAuthModal(true)}>
                Add Token
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  );
}

export default App;
