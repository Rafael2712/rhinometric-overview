#!/usr/bin/env python3
"""
Subir el archivo proxy PHP al servidor WordPress usando REST API
"""
import requests
import base64
import json
from pathlib import Path

# Configuración WordPress
WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"

# Leer el archivo proxy PHP
proxy_file = Path("wordpress-trial-proxy.php")
if not proxy_file.exists():
    print(f"❌ Error: No se encontró {proxy_file}")
    exit(1)

with open(proxy_file, 'r', encoding='utf-8') as f:
    proxy_content = f.read()

print(f"📄 Archivo leído: {len(proxy_content)} caracteres\n")

# WordPress REST API endpoint para media/files
# Primero intentamos con el plugin WP File Manager API si está instalado
# Si no, usaremos la Media Library

# Opción 1: Intentar subir vía Media Library (requiere que sea un tipo de archivo permitido)
# Para PHP necesitamos otro método

# Opción 2: Crear un plugin temporal que contenga el archivo
plugin_name = "rhinometric-trial-proxy"
plugin_content = f"""<?php
/**
 * Plugin Name: Rhinometric Trial Proxy
 * Description: Proxy para formulario de trial de Rhinometric
 * Version: 1.0
 * Author: Rhinometric
 */

// El código del proxy se incluye directamente
{proxy_content}
"""

# Codificar en base64 para enviar
plugin_b64 = base64.b64encode(plugin_content.encode('utf-8')).decode('utf-8')

print("🔧 Intentando crear el proxy como plugin de WordPress...\n")

# Endpoint para crear contenido custom
# Vamos a usar una táctica diferente: crear una página con shortcode que ejecute el PHP

# MEJOR OPCIÓN: Subir vía FTP usando Python ftplib
print("⚠️  No puedo subir archivos PHP directamente via REST API por seguridad de WordPress")
print("📋 SOLUCIÓN ALTERNATIVA: Voy a crear el código en una Custom Function\n")

# Intentar agregar el código a functions.php del tema usando la API
# Primero necesitamos saber qué tema está activo

auth = (WP_USER, WP_PASSWORD)

# Obtener información del tema activo
print("🔍 Consultando tema activo de WordPress...")
try:
    # WordPress no tiene endpoint directo para esto, pero podemos usar wp-json/wp/v2/
    # Intentemos con la API de temas (requiere plugin adicional usualmente)
    
    # PLAN B: Crear el archivo directamente en el child theme vía REST API
    # usando un plugin de File Manager si existe
    
    print("\n📝 INSTRUCCIONES PARA COMPLETAR LA INSTALACIÓN:\n")
    print("El archivo 'wordpress-trial-proxy.php' está listo localmente.")
    print("\nNecesitas subirlo al servidor WordPress usando UNO de estos métodos:\n")
    
    print("=" * 70)
    print("MÉTODO 1: Via WP-CLI (RECOMENDADO - más rápido)")
    print("=" * 70)
    print("""
1. Conectar al servidor WordPress:
   Tu servidor ya tiene acceso, ejecuta:
   
   ssh ubuntu@15.236.157.190
   
2. Crear el archivo directamente:
   
   sudo nano /var/www/html/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php
   
3. Pegar el contenido del archivo wordpress-trial-proxy.php
   
4. Ajustar permisos:
   
   sudo chown www-data:www-data /var/www/html/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php
   sudo chmod 644 /var/www/html/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php

5. Probar:
   
   curl -X POST https://rhinometric.com/wp-content/themes/twentytwentyfour/rhinometric-trial-proxy.php \\
     -H "Content-Type: application/json" \\
     -d '{"customer_name":"Test","client_email":"test@test.com","client_company":"Test"}'
""")
    
    print("\n" + "=" * 70)
    print("MÉTODO 2: Via SFTP (FileZilla/WinSCP)")
    print("=" * 70)
    print("""
1. Abrir FileZilla/WinSCP
2. Conectar a: 15.236.157.190
3. Usuario: ubuntu
4. Autenticación: Usar tu clave SSH (.pem)
5. Navegar a: /var/www/html/wp-content/themes/twentytwentyfour/
6. Subir: wordpress-trial-proxy.php
7. Cambiar permisos a: 644
""")
    
    print("\n" + "=" * 70)
    print("MÉTODO 3: Via WordPress Plugin (sin SSH)")
    print("=" * 70)
    print("""
1. Instalar plugin "File Manager" en WordPress:
   wp-admin → Plugins → Añadir nuevo → Buscar "File Manager"
   
2. Ir a: wp-admin → File Manager

3. Navegar a: wp-content/themes/twentytwentyfour/

4. Upload → Seleccionar wordpress-trial-proxy.php

5. Cambiar permisos a 644 (click derecho → Change Permissions)
""")

    print("\n" + "=" * 70)
    print("🎯 VERIFICACIÓN")
    print("=" * 70)
    print("""
Una vez subido, prueba desde tu navegador:
https://rhinometric.com/trial/

Rellena el formulario y debería funcionar correctamente.

Si aún da error, verifica los logs:
sudo tail -f /var/log/nginx/error.log
""")
    
    print("\n✅ Archivo wordpress-trial-proxy.php listo para subir\n")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nVer INSTRUCCIONES_PROXY_WORDPRESS.md para métodos alternativos")
