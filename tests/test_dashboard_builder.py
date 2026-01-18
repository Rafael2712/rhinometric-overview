"""
RHINOMETRIC v2.4.0 - Dashboard Builder Tests
============================================

Unit tests for Dashboard Builder backend API.

Test Coverage:
- Template retrieval
- Dashboard CRUD operations
- License validation
- Export to Grafana JSON
- Error handling
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dashboard-builder')))

from app import app, dashboards_db, generate_dashboard_id, DASHBOARD_TEMPLATES


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_header():
    """Generate valid JWT authorization header for testing."""
    import jwt
    from datetime import datetime, timedelta
    import time
    
    # Use same secret as app
    JWT_SECRET = os.getenv('JWT_SECRET', 'rhinometric-secret-key-change-in-production')
    
    # Generate token with proper integer timestamps
    now = int(time.time())
    expires = now + 3600  # 1 hour from now
    
    payload = {
        "iat": now,
        "exp": expires,
        "iss": "RHINOMETRIC",
        "user_id": "test_user_123",
        "username": "admin",
        "role": "admin",
        "license_key": "RHINO-TEST-2024-ABCD",
        "customer": "Test Customer"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_dashboard():
    """Sample dashboard configuration."""
    return {
        "title": "Test Dashboard",
        "description": "Test description",
        "tags": ["test", "infrastructure"],
        "panels": [
            {
                "id": 1,
                "type": "graph",
                "title": "CPU Usage",
                "datasource": "Prometheus",
                "query": "rate(cpu[5m])",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 8,
                "options": {"unit": "percent"}
            }
        ],
        "time_range": {"from": "now-6h", "to": "now"},
        "refresh": "30s",
        "variables": []
    }


@pytest.fixture(autouse=True)
def clear_db():
    """Clear in-memory database before each test."""
    dashboards_db.clear()
    yield
    dashboards_db.clear()


# ============================================================================
# TEST ROOT ENDPOINT
# ============================================================================

def test_root_health_check(client):
    """Test root endpoint returns health status."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "RHINOMETRIC Dashboard Builder"
    assert data["version"] == "2.4.0"
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ============================================================================
# TEST TEMPLATES
# ============================================================================

def test_get_templates(client):
    """Test retrieving all templates."""
    response = client.get("/api/templates")
    assert response.status_code == 200
    
    data = response.json()
    assert "templates" in data
    assert "count" in data
    assert data["count"] == 4  # infrastructure, api, messaging, sustainability
    
    # Check template structure
    templates = data["templates"]
    assert "infrastructure" in templates
    assert "api-monitoring" in templates
    assert "messaging" in templates
    assert "sustainability" in templates
    
    # Verify infrastructure template
    infra = templates["infrastructure"]
    assert infra["name"] == "Infraestructura Completa"
    assert infra["icon"] == "🏗️"
    assert len(infra["panels"]) == 4


def test_get_specific_template(client):
    """Test retrieving specific template by ID."""
    response = client.get("/api/templates/infrastructure")
    assert response.status_code == 200
    
    data = response.json()
    assert data["template_id"] == "infrastructure"
    assert data["template"]["name"] == "Infraestructura Completa"
    assert len(data["template"]["panels"]) == 4


def test_get_nonexistent_template(client):
    """Test retrieving non-existent template returns 404."""
    response = client.get("/api/templates/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ============================================================================
# TEST DASHBOARD CRUD
# ============================================================================

def test_create_dashboard(client, mock_auth_header, sample_dashboard):
    """Test creating new dashboard."""
    response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": False},
        headers=mock_auth_header
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "created successfully" in data["message"]
    assert "dashboard_id" in data
    assert "metadata" in data
    
    # Verify metadata
    metadata = data["metadata"]
    assert metadata["title"] == "Test Dashboard"
    assert metadata["panel_count"] == 1
    assert metadata["version"] == 1
    assert metadata["created_by"] == "admin"


def test_create_dashboard_without_auth(client, sample_dashboard):
    """Test creating dashboard without authorization fails."""
    response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": False}
    )
    assert response.status_code == 401
    assert "Missing or invalid authorization header" in response.json()["detail"]


def test_create_duplicate_dashboard(client, mock_auth_header, sample_dashboard):
    """Test creating duplicate dashboard without overwrite fails."""
    # Create first dashboard
    response1 = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": False},
        headers=mock_auth_header
    )
    assert response1.status_code == 200
    
    # Try to create again without overwrite
    response2 = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": False},
        headers=mock_auth_header
    )
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]


