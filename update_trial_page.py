#!/usr/bin/env python3
"""
Update Trial page in WordPress with corrected endpoint
"""

import requests
from pathlib import Path

# WordPress credentials
WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASS = "C8tUQIzW9DEc e8mFFVrA0Nx9".replace(" ", "")

# Read the corrected HTML
file_path = Path("docs/v2.5.0/wordpress/02-trial-linux-page.html")
print(f"Reading: {file_path}")

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

print(f"Content length: {len(html_content)} chars")

# Get existing 'trial' page
api_url = f"{WP_URL}/wp-json/wp/v2/pages"
print(f"\nSearching for 'trial' page...")

response = requests.get(
    api_url,
    params={"slug": "trial"},
    auth=(WP_USER, WP_PASS),
    verify=True
)

if response.status_code == 200:
    pages = response.json()
    if pages:
        # Update existing page
        page_id = pages[0]["id"]
        page_url = pages[0]["link"]
        print(f"Found page ID: {page_id}")
        print(f"Current URL: {page_url}")
        
        update_url = f"{api_url}/{page_id}"
        
        update_data = {
            "content": html_content,
            "status": "publish"
        }
        
        print(f"\nUpdating page...")
        update_response = requests.post(
            update_url,
            json=update_data,
            auth=(WP_USER, WP_PASS),
            verify=True
        )
        
        if update_response.status_code == 200:
            print(f"\n✅ Trial page updated successfully!")
            print(f"🔗 URL: {page_url}")
            print(f"\n📧 The form now uses the CORRECT endpoint:")
            print(f"   https://licensing.rhinometric.com:5000/api/admin/licenses")
        else:
            print(f"\n❌ Error updating page: {update_response.status_code}")
            print(update_response.text[:500])
    else:
        print("❌ Trial page not found with slug 'trial'")
else:
    print(f"❌ Error searching pages: {response.status_code}")
    print(response.text[:500])
