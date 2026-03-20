"""
Rhinometric Collector — Configuration

Loads settings with precedence: ENV > YAML > defaults.
Validates required values and fails fast with clear messages.
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("rhyno.collector.config")


@dataclass
class CollectorConfig:
    # Required
    api_url: str = ""
    service_key: str = ""
    telemetry_token: str = ""

    # Optional
    collect_interval: int = 15
    enable_metrics: bool = True
    enable_logs: bool = True
    enable_traces: bool = True
    log_level: str = "INFO"
    environment: str = "production"
    hostname: str = field(default_factory=lambda: _get_hostname())

    def validate(self) -> None:
        """Validate required config. Exits with clear error if invalid."""
        errors: list[str] = []

        if not self.api_url:
            errors.append("RHYNO_API_URL is required (e.g. http://your-rhinometric-host/api)")
        elif not self.api_url.startswith(("http://", "https://")):
            errors.append(f"RHYNO_API_URL must start with http:// or https:// (got: {self.api_url})")

        if not self.service_key:
            errors.append("RHYNO_SERVICE_KEY is required (from Rhinometric > Services > your service)")

        if not self.telemetry_token:
            errors.append("RHYNO_TELEMETRY_TOKEN is required (from Rhinometric > Services > Telemetry Setup)")

        if self.collect_interval < 5:
            errors.append("COLLECT_INTERVAL must be >= 5 seconds")

        if self.log_level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            errors.append(f"LOG_LEVEL must be DEBUG, INFO, WARNING, or ERROR (got: {self.log_level})")

        if not any([self.enable_metrics, self.enable_logs, self.enable_traces]):
            errors.append("At least one signal must be enabled (ENABLE_METRICS, ENABLE_LOGS, or ENABLE_TRACES)")

        if errors:
            print("\n╔══════════════════════════════════════════════════════════╗")
            print("║  Rhinometric Collector — Configuration Error            ║")
            print("╚══════════════════════════════════════════════════════════╝\n")
            for e in errors:
                print(f"  ✗ {e}")
            print("\n  Check your .env file or environment variables.")
            print("  See README.md for configuration details.\n")
            sys.exit(1)


def _get_hostname() -> str:
    """Get hostname safely across platforms."""
    import socket
    try:
        return socket.gethostname()
    except Exception:
        return os.environ.get("HOSTNAME", os.environ.get("COMPUTERNAME", "unknown"))


def _parse_bool(val: str) -> bool:
    """Parse boolean from string: true/1/yes/on → True."""
    return val.strip().lower() in ("1", "true", "yes", "on")


def load_config() -> CollectorConfig:
    """
    Load configuration with precedence: ENV > YAML > defaults.

    1. Start with defaults
    2. Override with YAML values (if config.yaml exists)
    3. Override with environment variables (always win)
    4. Validate and return
    """
    cfg = CollectorConfig()

    # ── Step 1: Optional YAML config ─────────────────────────
    yaml_path = os.environ.get("RHYNO_CONFIG_FILE", "config.yaml")
    if os.path.isfile(yaml_path):
        try:
            import yaml  # type: ignore
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            cfg.api_url = data.get("api_url", cfg.api_url)
            cfg.service_key = data.get("service_key", cfg.service_key)
            cfg.telemetry_token = data.get("telemetry_token", cfg.telemetry_token)
            cfg.collect_interval = int(data.get("collect_interval", cfg.collect_interval))
            cfg.environment = data.get("environment", cfg.environment)
            cfg.log_level = data.get("log_level", cfg.log_level)
            if "enable_metrics" in data:
                cfg.enable_metrics = bool(data["enable_metrics"])
            if "enable_logs" in data:
                cfg.enable_logs = bool(data["enable_logs"])
            if "enable_traces" in data:
                cfg.enable_traces = bool(data["enable_traces"])
            logger.info(f"Loaded YAML config from {yaml_path}")
        except ImportError:
            logger.warning("PyYAML not installed — skipping YAML config")
        except Exception as exc:
            logger.warning(f"Failed to load {yaml_path}: {exc}")

    # ── Step 2: Environment overrides (always win) ───────────
    cfg.api_url = os.environ.get("RHYNO_API_URL", cfg.api_url).rstrip("/")
    cfg.service_key = os.environ.get("RHYNO_SERVICE_KEY", cfg.service_key)
    cfg.telemetry_token = os.environ.get("RHYNO_TELEMETRY_TOKEN", cfg.telemetry_token)
    cfg.collect_interval = int(os.environ.get("COLLECT_INTERVAL", str(cfg.collect_interval)))
    cfg.environment = os.environ.get("RHYNO_ENVIRONMENT", cfg.environment)
    cfg.log_level = os.environ.get("LOG_LEVEL", cfg.log_level)

    if "ENABLE_METRICS" in os.environ:
        cfg.enable_metrics = _parse_bool(os.environ["ENABLE_METRICS"])
    if "ENABLE_LOGS" in os.environ:
        cfg.enable_logs = _parse_bool(os.environ["ENABLE_LOGS"])
    if "ENABLE_TRACES" in os.environ:
        cfg.enable_traces = _parse_bool(os.environ["ENABLE_TRACES"])

    # ── Step 3: Validate ─────────────────────────────────────
    cfg.validate()
    return cfg
