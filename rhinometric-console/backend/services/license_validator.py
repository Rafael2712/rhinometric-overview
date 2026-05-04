"""
License Validator for User/Role limits ? SERVICE-BASED MODEL.

Checks whether the current license plan allows creating
more users or assigning specific roles, using service-based
plan definitions (starter/growth/scale).

If the license is invalid/expired, user creation is blocked entirely.
"""

import logging
from typing import Tuple, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

logger = logging.getLogger("rhinometric.license_validator")

# ------------------------------------------------------------------
# Plan definitions ? SERVICE-BASED licensing
# ------------------------------------------------------------------
# Licensing plan limits + check intervals
# START   (starter) -> 25 monitors, 60s interval
# MEDIUM  (growth)  -> 50 monitors, 30s interval
# PRO     (scale)   -> 100 monitors, 15s interval
PLAN_DEFINITIONS = {
    "starter": {
        "max_services": 25,
        "check_interval_seconds": 60,
        "price_per_extra_service": 3.0,
        "plan_price_monthly": 109,
        "max_admins": 2,
        "max_operators": 3,
        "max_viewers": 5,
    },
    "growth": {
        "max_services": 50,
        "check_interval_seconds": 30,
        "price_per_extra_service": 2.5,
        "plan_price_monthly": 299,
        "max_admins": 5,
        "max_operators": 10,
        "max_viewers": 20,
    },
    "scale": {
        "max_services": 100,
        "check_interval_seconds": 15,
        "price_per_extra_service": 2.0,
        "plan_price_monthly": 599,
        "max_admins": 10,
        "max_operators": 25,
        "max_viewers": 50,
    },
}

# Map legacy plan names to new service-based plans
PLAN_ALIAS = {
    "community_trial": "starter",
    "trial": "starter",
    "annual_standard": "growth",
    "professional": "growth",
    "enterprise": "scale",
    "demo_cloud": "starter",
}

# Features mapping ? from license features to display modules
FEATURE_MODULE_MAP = {
    "monitoring": "Synthetic Monitoring",
    "alerting": "Alerts",
    "anomaly-detection": "AI Anomalies",
    "license-server": None,  # internal, not shown
}

# Always-on modules for this edition
DEFAULT_MODULES = [
    "Synthetic Monitoring",
    "Alerts",
    "Incidents",
    "SLO",
    "Backup",
]

DEFAULT_PLAN = "starter"


class LicenseLimitError(Exception):
    """Raised when an operation would exceed license limits."""
    pass


def _get_license_result():
    """Get current license validation result."""
    from utils.rust_license_validator import validate_license
    return validate_license()


def _resolve_plan(raw_plan: Optional[str]) -> str:
    """Resolve a Rust license plan name to a service-based plan."""
    if not raw_plan:
        return DEFAULT_PLAN
    normalized = raw_plan.lower().strip()
    if normalized in PLAN_DEFINITIONS:
        return normalized
    return PLAN_ALIAS.get(normalized, DEFAULT_PLAN)


def _get_plan_def(plan: str) -> dict:
    """Return the plan definition dict."""
    return PLAN_DEFINITIONS.get(plan, PLAN_DEFINITIONS[DEFAULT_PLAN])


def _count_active_users(db: Session) -> int:
    """Count current active (non-deleted) users."""
    from models.user import User
    return db.query(User).filter(
        User.is_active == True,
        User.is_deleted == False,
    ).count()


def _count_active_services(db: Session) -> int:
    """Count enabled external services ? source of truth for services_used."""
    from models.external_service import ExternalService
    return db.query(ExternalService).filter(
        ExternalService.enabled == True,
    ).count()


def _count_roles(db: Session) -> Dict[str, int]:
    """Count active users per role."""
    from models.user import User
    from models.role import Role, UserRole
    rows = (
        db.query(Role.name, sa_func.count(UserRole.user_id))
        .join(UserRole, Role.id == UserRole.role_id)
        .join(User, User.id == UserRole.user_id)
        .filter(User.is_active == True, User.is_deleted == False)
        .group_by(Role.name)
        .all()
    )
    return {name: cnt for name, cnt in rows}


