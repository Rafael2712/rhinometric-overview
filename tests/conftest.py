"""
RHINOMETRIC v2.3.0 - Test Suite Configuration
==============================================

pytest configuration with cross-platform fixtures and helpers.

Author: RHINOMETRIC Team
Date: November 2025
License: Proprietary
"""

import os
import sys
import json
import shutil
import tempfile
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Platform Detection Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def platform_info() -> Dict[str, Any]:
    """Detect current platform and return comprehensive info."""
    
    os_type = platform.system()
    
    # Detect WSL2
    is_wsl = False
    if os_type == "Linux":
        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    is_wsl = True
        except FileNotFoundError:
            pass
    
    info = {
        "os": os_type,
        "os_version": platform.version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "is_wsl": is_wsl,
        "is_linux": os_type == "Linux" and not is_wsl,
        "is_macos": os_type == "Darwin",
        "is_windows": os_type == "Windows" or is_wsl,
        "hostname": platform.node(),
    }
    
    return info


@pytest.fixture(scope="session")
def is_linux(platform_info):
    """Check if running on native Linux (not WSL)."""
    return platform_info["is_linux"]


@pytest.fixture(scope="session")
def is_macos(platform_info):
    """Check if running on macOS."""
    return platform_info["is_macos"]


@pytest.fixture(scope="session")
def is_windows(platform_info):
    """Check if running on Windows or WSL."""
    return platform_info["is_windows"]


@pytest.fixture(scope="session")
def is_wsl(platform_info):
    """Check if running on WSL2."""
    return platform_info["is_wsl"]


# ============================================================================
# Path Fixtures (Cross-Platform)
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def tests_dir(project_root) -> Path:
    """Return tests directory."""
    return project_root / "tests"


@pytest.fixture(scope="session")
def results_dir(tests_dir) -> Path:
    """Return results directory."""
    results = tests_dir / "results"
    results.mkdir(exist_ok=True)
    return results


@pytest.fixture(scope="session")
def logs_dir(results_dir) -> Path:
    """Return logs directory."""
    logs = results_dir / "logs"
    logs.mkdir(exist_ok=True)
    return logs


@pytest.fixture(scope="session")
def fixtures_dir(tests_dir) -> Path:
    """Return fixtures directory."""
    return tests_dir / "fixtures"


