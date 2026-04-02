#!/usr/bin/env python3
"""
Task 19 - Production Collector Packaging: Acceptance Test Suite

Tests all 9 acceptance criteria for the collector v1.1.0.
Run on the Docker host (not inside a container).
"""
import subprocess
import json
import time
import sys
import os

PASS = 0
FAIL = 0
IMAGE = "rhinometric-collector:v1.1.0"
NETWORK = "rhinometric_rhinometric_network"
API_URL = "http://rhinometric-nginx/api"
SERVICE_KEY = "t12-collector-key"
TOKEN = "rtk_7VgwIsGTXA-S24okEZIN_AFwtrAq5uyhcLzIWlCHSV5hduV-Sfz368SlgxZsc7wz"
COLLECTOR_DIR = "/opt/rhinometric/rhinometric-console/collector"


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}" + (f" -- {detail}" if detail else ""))
    return condition


def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", -1


def cleanup(name):
    sh(f"docker stop {name} 2>/dev/null; docker rm {name} 2>/dev/null")


print("=" * 60)
print("  Task 19: Production Collector Acceptance Tests")
print("=" * 60)

# -- AC1: Fail-fast on missing config --
print("\n[AC1] Fail-fast on missing config")
output, code = sh(f"docker run --rm {IMAGE}")
check("Exit code is non-zero", code != 0, f"got {code}")
check("Shows Configuration Error box", "Configuration Error" in output)
check("Lists RHYNO_API_URL as required", "RHYNO_API_URL" in output)
check("Lists RHYNO_SERVICE_KEY as required", "RHYNO_SERVICE_KEY" in output)
check("Lists RHYNO_TELEMETRY_TOKEN as required", "RHYNO_TELEMETRY_TOKEN" in output)
check("Has X markers for missing vars", output.count("\u2717") >= 3 or output.count("\\u2717") >= 3 or "required" in output.lower())

# -- AC2: Startup banner with masked token --
print("\n[AC2] Startup banner with masked token")
cname = "ac2-banner-test"
cleanup(cname)
sh(f"docker run -d --name {cname} --network {NETWORK} "
   f"-e RHYNO_API_URL={API_URL} "
   f"-e RHYNO_SERVICE_KEY={SERVICE_KEY} "
   f"-e RHYNO_TELEMETRY_TOKEN={TOKEN} "
   f"-e COLLECT_INTERVAL=60 "
   f"{IMAGE}")
time.sleep(6)
logs, _ = sh(f"docker logs {cname}")
cleanup(cname)

check("Banner contains version v1.1.0", "v1.1.0" in logs, logs[:200] if logs else "no logs")
check("Banner contains service key", SERVICE_KEY in logs)
banner_section = logs.split("Collector running")[0] if "Collector running" in logs else logs
check("Full token NOT visible in banner", TOKEN not in banner_section)
check("Shows masked token hint (c7wz)", "c7wz" in logs)
check("Shows hostname", "Hostname" in logs or "hostname" in logs)
check("Shows interval 60s", "60s" in logs)

# -- AC3: Preflight connectivity check --
print("\n[AC3] Preflight connectivity check")
check("Preflight shows API reachable", "API reachable" in logs)
check("Preflight check mentioned", "preflight" in logs.lower())

# -- AC4: ENV overrides (config precedence) --
print("\n[AC4] Config precedence (ENV overrides)")
cname2 = "ac4-override-test"
cleanup(cname2)
sh(f"docker run -d --name {cname2} --network {NETWORK} "
   f"-e RHYNO_API_URL={API_URL} "
   f"-e RHYNO_SERVICE_KEY={SERVICE_KEY} "
   f"-e RHYNO_TELEMETRY_TOKEN={TOKEN} "
   f"-e COLLECT_INTERVAL=30 "
   f"-e ENABLE_TRACES=false "
   f"-e LOG_LEVEL=DEBUG "
   f"{IMAGE}")
time.sleep(6)
logs2, _ = sh(f"docker logs {cname2}")
cleanup(cname2)

check("Interval shows 30s from ENV", "30s" in logs2)
signals_line = ""
for line in logs2.split("\n"):
    if "Signals" in line:
        signals_line = line
        break
check("Traces not in signals list", "traces" not in signals_line.lower() if signals_line else False,
      f"signals_line: {signals_line}")
check("LOG_LEVEL is DEBUG in banner", "DEBUG" in logs2)

