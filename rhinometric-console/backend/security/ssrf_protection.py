"""
SSRF Protection for External Services HTTP/HTTPS Connectors.

Validates target URLs before any outbound HTTP request to prevent
Server-Side Request Forgery (SSRF) attacks.
"""

import ipaddress
import logging
import socket
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger('rhinometric.ssrf_protection')

ALLOWED_SCHEMES = frozenset({'http', 'https'})

BLOCKED_HOSTNAMES = frozenset({
    'localhost',
    'localhost.localdomain',
    'host.docker.internal',
    'gateway.docker.internal',
    'kubernetes.default',
    'kubernetes.default.svc',
    'kubernetes.default.svc.cluster.local',
    'metadata.google.internal',
    'metadata.internal',
})

FORBIDDEN_IPV4_NETWORKS = [
    ipaddress.IPv4Network('127.0.0.0/8'),
    ipaddress.IPv4Network('10.0.0.0/8'),
    ipaddress.IPv4Network('172.16.0.0/12'),
    ipaddress.IPv4Network('192.168.0.0/16'),
    ipaddress.IPv4Network('169.254.0.0/16'),
    ipaddress.IPv4Network('0.0.0.0/8'),
    ipaddress.IPv4Network('100.64.0.0/10'),
    ipaddress.IPv4Network('224.0.0.0/4'),
    ipaddress.IPv4Network('240.0.0.0/4'),
    ipaddress.IPv4Network('255.255.255.255/32'),
]

FORBIDDEN_IPV6_NETWORKS = [
    ipaddress.IPv6Network('::1/128'),
    ipaddress.IPv6Network('::/128'),
    ipaddress.IPv6Network('fe80::/10'),
    ipaddress.IPv6Network('fc00::/7'),
    ipaddress.IPv6Network('ff00::/8'),
    ipaddress.IPv6Network('::ffff:127.0.0.0/104'),
    ipaddress.IPv6Network('::ffff:10.0.0.0/104'),
    ipaddress.IPv6Network('::ffff:172.16.0.0/108'),
    ipaddress.IPv6Network('::ffff:192.168.0.0/112'),
    ipaddress.IPv6Network('::ffff:169.254.0.0/112'),
    ipaddress.IPv6Network('::ffff:0.0.0.0/104'),
]


@dataclass
class SSRFValidationResult:
    """Result of SSRF URL validation."""
    is_safe: bool
    safe_url: Optional[str] = None
    hostname: Optional[str] = None
    resolved_ips: Optional[List[str]] = None
    reason: Optional[str] = None


def is_forbidden_ip(ip_str: str) -> Tuple[bool, str]:
    """Check if an IP address belongs to a forbidden range."""
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True, f'Invalid IP address: {ip_str}'

    if isinstance(addr, ipaddress.IPv4Address):
        for network in FORBIDDEN_IPV4_NETWORKS:
            if addr in network:
                return True, f'IP {ip_str} belongs to forbidden range {network}'
        return False, ''
    elif isinstance(addr, ipaddress.IPv6Address):
        for network in FORBIDDEN_IPV6_NETWORKS:
            if addr in network:
                return True, f'IP {ip_str} belongs to forbidden range {network}'
        if addr.ipv4_mapped:
            v4 = addr.ipv4_mapped
            for network in FORBIDDEN_IPV4_NETWORKS:
                if v4 in network:
                    return True, f'IPv4-mapped address {ip_str} resolves to forbidden range {network}'
        return False, ''
    return True, f'Unknown IP address type: {ip_str}'


def _is_blocked_hostname(hostname: str) -> Tuple[bool, str]:
    """Check if hostname is in the blocked list."""
    normalized = hostname.lower().strip().rstrip('.')
    if normalized in BLOCKED_HOSTNAMES:
        return True, f'Hostname "{hostname}" is a blocked internal target'
    if normalized.endswith('.internal') or normalized.endswith('.local'):
        return True, f'Hostname "{hostname}" appears to be an internal DNS name'
    return False, ''


def _is_ip_literal(hostname: str) -> bool:
    """Check if the hostname is an IP address literal."""
    clean = hostname.strip('[]')
    try:
        ipaddress.ip_address(clean)
        return True
    except ValueError:
        return False


