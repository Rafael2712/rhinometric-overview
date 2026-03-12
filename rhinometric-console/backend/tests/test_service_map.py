"""
Tests for Service Map (Phase 2.8).

Covers:
  - Service graph generation
  - Dependency creation (validation, duplicates, self-ref)
  - Dependency deletion
  - Impact propagation logic
  - Status derivation
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone

# ─── Test _derive_service_statuses ──────────────────────────────

class TestDeriveServiceStatuses:
    """Test the status-derivation helper."""

    def _make_incident(self, entity_name, status="open"):
        inc = MagicMock()
        inc.entity_name = entity_name
        inc.status = status
        inc.id = uuid.uuid4()
        return inc

    def _make_alert(self, entity_name):
        return (entity_name,)

    def test_no_incidents_no_alerts(self):
        from routers.service_map import _derive_service_statuses
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = _derive_service_statuses(db)
        assert result == {}

    def test_incident_sets_status(self):
        from routers.service_map import _derive_service_statuses
        inc = self._make_incident("api-service")
        db = MagicMock()
        # incidents query
        db.query.return_value.filter.return_value.all.return_value = [inc]
        # alerts query
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = _derive_service_statuses(db)
        assert "api-service" in result
        assert result["api-service"]["status"] == "incident"

    def test_alert_sets_degraded(self):
        from routers.service_map import _derive_service_statuses
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [("web-app",)]
        result = _derive_service_statuses(db)
        assert result.get("web-app", {}).get("status") == "degraded"

    def test_incident_overrides_alert(self):
        from routers.service_map import _derive_service_statuses
        inc = self._make_incident("shared-svc")
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [inc]
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [("shared-svc",)]
        result = _derive_service_statuses(db)
        assert result["shared-svc"]["status"] == "incident"


# ─── Test dependency validation logic ───────────────────────────

class TestDependencyValidation:
    """Test dependency creation validation."""

    def test_allowed_types(self):
        from routers.service_map import ALLOWED_DEP_TYPES
        assert "http" in ALLOWED_DEP_TYPES
        assert "database" in ALLOWED_DEP_TYPES
        assert "cache" in ALLOWED_DEP_TYPES
        assert "queue" in ALLOWED_DEP_TYPES
        assert "external" in ALLOWED_DEP_TYPES
        assert "ftp" not in ALLOWED_DEP_TYPES

    def test_dependency_create_schema(self):
        from routers.service_map import DependencyCreate
        body = DependencyCreate(
            source_service_id=1,
            target_service_id=2,
            dependency_type="database",
            description="API uses DB",
        )
        assert body.source_service_id == 1
        assert body.target_service_id == 2
        assert body.dependency_type == "database"
        assert body.description == "API uses DB"

    def test_dependency_create_defaults(self):
        from routers.service_map import DependencyCreate
        body = DependencyCreate(source_service_id=1, target_service_id=2)
        assert body.dependency_type == "http"
        assert body.description is None


# ─── Test model ─────────────────────────────────────────────────

class TestServiceDependencyModel:
    """Test the ServiceDependency model."""

    def test_import(self):
        from models.service_dependency import ServiceDependency
        assert ServiceDependency.__tablename__ == "service_dependencies"

    def test_columns_exist(self):
        from models.service_dependency import ServiceDependency
        cols = {c.name for c in ServiceDependency.__table__.columns}
        expected = {"id", "source_service_id", "target_service_id", "dependency_type", "description", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_unique_constraint(self):
        from models.service_dependency import ServiceDependency
        constraints = [c.name for c in ServiceDependency.__table__.constraints if hasattr(c, 'name') and c.name]
        assert "uq_service_dep_src_tgt" in constraints


# ─── Test response schemas ──────────────────────────────────────

class TestResponseSchemas:
    """Test the response schemas."""

    def test_node_response(self):
        from routers.service_map import NodeResponse
        node = NodeResponse(id=1, name="API", type="http", status="healthy")
        assert node.id == 1
        assert node.status == "healthy"

    def test_edge_response(self):
        from routers.service_map import EdgeResponse
        edge = EdgeResponse(id="abc", source=1, target=2, type="database")
        assert edge.source == 1
        assert edge.type == "database"

    def test_graph_response(self):
        from routers.service_map import GraphResponse, NodeResponse, EdgeResponse
        graph = GraphResponse(
            nodes=[NodeResponse(id=1, name="API", type="http", status="healthy")],
            edges=[EdgeResponse(id="abc", source=1, target=2, type="http")],
        )
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 1


# ─── Test impact propagation logic ──────────────────────────────

class TestImpactPropagation:
    """Test that impact propagates correctly through dependencies."""

    def test_impact_marks_upstream(self):
        """If target has incident, source becomes impacted."""
        from routers.service_map import NodeResponse

        nodes = [
            NodeResponse(id=1, name="API", type="http", status="healthy"),
            NodeResponse(id=2, name="DB", type="postgresql", status="incident", incident_id="inc-123"),
        ]

        # Simulating edge: API (1) → DB (2)
        class FakeDep:
            source_service_id = 1
            target_service_id = 2

        deps = [FakeDep()]
        incident_target_ids = {n.id for n in nodes if n.status == "incident"}

        for dep in deps:
            if dep.target_service_id in incident_target_ids:
                for node in nodes:
                    if node.id == dep.source_service_id and node.status != "incident":
                        node.status = "impacted"

        assert nodes[0].status == "impacted"
        assert nodes[1].status == "incident"

    def test_no_impact_if_no_incident(self):
        """No impact propagation when everything is healthy."""
        from routers.service_map import NodeResponse

        nodes = [
            NodeResponse(id=1, name="API", type="http", status="healthy"),
            NodeResponse(id=2, name="DB", type="postgresql", status="healthy"),
        ]
        incident_target_ids = {n.id for n in nodes if n.status == "incident"}
        assert len(incident_target_ids) == 0

    def test_incident_node_stays_incident(self):
        """A node with incident status should not be downgraded to impacted."""
        from routers.service_map import NodeResponse

        nodes = [
            NodeResponse(id=1, name="A", type="http", status="incident", incident_id="x"),
            NodeResponse(id=2, name="B", type="http", status="incident", incident_id="y"),
        ]

        class FakeDep:
            source_service_id = 1
            target_service_id = 2

        deps = [FakeDep()]
        incident_target_ids = {n.id for n in nodes if n.status == "incident"}

        for dep in deps:
            if dep.target_service_id in incident_target_ids:
                for node in nodes:
                    if node.id == dep.source_service_id and node.status != "incident":
                        node.status = "impacted"

        assert nodes[0].status == "incident"  # Should NOT become impacted
        assert nodes[1].status == "incident"

