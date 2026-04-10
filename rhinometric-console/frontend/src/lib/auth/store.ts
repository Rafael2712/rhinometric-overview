/**
 * Auth state management (Zustand).
 * Phase 1: Dual-mode - supports both Keycloak OIDC and legacy local login.
 * After full cutover, legacy login code can be removed.
 */
import { create } from 'zustand'
import { useState, useEffect } from 'react'
import { persist } from 'zustand/middleware'
import {
  fetchOidcConfig,
  initKeycloak,
  keycloakLogin,
  keycloakLogout,
  getAccessToken,
  getKeycloak,
  type KeycloakConfig,
} from './keycloak'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  roles: string[] // ['OWNER', 'ADMIN', 'OPERATOR', 'VIEWER']
  must_change_password: boolean
  last_login?: string
  sso_provider?: string
}

type AuthMode = 'initializing' | 'oidc' | 'legacy' | 'disabled'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  mustChangePassword: boolean
  authMode: AuthMode
  oidcConfig: KeycloakConfig | null

  // Actions
  initOidc: () => Promise<void>
  loginWithKeycloak: () => void
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<string | undefined>
  fetchUserProfile: (accessToken: string) => Promise<User>

  // Role helpers
  hasRole: (role: string) => boolean
  isOwner: () => boolean
  isAdmin: () => boolean
  canManageUsers: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      mustChangePassword: false,
      authMode: 'initializing' as AuthMode,
      oidcConfig: null,

      /**
       * Initialize OIDC: fetch config, init Keycloak, check-sso.
       * Called once on app startup.
       */
      initOidc: async () => {
        try {
          const config = await fetchOidcConfig()
          set({ oidcConfig: config })

          if (!config.enabled) {
            set({ authMode: 'legacy' })
            return
          }

          const authenticated = await initKeycloak(config)
          set({ authMode: 'oidc' })

          if (authenticated) {
            const kc = getKeycloak()
            if (kc?.token) {
              try {
                const user = await get().fetchUserProfile(kc.token)
                set({
                  user,
                  token: kc.token,
                  isAuthenticated: true,
                  mustChangePassword: user.must_change_password || false,
                })
              } catch (err) {
                console.error('[Auth] Failed to fetch user profile after SSO:', err)
                set({ isAuthenticated: false, user: null, token: null })
              }
            }
          }
        } catch (err) {
          console.warn('[Auth] OIDC init failed, falling back to legacy:', err)
          set({ authMode: 'legacy' })
        }
      },

      /**
       * Redirect to Keycloak login page.
       */
      loginWithKeycloak: () => {
        keycloakLogin()
      },

      /**
       * Legacy local login (username/password).
       */
      login: async (username: string, password: string) => {
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ username, password }),
          })

          if (!response.ok) {
            throw new Error('Invalid credentials')
          }

          const data = await response.json()
          const user = await get().fetchUserProfile(data.access_token)

          set({
            user,
            token: data.access_token,
            isAuthenticated: true,
            mustChangePassword: data.must_change_password || false,
          })
        } catch {
          throw new Error('Invalid credentials')
        }
      },

      /**
       * Logout: clear state + Keycloak session if OIDC mode.
       */
      logout: () => {
        const { authMode } = get()
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          mustChangePassword: false,
        })

        if (authMode === 'oidc') {
          keycloakLogout()
        }
      },

      /**
       * Refresh token and return new access token.
       */
      refreshToken: async () => {
        const { authMode } = get()
        if (authMode === 'oidc') {
          const newToken = await getAccessToken()
          if (newToken) {
            set({ token: newToken })
          }
          return newToken
        }
        return get().token || undefined
      },

      /**
       * Fetch user profile from /api/auth/me.
       */
      fetchUserProfile: async (accessToken: string): Promise<User> => {
        const resp = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${accessToken}` },
        })
        if (!resp.ok) {
          throw new Error('Failed to fetch user profile')
        }
        return resp.json()
      },

      // Role helpers (unchanged)
      hasRole: (role: string) => {
        const { user } = get()
        return user?.roles?.includes(role) || false
      },
      isOwner: () => {
        const { user } = get()
        return user?.roles?.includes('OWNER') || false
      },
      isAdmin: () => {
        const { user } = get()
        return (
          user?.roles?.includes('ADMIN') || user?.roles?.includes('OWNER') || false
        )
      },
      canManageUsers: () => {
        const { user } = get()
        return (
          user?.roles?.includes('OWNER') || user?.roles?.includes('ADMIN') || false
        )
      },
    }),
    {
      name: 'rhinometric-auth',
      // Only persist these fields (not authMode/oidcConfig which are runtime)
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
        mustChangePassword: state.mustChangePassword,
      }),
    }
  )
)

// Hydration gate
export const useHasHydrated = (): boolean => {
  const [hydrated, setHydrated] = useState(useAuthStore.persist.hasHydrated())
  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true))
    if (useAuthStore.persist.hasHydrated()) setHydrated(true)
    return unsub
  }, [])
  return hydrated
}
