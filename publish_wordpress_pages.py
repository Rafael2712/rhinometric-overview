#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress Pages Publisher for Rhinometric
Publishes 5 HTML pages via WordPress REST API
"""

import requests
import json
import os
from pathlib import Path

# WordPress credentials
WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASS = "C8tUQIzW9DEc e8mFFVrA0Nx9"  # Application Password (sin espacios)

# Pages directory
PAGES_DIR = Path("docs/v2.5.0/wordpress")

# Pages configuration
PAGES = [
    {
        "file": "00-home-page.html",
        "title": "Home",
        "slug": "home",
        "status": "publish"
    },
    {
        "file": "01-demo-ova-page.html",
        "title": "Demo",
        "slug": "demo",
        "status": "publish"
    },
    {
        "file": "02-trial-linux-page.html",
        "title": "Trial",
        "slug": "trial",
        "status": "publish"
    },
    {
        "file": "03-documentation-page.html",
        "title": "Documentation",
        "slug": "documentation",
        "status": "publish"
    },
    {
        "file": "04-contact-page.html",
        "title": "Contact",
        "slug": "contact",
        "status": "publish"
    }
]

def publish_page(page_config):
    """Publish a single page to WordPress"""
    print(f"\n📄 Publishing: {page_config['title']} ({page_config['file']})")
    
    # Read HTML content
    file_path = PAGES_DIR / page_config['file']
    if not file_path.exists():
        print(f"   ❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Prepare page data
    page_data = {
        "title": page_config['title'],
        "slug": page_config['slug'],
        "content": html_content,
        "status": page_config['status'],
        "type": "page"
    }
    
    # API endpoint
    api_url = f"{WP_URL}/wp-json/wp/v2/pages"
    
    # Make request with basic auth
    try:
        response = requests.post(
            api_url,
            json=page_data,
            auth=(WP_USER, WP_PASS),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            page_id = response.json().get('id')
            page_url = response.json().get('link')
            print(f"   ✅ Published successfully!")
            print(f"   📍 ID: {page_id}")
            print(f"   🔗 URL: {page_url}")
            return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def set_homepage(page_slug="home"):
    """Set a page as the homepage"""
    print(f"\n🏠 Setting '{page_slug}' as homepage...")
    
    # First, get the page ID
    api_url = f"{WP_URL}/wp-json/wp/v2/pages"
    try:
        response = requests.get(
            api_url,
            params={"slug": page_slug},
            auth=(WP_USER, WP_PASS)
        )
        
        if response.status_code == 200:
            pages = response.json()
            if pages:
                page_id = pages[0]['id']
                print(f"   📍 Found page ID: {page_id}")
                
                # Update site settings
                settings_url = f"{WP_URL}/wp-json/wp/v2/settings"
                settings_data = {
                    "show_on_front": "page",
                    "page_on_front": page_id
                }
                
                settings_response = requests.post(
                    settings_url,
                    json=settings_data,
                    auth=(WP_USER, WP_PASS)
                )
                
                if settings_response.status_code == 200:
                    print(f"   ✅ Homepage set successfully!")
                    return True
                else:
                    print(f"   ⚠️ Could not set homepage: {settings_response.status_code}")
                    return False
            else:
                print(f"   ⚠️ Page '{page_slug}' not found")
                return False
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("  RHINOMETRIC - WordPress Pages Publisher")
    print("=" * 60)
    print(f"Target: {WP_URL}")
    print(f"Pages to publish: {len(PAGES)}")
    print("=" * 60)
    
    # Publish all pages
    success_count = 0
    for page in PAGES:
        if publish_page(page):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Published: {success_count}/{len(PAGES)} pages")
    print("=" * 60)
    
    # Set homepage if all pages published
    if success_count == len(PAGES):
        set_homepage("home")
    
    print("\n🎉 DONE! Visit: https://rhinometric.com\n")

if __name__ == "__main__":
    main()
