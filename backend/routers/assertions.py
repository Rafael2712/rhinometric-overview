"""
Assertions router — CRUD for service assertion definitions.

All endpoints are nested under /api/external-services/{service_id}/assertions.

Auth:
  - GET (list, detail, history): any authenticated user (VIEWER+)
  - POST / PUT / DELETE:         ADMIN or OWNER only

v1 assertion types (fixed):
  - status_code      (operator: equals)
  - response_time    (operator: less_than)
  - text_contains    (operator: contains)
  - json_path_equals (operator: equals)
"""

import re
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from database import get_db
from routers.auth import get_current_user, require_role
from models.user import User as UserModel
from models.external_service import ExternalService
from models.service_assertion import ServiceAssertion
from models.assertion_result import AssertionResult
from models.external_service_check import ExternalServiceCheck

logger = logging.getLogger("rhinometric.assertions")

router = APIRouter()

# Role guards
admin_only = require_role(["OWNER", "ADMIN"])

# ── Validation constants ─────────────────────────────────────────

VALID_TYPES = {"status_code", "response_time", "text_contains", "json_path_equals"}
TYPE_OPERATOR_MAP = {
    "status_code": "equals",
    "response_time": "less_than",
    "text_contains": "contains",
    "json_path_equals": "equals",
}
VALID_SEVERITIES = {"info", "warning", "critical"}

# Simple dot-notation JSON path: $.key.subkey[0].name
_SIMPLE_PATH_RE = re.compile(r'^\$(\.[a-zA-Z_][a-zA-Z0-9_]*(\[\d+\])?)+$')


# ── Pydantic schemas ─────────────────────────────────────────────

class AssertionCreate(BaseModel):
    assertion_type: str = Field(..., description="One of: status_code, response_time, text_contains, json_path_equals")
    expected_value: str = Field(..., min_length=1, max_length=1000)
    json_path: Optional[str] = Field(None, max_length=500)
    name: Optional[str] = Field(None, max_length=255)
    severity: str = Field("warning")
    enabled: bool = True
    order: int = Field(0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_assertion(self):
        # Validate type
        if self.assertion_type not in VALID_TYPES:
            raise ValueError(f"assertion_type must be one of {sorted(VALID_TYPES)}")

        # Validate severity
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")

        # json_path required for json_path_equals
        if self.assertion_type == "json_path_equals":
            if not self.json_path:
                raise ValueError("json_path is required for json_path_equals assertions")
            if not _SIMPLE_PATH_RE.match(self.json_path):
                raise ValueError(
                    "Invalid JSON path. v1 supports simple dot notation only: "
                    "$.key.subkey or $.items[0].id"
                )

        # status_code must be integer 100-599
        if self.assertion_type == "status_code":
            try:
                code = int(self.expected_value)
                if code < 100 or code > 599:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError("expected_value for status_code must be an integer between 100 and 599")

        # response_time must be positive number
        if self.assertion_type == "response_time":
            try:
                val = float(self.expected_value)
                if val <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError("expected_value for response_time must be a positive number (ms)")

        return self


class AssertionUpdate(BaseModel):
    expected_value: Optional[str] = Field(None, max_length=1000)
    json_path: Optional[str] = Field(None, max_length=500)
    name: Optional[str] = Field(None, max_length=255)
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    order: Optional[int] = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_update(self):
        if self.severity is not None and self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}")
        if self.json_path is not None and self.json_path != "":
            if not _SIMPLE_PATH_RE.match(self.json_path):
                raise ValueError(
                    "Invalid JSON path. v1 supports simple dot notation only: "
                    "$.key.subkey or $.items[0].id"
                )
        return self


class BulkAssertionCreate(BaseModel):
    assertions: List[AssertionCreate] = Field(..., min_length=1, max_length=20)


class AssertionResponse(BaseModel):
    id: str
    service_id: int
    assertion_type: str
    operator: str
    expected_value: str
    json_path: Optional[str]
    name: Optional[str]
    enabled: bool
    severity: str
    order: int
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class AssertionResultResponse(BaseModel):
    id: str
    check_id: int
    assertion_id: str
    service_id: int
    assertion_type: str
    assertion_name: Optional[str]
    expected_value: str
    actual_value: Optional[str]
    error_message: Optional[str]
    evaluated_at: Optional[str]

    class Config:
        from_attributes = True


