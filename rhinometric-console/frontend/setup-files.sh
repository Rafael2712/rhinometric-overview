#!/bin/bash
set -e

echo "íº€ Creating Rhinometric Console source files..."

# Create index.html
cat > index.html << 'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <title>Rhinometric Console</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTML

# Create tsconfig.json
cat > tsconfig.json << 'TSCONFIG'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
TSCONFIG

# Create tsconfig.node.json
cat > tsconfig.node.json << 'TSCONFIGNODE'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
TSCONFIGNODE

# Create tailwind.config.js
cat > tailwind.config.js << 'TAILWIND'
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0ea5e9',
          dark: '#0284c7',
          light: '#38bdf8',
        },
        secondary: {
          DEFAULT: '#14b8a6',
          dark: '#0d9488',
          light: '#2dd4bf',
        },
        background: '#0f172a',
        surface: '#1e293b',
        'surface-light': '#334155',
        error: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
        text: {
          primary: '#f1f5f9',
          secondary: '#cbd5e1',
          muted: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
TAILWIND

# Create postcss.config.js
cat > postcss.config.js << 'POSTCSS'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
POSTCSS

echo "âœ… Configuration files created"

# Create src/index.css
cat > src/index.css << 'CSS'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-surface-light;
  }
  body {
    @apply bg-background text-text-primary font-sans antialiased;
  }
  h1, h2, h3, h4, h5, h6 {
    @apply font-semibold;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-md font-medium transition-colors duration-200;
  }
  .btn-primary {
    @apply bg-primary hover:bg-primary-dark text-white;
  }
  .btn-secondary {
    @apply bg-surface hover:bg-surface-light text-text-primary;
  }
  .card {
    @apply bg-surface rounded-lg border border-surface-light p-6;
  }
  .input {
    @apply bg-surface border border-surface-light rounded-md px-4 py-2 text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary;
  }
}
CSS

echo "âœ… index.css created"
echo "í¾¨ Creating React components..."


# Create src/main.tsx
cat > src/main.tsx << 'MAIN'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
MAIN

# Create src/App.tsx
cat > src/App.tsx << 'APP'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage } from './pages/Login'
import { Layout } from './components/Layout'
import { HomePage } from './pages/Home'
import { AnomaliesPage } from './pages/Anomalies'
import { LicensePage } from './pages/License'
import { SettingsPage } from './pages/Settings'
import { useAuthStore } from './lib/auth/store'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <Layout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/anomalies" element={<AnomaliesPage />} />
                  <Route path="/license" element={<LicensePage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
APP

# Create src/lib/auth/store.ts
cat > src/lib/auth/store.ts << 'AUTHSTORE'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'viewer'
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: async (username: string, password: string) => {
        if (username === 'admin' && password === 'admin') {
          const mockUser: User = {
            id: '1',
            username: 'admin',
            email: 'admin@rhinometric.com',
            role: 'admin',
          }
          const mockToken = 'mock-jwt-token'
          set({ user: mockUser, token: mockToken, isAuthenticated: true })
        } else {
          throw new Error('Invalid credentials')
        }
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    {
      name: 'rhinometric-auth',
    }
  )
)
AUTHSTORE

echo "âœ… Core files created (main.tsx, App.tsx, auth store)"


# Create src/pages/Login.tsx
cat > src/pages/Login.tsx << 'LOGIN'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/auth/store'
import { Activity } from 'lucide-react'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      navigate('/')
    } catch (err) {
      setError('Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex flex-col items-center mb-8">
            <div className="bg-primary rounded-lg p-3 mb-4">
              <Activity className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white">Rhinometric</h1>
            <p className="text-text-muted mt-2">AI-Powered Observability Platform</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-text-secondary mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                className="input w-full"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-secondary mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="input w-full"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="bg-error/10 border border-error text-error px-4 py-2 rounded-md text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-surface-light">
            <p className="text-xs text-text-muted text-center">
              Demo credentials: <span className="text-primary">admin</span> / <span className="text-primary">admin</span>
            </p>
          </div>
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          Â© 2025 Rhinometric. All rights reserved.
        </p>
      </div>
    </div>
  )
}
LOGIN

echo "âœ… Login page created"

