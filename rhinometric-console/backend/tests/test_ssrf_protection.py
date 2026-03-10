"""
Tests for security.ssrf_protection module.

Run inside the backend container:
    python -m pytest tests/test_ssrf_protection.py -v
Or from host:
    docker exec rhinometric-console-backend python -m pytest tests/test_ssrf_protection.py -v
"""

import pytest
from security.ssrf_protection import validate_url, is_forbidden_ip


# -- Valid / Safe URLs -------------------------------------------

class TestValidUrls:
    """URLs that should pass SSRF validation."""

    def test_https_public_domain(self):
        r = validate_url("https://httpbin.org/get")
        assert r.is_safe is True
        assert r.safe_url == "https://httpbin.org/get"

    def test_http_public_domain(self):
        r = validate_url("http://example.com")
        assert r.is_safe is True

    def test_https_with_port(self):
        r = validate_url("https://example.com:8443/health")
        assert r.is_safe is True

    def test_public_ip(self):
        r = validate_url("http://8.8.8.8/dns-query")
        assert r.is_safe is True


# -- Blocked: Localhost / Loopback -------------------------------

class TestBlockedLocalhost:
    """Localhost and loopback must be blocked."""

    def test_localhost_keyword(self):
        r = validate_url("http://localhost/admin")
        assert r.is_safe is False
        assert "not allowed" in r.reason.lower() or "internal" in r.reason.lower()

    def test_localhost_localdomain(self):
        r = validate_url("http://localhost.localdomain/")
        assert r.is_safe is False

    def test_loopback_127(self):
        r = validate_url("http://127.0.0.1/")
        assert r.is_safe is False
        assert "forbidden" in r.reason.lower() or "private" in r.reason.lower()

    def test_loopback_127_x(self):
        r = validate_url("http://127.0.0.2:8080/")
        assert r.is_safe is False

    def test_ipv6_loopback(self):
        r = validate_url("http://[::1]/")
        assert r.is_safe is False


# -- Blocked: RFC1918 Private Networks ---------------------------

class TestBlockedPrivateNetworks:
    """RFC1918 ranges must be blocked."""

    def test_10_network(self):
        r = validate_url("http://10.0.0.1/")
        assert r.is_safe is False

    def test_10_deep(self):
        r = validate_url("http://10.255.255.255:9090/api")
        assert r.is_safe is False

    def test_172_16_network(self):
        r = validate_url("http://172.16.0.1/")
        assert r.is_safe is False

    def test_172_31_network(self):
        r = validate_url("http://172.31.255.255/")
        assert r.is_safe is False

    def test_192_168_network(self):
        r = validate_url("http://192.168.1.1/")
        assert r.is_safe is False

    def test_192_168_deep(self):
        r = validate_url("http://192.168.100.200:3000/grafana")
        assert r.is_safe is False


# -- Blocked: Cloud Metadata / Link-Local ------------------------

class TestBlockedMetadata:
    """Cloud metadata and link-local addresses must be blocked."""

    def test_aws_metadata(self):
        r = validate_url("http://169.254.169.254/latest/meta-data/")
        assert r.is_safe is False

    def test_link_local(self):
        r = validate_url("http://169.254.0.1/")
        assert r.is_safe is False

    def test_metadata_google_internal(self):
        r = validate_url("http://metadata.google.internal/computeMetadata/v1/")
        assert r.is_safe is False


# -- Blocked: Docker/K8s Internal Hostnames ----------------------

class TestBlockedInternalHostnames:
    """Docker and Kubernetes internal hostnames must be blocked."""

    def test_docker_internal(self):
        r = validate_url("http://host.docker.internal:8080/")
        assert r.is_safe is False

    def test_gateway_docker(self):
        r = validate_url("http://gateway.docker.internal/")
        assert r.is_safe is False

    def test_k8s_default(self):
        r = validate_url("http://kubernetes.default.svc.cluster.local/")
        assert r.is_safe is False

    def test_any_dot_internal(self):
        r = validate_url("http://myservice.internal/")
        assert r.is_safe is False

    def test_any_dot_local(self):
        r = validate_url("http://myservice.local/")
        assert r.is_safe is False


# -- Blocked: Bad Schemes ----------------------------------------

class TestBlockedSchemes:
    """Non-HTTP/HTTPS schemes must be blocked."""

    def test_ftp(self):
        r = validate_url("ftp://evil.com/file")
        assert r.is_safe is False
        assert "protocol" in r.reason.lower() or "scheme" in r.reason.lower()

    def test_file(self):
        r = validate_url("file:///etc/passwd")
        assert r.is_safe is False

    def test_gopher(self):
        r = validate_url("gopher://evil.com/")
        assert r.is_safe is False

    def test_no_scheme(self):
        r = validate_url("just-a-hostname.com")
        assert r.is_safe is False


# -- Blocked: URL Tricks -----------------------------------------

class TestBlockedUrlTricks:
    """URL manipulation tricks must be caught."""

    def test_userinfo_bypass(self):
        r = validate_url("http://evil@127.0.0.1/")
        assert r.is_safe is False

    def test_user_pass_bypass(self):
        r = validate_url("http://user:pass@internal.example.com/")
        assert r.is_safe is False
        assert "credentials" in r.reason.lower() or "user" in r.reason.lower()

    def test_empty_url(self):
        r = validate_url("")
        assert r.is_safe is False

    def test_none_url(self):
        r = validate_url(None)
        assert r.is_safe is False


# -- is_forbidden_ip direct tests --------------------------------

class TestIsForbiddenIp:
    """Direct unit tests for the is_forbidden_ip helper."""

    def test_public_ipv4(self):
        forbidden, _ = is_forbidden_ip("8.8.8.8")
        assert forbidden is False

    def test_loopback(self):
        forbidden, _ = is_forbidden_ip("127.0.0.1")
        assert forbidden is True

    def test_rfc1918_10(self):
        forbidden, _ = is_forbidden_ip("10.0.0.1")
        assert forbidden is True

    def test_rfc1918_172(self):
        forbidden, _ = is_forbidden_ip("172.16.0.1")
        assert forbidden is True

    def test_rfc1918_192(self):
        forbidden, _ = is_forbidden_ip("192.168.1.1")
        assert forbidden is True

    def test_link_local(self):
        forbidden, _ = is_forbidden_ip("169.254.169.254")
        assert forbidden is True

    def test_ipv6_loopback(self):
        forbidden, _ = is_forbidden_ip("::1")
        assert forbidden is True

    def test_ipv6_ula(self):
        forbidden, _ = is_forbidden_ip("fd12:3456:789a::1")
        assert forbidden is True

    def test_ipv6_public(self):
        forbidden, _ = is_forbidden_ip("2607:f8b0:4004:800::200e")
        assert forbidden is False

    def test_carrier_grade_nat(self):
        forbidden, _ = is_forbidden_ip("100.64.0.1")
        assert forbidden is True

    def test_unspecified(self):
        forbidden, _ = is_forbidden_ip("0.0.0.0")
        assert forbidden is True

    def test_broadcast(self):
        forbidden, _ = is_forbidden_ip("255.255.255.255")
        assert forbidden is True
