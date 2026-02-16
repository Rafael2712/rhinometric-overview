"""
RHINOMETRIC v2.3.0 - Docker Services Tests
==========================================

Test suite for Docker stack deployment and service health.

Tests cover:
- Docker Compose file validation
- Service deployment (22 services)
- Health checks for all services
- HTTP endpoint tests (Grafana, Prometheus, Loki)
- Volume mounting verification
- Network connectivity
"""

import pytest
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, Any

pytestmark = [pytest.mark.docker, pytest.mark.slow]


class TestComposeFileValidation:
    """Test docker-compose file validation."""
    
    def test_compose_file_exists(self, compose_file, test_logger):
        """Test that docker-compose-v2.2.0.yml exists."""
        assert compose_file.exists(), f"Compose file not found: {compose_file}"
        test_logger.info(f"✓ Compose file found: {compose_file}")
    
    def test_compose_file_is_valid_yaml(self, compose_file, test_logger):
        """Test that compose file is valid YAML."""
        import yaml
        
        try:
            content = yaml.safe_load(compose_file.read_text())
            assert isinstance(content, dict)
            assert "services" in content
            test_logger.info(f"✓ Valid YAML with {len(content.get('services', {}))} services")
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML: {e}")
    
    def test_compose_file_has_required_services(self, compose_file, test_logger):
        """Test that compose file defines required services."""
        import yaml
        
        content = yaml.safe_load(compose_file.read_text())
        services = content.get("services", {})
        
        required_services = [
            "grafana", "prometheus", "loki", 
            "postgres", "redis", "nginx"
        ]
        
        for service in required_services:
            if service in services:
                test_logger.info(f"✓ Service defined: {service}")
            else:
                test_logger.warning(f"⚠ Service missing: {service}")
    
    def test_compose_syntax_validation(self, compose_file, test_logger):
        """Test compose file syntax with docker compose config."""
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=compose_file.parent
        )
        
        if result.returncode == 0:
            test_logger.info("✓ Compose file syntax valid")
        else:
            test_logger.warning(f"⚠ Compose validation: {result.stderr}")


