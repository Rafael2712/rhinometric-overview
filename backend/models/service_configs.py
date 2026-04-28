"""
Pydantic validation models for External Service configurations.

Enforces strict schema validation for HTTP and PostgreSQL service types.
Ensures only valid configurations can be stored in the database.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict
from urllib.parse import urlparse


# ── HTTP Service Config ──────────────────────────────────────────

ALLOWED_HTTP_METHODS = frozenset({"GET", "POST", "HEAD"})
ALLOWED_AUTH_TYPES = frozenset({"bearer", "api_key", "basic"})


class HttpServiceConfig(BaseModel):
    """Strict schema for HTTP/HTTPS service configurations."""

    url: str = Field(..., min_length=1, description="Target URL (http or https)")
    method: str = Field(default="GET", description="HTTP method: GET, POST, or HEAD")
    health_path: Optional[str] = Field(default=None, description="Health-check sub-path")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Custom HTTP headers")
    auth_type: Optional[str] = Field(default=None, description="Auth type: bearer, api_key, basic")
    auth_value: Optional[str] = Field(default=None, description="Auth credential value")
    skip_tls_verify: bool = Field(default=False, description="Skip TLS certificate verification")

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url must not be empty")
        try:
            parsed = urlparse(v)
        except Exception:
            raise ValueError("url is not a valid URL")
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"url must use http or https scheme, got: {scheme!r}")
        if not parsed.hostname:
            raise ValueError("url must contain a valid hostname")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        upper = v.strip().upper()
        if upper not in ALLOWED_HTTP_METHODS:
            raise ValueError(f"method must be one of {sorted(ALLOWED_HTTP_METHODS)}, got: {v!r}")
        return upper

    @field_validator("auth_type")
    @classmethod
    def validate_auth_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        lower = v.strip().lower()
        if lower not in ALLOWED_AUTH_TYPES:
            raise ValueError(f"auth_type must be one of {sorted(ALLOWED_AUTH_TYPES)}, got: {v!r}")
        return lower

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, v):
        if v is None:
            return None
        if not isinstance(v, dict):
            raise ValueError("headers must be a dictionary")
        for k, val in v.items():
            if not isinstance(k, str) or not isinstance(val, str):
                raise ValueError("headers keys and values must be strings")
        return v


# ── PostgreSQL Service Config ────────────────────────────────────

VALID_SSL_MODES = frozenset({"disable", "prefer", "require", "verify-ca", "verify-full"})


class PostgresServiceConfig(BaseModel):
    """Strict schema for PostgreSQL service configurations."""

    host: str = Field(..., min_length=1, description="Database hostname")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database_name: str = Field(..., min_length=1, description="Database name")
    username: str = Field(..., min_length=1, description="Database user")
    password: Optional[str] = Field(default=None, description="Database password")
    ssl_mode: Optional[str] = Field(default=None, description="SSL mode")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("host must not be empty")
        return v

    @field_validator("database_name")
    @classmethod
    def validate_database_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("database_name must not be empty")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username must not be empty")
        return v

    @field_validator("ssl_mode")
    @classmethod
    def validate_ssl_mode(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        lower = v.strip().lower()
        if lower not in VALID_SSL_MODES:
            raise ValueError(
                f"ssl_mode must be one of {sorted(VALID_SSL_MODES)}, got: {v!r}"
            )
        return lower