def _resolve_features(raw_features: Optional[list]) -> List[str]:
    """Turn license feature keys into user-facing module names."""
    modules = set(DEFAULT_MODULES)
    if raw_features:
        for feat in raw_features:
            mapped = FEATURE_MODULE_MAP.get(feat)
            if mapped:
                modules.add(mapped)
    # AI Anomalies depends on "anomaly-detection" feature
    if raw_features and "anomaly-detection" in raw_features:
        modules.add("AI Anomalies")
    return sorted(modules)


# ------------------------------------------------------------------
# Public API ? consumed by routers/license.py
# ------------------------------------------------------------------

def get_license_status_payload(db: Session) -> Dict[str, Any]:
    """
    Build the full service-based license status payload.
    This is the SINGLE source of truth for the GET /api/license/status response.
    """
    lic = _get_license_result()

    # Resolve plan
    plan_name = _resolve_plan(lic.plan)
    plan_def = _get_plan_def(plan_name)

    # Services
    services_used = _count_active_services(db)
    max_services = plan_def["max_services"]
    remaining_services = max(0, max_services - services_used)
    extra_services_used = max(0, services_used - max_services)

    # Users / roles
    role_counts = _count_roles(db)
    owner_count = role_counts.get("OWNER", 0)
    admins_used = role_counts.get("ADMIN", 0)
    operators_used = role_counts.get("OPERATOR", 0)
    viewers_used = role_counts.get("VIEWER", 0)

    # Features / modules
    features = _resolve_features(lic.features)

    # Warnings
    warnings = []
    breaches = []

    if services_used > max_services:
        breaches.append(f"Service limit exceeded: {services_used}/{max_services}")
    elif max_services > 0 and services_used / max_services >= 0.8:
        warnings.append(f"Service usage at {services_used}/{max_services} ? approaching limit")

    if admins_used > plan_def["max_admins"]:
        breaches.append(f"Admin limit exceeded: {admins_used}/{plan_def['max_admins']}")
    if operators_used > plan_def["max_operators"]:
        breaches.append(f"Operator limit exceeded: {operators_used}/{plan_def['max_operators']}")
    if viewers_used > plan_def["max_viewers"]:
        breaches.append(f"Viewer limit exceeded: {viewers_used}/{plan_def['max_viewers']}")

    # Time / status
    from routers.license import _calculate_time_remaining
    days_remaining, hours_remaining = _calculate_time_remaining(lic.expires_at)

    if days_remaining is not None and 0 < days_remaining <= 7:
        warnings.append(f"License expires in {days_remaining} days")

    # Overall status
    if not lic.is_valid:
        status = lic.status
        is_valid = False
        message = lic.error_message or f"License is {lic.status}"
    else:
        status = "active"
        is_valid = True
        message = "License is active and valid"

    warning_text = "; ".join(breaches + warnings) if (breaches or warnings) else None

    return {
        # Plan
        "plan": plan_name,
        "plan_display": plan_name.capitalize(),
        "plan_price_monthly": plan_def["plan_price_monthly"],
        "currency": "EUR",

        # Services
        "max_services": max_services,
        "services_used": services_used,
        "remaining_services": remaining_services,
        "extra_services_used": extra_services_used,
        "price_per_extra_service": plan_def["price_per_extra_service"],
        "estimated_extra_cost": round(extra_services_used * plan_def["price_per_extra_service"], 2),
        "usage_status": "exceeded" if services_used > max_services else ("warning" if max_services > 0 and services_used > 0.8 * max_services else "ok"),

        # Users
        "users": {
            "owner": owner_count,
            "owner_limit": 1,
            "admins_used": admins_used,
            "admins_limit": plan_def["max_admins"],
            "operators_used": operators_used,
            "operators_limit": plan_def["max_operators"],
            "viewers_used": viewers_used,
            "viewers_limit": plan_def["max_viewers"],
        },

        # License metadata
        "tenant_id": lic.tenant_id,
        "organization": lic.customer,
        "expires_at": lic.expires_at,
        "issued_at": lic.issued_at,
        "edition": lic.plan or "community_trial",
        "features": features,

        # Status
        "status": status,
        "is_valid": is_valid,
        "message": message,
        "warning": warning_text,
        "days_remaining": days_remaining,
        "hours_remaining": hours_remaining,
        "validator": "rust" if lic.exit_code != -1 else "legacy",

        # Breach flags (soft ? no blocking)
        "breaches": breaches if breaches else None,
    }


