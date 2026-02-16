#!/usr/bin/env python3
"""
RHINOMETRIC v2.4.0 - JWT Token Generator
=========================================

Helper to generate valid JWT tokens for testing Dashboard Builder API.

Usage:
    python generate_jwt.py --username admin --role admin
    python generate_jwt.py --username viewer --role viewer --expires-in 7200

Outputs JWT token that can be used with Authorization header.
"""

import jwt
import os
import sys
from datetime import datetime, timedelta
import argparse


JWT_SECRET = os.getenv('JWT_SECRET', 'rhinometric-secret-key-change-in-production')


def generate_jwt(
    username: str = "admin",
    user_id: str = None,
    role: str = "admin",
    license_key: str = "RHINO-DEMO-2024-ABCD",
    customer: str = "Demo Customer",
    expires_in_seconds: int = 3600  # 1 hour default
) -> str:
    """
    Generate JWT token with standard claims.
    
    Args:
        username: Username for the token
        user_id: User ID (auto-generated if not provided)
        role: User role (admin, editor, viewer)
        license_key: RHINOMETRIC license key
        customer: Customer name
        expires_in_seconds: Token validity duration
    
    Returns:
        JWT token string
    """
    if not user_id:
        user_id = f"user_{username.lower().replace(' ', '_')}"
    
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=expires_in_seconds)
    
    payload = {
        # Standard JWT claims
        "iat": now.timestamp(),  # Issued at
        "exp": expires_at.timestamp(),  # Expiration
        "iss": "RHINOMETRIC",  # Issuer
        
        # Custom claims
        "user_id": user_id,
        "username": username,
        "role": role,
        "license_key": license_key,
        "customer": customer
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    return token


def main():
    parser = argparse.ArgumentParser(
        description="Generate JWT tokens for RHINOMETRIC Dashboard Builder"
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Username for the token (default: admin)"
    )
    parser.add_argument(
        "--user-id",
        help="User ID (auto-generated if not provided)"
    )
    parser.add_argument(
        "--role",
        default="admin",
        choices=["admin", "editor", "viewer"],
        help="User role (default: admin)"
    )
    parser.add_argument(
        "--license-key",
        default="RHINO-DEMO-2024-ABCD",
        help="License key (default: RHINO-DEMO-2024-ABCD)"
    )
    parser.add_argument(
        "--customer",
        default="Demo Customer",
        help="Customer name (default: Demo Customer)"
    )
    parser.add_argument(
        "--expires-in",
        type=int,
        default=3600,
        help="Token validity in seconds (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--output-curl",
        action="store_true",
        help="Output as curl command example"
    )
    
    args = parser.parse_args()
    
    # Generate token
    token = generate_jwt(
        username=args.username,
        user_id=args.user_id,
        role=args.role,
        license_key=args.license_key,
        customer=args.customer,
        expires_in_seconds=args.expires_in
    )
    
    # Decode to show payload (for verification)
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    expires_dt = datetime.fromtimestamp(payload["exp"])
    
    print("=" * 70)
    print("RHINOMETRIC JWT Token Generator")
    print("=" * 70)
    print(f"Username:     {args.username}")
    print(f"User ID:      {payload['user_id']}")
    print(f"Role:         {args.role}")
    print(f"License Key:  {args.license_key}")
    print(f"Customer:     {args.customer}")
    print(f"Expires:      {expires_dt.isoformat()} ({args.expires_in}s)")
    print("=" * 70)
    print("\nJWT Token:")
    print(token)
    print("=" * 70)
    
    if args.output_curl:
        print("\nCURL Example:")
        print(f"""
curl -X POST http://localhost:8001/api/dashboards \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {token}" \\
  -d '{{
    "dashboard": {{
      "title": "Test Dashboard",
      "description": "Created via API",
      "tags": ["test"],
      "panels": [],
      "time_range": {{"from": "now-6h", "to": "now"}},
      "refresh": "30s",
      "variables": []
    }},
    "overwrite": false
  }}'
""")
    
    print("\nTo use in Python requests:")
    print(f"""
import requests

headers = {{
    "Authorization": "Bearer {token}"
}}

response = requests.get("http://localhost:8001/api/dashboards", headers=headers)
print(response.json())
""")


if __name__ == "__main__":
    main()
