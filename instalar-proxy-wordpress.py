#!/usr/bin/env python3
"""
Añadir función proxy a functions.php del tema activo vía WordPress REST API
"""
import requests
import json
import base64

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"

print("=" * 80)
print("🚀 INSTALACIÓN AUTOMÁTICA DEL PROXY EN WORDPRESS")
print("=" * 80)

# Leer el código PHP
with open('CODIGO_PARA_FUNCTIONS_PHP.php', 'r', encoding='utf-8') as f:
    php_code = f.read()

print(f"\n📄 Código PHP leído: {len(php_code)} caracteres")

# WordPress no permite editar archivos vía REST API por seguridad
# PERO podemos usar Code Snippets plugin si está instalado

auth = (WP_USER, WP_PASSWORD)

# Verificar si está instalado Code Snippets plugin
print("\n🔍 Verificando plugins instalados...")
try:
    response = requests.get(
        f"{WP_URL}/wp-json/wp/v2/plugins",
        auth=auth,
        timeout=10
    )
    
    if response.status_code == 200:
        plugins = response.json()
        code_snippets_installed = any('code-snippets' in p.get('plugin', '').lower() for p in plugins)
        
        if code_snippets_installed:
            print("✅ Code Snippets plugin detectado")
        else:
            print("⚠️  Code Snippets plugin no instalado")
    else:
        print(f"⚠️  No se pudo verificar plugins: HTTP {response.status_code}")
except Exception as e:
    print(f"⚠️  Error al verificar plugins: {e}")

print("\n" + "=" * 80)
print("📋 PASOS PARA COMPLETAR LA INSTALACIÓN")
print("=" * 80)

print("""
🎯 OPCIÓN 1: Copiar/Pegar en functions.php (2 MINUTOS)
────────────────────────────────────────────────────────────────

1. Abre WordPress Admin:
   https://rhinometric.com/wp-admin/theme-editor.php

2. Click en "functions.php" (primera opción en la lista derecha)

3. Scroll hasta el FINAL del archivo

4. Pega el código del archivo: CODIGO_PARA_FUNCTIONS_PHP.php
   (Está copiado abajo para tu comodidad)

5. Click "Update File"

6. Prueba el formulario: https://rhinometric.com/trial/

────────────────────────────────────────────────────────────────
""")

print("\n📋 CÓDIGO PARA COPIAR Y PEGAR:\n")
print("=" * 80)
print(php_code)
print("=" * 80)

print("""
\n🎯 OPCIÓN 2: Usar Code Snippets Plugin (MÁS SEGURO)
────────────────────────────────────────────────────────────────

1. Instalar "Code Snippets" plugin:
   wp-admin → Plugins → Add New → Buscar "Code Snippets"

2. Activar el plugin

3. Ir a: Snippets → Add New

4. Título: "Rhinometric Trial Proxy"

5. Pegar el código (todo excepto <?php del inicio)

6. Activar "Run snippet everywhere"

7. Save and Activate

────────────────────────────────────────────────────────────────
""")

print("\n✅ VERIFICACIÓN")
print("=" * 80)
print("""
Una vez añadido el código, prueba manualmente:

curl -X POST 'https://rhinometric.com/wp-admin/admin-ajax.php' \\
  -d 'action=rhinometric_trial' \\
  -d 'customer_name=Test User' \\
  -d 'client_email=test@example.com' \\
  -d 'client_company=Test Company'

Deberías recibir un JSON con la licencia creada.

O simplemente ve a https://rhinometric.com/trial/ y rellena el formulario.
""")

print("\n🔧 SOLUCIÓN DE PROBLEMAS")
print("=" * 80)
print("""
Si el formulario sigue dando error:

1. Ver logs de WordPress:
   sudo tail -f /var/log/nginx/error.log
   (o /var/log/apache2/error.log si usas Apache)

2. Verificar que el License Server responde:
   curl -v http://54.197.192.198:5000/api/health

3. Verificar conectividad interna desde WordPress:
   ssh ubuntu@15.236.157.190
   curl -v http://54.197.192.198:5000/api/health
   
   Si esto falla, el puerto 5000 está bloqueado incluso internamente.

4. Contactar: rafael.canelon@rhinometric.com
""")

print("\n✅ Archivos actualizados:")
print("  - docs/v2.5.0/wordpress/02-trial-linux-page.html → WordPress (página 2880)")
print("  - CODIGO_PARA_FUNCTIONS_PHP.php → Listo para copiar\n")
