#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
RHINOMETRIC LICENSE SERVER - API Testing Script
═══════════════════════════════════════════════════════════════════════════

Tests all license validation and activation endpoints.

Usage:
    python test_license_api.py

Requirements:
    pip install httpx rich
═══════════════════════════════════════════════════════════════════════════
"""

import httpx
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import json

console = Console()

# Configuration
BASE_URL = "http://localhost:8090"  # License server URL
TEST_LICENSE_KEY = "RHINO-TRIAL-2025-DEMO001"  # Replace with actual test key

async def test_health():
    """Test health endpoint"""
    console.print("\n[bold cyan]1. Testing Health Endpoint[/bold cyan]")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                data = response.json()
                console.print(f"✅ Health check: [green]{data['status']}[/green]")
                console.print(f"   Version: {data['version']}")
                console.print(f"   Database: {data['database']}")
                return True
            else:
                console.print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            console.print(f"❌ Connection error: {str(e)}")
            return False

async def test_create_license():
    """Test creating a new license"""
    console.print("\n[bold cyan]2. Testing License Creation[/bold cyan]")
    
    payload = {
        "customer_name": "Test Customer API",
        "client_email": "test@rhinometric.com",
        "client_company": "Test Corp",
        "license_type": "trial",
        "client_phone": "+1234567890",
        "client_country": "Spain",
        "notes": "API Test License"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/admin/licenses",
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                console.print(f"✅ License created successfully!")
                console.print(f"   License Key: [yellow]{data['license_key']}[/yellow]")
                console.print(f"   Customer: {data['customer_name']}")
                console.print(f"   Expires: {data.get('expires_at', 'N/A')}")
                console.print(f"   Email sent: {data.get('email_sent', False)}")
                return data['license_key']
            else:
                console.print(f"❌ Creation failed: {response.status_code}")
                console.print(f"   Error: {response.text}")
                return None
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return None

async def test_validate_license(license_key: str):
    """Test license validation endpoint"""
    console.print(f"\n[bold cyan]3. Testing License Validation[/bold cyan]")
    
    payload = {
        "license_key": license_key,
        "hardware_id": "TEST-HARDWARE-001",
        "hostname": "test-server.local",
        "ip_address": "192.168.1.100",
        "user_agent": "Rhinometric-Installer/2.1.0",
        "client_info": {
            "os": "Ubuntu 22.04",
            "docker_version": "24.0.5"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/licenses/validate",
                json=payload
            )
            
            data = response.json()
            
            if response.status_code == 200:
                if data['valid']:
                    console.print(f"✅ License validation: [green]VALID[/green]")
                    console.print(f"   Customer: {data.get('customer_name')}")
                    console.print(f"   Type: {data.get('license_type')}")
                    console.print(f"   Days remaining: {data.get('days_remaining', 'N/A')}")
                    console.print(f"   Download allowed: {data['download_allowed']}")
                    console.print(f"   Download URL: {data.get('download_url', 'N/A')[:50]}...")
                    console.print(f"   Activation ID: {data.get('activation_id')}")
                    return True
                else:
                    console.print(f"❌ License validation: [red]INVALID[/red]")
                    console.print(f"   Message: {data['message']}")
                    return False
            else:
                console.print(f"❌ Validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return False

async def test_validate_invalid_license():
    """Test validation with invalid license"""
    console.print(f"\n[bold cyan]4. Testing Invalid License (Security)[/bold cyan]")
    
    payload = {
        "license_key": "RHINO-FAKE-9999-INVALID",
        "hardware_id": "ATTACKER-HARDWARE",
        "ip_address": "123.45.67.89",
        "user_agent": "curl/7.68.0"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/licenses/validate",
                json=payload
            )
            
            data = response.json()
            
            if not data['valid']:
                console.print(f"✅ Invalid license correctly rejected")
                console.print(f"   Message: {data['message']}")
                console.print(f"   (Failed attempt should be logged)")
                return True
            else:
                console.print(f"❌ Invalid license was accepted (SECURITY ISSUE!)")
                return False
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return False

async def test_get_activations(license_key: str):
    """Test getting activation history"""
    console.print(f"\n[bold cyan]5. Testing Activation History[/bold cyan]")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/licenses/{license_key}/activations"
            )
            
            if response.status_code == 200:
                activations = response.json()
                console.print(f"✅ Retrieved {len(activations)} activation(s)")
                
                if activations:
                    table = Table(title="Recent Activations")
                    table.add_column("ID", style="cyan")
                    table.add_column("Date", style="green")
                    table.add_column("IP Address", style="yellow")
                    table.add_column("Hardware ID", style="magenta")
                    table.add_column("Status", style="blue")
                    
                    for act in activations[:5]:  # Show only first 5
                        activated_at = datetime.fromisoformat(act['activated_at'].replace('Z', '+00:00'))
                        table.add_row(
                            str(act['id']),
                            activated_at.strftime('%Y-%m-%d %H:%M'),
                            act.get('ip_address', 'N/A'),
                            act.get('hardware_id', 'N/A')[:20],
                            act['validation_status']
                        )
                    
                    console.print(table)
                return True
            else:
                console.print(f"❌ Failed to get activations: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return False

async def test_get_stats():
    """Test license statistics endpoint"""
    console.print(f"\n[bold cyan]6. Testing License Statistics[/bold cyan]")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/admin/licenses/stats")
            
            if response.status_code == 200:
                stats = response.json()
                console.print(f"✅ Statistics retrieved successfully")
                
                # License counts
                licenses = stats.get('licenses', {})
                console.print(f"\n📊 [bold]License Summary:[/bold]")
                console.print(f"   Total: {licenses.get('total', 0)}")
                console.print(f"   Active: {licenses.get('active', 0)}")
                console.print(f"   Expired: {licenses.get('expired', 0)}")
                console.print(f"   Revoked: {licenses.get('revoked', 0)}")
                console.print(f"   Expiring soon: {licenses.get('expiring_soon', 0)}")
                
                # By type
                by_type = licenses.get('by_type', {})
                console.print(f"\n📋 [bold]By Type:[/bold]")
                console.print(f"   Trial: {by_type.get('trial', 0)}")
                console.print(f"   Annual: {by_type.get('annual', 0)}")
                console.print(f"   Permanent: {by_type.get('permanent', 0)}")
                
                # Activations
                activations = stats.get('activations', {})
                console.print(f"\n🔄 [bold]Activations:[/bold]")
                console.print(f"   Total: {activations.get('total', 0)}")
                console.print(f"   Unique IPs: {activations.get('unique_ips', 0)}")
                console.print(f"   Unique Hardware: {activations.get('unique_hardware', 0)}")
                console.print(f"   Today: {activations.get('today', 0)}")
                console.print(f"   Avg per license: {activations.get('avg_per_license', 0)}")
                
                # Security
                security = stats.get('security', {})
                console.print(f"\n🔒 [bold]Security:[/bold]")
                console.print(f"   Failed attempts (today): {security.get('failed_attempts_today', 0)}")
                console.print(f"   Failed attempts (total): {security.get('failed_attempts_total', 0)}")
                console.print(f"   Success rate: {security.get('success_rate', 100)}%")
                
                # Top licenses
                top = stats.get('top_licenses', [])
                if top:
                    console.print(f"\n🏆 [bold]Top Active Licenses:[/bold]")
                    for lic in top:
                        console.print(f"   {lic['customer_name']}: {lic['activations']} activations")
                
                return True
            else:
                console.print(f"❌ Failed to get stats: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return False

async def test_security_alerts():
    """Test security alerts endpoint"""
    console.print(f"\n[bold cyan]7. Testing Security Alerts[/bold cyan]")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/admin/licenses/security")
            
            if response.status_code == 200:
                data = response.json()
                suspicious = data.get('suspicious_activations', [])
                failures = data.get('failed_attempts', [])
                alert_count = data.get('alert_count', 0)
                
                console.print(f"✅ Security check completed")
                console.print(f"   Total alerts: {alert_count}")
                console.print(f"   Suspicious activations: {len(suspicious)}")
                console.print(f"   Failed attempts: {len(failures)}")
                
                if alert_count == 0:
                    console.print(f"   [green]No security issues detected[/green]")
                else:
                    console.print(f"   [yellow]⚠️  Review alerts for potential issues[/yellow]")
                
                return True
            else:
                console.print(f"❌ Failed to get security alerts: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
            return False

async def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold magenta]RHINOMETRIC LICENSE SERVER - API TEST SUITE[/bold magenta]\n"
        f"Target: {BASE_URL}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="magenta"
    ))
    
    results = {
        "passed": 0,
        "failed": 0
    }
    
    # Run tests
    tests = [
        ("Health Check", test_health()),
        ("Create License", test_create_license()),
    ]
    
    # Test 1: Health
    if await tests[0][1]:
        results["passed"] += 1
    else:
        results["failed"] += 1
        console.print("\n[bold red]❌ Server not ready, aborting tests[/bold red]")
        return
    
    # Test 2: Create license
    license_key = await tests[1][1]
    if license_key:
        results["passed"] += 1
    else:
        results["failed"] += 1
        license_key = TEST_LICENSE_KEY
        console.print(f"\n[yellow]Using fallback license key: {license_key}[/yellow]")
    
    # Test 3-7: Remaining tests
    remaining_tests = [
        ("Validate License", test_validate_license(license_key)),
        ("Invalid License", test_validate_invalid_license()),
        ("Activation History", test_get_activations(license_key)),
        ("Statistics", test_get_stats()),
        ("Security Alerts", test_security_alerts()),
    ]
    
    for test_name, test_coro in remaining_tests:
        if await test_coro:
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # Summary
    total_tests = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total_tests * 100) if total_tests > 0 else 0
    
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        f"[bold]TEST SUMMARY[/bold]\n\n"
        f"✅ Passed: [green]{results['passed']}[/green]\n"
        f"❌ Failed: [red]{results['failed']}[/red]\n"
        f"📊 Pass Rate: {pass_rate:.1f}%",
        border_style="cyan" if results['failed'] == 0 else "red"
    ))
    
    if results['failed'] == 0:
        console.print("\n[bold green]🎉 All tests passed! License API is ready for production.[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️  {results['failed']} test(s) failed. Review logs above.[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(main())