def _resolve_hostname(hostname: str) -> Tuple[List[str], Optional[str]]:
    """Resolve a hostname to all A and AAAA records."""
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = list(set(r[4][0] for r in results))
        if not ips:
            return [], f'DNS resolution returned no results for "{hostname}"'
        return ips, None
    except socket.gaierror as e:
        return [], f'DNS resolution failed for "{hostname}": {e}'
    except Exception as e:
        return [], f'Unexpected error resolving "{hostname}": {e}'


def validate_url(url: str, service_name: str = '') -> SSRFValidationResult:
    """
    Validate a URL for SSRF safety before making an outbound request.

    Performs:
    1. Scheme validation (http/https only)
    2. URL parsing and normalization
    3. Hostname blocklist check
    4. Direct IP validation (if IP literal)
    5. DNS resolution + resolved IP validation (if hostname)
    """
    if not url or not isinstance(url, str):
        return SSRFValidationResult(
            is_safe=False,
            reason='URL is empty or invalid',
        )

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception as e:
        return SSRFValidationResult(
            is_safe=False,
            reason=f'Failed to parse URL: {e}',
        )

    scheme = (parsed.scheme or '').lower()
    if scheme not in ALLOWED_SCHEMES:
        _log_blocked(service_name, url, f'Forbidden scheme: {scheme}')
        return SSRFValidationResult(
            is_safe=False,
            reason=f'Only HTTP and HTTPS protocols are allowed. Got: "{scheme}"',
        )

    hostname = parsed.hostname
    if not hostname:
        return SSRFValidationResult(
            is_safe=False,
            reason='URL does not contain a valid hostname',
        )

    hostname = hostname.lower().strip().rstrip('.')
    if not hostname:
        return SSRFValidationResult(
            is_safe=False,
            reason='URL hostname is empty after normalization',
        )

    if parsed.username or parsed.password:
        _log_blocked(service_name, hostname, 'URL contains userinfo (potential bypass)')
        return SSRFValidationResult(
            is_safe=False,
            hostname=hostname,
            reason='URLs with embedded credentials (user:pass@host) are not allowed',
        )

    blocked, block_reason = _is_blocked_hostname(hostname)
    if blocked:
        _log_blocked(service_name, hostname, block_reason)
        return SSRFValidationResult(
            is_safe=False,
            hostname=hostname,
            reason='Localhost and internal network targets are not allowed',
        )

    if _is_ip_literal(hostname):
        clean_ip = hostname.strip('[]')
        forbidden, ip_reason = is_forbidden_ip(clean_ip)
        if forbidden:
            _log_blocked(service_name, hostname, ip_reason)
            return SSRFValidationResult(
                is_safe=False,
                hostname=hostname,
                resolved_ips=[clean_ip],
                reason='Target host resolves to a private or forbidden IP range',
            )
        return SSRFValidationResult(
            is_safe=True,
            safe_url=url,
            hostname=hostname,
            resolved_ips=[clean_ip],
        )

    resolved_ips, resolve_error = _resolve_hostname(hostname)
    if resolve_error:
        return SSRFValidationResult(
            is_safe=False,
            hostname=hostname,
            reason=f'Cannot resolve hostname: DNS lookup failed for "{hostname}"',
        )

    for ip in resolved_ips:
        forbidden, ip_reason = is_forbidden_ip(ip)
        if forbidden:
            _log_blocked(service_name, hostname, f'Resolved IP {ip} is forbidden: {ip_reason}')
            return SSRFValidationResult(
                is_safe=False,
                hostname=hostname,
                resolved_ips=resolved_ips,
                reason='Target host resolves to a private or forbidden IP range',
            )

    return SSRFValidationResult(
        is_safe=True,
        safe_url=url,
        hostname=hostname,
        resolved_ips=resolved_ips,
    )


def _log_blocked(service_name: str, hostname: str, reason: str):
    """Log a blocked SSRF attempt at warning level."""
    ctx = f' (service: {service_name})' if service_name else ''
    logger.warning(f'[SSRF] Blocked request to "{hostname}"{ctx}: {reason}')