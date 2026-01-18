import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Plus, History, Settings, LogOut } from 'lucide-react';
import { Button } from './ui';
import { useAuthStore } from '../lib/store';

export default function Header() {
  const location = useLocation();
  const { isAuthenticated, clearToken } = useAuthStore();

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Templates' },
    { path: '/new', icon: Plus, label: 'Create Dashboard' },
    { path: '/dashboards', icon: History, label: 'History' },
  ];

  const handleLogout = () => {
    clearToken();
    window.location.href = '/';
  };

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold">
                R
              </div>
              <span className="font-bold text-xl">Dashboard Studio</span>
            </Link>

            {isAuthenticated && (
              <nav className="flex gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link key={item.path} to={item.path}>
                      <Button
                        variant={isActive ? 'default' : 'ghost'}
                        size="sm"
                        className="gap-2"
                      >
                        <Icon className="h-4 w-4" />
                        {item.label}
                      </Button>
                    </Link>
                  );
                })}
              </nav>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Button variant="ghost" size="icon">
                  <Settings className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2">
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">
                Not authenticated
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