def get_license_limits_summary(db: Session) -> Dict[str, Any]:
    """
    Return a summary of license limits vs current usage.
    Used by GET /api/license/limits.
    """
    lic = _get_license_result()
    plan_name = _resolve_plan(lic.plan)
    plan_def = _get_plan_def(plan_name)
    role_counts = _count_roles(db)
    services_used = _count_active_services(db)

    return {
        "plan": plan_name,
        "services": {
            "used": services_used,
            "limit": plan_def["max_services"],
            "extra": max(0, services_used - plan_def["max_services"]),
        },
        "roles": {
            "OWNER": {"used": role_counts.get("OWNER", 0), "limit": 1},
            "ADMIN": {"used": role_counts.get("ADMIN", 0), "limit": plan_def["max_admins"]},
            "OPERATOR": {"used": role_counts.get("OPERATOR", 0), "limit": plan_def["max_operators"]},
            "VIEWER": {"used": role_counts.get("VIEWER", 0), "limit": plan_def["max_viewers"]},
        },
    }


# ------------------------------------------------------------------
# User creation validation (used by users router)
# ------------------------------------------------------------------

def validate_user_roles(db: Session, role_names: List[str]) -> None:
    """
    Validate that creating a user with the given roles is allowed
    under the current license.

    Raises LicenseLimitError if:
      - License is invalid or expired
      - Adding a user would exceed role-specific limits
    """
    lic = _get_license_result()

    if not lic.is_valid:
        msg = f"License is {lic.status}. Cannot create users."
        if lic.error_message:
            msg += f" ({lic.error_message})"
        logger.warning(f"User creation blocked: {msg}")
        raise LicenseLimitError(msg)

    plan_name = _resolve_plan(lic.plan)
    plan_def = _get_plan_def(plan_name)
    role_counts = _count_roles(db)

    for role_name in role_names:
        upper = role_name.upper()
        if upper == "OWNER":
            if role_counts.get("OWNER", 0) >= 1:
                raise LicenseLimitError("Only one OWNER is allowed.")
        elif upper == "ADMIN":
            if role_counts.get("ADMIN", 0) >= plan_def["max_admins"]:
                raise LicenseLimitError(
                    f"Admin limit reached ({plan_def['max_admins']}). Upgrade your plan."
                )
        elif upper == "OPERATOR":
            if role_counts.get("OPERATOR", 0) >= plan_def["max_operators"]:
                raise LicenseLimitError(
                    f"Operator limit reached ({plan_def['max_operators']}). Upgrade your plan."
                )
        elif upper == "VIEWER":
            if role_counts.get("VIEWER", 0) >= plan_def["max_viewers"]:
                raise LicenseLimitError(
                    f"Viewer limit reached ({plan_def['max_viewers']}). Upgrade your plan."
                )

    logger.info(
        f"License check passed: plan={plan_name}, roles={role_names}"
    )


def can_add_user_with_role(db: Session, role_name: str) -> Tuple[bool, str]:
    """
    Check if we can add a user (or assign a role) under the current license.
    """
    try:
        validate_user_roles(db, [role_name])
        return True, ""
    except LicenseLimitError as e:
        return False, str(e)

# ----------------------------------------------------------------
# Licensing enforcement helpers (added by licensing task)
# ----------------------------------------------------------------

def get_plan_check_interval(db):
    # type: (Session) -> int
    """Return the check interval in seconds for the current plan.
    starter=60s, growth=30s, scale=15s"""
    lic = _get_license_result()
    plan_name = _resolve_plan(lic.plan)
    plan_def = _get_plan_def(plan_name)
    return int(plan_def.get('check_interval_seconds', 60))


def validate_service_creation(db):
    # type: (Session) -> None
    """Hard-enforce monitor limit. Raises LicenseLimitError if limit reached.
    Counts ALL services (enabled+disabled) to prevent bypass via toggling.
    starter->25, growth->50, scale->100"""
    from models.external_service import ExternalService as _ES
    lic = _get_license_result()
    plan_name = _resolve_plan(lic.plan)
    plan_def = _get_plan_def(plan_name)
    max_sv = plan_def['max_services']
    total = db.query(_ES).count()
    logger.info('[LicenseLimit] plan=%s limit=%d total=%d', plan_name, max_sv, total)
    if total >= max_sv:
        raise LicenseLimitError(
            'Monitor limit reached for your plan (%s: %d monitors). '
            'You have %d/%d monitors. Upgrade your plan to add more.' %
            (plan_name.upper(), max_sv, total, max_sv)
        )