@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test, cleanup after."""
    temp = tempfile.mkdtemp(prefix="rhinometric_test_")
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


# ============================================================================
# Security & Crypto Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def security_dir(project_root) -> Path:
    """Return security directory with RSA keys."""
    return project_root / "security"


@pytest.fixture(scope="session")
def public_key_path(security_dir) -> Path:
    """Return path to RSA public key."""
    pub_key = security_dir / "rhinometric_public.pem"
    
    if not pub_key.exists():
        pytest.skip(f"Public key not found: {pub_key}")
    
    return pub_key


@pytest.fixture(scope="session")
def private_key_path(security_dir) -> Path:
    """Return path to RSA private key (if available)."""
    priv_key = security_dir / "rhinometric_private.pem"
    
    if not priv_key.exists():
        pytest.skip(f"Private key not found: {priv_key}")
    
    return priv_key


@pytest.fixture(scope="function")
def mock_license_data() -> Dict[str, Any]:
    """Generate mock license data for testing."""
    
    from datetime import datetime, timedelta
    
    return {
        "customer": "TestCompany",
        "type": "trial",
        "hwid": "A1B2C3D4E5F6G7H8",
        "issued_at": datetime.utcnow().isoformat() + "Z",
        "expires": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "features": ["monitoring", "alerting", "reporting"],
        "signature": ""  # Will be filled by crypto tests
    }


@pytest.fixture(scope="function")
def expired_license_data(mock_license_data) -> Dict[str, Any]:
    """Generate expired license data."""
    
    expired = mock_license_data.copy()
    expired["expires"] = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    return expired


@pytest.fixture(scope="function")
def temp_license_file(temp_dir, mock_license_data):
    """Create temporary license file for testing."""
    
    license_file = temp_dir / "test_license.lic"
    
    with open(license_file, "w") as f:
        json.dump(mock_license_data, f, indent=2)
    
    yield license_file
    
    # Cleanup
    if license_file.exists():
        license_file.unlink()


# ============================================================================
# Docker Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def docker_available() -> bool:
    """Check if Docker is available."""
    
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def docker_compose_available() -> bool:
    """Check if Docker Compose is available."""
    
    # Try Docker Compose V2
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Try Docker Compose V1 (legacy)
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def compose_file(project_root) -> Path:
    """Return path to docker-compose file."""
    
    compose = project_root / "docker-compose-v2.2.0.yml"
    
    if not compose.exists():
        pytest.skip(f"Docker Compose file not found: {compose}")
    
    return compose


# ============================================================================
# HWID Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def get_hwid_script(project_root) -> Path:
    """Return path to get-hwid.sh script."""
    
    script = project_root / "get-hwid.sh"
    
    if not script.exists():
        pytest.skip(f"HWID script not found: {script}")
    
    return script


@pytest.fixture(scope="function")
def current_hwid(get_hwid_script, platform_info) -> Optional[str]:
    """Get current machine's HWID."""
    
    try:
        result = subprocess.run(
            ["bash", str(get_hwid_script)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Extract HWID from output
            for line in result.stdout.split("\n"):
                if "HWID:" in line or "Hardware ID" in line:
                    hwid = line.split(":")[-1].strip()
                    return hwid
        
        return None
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


# ============================================================================
# Validator Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def validator_script(project_root) -> Path:
    """Return path to validate_license.py script."""
    
    script = project_root / "validate_license.py"
    
    if not script.exists():
        pytest.skip(f"Validator script not found: {script}")
    
    return script


# ============================================================================
# License Monitor Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def license_monitor_script(project_root) -> Path:
    """Return path to license_monitor.py script."""
    
    script = project_root / "license-monitor" / "license_monitor.py"
    
    if not script.exists():
        pytest.skip(f"License monitor script not found: {script}")
    
    return script


# ============================================================================
# Installer Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def installer_script(project_root) -> Path:
    """Return path to install-secure.sh script."""
    
    script = project_root / "install-secure.sh"
    
    if not script.exists():
        pytest.skip(f"Installer script not found: {script}")
    
    return script


# ============================================================================
# Test Logging Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_logger(logs_dir, request):
    """Create logger for individual test."""
    
    import logging
    
    test_name = request.node.name
    log_file = logs_dir / f"{test_name}.log"
    
    logger = logging.getLogger(test_name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    
    yield logger
    
    # Cleanup
    logger.removeHandler(fh)
    fh.close()


# ============================================================================
# Cleanup Hooks
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """Cleanup after all tests complete."""
    
    yield
    
    # Any global cleanup can go here
    print("\n✓ Test session completed - cleanup done")


@pytest.fixture(scope="function", autouse=True)
def test_cleanup(request):
    """Cleanup after each test."""
    
    yield
    
    # Per-test cleanup
    pass


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest before test run."""
    
    # Add custom markers
    config.addinivalue_line(
        "markers", "crypto: mark test as cryptography test"
    )
    config.addinivalue_line(
        "markers", "hwid: mark test as HWID test"
    )
    config.addinivalue_line(
        "markers", "validator: mark test as validator test"
    )
    config.addinivalue_line(
        "markers", "monitor: mark test as license monitor test"
    )
    config.addinivalue_line(
        "markers", "installer: mark test as installer test"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as Docker services test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected tests."""
    
    # Skip Docker tests if Docker not available
    skip_docker = pytest.mark.skip(reason="Docker not available")
    
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        docker_available = result.returncode == 0
    except:
        docker_available = False
    
    if not docker_available:
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(skip_docker)


def pytest_sessionstart(session):
    """Called before test run starts."""
    
    print("\n" + "="*70)
    print("RHINOMETRIC v2.3.0 - Test Suite")
    print("="*70)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Test directory: {Path(__file__).parent}")
    print("="*70 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Called after test run completes."""
    
    print("\n" + "="*70)
    print(f"Test session finished with exit status: {exitstatus}")
    print("="*70 + "\n")


# ============================================================================
# Helper Functions (Available in all tests)
# ============================================================================

def run_command(cmd: list, timeout: int = 30, check: bool = False) -> subprocess.CompletedProcess:
    """
    Run shell command with timeout.
    
    Args:
        cmd: Command as list of strings
        timeout: Timeout in seconds
        check: Raise exception if command fails
    
    Returns:
        CompletedProcess object
    """
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        return result
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")


def assert_file_exists(path: Path, message: str = None):
    """Assert that file exists."""
    
    if not path.exists():
        msg = message or f"File not found: {path}"
        pytest.fail(msg)


def assert_file_contains(path: Path, text: str, message: str = None):
    """Assert that file contains specific text."""
    
    assert_file_exists(path)
    
    content = path.read_text()
    
    if text not in content:
        msg = message or f"File {path} does not contain: {text}"
        pytest.fail(msg)


def assert_json_valid(path: Path):
    """Assert that file is valid JSON."""
    
    assert_file_exists(path)
    
    try:
        with open(path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {path}: {e}")
