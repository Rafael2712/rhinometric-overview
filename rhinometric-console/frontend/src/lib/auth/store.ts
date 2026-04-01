import { create } from 'zustand'
import { useState, useEffect } from 'react'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  roles: string[] // ['OWNER', 'ADMIN', 'OPERATOR', 'VIEWER']
  must_change_password: boolean
  last_login?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  mustChangePassword: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
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
      login: async (username: string, password: string) => {
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              username,
              password,
            }),
          })

          if (!response.ok) {
            throw new Error('Invalid credentials')
          }

          const data = await response.json()
          
          // Fetch user details with roles
          const userResponse = await fetch('/api/auth/me', {
            headers: {
              'Authorization': `Bearer ${data.access_token}`
            }
          })
          
          if (!userResponse.ok) {
            throw new Error('Failed to fetch user details')
          }
          
          const user: User = await userResponse.json()
          
          set({ 
            user, 
            token: data.access_token, 
            isAuthenticated: true,
            mustChangePassword: data.must_change_password || false
          })
        } catch (error) {
          throw new Error('Invalid credentials')
        }
      },
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false, mustChangePassword: false })
      },
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
        return user?.roles?.includes('ADMIN') || user?.roles?.includes('OWNER') || false
      },
      canManageUsers: () => {
        const { user } = get()
        return user?.roles?.includes('OWNER') || user?.roles?.includes('ADMIN') || false
      }
    }),
    {
      name: 'rhinometric-auth',
    }
  )
)

// Hydration gate – blocks renders/fetches until persist has restored state from localStorage
export const useHasHydrated = (): boolean => {
  const [hydrated, setHydrated] = useState(useAuthStore.persist.hasHydrated())
  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => setHydrated(true))
    // Safety: in case hydration finished between useState init and this effect
    if (useAuthStore.persist.hasHydrated()) setHydrated(true)
    return unsub
  }, [])
  return hydrated
}
