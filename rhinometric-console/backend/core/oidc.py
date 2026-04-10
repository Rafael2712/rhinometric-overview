"""
Keycloak OIDC Token Validator for FastAPI.
Phase 1: Validates Keycloak-issued JWTs using JWKS public keys.

This module:
- Fetches and caches JWKS from Keycloak
- Validates RS256 tokens (Keycloak default)
- Extracts user claims (username, email, roles)
- Provides JIT user provisioning into local DB
"""

import os
import time
import logging
from typing import Optional, Dict, List, Any

import httpx
from jose import jwt, jwk, JWTError
from jose.utils import base64url_decode

logger = logging.getLogger("rhinometric.oidc")

# ============================================================
# Configuration (from environment variables)
# ============================================================

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "rhinometric")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "rhinometric-console")
OIDC_ENABLED = os.getenv("OIDC_ENABLED", "true").lower() == "true"

# Issuer as seen by PUBLIC clients (browser)
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://46.225.231.117:80")
KEYCLOAK_ISSUER = f"{KEYCLOAK_PUBLIC_URL}/auth/realms/{KEYCLOAK_REALM}"

# Internal JWKS URL (backend fetches keys from internal Docker network)
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_URL}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"

# JWKS cache duration (seconds)
JWKS_CACHE_TTL = 3600  # 1 hour


# ============================================================
# JWKS Key Cache
# ============================================================

class JWKSCache:
    """Caches JWKS keys from Keycloak to avoid per-request fetches."""
    
    def __init__(self):
        self._keys: Dict[str, Any] = {}
        self._last_fetch: float = 0
        self._ttl: int = JWKS_CACHE_TTL

    def _should_refresh(self) -> bool:
        return time.time() - self._last_fetch > self._ttl

    def _fetch_keys(self) -> None:
        """Fetch JWKS from Keycloak."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(KEYCLOAK_JWKS_URL)
                response.raise_for_status()
                jwks_data = response.json()
                
                self._keys = {}
                for key_data in jwks_data.get("keys", []):
                    kid = key_data.get("kid")
                    if kid:
                        self._keys[kid] = key_data
                
                self._last_fetch = time.time()
                logger.info(
                    f"[OIDC] Fetched {len(self._keys)} keys from JWKS endpoint"
                )
        except Exception as e:
            logger.error(f"[OIDC] Failed to fetch JWKS: {str(e)}")
            if not self._keys:
                raise

    def get_key(self, kid: str) -> Optional[Dict]:
        """Get a specific key by kid, refreshing cache if needed."""
        if self._should_refresh() or kid not in self._keys:
            self._fetch_keys()
        return self._keys.get(kid)

    def clear(self):
        """Force cache clear."""
        self._keys = {}
        self._last_fetch = 0


# Global JWKS cache instance
_jwks_cache = JWKSCache()


# ============================================================
# Token Validation
# ============================================================

def is_keycloak_token(token: str) -> bool:
    """
    Quick check if a JWT was issued by Keycloak (RS256 algorithm).
    Local tokens use HS256.
    """
    try:
        header = jwt.get_unverified_header(token)
        return header.get("alg") in ("RS256", "RS384", "RS512")
    except Exception:
        return False


def validate_keycloak_token(token: str) -> Dict[str, Any]:
    """
    Validate a Keycloak-issued JWT token.
    
    Returns decoded claims dict if valid.
    Raises JWTError if invalid.
    """
    if not OIDC_ENABLED:
        raise JWTError("OIDC is disabled")

    # Get the key ID from token header
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "RS256")
    except Exception as e:
        raise JWTError(f"Invalid token header: {str(e)}")

    if not kid:
        raise JWTError("Token missing 'kid' header")

    # Get the public key from JWKS cache
    key_data = _jwks_cache.get_key(kid)
    if not key_data:
        raise JWTError(f"Unknown key ID: {kid}")

    # Decode and validate the token
    # Note: Keycloak access tokens for public clients may not include 'aud'.
    # We validate 'azp' (authorized party) instead.
    try:
        claims = jwt.decode(
            token,
            key_data,
            algorithms=[alg],
            issuer=KEYCLOAK_ISSUER,
            options={
                "verify_aud": False,  # KC public clients omit aud
                "verify_iss": True,
                "verify_exp": True,
                "verify_iat": True,
            }
        )

        # Verify authorized party (azp) matches our client_id
        azp = claims.get("azp")
        if azp and azp != KEYCLOAK_CLIENT_ID:
            raise JWTError(
                f"Token azp '{azp}' does not match client '{KEYCLOAK_CLIENT_ID}'"
            )

        return claims
    except JWTError:
        raise
    except Exception as e:
        raise JWTError(f"Token validation failed: {str(e)}")


def extract_user_info(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from Keycloak token claims.
    
    Returns:
        {
            "username": "admin",
            "email": "admin@rhinometric.local",
            "full_name": "System Administrator",
            "keycloak_sub": "uuid-from-keycloak",
            "roles": ["admin", "operator"],
            "email_verified": true
        }
    """
    # Extract realm roles from token
    realm_roles = claims.get("realm_roles", [])
    
    # Fallback: check realm_access.roles (standard Keycloak claim)
    if not realm_roles:
        realm_access = claims.get("realm_access", {})
        realm_roles = realm_access.get("roles", [])
    
    # Filter to our known roles only
    known_roles = {"admin", "operator", "viewer"}
    user_roles = [r for r in realm_roles if r.lower() in known_roles]
    
    return {
        "username": claims.get("preferred_username", claims.get("sub")),
        "email": claims.get("email", ""),
        "full_name": f"{claims.get('given_name', '')} {claims.get('family_name', '')}".strip(),
        "keycloak_sub": claims.get("sub"),
        "roles": user_roles,
        "email_verified": claims.get("email_verified", False),
    }


# ============================================================
# Keycloak Role -> Local Role Mapping
# ============================================================

ROLE_MAP = {
    "admin": "OWNER",     # Keycloak 'admin' -> local OWNER
    "operator": "OPERATOR",
    "viewer": "VIEWER",
}

def map_keycloak_roles(kc_roles: List[str]) -> List[str]:
    """Map Keycloak realm roles to local role names."""
    mapped = []
    for role in kc_roles:
        local_role = ROLE_MAP.get(role.lower())
        if local_role:
            mapped.append(local_role)
    
    # Default to VIEWER if no known roles
    if not mapped:
        mapped = ["VIEWER"]
    
    return mapped