# ── Helper ────────────────────────────────────────────────────────

def _get_service_or_404(service_id: int, db: Session) -> ExternalService:
    svc = db.query(ExternalService).filter(ExternalService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
    return svc


def _get_assertion_or_404(assertion_id: UUID, service_id: int, db: Session) -> ServiceAssertion:
    a = (
        db.query(ServiceAssertion)
        .filter(ServiceAssertion.id == assertion_id, ServiceAssertion.service_id == service_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail=f"Assertion {assertion_id} not found for service {service_id}")
    return a


# ── CRUD Endpoints ────────────────────────────────────────────────

@router.get(
    "/external-services/{service_id}/assertions",
    response_model=List[AssertionResponse],
    summary="List assertions for a service",
)
def list_assertions(
    service_id: int,
    enabled_only: bool = Query(False, description="Filter to enabled assertions only"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _get_service_or_404(service_id, db)
    query = db.query(ServiceAssertion).filter(ServiceAssertion.service_id == service_id)
    if enabled_only:
        query = query.filter(ServiceAssertion.enabled == True)
    assertions = query.order_by(ServiceAssertion.order, ServiceAssertion.created_at).all()
    return [a.to_dict() for a in assertions]


@router.post(
    "/external-services/{service_id}/assertions",
    response_model=AssertionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assertion",
)
def create_assertion(
    service_id: int,
    body: AssertionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    svc = _get_service_or_404(service_id, db)

    # Validate type is applicable to service_type
    if svc.service_type and hasattr(svc.service_type, 'value'):
        svc_type = svc.service_type.value
    else:
        svc_type = str(svc.service_type)

    if svc_type == "postgresql" and body.assertion_type not in ("response_time",):
        raise HTTPException(
            status_code=400,
            detail=f"assertion_type '{body.assertion_type}' is not supported for PostgreSQL services. "
                   f"Only 'response_time' is available.",
        )

    operator = TYPE_OPERATOR_MAP[body.assertion_type]

    assertion = ServiceAssertion(
        service_id=service_id,
        assertion_type=body.assertion_type,
        operator=operator,
        expected_value=body.expected_value.strip(),
        json_path=body.json_path.strip() if body.json_path else None,
        name=body.name.strip() if body.name else None,
        enabled=body.enabled,
        severity=body.severity,
        order=body.order,
    )
    db.add(assertion)
    db.commit()
    db.refresh(assertion)

    logger.info(
        f"Assertion created: {assertion.assertion_type} "
        f"for service '{svc.name}' (id={service_id}) "
        f"by user={current_user.username}"
    )
    return assertion.to_dict()


@router.put(
    "/external-services/{service_id}/assertions/{assertion_id}",
    response_model=AssertionResponse,
    summary="Update an assertion",
)
def update_assertion(
    service_id: int,
    assertion_id: UUID,
    body: AssertionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    _get_service_or_404(service_id, db)
    assertion = _get_assertion_or_404(assertion_id, service_id, db)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # If updating json_path on a non-json_path assertion, reject
    if "json_path" in updates and assertion.assertion_type != "json_path_equals":
        raise HTTPException(status_code=400, detail="json_path can only be set on json_path_equals assertions")

    # Validate expected_value changes per type
    if "expected_value" in updates:
        val = updates["expected_value"].strip()
        if assertion.assertion_type == "status_code":
            try:
                code = int(val)
                if code < 100 or code > 599:
                    raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="expected_value must be integer 100-599 for status_code")
        elif assertion.assertion_type == "response_time":
            try:
                f = float(val)
                if f <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="expected_value must be positive number for response_time")
        updates["expected_value"] = val

    for field, value in updates.items():
        setattr(assertion, field, value)

    db.commit()
    db.refresh(assertion)

    logger.info(
        f"Assertion updated: {assertion.id} ({assertion.assertion_type}) "
        f"for service_id={service_id} by user={current_user.username}"
    )
    return assertion.to_dict()


@router.delete(
    "/external-services/{service_id}/assertions/{assertion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assertion",
)
def delete_assertion(
    service_id: int,
    assertion_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    _get_service_or_404(service_id, db)
    assertion = _get_assertion_or_404(assertion_id, service_id, db)

    db.delete(assertion)
    db.commit()

    logger.info(
        f"Assertion deleted: {assertion_id} ({assertion.assertion_type}) "
        f"for service_id={service_id} by user={current_user.username}"
    )
    return None


@router.post(
    "/external-services/{service_id}/assertions/bulk",
    response_model=List[AssertionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk replace all assertions for a service",
)
def bulk_replace_assertions(
    service_id: int,
    body: BulkAssertionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_only),
):
    svc = _get_service_or_404(service_id, db)

    if svc.service_type and hasattr(svc.service_type, 'value'):
        svc_type = svc.service_type.value
    else:
        svc_type = str(svc.service_type)

    # Validate all assertions before any writes
    for item in body.assertions:
        if svc_type == "postgresql" and item.assertion_type not in ("response_time",):
            raise HTTPException(
                status_code=400,
                detail=f"assertion_type '{item.assertion_type}' is not supported for PostgreSQL services.",
            )

    # Delete existing assertions for this service
    db.query(ServiceAssertion).filter(ServiceAssertion.service_id == service_id).delete()

    # Create new ones
    created = []
    for item in body.assertions:
        operator = TYPE_OPERATOR_MAP[item.assertion_type]
        assertion = ServiceAssertion(
            service_id=service_id,
            assertion_type=item.assertion_type,
            operator=operator,
            expected_value=item.expected_value.strip(),
            json_path=item.json_path.strip() if item.json_path else None,
            name=item.name.strip() if item.name else None,
            enabled=item.enabled,
            severity=item.severity,
            order=item.order,
        )
        db.add(assertion)
        created.append(assertion)

    db.commit()
    for a in created:
        db.refresh(a)

    logger.info(
        f"Bulk assertion replace: {len(created)} assertions "
        f"for service '{svc.name}' (id={service_id}) by user={current_user.username}"
    )
    return [a.to_dict() for a in created]


# ── Read-only Endpoints ───────────────────────────────────────────

@router.get(
    "/external-services/{service_id}/checks/{check_id}/assertion-results",
    response_model=List[AssertionResultResponse],
    summary="Get assertion failure details for a specific check",
)
def get_assertion_results_for_check(
    service_id: int,
    check_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _get_service_or_404(service_id, db)

    # Verify check belongs to this service
    check = (
        db.query(ExternalServiceCheck)
        .filter(ExternalServiceCheck.id == check_id, ExternalServiceCheck.service_id == service_id)
        .first()
    )
    if not check:
        raise HTTPException(status_code=404, detail=f"Check {check_id} not found for service {service_id}")

    results = (
        db.query(AssertionResult)
        .filter(AssertionResult.check_id == check_id)
        .order_by(AssertionResult.evaluated_at)
        .all()
    )
    return [r.to_dict() for r in results]


@router.get(
    "/external-services/{service_id}/assertion-history",
    summary="Assertion pass/fail timeline for a service",
)
def get_assertion_history(
    service_id: int,
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours"),
    limit: int = Query(100, ge=1, le=1000, description="Max check records to return"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _get_service_or_404(service_id, db)

    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Get checks that had assertions evaluated
    checks = (
        db.query(ExternalServiceCheck)
        .filter(
            ExternalServiceCheck.service_id == service_id,
            ExternalServiceCheck.checked_at >= cutoff,
            ExternalServiceCheck.assertions_total > 0,
        )
        .order_by(ExternalServiceCheck.checked_at.desc())
        .limit(limit)
        .all()
    )

    total_checks = len(checks)
    all_passed = sum(1 for c in checks if c.assertions_failed == 0)
    some_failed = total_checks - all_passed
    pass_rate = round(all_passed / total_checks, 4) if total_checks > 0 else 1.0

    timeline = []
    for c in checks:
        entry = {
            "check_id": c.id,
            "checked_at": c.checked_at.isoformat() if c.checked_at else None,
            "status": c.status,
            "assertions_total": c.assertions_total,
            "assertions_passed": c.assertions_passed,
            "assertions_failed": c.assertions_failed,
            "first_failed_assertion": c.first_failed_assertion,
            "first_failed_message": c.first_failed_message,
        }
        timeline.append(entry)

    return {
        "service_id": service_id,
        "period_hours": hours,
        "total_checks": total_checks,
        "all_passed": all_passed,
        "some_failed": some_failed,
        "pass_rate": pass_rate,
        "timeline": timeline,
    }