def test_create_dashboard_with_overwrite(client, mock_auth_header, sample_dashboard):
    """Test creating dashboard with overwrite replaces existing."""
    # Create first dashboard
    response1 = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": False},
        headers=mock_auth_header
    )
    dashboard_id = response1.json()["dashboard_id"]
    
    # Overwrite with modified dashboard
    sample_dashboard["description"] = "Updated description"
    response2 = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard, "overwrite": True},
        headers=mock_auth_header
    )
    assert response2.status_code == 200
    
    # Verify version incremented
    metadata = response2.json()["metadata"]
    assert metadata["version"] == 2
    assert metadata["description"] == "Updated description"


def test_list_dashboards_empty(client, mock_auth_header):
    """Test listing dashboards when none exist."""
    response = client.get("/api/dashboards", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 0
    assert data["dashboards"] == []


def test_list_dashboards(client, mock_auth_header, sample_dashboard):
    """Test listing dashboards."""
    # Create 3 dashboards
    for i in range(3):
        dashboard = sample_dashboard.copy()
        dashboard["title"] = f"Dashboard {i+1}"
        dashboard["tags"] = [f"tag{i}"]
        client.post(
            "/api/dashboards",
            json={"dashboard": dashboard, "overwrite": False},
            headers=mock_auth_header
        )
    
    # List all
    response = client.get("/api/dashboards", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 3
    assert len(data["dashboards"]) == 3


def test_list_dashboards_with_tag_filter(client, mock_auth_header, sample_dashboard):
    """Test filtering dashboards by tags."""
    # Create dashboards with different tags
    dashboard1 = sample_dashboard.copy()
    dashboard1["title"] = "Infrastructure Dashboard"
    dashboard1["tags"] = ["infrastructure", "production"]
    
    dashboard2 = sample_dashboard.copy()
    dashboard2["title"] = "API Dashboard"
    dashboard2["tags"] = ["api", "monitoring"]
    
    client.post("/api/dashboards", json={"dashboard": dashboard1}, headers=mock_auth_header)
    client.post("/api/dashboards", json={"dashboard": dashboard2}, headers=mock_auth_header)
    
    # Filter by "infrastructure" tag
    response = client.get("/api/dashboards?tags=infrastructure", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 1
    assert data["dashboards"][0]["title"] == "Infrastructure Dashboard"


def test_list_dashboards_with_search(client, mock_auth_header, sample_dashboard):
    """Test searching dashboards by title."""
    # Create dashboards
    dashboard1 = sample_dashboard.copy()
    dashboard1["title"] = "CPU Monitoring"
    
    dashboard2 = sample_dashboard.copy()
    dashboard2["title"] = "Memory Monitoring"
    
    client.post("/api/dashboards", json={"dashboard": dashboard1}, headers=mock_auth_header)
    client.post("/api/dashboards", json={"dashboard": dashboard2}, headers=mock_auth_header)
    
    # Search for "cpu"
    response = client.get("/api/dashboards?search=cpu", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 1
    assert data["dashboards"][0]["title"] == "CPU Monitoring"


def test_get_dashboard(client, mock_auth_header, sample_dashboard):
    """Test getting specific dashboard."""
    # Create dashboard
    create_response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard},
        headers=mock_auth_header
    )
    dashboard_id = create_response.json()["dashboard_id"]
    
    # Get dashboard
    response = client.get(f"/api/dashboards/{dashboard_id}", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert "dashboard" in data
    assert "metadata" in data
    assert data["dashboard"]["title"] == "Test Dashboard"


def test_get_nonexistent_dashboard(client, mock_auth_header):
    """Test getting non-existent dashboard returns 404."""
    response = client.get("/api/dashboards/nonexistent", headers=mock_auth_header)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_dashboard(client, mock_auth_header, sample_dashboard):
    """Test updating dashboard."""
    # Create dashboard
    create_response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard},
        headers=mock_auth_header
    )
    dashboard_id = create_response.json()["dashboard_id"]
    
    # Update dashboard
    sample_dashboard["title"] = "Updated Title"
    sample_dashboard["panels"].append({
        "id": 2,
        "type": "gauge",
        "title": "Memory",
        "datasource": "Prometheus",
        "query": "memory_usage",
        "x": 12,
        "y": 0,
        "width": 12,
        "height": 8,
        "options": {}
    })
    
    response = client.put(
        f"/api/dashboards/{dashboard_id}",
        json=sample_dashboard,
        headers=mock_auth_header
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["metadata"]["version"] == 2
    assert data["metadata"]["panel_count"] == 2


def test_update_nonexistent_dashboard(client, mock_auth_header, sample_dashboard):
    """Test updating non-existent dashboard returns 404."""
    response = client.put(
        "/api/dashboards/nonexistent",
        json=sample_dashboard,
        headers=mock_auth_header
    )
    assert response.status_code == 404


def test_delete_dashboard(client, mock_auth_header, sample_dashboard):
    """Test deleting dashboard."""
    # Create dashboard
    create_response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard},
        headers=mock_auth_header
    )
    dashboard_id = create_response.json()["dashboard_id"]
    
    # Delete dashboard
    response = client.delete(f"/api/dashboards/{dashboard_id}", headers=mock_auth_header)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify deleted
    get_response = client.get(f"/api/dashboards/{dashboard_id}", headers=mock_auth_header)
    assert get_response.status_code == 404


