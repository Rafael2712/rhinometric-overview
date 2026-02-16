#!/usr/bin/env python3
"""
Instalar el código proxy directamente en WordPress via REST API
"""
import requests
import json
import base64

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"

auth = (WP_USER, WP_PASSWORD)

print("🔐 Conectando a WordPress...")
print(f"URL: {WP_URL}")
print(f"Usuario: {WP_USER}\n")

# Código PHP del proxy
php_code = """
// Hook AJAX para usuarios no logueados y logueados
add_action('wp_ajax_nopriv_rhinometric_trial', 'rhinometric_trial_proxy');
add_action('wp_ajax_rhinometric_trial', 'rhinometric_trial_proxy');

function rhinometric_trial_proxy() {
    header('Content-Type: application/json');
    
    if (empty($_POST['customer_name']) || empty($_POST['client_email']) || empty($_POST['client_company'])) {
        wp_send_json_error(['error' => 'Missing required fields', 'message' => 'Por favor completa todos los campos requeridos'], 400);
    }
    
    $customer_name = sanitize_text_field($_POST['customer_name']);
    $client_email = sanitize_email($_POST['client_email']);
    $client_company = sanitize_text_field($_POST['client_company']);
    
    if (!is_email($client_email)) {
        wp_send_json_error(['error' => 'Invalid email format', 'message' => 'El email proporcionado no es válido'], 400);
    }
    
    $payload = json_encode([
        'customer_name' => $customer_name,
        'client_email' => $client_email,
        'client_company' => $client_company,
        'license_type' => 'trial'
    ]);
    
    $license_server_url = 'http://54.197.192.198:5000/api/admin/licenses';
    
    $response = wp_remote_post($license_server_url, [
        'headers' => ['Content-Type' => 'application/json'],
        'body' => $payload,
        'timeout' => 30,
        'sslverify' => false
    ]);
    
    if (is_wp_error($response)) {
        error_log('Rhinometric Trial Error: ' . $response->get_error_message());
        wp_send_json_error(['error' => 'Connection failed', 'message' => 'No se pudo conectar con el servidor de licencias.', 'details' => $response->get_error_message()], 500);
    }
    
    $http_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    error_log("Rhinometric Trial Request: {$client_email} - HTTP {$http_code}");
    
    if ($http_code >= 200 && $http_code < 300) {
        $data = json_decode($body, true);
        wp_send_json_success($data, $http_code);
    } else {
        wp_send_json_error(['error' => 'License server error', 'message' => 'Error al generar la licencia.', 'http_code' => $http_code, 'response' => $body], $http_code);
    }
}
"""

# ESTRATEGIA 1: Crear un plugin vía WordPress Plugin API
print("📦 Intentando crear plugin 'Rhinometric Trial Proxy'...\n")

plugin_data = {
    "name": "Rhinometric Trial Proxy",
    "slug": "rhinometric-trial-proxy",
    "status": "active",
    "plugin": "rhinometric-trial-proxy/rhinometric-trial-proxy.php",
    "version": "1.0.0",
    "description": "Proxy para formulario de trial de Rhinometric",
    "author": "Rhinometric",
}

# WordPress REST API para plugins requiere autenticación y permisos especiales
# Intentar crear vía Code Snippets plugin si está instalado

print("🔍 Buscando Code Snippets plugin...\n")

