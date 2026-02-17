#!/usr/bin/env python3
"""
Lightweight simulated node_exporter for Rhinometric load testing.

Spawns N HTTP servers, each on a different port (starting at 9200),
each exposing /metrics with realistic node_exporter-style Prometheus
metrics. Each port = one simulated host.

Usage:
    python3 sim_node_exporter.py <num_hosts>
    python3 sim_node_exporter.py 20     # simulate 20 hosts
    python3 sim_node_exporter.py 100    # simulate 100 hosts

Each simulated host exposes:
    - node_cpu_seconds_total (per-CPU with mode labels)
    - node_memory_MemTotal_bytes / MemAvailable_bytes
    - node_filesystem_size_bytes / avail_bytes
    - node_network_receive_bytes_total / transmit_bytes_total
    - node_load1 / node_load5 / node_load15
    - node_uname_info (with unique nodename per host)
    - node_boot_time_seconds
    - up (always 1)

Metrics have small random variations to look realistic.
"""

import http.server
import threading
import time
import random
import sys
import os
import signal
import socket

BASE_PORT = 9200
START_TIME = time.time()

# Realistic base values
BASE_MEM_TOTAL = 16 * 1024 * 1024 * 1024        # 16 GB
BASE_DISK_TOTAL = 500 * 1024 * 1024 * 1024       # 500 GB
BASE_BOOT_TIME = time.time() - random.randint(86400, 864000)


