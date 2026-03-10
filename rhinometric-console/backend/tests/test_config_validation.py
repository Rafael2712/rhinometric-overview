"""
Unit tests for strict configuration validation.
Covers schema validation, SSRF integration, and edge cases.
"""
import pytest
from unittest.mock import patch, MagicMock

from models.service_configs import HttpServiceConfig, PostgresServiceConfig
from services.config_validation import validate_service_config


# ── HttpServiceConfig Tests ──────────────────────────────────────

class TestHttpServiceConfig:

    def test_valid_minimal_config(self):
        cfg = HttpServiceConfig(url="https://api.example.com")
        assert cfg.url == "https://api.example.com"
        assert cfg.method == "GET"
        assert cfg.skip_tls_verify is False

    def test_valid_full_config(self):
        cfg = HttpServiceConfig(
            url="https://api.example.com/health",
            method="POST",
            health_path="/status",
            headers={"X-Token": "abc"},
            auth_type="bearer",
            auth_value="tok123",
            skip_tls_verify=True,
        )
        assert cfg.method == "POST"
        assert cfg.auth_type == "bearer"
        assert cfg.headers == {"X-Token": "abc"}

    def test_reject_ftp_url(self):
        with pytest.raises(Exception) as exc:
            HttpServiceConfig(url="ftp://example.com")
        assert "http or https" in str(exc.value).lower()

    def test_reject_empty_url(self):
        with pytest.raises(Exception):
            HttpServiceConfig(url="")

    def test_reject_no_url(self):
        with pytest.raises(Exception):
            HttpServiceConfig()

    def test_reject_invalid_method(self):
        with pytest.raises(Exception) as exc:
            HttpServiceConfig(url="https://example.com", method="DELETE")
        assert "method" in str(exc.value).lower()

    def test_method_case_insensitive(self):
        cfg = HttpServiceConfig(url="https://example.com", method="post")
        assert cfg.method == "POST"

    def test_reject_invalid_auth_type(self):
        with pytest.raises(Exception) as exc:
            HttpServiceConfig(url="https://example.com", auth_type="oauth2")
        assert "auth_type" in str(exc.value).lower()

    def test_headers_must_be_dict(self):
        with pytest.raises(Exception):
            HttpServiceConfig(url="https://example.com", headers="bad")

    def test_reject_no_hostname(self):
        with pytest.raises(Exception):
            HttpServiceConfig(url="https://")


# ── PostgresServiceConfig Tests ──────────────────────────────────

class TestPostgresServiceConfig:

    def test_valid_minimal_config(self):
        cfg = PostgresServiceConfig(
            host="db.internal", database_name="app", username="monitor"
        )
        assert cfg.port == 5432
        assert cfg.ssl_mode is None

    def test_valid_full_config(self):
        cfg = PostgresServiceConfig(
            host="db.internal",
            port=5433,
            database_name="app",
            username="monitor",
            password="secret",
            ssl_mode="require",
        )
        assert cfg.port == 5433
        assert cfg.ssl_mode == "require"

    def test_reject_port_too_high(self):
        with pytest.raises(Exception) as exc:
            PostgresServiceConfig(
                host="db", port=99999, database_name="app", username="u"
            )
        assert "65535" in str(exc.value) or "port" in str(exc.value).lower()

    def test_reject_port_zero(self):
        with pytest.raises(Exception):
            PostgresServiceConfig(
                host="db", port=0, database_name="app", username="u"
            )

    def test_reject_empty_host(self):
        with pytest.raises(Exception):
            PostgresServiceConfig(
                host="", database_name="app", username="u"
            )

    def test_reject_missing_database_name(self):
        with pytest.raises(Exception):
            PostgresServiceConfig(host="db", username="u")

    def test_reject_missing_username(self):
        with pytest.raises(Exception):
            PostgresServiceConfig(host="db", database_name="app")

    def test_reject_invalid_ssl_mode(self):
        with pytest.raises(Exception) as exc:
            PostgresServiceConfig(
                host="db", database_name="app", username="u", ssl_mode="none"
            )
        assert "ssl_mode" in str(exc.value).lower()

    def test_valid_ssl_modes(self):
        for mode in ("disable", "prefer", "require", "verify-ca", "verify-full"):
            cfg = PostgresServiceConfig(
                host="db", database_name="app", username="u", ssl_mode=mode
            )
            assert cfg.ssl_mode == mode


# ── validate_service_config Integration Tests ────────────────────

class TestValidateServiceConfig:

    @patch("services.config_validation.validate_url")
    def test_valid_http_passes_ssrf(self, mock_ssrf):
        mock_ssrf.return_value = MagicMock(is_safe=True)
        config = {"url": "https://example.com", "method": "GET"}
        result, errors = validate_service_config("http", config, "test")
        assert errors is None
        assert result == config
        mock_ssrf.assert_called_once()

    @patch("services.config_validation.validate_url")
    def test_http_ssrf_blocked(self, mock_ssrf):
        mock_ssrf.return_value = MagicMock(
            is_safe=False, reason="Internal IP"
        )
        config = {"url": "http://10.0.0.1"}
        result, errors = validate_service_config("http", config)
        assert errors is not None
        assert any("SSRF" in e for e in errors)

    def test_http_schema_errors_before_ssrf(self):
        config = {"url": "ftp://bad.com"}
        result, errors = validate_service_config("http", config)
        assert errors is not None
        assert any("http or https" in e.lower() for e in errors)

    def test_valid_postgres(self):
        config = {
            "host": "db.internal",
            "database_name": "app",
            "username": "monitor",
        }
        result, errors = validate_service_config("postgresql", config)
        assert errors is None
        assert result == config

    def test_postgres_invalid_port(self):
        config = {
            "host": "db",
            "port": 99999,
            "database_name": "app",
            "username": "u",
        }
        result, errors = validate_service_config("postgresql", config)
        assert errors is not None
        assert any("65535" in e or "port" in e.lower() for e in errors)

    def test_unknown_service_type(self):
        result, errors = validate_service_config("redis", {})
        assert errors is not None
        assert any("Unknown" in e for e in errors)

    def test_http_missing_url(self):
        config = {"method": "GET"}
        result, errors = validate_service_config("http", config)
        assert errors is not None
        assert any("url" in e.lower() for e in errors)