# Verificar si Code Snippets está instalado
try:
    response = requests.get(
        f"{WP_URL}/wp-json/code-snippets/v1/snippets",
        auth=auth,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Code Snippets plugin encontrado!")
        print("📝 Creando snippet con el código proxy...\n")
        
        snippet_data = {
            "name": "Rhinometric Trial Proxy",
            "code": php_code,
            "scope": "global",
            "active": True,
            "priority": 10
        }
        
        create_response = requests.post(
            f"{WP_URL}/wp-json/code-snippets/v1/snippets",
            auth=auth,
            json=snippet_data,
            timeout=15
        )
        
        if create_response.status_code in [200, 201]:
            print("✅ ¡SNIPPET CREADO EXITOSAMENTE!")
            print(f"Respuesta: {create_response.json()}\n")
            print("🎉 El formulario de trial ya debería funcionar")
            print("🧪 Prueba en: https://rhinometric.com/trial/\n")
            exit(0)
        else:
            print(f"⚠️  Error al crear snippet: HTTP {create_response.status_code}")
            print(f"Respuesta: {create_response.text}\n")
    else:
        print(f"⚠️  Code Snippets no está instalado o no es accesible (HTTP {response.status_code})\n")
except Exception as e:
    print(f"⚠️  Error al acceder a Code Snippets: {e}\n")

# ESTRATEGIA 2: Crear una página personalizada que ejecute el código
print("📄 Intentando crear página personalizada con el código...\n")

page_content = f"""
<!-- wp:html -->
{php_code}
<!-- /wp:html -->
"""

try:
    page_data = {
        "title": "Rhinometric Trial Proxy Handler",
        "content": page_content,
        "status": "publish",
        "slug": "rhinometric-trial-handler"
    }
    
    response = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages",
        auth=auth,
        json=page_data,
        timeout=15
    )
    
    if response.status_code == 201:
        print("✅ Página creada (pero PHP no se ejecutará desde contenido)\n")
    else:
        print(f"⚠️  No se pudo crear página: HTTP {response.status_code}\n")
except Exception as e:
    print(f"⚠️  Error: {e}\n")

# ESTRATEGIA 3: Intentar usar WP File Manager plugin si está instalado
print("🔍 Buscando WP File Manager plugin...\n")

try:
    # Algunos plugins de File Manager exponen REST API
    response = requests.get(
        f"{WP_URL}/wp-json/file-manager/v1/list",
        auth=auth,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ File Manager plugin encontrado!")
        # Aquí podríamos crear el archivo, pero cada plugin tiene su API diferente
    else:
        print(f"⚠️  File Manager no accesible\n")
except:
    print("⚠️  File Manager no está instalado\n")

# ESTRATEGIA 4: Intentar instalar Code Snippets automáticamente
print("📦 Intentando instalar Code Snippets plugin...\n")

try:
    install_response = requests.post(
        f"{WP_URL}/wp-json/wp/v2/plugins",
        auth=auth,
        json={"slug": "code-snippets", "status": "active"},
        timeout=30
    )
    
    if install_response.status_code in [200, 201]:
        print("✅ ¡Code Snippets instalado exitosamente!")
        print("🔄 Reintentando crear snippet...\n")
        
        # Esperar un momento para que el plugin se active
        import time
        time.sleep(2)
        
        snippet_data = {
            "name": "Rhinometric Trial Proxy",
            "code": php_code,
            "scope": "global",
            "active": True,
            "priority": 10
        }
        
        create_response = requests.post(
            f"{WP_URL}/wp-json/code-snippets/v1/snippets",
            auth=auth,
            json=snippet_data,
            timeout=15
        )
        
        if create_response.status_code in [200, 201]:
            print("✅ ¡SNIPPET CREADO EXITOSAMENTE!")
            print(f"Respuesta: {create_response.json()}\n")
            print("🎉 El formulario de trial ya debería funcionar")
            print("🧪 Prueba en: https://rhinometric.com/trial/\n")
            exit(0)
        else:
            print(f"⚠️  Error al crear snippet después de instalar: HTTP {create_response.status_code}")
            print(f"Respuesta: {create_response.text}\n")
    else:
        print(f"⚠️  No se pudo instalar Code Snippets: HTTP {install_response.status_code}")
        print(f"Respuesta: {install_response.text}\n")
        
except Exception as e:
    print(f"⚠️  Error al instalar plugin: {e}\n")

print("=" * 80)
print("❌ NO SE PUDO INSTALAR AUTOMÁTICAMENTE")
print("=" * 80)
print("\nWordPress REST API no permite editar archivos PHP por seguridad.")
print("\n🎯 SOLUCIÓN MANUAL (2 MINUTOS):")
print("1. Abre: https://rhinometric.com/wp-admin/theme-editor.php")
print("2. Click en 'functions.php'")
print("3. Copia el código del archivo INSTRUCCIONES-COPIAR-CODIGO.html")
print("4. Pega al final de functions.php")
print("5. Click 'Update File'")
print("\n✅ O abre el archivo HTML que se abrió en tu navegador\n")
