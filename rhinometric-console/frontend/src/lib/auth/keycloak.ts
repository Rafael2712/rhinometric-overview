/**
 * Keycloak OIDC integration module.
 * Phase 1: Manages Keycloak initialization, token lifecycle, and auth state.
 */
import Keycloak from 'keycloak-js'

// Keycloak instance (singleton)
let _keycloak: Keycloak | null = null
let _initPromise: Promise<boolean> | null = null

// Token refresh callback - allows auth store to sync refreshed tokens
type TokenRefreshCb = (token: string) => void
let _onTokenRefreshed: TokenRefreshCb | null = null

/**
 * Register a callback invoked whenever the Keycloak adapter refreshes the token.
 * Used by the auth store to keep its copy of the token in sync.
 */
export function onTokenRefreshed(cb: TokenRefreshCb): void {
  _onTokenRefreshed = cb
}

export interface KeycloakConfig {
  enabled: boolean
  keycloak_url: string
  realm: string
  client_id: string
}

/**
 * Fetch OIDC config from backend.
 */
export async function fetchOidcConfig(): Promise<KeycloakConfig> {
  const resp = await fetch('/api/auth/oidc/config')
  if (!resp.ok) {
    throw new Error('Failed to fetch OIDC config')
  }
  return resp.json()
}

/**
 * Get the singleton Keycloak instance, creating it if needed.
 */
export function getKeycloak(): Keycloak | null {
  return _keycloak
}

/**
 * Initialize Keycloak. Returns true if user is authenticated.
 * Uses check-sso to silently check if user has an existing session.
 */
export async function initKeycloak(config: KeycloakConfig): Promise<boolean> {
  if (_initPromise) return _initPromise

  _keycloak = new Keycloak({
    url: config.keycloak_url,
    realm: config.realm,
    clientId: config.client_id,
  })

  _initPromise = _keycloak.init({
    onLoad: 'check-sso',
    pkceMethod: 'S256',
    checkLoginIframe: false,
    silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
  })

  const authenticated = await _initPromise

  if (authenticated) {
    // Set up token refresh
    _setupTokenRefresh()
  }

  return authenticated
}

/**
 * Trigger Keycloak login redirect.
 */
export function keycloakLogin(returnTo?: string): void {
  if (_keycloak) {
    const redirectUri = returnTo
      ? window.location.origin + returnTo
      : window.location.origin + '/'
    _keycloak.login({ redirectUri })
  }
}

/**
 * Trigger Keycloak logout.
 */
export function keycloakLogout(): void {
  if (_keycloak) {
    _keycloak.logout({ redirectUri: window.location.origin + '/login' })
  }
}

/**
 * Get the current access token (refreshing if needed).
 */
export async function getAccessToken(): Promise<string | undefined> {
  if (!_keycloak || !_keycloak.authenticated) return undefined

  try {
    // Refresh token if it expires within 30 seconds
    await _keycloak.updateToken(30)
    return _keycloak.token
  } catch {
    // Token refresh failed - session expired
    keycloakLogin()
    return undefined
  }
}

/**
 * Set up automatic token refresh.
 */
function _setupTokenRefresh(): void {
  if (!_keycloak) return

  // Refresh token every 60 seconds
  setInterval(async () => {
    if (_keycloak?.authenticated) {
      try {
        await _keycloak.updateToken(70)
      } catch {
        console.warn('[KC] Token refresh failed, session may have expired')
      }
    }
  }, 60000)

  // Sync refreshed token to auth store on auto-refresh
  _keycloak.onAuthRefreshSuccess = () => {
    if (_keycloak?.token && _onTokenRefreshed) {
      _onTokenRefreshed(_keycloak.token)
    }
  }

  // Handle token expiry events
  _keycloak.onTokenExpired = () => {
    console.warn('[KC] Token expired, attempting refresh...')
    _keycloak?.updateToken(5).catch(() => {
      console.error('[KC] Token refresh failed after expiry')
      keycloakLogout()
    })
  }

  _keycloak.onAuthLogout = () => {
    console.warn('[KC] Session ended by Keycloak')
    window.location.href = '/login'
  }
}