# -- AC5: Per-cycle signal-level results --
print("\n[AC5] Per-cycle signal-level results")
cname3 = "ac5-cycle-test"
cleanup(cname3)
sh(f"docker run -d --name {cname3} --network {NETWORK} "
   f"-e RHYNO_API_URL={API_URL} "
   f"-e RHYNO_SERVICE_KEY={SERVICE_KEY} "
   f"-e RHYNO_TELEMETRY_TOKEN={TOKEN} "
   f"-e COLLECT_INTERVAL=8 "
   f"{IMAGE}")
time.sleep(22)
logs3, _ = sh(f"docker logs {cname3}")
cleanup(cname3)

check("Shows Cycle 1 in logs", "Cycle 1" in logs3)
check("Shows Cycle 2 in logs", "Cycle 2" in logs3)
check("Shows OK status", "OK" in logs3)
check("Shows signal metrics in log", "metrics:" in logs3)
check("Shows signal logs in log", "logs:" in logs3)
check("Shows signal traces in log", "traces:" in logs3)
check("Shows cycle duration ms", "ms" in logs3)

# -- AC6: Docker image metadata --
print("\n[AC6] Docker image metadata")
out6, rc6 = sh(f"docker inspect {IMAGE}")
inspect_data = {}
if rc6 == 0:
    try:
        inspect_data = json.loads(out6)[0]
    except Exception:
        pass
labels = inspect_data.get("Config", {}).get("Labels", {})
check("Image exists", rc6 == 0)
check("Has version label 1.1.0", labels.get("version") == "1.1.0", f"got: {labels.get('version')}")
check("Has description label", bool(labels.get("description", "")))
check("Has maintainer label", bool(labels.get("maintainer", "")))
healthcheck = inspect_data.get("Config", {}).get("Healthcheck", {})
check("Has HEALTHCHECK defined", bool(healthcheck))

# -- AC7: .env.example completeness --
print("\n[AC7] .env.example completeness")
env_path = os.path.join(COLLECTOR_DIR, ".env.example")
try:
    with open(env_path) as f:
        env_content = f.read()
    check("Contains RHYNO_API_URL", "RHYNO_API_URL" in env_content)
    check("Contains RHYNO_SERVICE_KEY", "RHYNO_SERVICE_KEY" in env_content)
    check("Contains RHYNO_TELEMETRY_TOKEN", "RHYNO_TELEMETRY_TOKEN" in env_content)
    check("Contains COLLECT_INTERVAL", "COLLECT_INTERVAL" in env_content)
    check("Contains ENABLE_METRICS", "ENABLE_METRICS" in env_content)
    check("Contains LOG_LEVEL", "LOG_LEVEL" in env_content)
    check("Has helpful comments", env_content.count("#") >= 5)
except FileNotFoundError:
    check(".env.example exists", False, "File not found")

# -- AC8: README.md quality --
print("\n[AC8] README.md quality")
readme_path = os.path.join(COLLECTOR_DIR, "README.md")
try:
    with open(readme_path) as f:
        readme = f.read()
    check("README > 5KB", len(readme) > 5000, f"got {len(readme)} bytes")
    check("Has Quick Start section", "quick start" in readme.lower())
    check("Has Troubleshooting section", "troubleshoot" in readme.lower())
    check("Has docker run example", "docker run" in readme)
    check("Has docker compose example", "docker-compose" in readme.lower() or "docker compose" in readme.lower())
    check("Has config table", "RHYNO_API_URL" in readme and "Required" in readme)
    check("Has architecture section", "architecture" in readme.lower())
    check("Has version history", "1.1.0" in readme)
except FileNotFoundError:
    check("README.md exists", False, "File not found")

# -- AC9: Service state = receiving_data --
print("\n[AC9] Service state = receiving_data")
out9, _ = sh(
    "docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -t -A -c "
    "\"SELECT telemetry_status, last_telemetry_at IS NOT NULL as has_ts, telemetry_attached "
    f"FROM external_services WHERE telemetry_service_key = '{SERVICE_KEY}'\""
)
parts = out9.strip().split("|") if "|" in out9 else []
if len(parts) >= 3:
    check("Status is receiving_data", parts[0].strip().lower() == "receiving_data", f"got: {parts[0].strip()}")
    check("last_telemetry_at is set", parts[1].strip() == "t")
    check("telemetry_attached is True", parts[2].strip() == "t")
else:
    check("Service found in DB", False, f"output: {out9[:100]}")

# -- Summary --
print("\n" + "=" * 60)
total = PASS + FAIL
pct = (PASS / total * 100) if total > 0 else 0
print(f"  Results: {PASS}/{total} passed ({pct:.0f}%), {FAIL} failed")
if FAIL == 0:
    print("  ALL ACCEPTANCE CRITERIA MET")
else:
    print(f"  {FAIL} check(s) failed")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
