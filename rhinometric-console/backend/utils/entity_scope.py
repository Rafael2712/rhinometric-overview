"""
ENTITY SCOPE — Central classification for Rhinometric monitored entities.

Every monitored entity (service, exporter, probe) is classified as either:
  PLATFORM  – Rhinometric-managed infrastructure (never consumes licensed hosts)
  CUSTOMER  – Customer-managed services (counted toward max_hosts)

Classification is deterministic via the PLATFORM_JOBS set — any Prometheus
job NOT in that set is automatically CUSTOMER.

The get_visible_entities() filter controls what the UI sees based on
deployment_mode:
  ON_PREMISE          → PLATFORM + CUSTOMER  (customer sees full stack)
  SAAS_SINGLE_TENANT  → CUSTOMER only        (customer sees only their services)
"""

from enum import Enum
from typing import List, Dict, Any, Optional


# ═══════════════════════════════════════════════════════════════
# ENUM
# ═══════════════════════════════════════════════════════════════

class EntityScope(str, Enum):
    """Scope classification for a monitored entity."""
    PLATFORM = "PLATFORM"
    CUSTOMER = "CUSTOMER"


# ═══════════════════════════════════════════════════════════════
# PLATFORM JOB REGISTRY  (single source of truth)
# ═══════════════════════════════════════════════════════════════
# Any Prometheus job whose name appears here is PLATFORM-managed.
# Everything else is CUSTOMER by default.
#
# To add a new internal service, just add its job name here.

PLATFORM_JOBS = frozenset({
    # Core observability stack
    "prometheus",
    "grafana",
    "loki",
    "jaeger",
    "alertmanager",
    "otel-collector",
    "promtail",

    # Rhinometric application services
    "console-backend",
    "license-server-v2",
    "ai-anomaly",

    # Infrastructure data stores
    "postgres",
    "redis",
})

# Infrastructure exporters — PLATFORM but excluded from the services list
INFRA_JOBS = frozenset({
    "node-exporter",
    "cadvisor",
    "blackbox-exporter",
})

# Internal probe jobs — PLATFORM
INTERNAL_PROBE_JOBS = frozenset({
    "blackbox-http",
})

# Convenience unions
ALL_INTERNAL_JOBS = PLATFORM_JOBS | INFRA_JOBS | INTERNAL_PROBE_JOBS
ALL_PLATFORM_JOBS = ALL_INTERNAL_JOBS  # alias

# Pre-built regex fragments for PromQL
EXCLUDE_REGEX = "|".join(sorted(ALL_INTERNAL_JOBS))
PLATFORM_REGEX = "|".join(sorted(PLATFORM_JOBS))


# ═══════════════════════════════════════════════════════════════
# CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

def classify_entity(job: str) -> EntityScope:
    """
    Deterministically classify a Prometheus job as PLATFORM or CUSTOMER.

    Rules:
      1. If job is in PLATFORM_JOBS, INFRA_JOBS, or INTERNAL_PROBE_JOBS → PLATFORM
      2. Everything else → CUSTOMER

    This is the ONLY place classification happens.  All other modules
    must call this function rather than maintaining their own logic.
    """
    if job in ALL_INTERNAL_JOBS:
        return EntityScope.PLATFORM
    return EntityScope.CUSTOMER


# ═══════════════════════════════════════════════════════════════
# VISIBILITY FILTER
# ═══════════════════════════════════════════════════════════════

def get_visible_entities(
    entities: List[Dict[str, Any]],
    deployment_mode: str,
    scope_key: str = "entity_scope",
) -> List[Dict[str, Any]]:
    """
    Filter a list of entity dicts by deployment_mode.

    Args:
        entities:        List of entity dicts, each must have a key
                         identified by scope_key whose value is
                         EntityScope.PLATFORM or EntityScope.CUSTOMER
                         (or the string equivalents).
        deployment_mode: "ON_PREMISE" or "SAAS_SINGLE_TENANT".
        scope_key:       Dict key that holds the entity scope value.

    Returns:
        ON_PREMISE          → all entities (PLATFORM + CUSTOMER)
        SAAS_SINGLE_TENANT  → CUSTOMER entities only
    """
    if deployment_mode == "SAAS_SINGLE_TENANT":
        return [
            e for e in entities
            if str(e.get(scope_key, "")) == EntityScope.CUSTOMER.value
        ]
    # ON_PREMISE (default) — return everything
    return list(entities)


def is_customer_host(job: str) -> bool:
    """
    Returns True if a host running this job should count toward
    the licensed max_hosts.  Only CUSTOMER hosts are billable.

    Used by the license host-counting logic to exclude platform
    infrastructure from the host limit.
    """
    return classify_entity(job) == EntityScope.CUSTOMER