def generate_metrics(host_id: int) -> str:
    """Generate realistic node_exporter metrics for a simulated host."""
    now = time.time()
    uptime = now - START_TIME
    hostname = f"sim-host-{host_id:03d}"

    # Vary base values per host (deterministic seed from host_id)
    rng = random.Random(host_id)
    mem_total = BASE_MEM_TOTAL + rng.randint(-4, 4) * 1024 * 1024 * 1024
    disk_total = BASE_DISK_TOTAL + rng.randint(-100, 100) * 1024 * 1024 * 1024
    num_cpus = rng.choice([2, 4, 8])
    boot_time = BASE_BOOT_TIME - rng.randint(0, 86400 * 30)

    # Dynamic variations (changes on every scrape)
    cpu_idle_pct = 0.65 + random.uniform(-0.15, 0.15)
    mem_used_pct = 0.35 + random.uniform(-0.15, 0.20)
    disk_used_pct = 0.20 + random.uniform(-0.05, 0.30)
    load1 = num_cpus * (0.3 + random.uniform(-0.2, 0.5))
    load5 = num_cpus * (0.25 + random.uniform(-0.15, 0.4))
    load15 = num_cpus * (0.2 + random.uniform(-0.1, 0.3))

    net_rx = int(uptime * (500000 + random.randint(0, 1000000)))
    net_tx = int(uptime * (200000 + random.randint(0, 500000)))

    mem_avail = int(mem_total * (1 - mem_used_pct))
    disk_avail = int(disk_total * (1 - disk_used_pct))

    lines = []
    lines.append("# HELP up Whether the target is up.")
    lines.append("# TYPE up gauge")
    lines.append("up 1")
    lines.append("")

    # CPU seconds (cumulative, grows with uptime)
    lines.append("# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.")
    lines.append("# TYPE node_cpu_seconds_total counter")
    for cpu in range(num_cpus):
        base = uptime + cpu * 0.1
        lines.append(f'node_cpu_seconds_total{{cpu="{cpu}",mode="idle"}} {base * cpu_idle_pct:.2f}')
        lines.append(f'node_cpu_seconds_total{{cpu="{cpu}",mode="user"}} {base * (1 - cpu_idle_pct) * 0.6:.2f}')
        lines.append(f'node_cpu_seconds_total{{cpu="{cpu}",mode="system"}} {base * (1 - cpu_idle_pct) * 0.3:.2f}')
        lines.append(f'node_cpu_seconds_total{{cpu="{cpu}",mode="iowait"}} {base * (1 - cpu_idle_pct) * 0.1:.2f}')
    lines.append("")

    # Memory
    lines.append("# HELP node_memory_MemTotal_bytes Total memory in bytes.")
    lines.append("# TYPE node_memory_MemTotal_bytes gauge")
    lines.append(f"node_memory_MemTotal_bytes {mem_total}")
    lines.append("# HELP node_memory_MemAvailable_bytes Available memory in bytes.")
    lines.append("# TYPE node_memory_MemAvailable_bytes gauge")
    lines.append(f"node_memory_MemAvailable_bytes {mem_avail}")
    lines.append("")

    # Filesystem
    lines.append("# HELP node_filesystem_size_bytes Filesystem size in bytes.")
    lines.append("# TYPE node_filesystem_size_bytes gauge")
    lines.append(f'node_filesystem_size_bytes{{device="/dev/sda1",fstype="ext4",mountpoint="/"}} {disk_total}')
    lines.append("# HELP node_filesystem_avail_bytes Filesystem available in bytes.")
    lines.append("# TYPE node_filesystem_avail_bytes gauge")
    lines.append(f'node_filesystem_avail_bytes{{device="/dev/sda1",fstype="ext4",mountpoint="/"}} {disk_avail}')
    lines.append("")

    # Network
    lines.append("# HELP node_network_receive_bytes_total Network bytes received.")
    lines.append("# TYPE node_network_receive_bytes_total counter")
    lines.append(f'node_network_receive_bytes_total{{device="eth0"}} {net_rx}')
    lines.append("# HELP node_network_transmit_bytes_total Network bytes transmitted.")
    lines.append("# TYPE node_network_transmit_bytes_total counter")
    lines.append(f'node_network_transmit_bytes_total{{device="eth0"}} {net_tx}')
    lines.append("")

    # Load averages
    lines.append("# HELP node_load1 1-minute load average.")
    lines.append("# TYPE node_load1 gauge")
    lines.append(f"node_load1 {load1:.2f}")
    lines.append("# HELP node_load5 5-minute load average.")
    lines.append("# TYPE node_load5 gauge")
    lines.append(f"node_load5 {load5:.2f}")
    lines.append("# HELP node_load15 15-minute load average.")
    lines.append("# TYPE node_load15 gauge")
    lines.append(f"node_load15 {load15:.2f}")
    lines.append("")

    # Uname info
    lines.append("# HELP node_uname_info Labeled system information from uname.")
    lines.append("# TYPE node_uname_info gauge")
    lines.append(f'node_uname_info{{domainname="(none)",machine="x86_64",nodename="{hostname}",release="5.15.0-generic",sysname="Linux",version="#1 SMP"}} 1')
    lines.append("")

    # Boot time
    lines.append("# HELP node_boot_time_seconds Node boot time in seconds since epoch.")
    lines.append("# TYPE node_boot_time_seconds gauge")
    lines.append(f"node_boot_time_seconds {boot_time:.0f}")
    lines.append("")

    return "\n".join(lines) + "\n"


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that serves Prometheus metrics."""

    def do_GET(self):
        if self.path == "/metrics":
            body = generate_metrics(self.server.host_id)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default access logs to keep output clean."""
        pass


def start_server(host_id: int, port: int):
    """Start an HTTP server for one simulated host."""
    server = http.server.HTTPServer(("0.0.0.0", port), MetricsHandler)
    server.host_id = host_id
    server.serve_forever()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <num_hosts>")
        print(f"  Example: {sys.argv[0]} 20")
        sys.exit(1)

    num_hosts = int(sys.argv[1])
    if num_hosts < 1 or num_hosts > 200:
        print("Error: num_hosts must be between 1 and 200")
        sys.exit(1)

    print(f"Starting {num_hosts} simulated node_exporters on ports {BASE_PORT}-{BASE_PORT + num_hosts - 1}")

    threads = []
    for i in range(num_hosts):
        host_id = i + 1
        port = BASE_PORT + i
        t = threading.Thread(target=start_server, args=(host_id, port), daemon=True)
        t.start()
        threads.append(t)

    print(f"All {num_hosts} simulated hosts are running.")
    print("Press Ctrl+C to stop.")

    # Handle graceful shutdown
    def shutdown(signum, frame):
        print(f"\nShutting down {num_hosts} simulated hosts...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Keep main thread alive
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
