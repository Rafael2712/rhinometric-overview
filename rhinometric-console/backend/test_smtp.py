#!/usr/bin/env python3
"""
SMTP Connection Test for Zoho Mail
Tests email sending capability
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_smtp():
    """Test SMTP connection and send test email"""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         ZOHO SMTP CONNECTION TEST                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Import email service
    from services.email_service import test_smtp_connection
    
    print("📧 Testing SMTP connection to Zoho...")
    print(f"   Server: {os.getenv('MAIL_SERVER')}")
    print(f"   Port: {os.getenv('MAIL_PORT')}")
    print(f"   From: {os.getenv('MAIL_FROM')}")
    print(f"   STARTTLS: {os.getenv('MAIL_STARTTLS')}")
    print()
    
    # Test connection
    result = await test_smtp_connection()
    
    if result["status"] == "success":
        print("✅ SMTP CONNECTION SUCCESSFUL")
        print(f"   Message: {result['message']}")
        print(f"   Test email sent to: {result['from']}")
    else:
        print("❌ SMTP CONNECTION FAILED")
        print(f"   Error: {result['message']}")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Check MAIL_USERNAME and MAIL_PASSWORD in .env")
        print("   2. Verify Zoho account allows SMTP (App Passwords may be required)")
        print("   3. Check firewall allows outbound port 587")
        print("   4. Verify MAIL_FROM matches MAIL_USERNAME exactly")
    
    print()
    return result

if __name__ == "__main__":
    result = asyncio.run(test_smtp())
    exit(0 if result["status"] == "success" else 1)