def test_delete_nonexistent_dashboard(client, mock_auth_header):
    """Test deleting non-existent dashboard returns 404."""
    response = client.delete("/api/dashboards/nonexistent", headers=mock_auth_header)
    assert response.status_code == 404


# ============================================================================
# TEST EXPORT
# ============================================================================

def test_export_dashboard(client, mock_auth_header, sample_dashboard):
    """Test exporting dashboard to Grafana JSON."""
    # Create dashboard
    create_response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard},
        headers=mock_auth_header
    )
    dashboard_id = create_response.json()["dashboard_id"]
    
    # Export dashboard
    response = client.get(f"/api/dashboards/{dashboard_id}/export", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert "dashboard" in data
    assert "metadata" in data
    
    # Verify Grafana JSON structure
    grafana_json = data["dashboard"]
    assert "dashboard" in grafana_json
    dashboard_obj = grafana_json["dashboard"]
    assert dashboard_obj["title"] == "Test Dashboard"
    assert dashboard_obj["uid"] == dashboard_id
    assert len(dashboard_obj["panels"]) == 1
    assert dashboard_obj["schemaVersion"] == 38


def test_export_nonexistent_dashboard(client, mock_auth_header):
    """Test exporting non-existent dashboard returns 404."""
    response = client.get("/api/dashboards/nonexistent/export", headers=mock_auth_header)
    assert response.status_code == 404


# ============================================================================
# TEST UTILITIES
# ============================================================================

def test_generate_dashboard_id():
    """Test deterministic dashboard ID generation."""
    id1 = generate_dashboard_id("Test Dashboard")
    id2 = generate_dashboard_id("Test Dashboard")
    
    # IDs should be identical (deterministic, no timestamp)
    assert id1 == id2 == "test-dashboard"
    
    # Test normalization rules
    assert generate_dashboard_id("My_Cool-Dashboard!") == "my-cool-dashboard"
    assert generate_dashboard_id("  Spaces   Everywhere  ") == "spaces-everywhere"
    assert generate_dashboard_id("Special@#$%Characters^&*()") == "specialcharacters"
    assert generate_dashboard_id("Multiple---Hyphens") == "multiple-hyphens"
    assert generate_dashboard_id("") == "dashboard"  # Fallback for empty string


# ============================================================================
# TEST PERFORMANCE
# ============================================================================

def test_create_dashboard_performance(client, mock_auth_header, sample_dashboard):
    """Test dashboard creation completes within 1 second."""
    import time
    
    start = time.time()
    response = client.post(
        "/api/dashboards",
        json={"dashboard": sample_dashboard},
        headers=mock_auth_header
    )
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 1.0, f"Dashboard creation took {duration:.2f}s (expected <1s)"


def test_list_dashboards_performance(client, mock_auth_header, sample_dashboard):
    """Test listing 100 dashboards completes within 2 seconds."""
    import time
    
    # Create 100 dashboards
    for i in range(100):
        dashboard = sample_dashboard.copy()
        dashboard["title"] = f"Dashboard {i}"
        client.post(
            "/api/dashboards",
            json={"dashboard": dashboard},
            headers=mock_auth_header
        )
    
    # List all
    start = time.time()
    response = client.get("/api/dashboards", headers=mock_auth_header)
    duration = time.time() - start
    
    assert response.status_code == 200
    assert response.json()["count"] == 100
    assert duration < 2.0, f"Listing 100 dashboards took {duration:.2f}s (expected <2s)"


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])
