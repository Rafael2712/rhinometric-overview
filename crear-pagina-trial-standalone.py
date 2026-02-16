#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import base64

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"
auth = (WP_USER, WP_PASSWORD)

# Leer el archivo HTML
with open('rhinometric-trial-form.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

print("📄 Creando página standalone de trial en WordPress...\n")

# Crear una nueva página con el formulario
page_data = {
    "title": "Trial Request - Rhinometric",
    "content": f"<!-- wp:html -->\n{html_content}\n<!-- /wp:html -->",
    "status": "publish",
    "slug": "trial-request",
    "template": "blank"  # Intentar usar plantilla en blanco si está disponible
}

try:
    response = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages",
        auth=auth,
        json=page_data,
        timeout=30
    )
    
    if response.status_code == 201:
        page = response.json()
        print("✅ ¡PÁGINA CREADA EXITOSAMENTE!")
        print(f"\n🔗 URL: {page['link']}")
        print(f"📝 ID: {page['id']}")
        print("\n" + "="*80)
        print("🎯 PRUEBA EL FORMULARIO AHORA:")
        print(f"{page['link']}")
        print("="*80)
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
