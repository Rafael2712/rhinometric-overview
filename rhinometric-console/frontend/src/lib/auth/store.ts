/**
 * Auth state management (Zustand).
 * Keycloak-only mode — all legacy local auth has been removed.
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
  onTokenRefreshed,
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

type AuthMode = 'initializing' | 'oidc'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  authMode: AuthMode
  oidcConfig: KeycloakConfig | null

  // Actions
  initOidc: () => Promise<void>
  loginWithKeycloak: () => void
  logout: () => void
  refreshToken: () => Promise<string | undefined>
  fetchUserProfile: (accessToken: string) => Promise<User>

  // Role helpers
  hasRole: (role: string) => boolean
  isOwner: () => boolean
  isAdmin: () => boolean
  isOperator: () => boolean
  isViewer: () => boolean
  canManageUsers: () => boolean
  canWrite: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      authMode: 'initializing' as AuthMode,
      oidcConfig: null,

      /**
       * Initialize OIDC: fetch config, init Keycloak, check-sso.
       * Called once on app startup.
       */
      initOidc: async () => {
        try {
          const config = await fetchOidcConfig()
          set({ oidcConfig: config, authMode: 'oidc' })

          const authenticated = await initKeycloak(config)

          // Keep Zustand token in sync with Keycloak auto-refresh
          onTokenRefreshed((newToken) => set({ token: newToken }))

          if (authenticated) {
            const kc = getKeycloak()
            if (kc?.token) {
              try {
                const user = await get().fetchUserProfile(kc.token)
                set({
                  user,
                  token: kc.token,
                  isAuthenticated: true,
                })
              } catch (err) {
                console.error('[Auth] Failed to fetch user profile after SSO:', err)
                set({ isAuthenticated: false, user: null, token: null })
              }
            }
          }
        } catch (err) {
          console.error('[Auth] OIDC init failed:', err)
          set({ authMode: 'oidc' })
        }
      },

      /**
       * Redirect to Keycloak login page.
       */
      loginWithKeycloak: () => {
        keycloakLogin()
      },

      /**
       * Logout: clear state + Keycloak session.
       */
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        })
        keycloakLogout()
      },

      /**
       * Refresh token and return new access token.
       */
      refreshToken: async () => {
        const newToken = await getAccessToken()
        if (newToken) {
          set({ token: newToken })
        }
        return newToken
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

      // Role helpers
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
      isOperator: () => {
        const { user } = get()
        return (
          user?.roles?.includes('OPERATOR') ||
          user?.roles?.includes('ADMIN') ||
          user?.roles?.includes('OWNER') ||
          false
        )
      },
      isViewer: () => {
        const { user } = get()
        return user?.roles?.length ? true : false
      },
      canManageUsers: () => {
        const { user } = get()
        return (
          user?.roles?.includes('OWNER') || user?.roles?.includes('ADMIN') || false
        )
      },
      canWrite: () => {
        const { user } = get()
        return (
          user?.roles?.includes('OWNER') ||
          user?.roles?.includes('ADMIN') ||
          user?.roles?.includes('OPERATOR') ||
          false
        )
      },
    }),
    {
      name: 'rhinometric-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
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
