"""
License Validator for User/Role limits.

Checks whether the current license plan allows creating
more users or assigning specific roles.

Plan limits (max active users):
  - community_trial: 5 users
  - starter: 10 users
  - professional: 50 users
  - enterprise: unlimited

If the license is invalid/expired, user creation is blocked entirely.
"""

import logging
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("rhinometric.license_validator")

# ---------------------------------------------------------------------------
# Plan-based limits
# ---------------------------------------------------------------------------
PLAN_USER_LIMITS = {
    "community_trial": 5,
    "starter": 10,
    "professional": 50,
    "enterprise": 999999,  # effectively unlimited
}

DEFAULT_USER_LIMIT = 5  # fallback if plan is unknown


class LicenseLimitError(Exception):
    """Raised when an operation would exceed license limits."""
    pass


def _get_license_result():
    """Get current license validation result (cached per call)."""
    from utils.rust_license_validator import validate_license
    return validate_license()


def _count_active_users(db: Session) -> int:
    """Count current active (non-deleted) users in the database."""
    from models.user import User
    return db.query(User).filter(User.is_active == True).count()


def _get_max_users(plan: Optional[str]) -> int:
    """Return the max-users limit for a given plan name."""
    if not plan:
        return DEFAULT_USER_LIMIT
    return PLAN_USER_LIMITS.get(plan.lower(), DEFAULT_USER_LIMIT)


# ---------------------------------------------------------------------------
# Public API (used by routers/users.py)
# ---------------------------------------------------------------------------

def validate_user_roles(db: Session, role_names: List[str]) -> None:
    """
    Validate that creating a user with the given roles is allowed
    under the current license.

    Raises LicenseLimitError if:
      - License is invalid or expired
      - Adding one more user would exceed the plan's user limit

    Args:
        db: SQLAlchemy session
        role_names: List of role names to assign to the new user
    """
    lic = _get_license_result()

    # Block if license is not valid
    if not lic.is_valid:
        msg = f"License is {lic.status}. Cannot create users."
        if lic.error_message:
            msg += f" ({lic.error_message})"
        logger.warning(f"User creation blocked: {msg}")
        raise LicenseLimitError(msg)

    # Check user count limit
    max_users = _get_max_users(lic.plan)
    current_users = _count_active_users(db)

    if current_users >= max_users:
        msg = (
            f"License plan '{lic.plan}' allows a maximum of {max_users} users. "
            f"Currently {current_users} active users exist. "
            f"Please upgrade your license to add more users."
        )
        logger.warning(f"User creation blocked: {msg}")
        raise LicenseLimitError(msg)

    logger.info(
        f"License check passed: plan={lic.plan}, "
        f"users={current_users}/{max_users}, roles={role_names}"
    )


def can_add_user_with_role(db: Session, role_name: str) -> Tuple[bool, str]:
    """
    Check if we can add a user (or assign a role) under the current license.

    Returns:
        Tuple of (can_add: bool, error_message: str).
        If can_add is True, error_message is empty.
    """
    try:
        validate_user_roles(db, [role_name])
        return True, ""
    except LicenseLimitError as e:
        return False, str(e)
