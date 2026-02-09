#!/usr/bin/env python3
"""
Test script for forgot password email functionality
"""
import asyncio
from services.email_service import send_password_reset_email
from config import settings

async def test_forgot_password_email():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║    PASSWORD RESET EMAIL TEST - PRODUCTION FLOW            ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    email = "rafael.canelon@rhinometric.com"
    username = "admin"
    test_token = "TEST-TOKEN-12345-ABCDE-REAL-FLOW"
    
    print(f"📧 Sending password reset email to: {email}")
    print(f"👤 Username: {username}")
    print(f"🔗 Reset token: {test_token}")
    print(f"🌐 Frontend URL: {settings.FRONTEND_URL}\n")
    
    try:
        await send_password_reset_email(
            email=email,
            username=username,
            reset_token=test_token,
            frontend_url=settings.FRONTEND_URL
        )
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print(f"\n📬 Check inbox: {email}")
        print(f"🔗 Reset link: {settings.FRONTEND_URL}/reset-password?token={test_token}")
        
    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL")
        print(f"   Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_forgot_password_email())