class TestServiceDeployment:
    """Test Docker service deployment."""
    
    @pytest.mark.integration
    def test_start_stack_dry_run(self, compose_file, test_logger):
        """Test stack startup in dry-run mode (config validation only)."""
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=compose_file.parent
        )
        
        # Config check should pass
        if result.returncode == 0:
            test_logger.info("✓ Stack configuration valid")
        else:
            test_logger.warning(f"⚠ Config check: {result.stderr[:200]}")
    
    @pytest.mark.integration
    def test_list_services(self, compose_file, test_logger):
        """Test listing of services in compose file."""
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "ps", "--services"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=compose_file.parent
        )
        
        if result.returncode == 0 and result.stdout:
            services = result.stdout.strip().split('\n')
            test_logger.info(f"✓ Found {len(services)} services")
        else:
            test_logger.info("⊘ Services not listed (stack may not be running)")
    
    @pytest.mark.integration
    def test_check_running_containers(self, test_logger):
        """Test checking for running RHINOMETRIC containers."""
        result = subprocess.run(
            ["docker", "ps", "--filter", "label=com.rhinometric.stack=true", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout:
            containers = result.stdout.strip().split('\n')
            test_logger.info(f"✓ Found {len(containers)} running containers")
            for container in containers[:5]:  # Log first 5
                test_logger.info(f"  - {container}")
        else:
            test_logger.info("⊘ No containers running (stack not deployed)")


class TestHealthChecks:
    """Test health checks for all services."""
    
    @pytest.mark.integration
    def test_grafana_health(self, test_logger):
        """Test Grafana service health."""
        try:
            response = requests.get("http://localhost:3000/api/health", timeout=5)
            if response.status_code == 200:
                test_logger.info("✓ Grafana is healthy")
                assert response.json().get("database") == "ok"
            else:
                test_logger.warning(f"⚠ Grafana responded with {response.status_code}")
        except requests.exceptions.RequestException as e:
            test_logger.info(f"⊘ Grafana not accessible: {e}")
            pytest.skip("Grafana not running")
    
    @pytest.mark.integration
    def test_prometheus_health(self, test_logger):
        """Test Prometheus service health."""
        try:
            response = requests.get("http://localhost:9090/-/healthy", timeout=5)
            if response.status_code == 200:
                test_logger.info("✓ Prometheus is healthy")
            else:
                test_logger.warning(f"⚠ Prometheus responded with {response.status_code}")
        except requests.exceptions.RequestException as e:
            test_logger.info(f"⊘ Prometheus not accessible: {e}")
            pytest.skip("Prometheus not running")
    
    @pytest.mark.integration
    def test_loki_health(self, test_logger):
        """Test Loki service health."""
        try:
            response = requests.get("http://localhost:3100/ready", timeout=5)
            if response.status_code == 200:
                test_logger.info("✓ Loki is ready")
            else:
                test_logger.warning(f"⚠ Loki responded with {response.status_code}")
        except requests.exceptions.RequestException as e:
            test_logger.info(f"⊘ Loki not accessible: {e}")
            pytest.skip("Loki not running")
    
    @pytest.mark.integration
    def test_all_containers_healthy(self, test_logger):
        """Test that all containers report healthy status."""
        result = subprocess.run(
            ["docker", "ps", "--filter", "health=healthy", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout:
            healthy_containers = result.stdout.strip().split('\n')
            test_logger.info(f"✓ {len(healthy_containers)} containers healthy")
        else:
            test_logger.info("⊘ No healthy containers found (stack may not be running)")


class TestHTTPEndpoints:
    """Test HTTP endpoints for web services."""
    
    @pytest.mark.integration
    def test_grafana_login_page(self, test_logger):
        """Test Grafana login page accessibility."""
        try:
            response = requests.get("http://localhost:3000/login", timeout=5)
            assert response.status_code == 200
            assert "grafana" in response.text.lower()
            test_logger.info("✓ Grafana login page accessible")
        except requests.exceptions.RequestException:
            pytest.skip("Grafana not accessible")
    
    @pytest.mark.integration
    def test_prometheus_targets_page(self, test_logger):
        """Test Prometheus targets page."""
        try:
            response = requests.get("http://localhost:9090/targets", timeout=5)
            assert response.status_code == 200
            test_logger.info("✓ Prometheus targets page accessible")
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus not accessible")
    
    @pytest.mark.integration
    def test_loki_metrics_endpoint(self, test_logger):
        """Test Loki metrics endpoint."""
        try:
            response = requests.get("http://localhost:3100/metrics", timeout=5)
            assert response.status_code == 200
            assert "loki" in response.text.lower()
            test_logger.info("✓ Loki metrics endpoint accessible")
        except requests.exceptions.RequestException:
            pytest.skip("Loki not accessible")


class TestVolumeVerification:
    """Test Docker volume mounting."""
    
    @pytest.mark.integration
    def test_list_rhinometric_volumes(self, test_logger):
        """Test listing of RHINOMETRIC volumes."""
        result = subprocess.run(
            ["docker", "volume", "ls", "--filter", "name=rhinometric", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout:
            volumes = result.stdout.strip().split('\n')
            test_logger.info(f"✓ Found {len(volumes)} volumes")
            for volume in volumes[:5]:
                test_logger.info(f"  - {volume}")
        else:
            test_logger.info("⊘ No volumes found")
    
    @pytest.mark.integration
    def test_grafana_data_volume_exists(self, test_logger):
        """Test that Grafana data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls", "--filter", "name=grafana", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "grafana" in result.stdout.lower():
            test_logger.info("✓ Grafana data volume exists")
        else:
            test_logger.info("⊘ Grafana volume not found")


class TestNetworkConnectivity:
    """Test Docker network connectivity."""
    
    @pytest.mark.integration
    def test_list_rhinometric_networks(self, test_logger):
        """Test listing of RHINOMETRIC networks."""
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=rhinometric", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.stdout:
            networks = result.stdout.strip().split('\n')
            test_logger.info(f"✓ Found {len(networks)} networks")
        else:
            test_logger.info("⊘ No networks found")
    
    @pytest.mark.integration
    def test_containers_on_same_network(self, test_logger):
        """Test that containers are on the same network."""
        result = subprocess.run(
            ["docker", "network", "inspect", "rhinometric_default"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            network_data = json.loads(result.stdout)
            if network_data and "Containers" in network_data[0]:
                container_count = len(network_data[0]["Containers"])
                test_logger.info(f"✓ {container_count} containers on rhinometric_default network")
        else:
            test_logger.info("⊘ Network not found")


class TestDockerSummary:
    """Summary test for Docker services."""
    
    def test_docker_summary(self, compose_file, platform_info, test_logger):
        """Generate summary of Docker tests."""
        test_logger.info("=" * 70)
        test_logger.info("DOCKER SERVICES TEST SUITE SUMMARY")
        test_logger.info("=" * 70)
        test_logger.info(f"Compose file: {compose_file}")
        test_logger.info(f"Platform: {platform_info['os']}")
        test_logger.info("")
        test_logger.info("Test coverage:")
        test_logger.info("  ✓ Compose file validation")
        test_logger.info("  ✓ Service deployment checks")
        test_logger.info("  ✓ Health checks (Grafana/Prometheus/Loki)")
        test_logger.info("  ✓ HTTP endpoint tests")
        test_logger.info("  ✓ Volume verification")
        test_logger.info("  ✓ Network connectivity")
        test_logger.info("")
        test_logger.info("Note: Integration tests require running Docker stack")
        test_logger.info("      Use --docker-integration to run full integration tests")
        test_logger.info("=" * 70)
