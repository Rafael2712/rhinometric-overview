"""
Keycloak Admin API client.
Syncs platform user operations (create, delete, role changes) with Keycloak.
Keycloak is the ONLY source of truth for user identity and authentication.
"""
import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger("rhinometric.keycloak_admin")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "rhinometric")
KC_ADMIN_USER = os.getenv("KC_ADMIN_USER", "admin")
KC_ADMIN_PASSWORD = os.getenv("KC_ADMIN_PASSWORD", "Rh1n0K3ycl0ak2026!")

ADMIN_API = f"{KEYCLOAK_URL}/auth/admin/realms/{KEYCLOAK_REALM}"
MASTER_TOKEN_URL = f"{KEYCLOAK_URL}/auth/realms/master/protocol/openid-connect/token"


class KeycloakAdminError(Exception):
    pass


def _get_admin_token() -> str:
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(MASTER_TOKEN_URL, data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": KC_ADMIN_USER,
            "password": KC_ADMIN_PASSWORD,
        })
        if resp.status_code != 200:
            raise KeycloakAdminError(f"KC admin token failed: {resp.status_code}")
        return resp.json()["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_admin_token()}",
        "Content-Type": "application/json",
    }


PLATFORM_ROLES = {"owner", "admin", "operator", "viewer"}


# ---------- user operations ----------

def create_kc_user(
    username: str,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    role_name: str = "viewer",
) -> str:
    """Create user in KC. Returns KC user UUID."""
    headers = _headers()
    payload = {
        "username": username,
        "email": email,
        "emailVerified": True,
        "enabled": True,
        "firstName": first_name,
        "lastName": last_name,
        "credentials": [{"type": "password", "value": password, "temporary": True}],
    }
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(f"{ADMIN_API}/users", json=payload, headers=headers)
        if resp.status_code == 409:
            logger.warning("[KC] User %s already exists, updating", email)
            kc_user = find_kc_user(email=email) or find_kc_user(username=username)
            if not kc_user:
                raise KeycloakAdminError(f"KC conflict but user not found: {username}")
            kc_id = kc_user["id"]
            client.put(f"{ADMIN_API}/users/{kc_id}", json={
                "enabled": True, "email": email, "emailVerified": True,
                "firstName": first_name, "lastName": last_name,
            }, headers=headers)
            client.put(f"{ADMIN_API}/users/{kc_id}/reset-password", json={
                "type": "password", "value": password, "temporary": True,
            }, headers=headers)
        elif resp.status_code == 201:
            loc = resp.headers.get("Location", "")
            kc_id = loc.rstrip("/").split("/")[-1] if loc else None
            if not kc_id:
                found = find_kc_user(email=email)
                kc_id = found["id"] if found else None
            if not kc_id:
                raise KeycloakAdminError("Created KC user but could not find ID")
        else:
            raise KeycloakAdminError(f"create_kc_user failed: {resp.status_code} {resp.text}")
        _set_realm_role(client, headers, kc_id, role_name.lower())
        logger.info("[KC] Created user %s (%s) role=%s kc_id=%s", username, email, role_name, kc_id)
        return kc_id


def find_kc_user(email: str = None, username: str = None) -> Optional[dict]:
    headers = _headers()
    with httpx.Client(timeout=10.0) as client:
        if email:
            r = client.get(f"{ADMIN_API}/users", params={"email": email, "exact": "true"}, headers=headers)
            r.raise_for_status()
            if r.json():
                return r.json()[0]
        if username:
            r = client.get(f"{ADMIN_API}/users", params={"username": username, "exact": "true"}, headers=headers)
            r.raise_for_status()
            if r.json():
                return r.json()[0]
    return None


def update_kc_user(kc_id: str, **kwargs):
    """Update KC user fields (email, firstName, lastName, enabled)."""
    payload = {k: v for k, v in kwargs.items() if v is not None}
    if not payload:
        return
    headers = _headers()
    with httpx.Client(timeout=10.0) as client:
        resp = client.put(f"{ADMIN_API}/users/{kc_id}", json=payload, headers=headers)
        resp.raise_for_status()
    logger.info("[KC] Updated %s: %s", kc_id, list(payload.keys()))


def disable_kc_user(kc_id: str):
    update_kc_user(kc_id, enabled=False)


def enable_kc_user(kc_id: str):
    update_kc_user(kc_id, enabled=True)


def delete_kc_user(kc_id: str):
    """Permanently delete user from Keycloak."""
    headers = _headers()
    with httpx.Client(timeout=10.0) as client:
        resp = client.delete(f"{ADMIN_API}/users/{kc_id}", headers=headers)
        if resp.status_code not in (200, 204, 404):
            raise KeycloakAdminError(f"delete failed: {resp.status_code}")
    logger.info("[KC] Deleted user %s", kc_id)


# ---------- password operations ----------

def set_kc_user_password(kc_id: str, password: str, temporary: bool = True):
    """Set a user's password in Keycloak via Admin API."""
    headers = _headers()
    payload = {
        "type": "password",
        "value": password,
        "temporary": temporary,
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.put(
            f"{ADMIN_API}/users/{kc_id}/reset-password",
            json=payload,
            headers=headers,
        )
        if resp.status_code not in (200, 204):
            raise KeycloakAdminError(
                f"set_kc_user_password failed: {resp.status_code} {resp.text}"
            )
    logger.info("[KC] Password set for user %s (temporary=%s)", kc_id, temporary)


def send_kc_reset_password_email(kc_id: str):
    """
    Trigger Keycloak's built-in 'UPDATE_PASSWORD' required action email.
    Requires SMTP configured in Keycloak realm settings.
    """
    headers = _headers()
    with httpx.Client(timeout=15.0) as client:
        resp = client.put(
            f"{ADMIN_API}/users/{kc_id}/execute-actions-email",
            json=["UPDATE_PASSWORD"],
            headers=headers,
        )
        if resp.status_code not in (200, 204):
            raise KeycloakAdminError(
                f"send_kc_reset_password_email failed: {resp.status_code} {resp.text}"
            )
    logger.info("[KC] Reset password email triggered for user %s", kc_id)


# ---------- role operations ----------

def _set_realm_role(client, headers, kc_id: str, role_name: str):
    """Replace all custom realm roles with the given one."""
    resp = client.get(f"{ADMIN_API}/users/{kc_id}/role-mappings/realm", headers=headers)
    resp.raise_for_status()
    to_remove = [r for r in resp.json() if r["name"].lower() in PLATFORM_ROLES]
    if to_remove:
        # httpx Client.delete() does not support json= parameter;
        # use client.request("DELETE", ...) for DELETE with a body.
        client.request(
            "DELETE",
            f"{ADMIN_API}/users/{kc_id}/role-mappings/realm",
            json=to_remove,
            headers=headers,
        )
    resp = client.get(f"{ADMIN_API}/roles/{role_name}", headers=headers)
    if resp.status_code == 404:
        logger.warning("[KC] Role '%s' not found", role_name)
        return
    resp.raise_for_status()
    client.post(f"{ADMIN_API}/users/{kc_id}/role-mappings/realm", json=[resp.json()], headers=headers)


def set_kc_user_role(kc_id: str, role_name: str):
    headers = _headers()
    with httpx.Client(timeout=15.0) as client:
        _set_realm_role(client, headers, kc_id, role_name.lower())
    logger.info("[KC] Set role %s for %s", role_name, kc_id)
