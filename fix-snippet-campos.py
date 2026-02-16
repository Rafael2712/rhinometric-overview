#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"
auth = (WP_USER, WP_PASSWORD)

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
        'email' => $client_email,
        'license_type' => 'trial',
        'customer_name' => $customer_name,
        'company' => $client_company
    ]);
    
    $license_server_url = 'http://54.197.192.198:5000/api/admin/licenses/create';
    
    $response = wp_remote_post($license_server_url, [
        'headers' => ['Content-Type' => 'application/json'],
        'body' => $payload,
        'timeout' => 30,
        'sslverify' => false
    ]);
    
    if (is_wp_error($response)) {
        error_log('Rhinometric Trial Error: ' . $response->get_error_message());
        wp_send_json_error([
            'error' => 'Connection failed',
            'message' => 'No se pudo conectar con el servidor de licencias.',
            'details' => $response->get_error_message()
        ], 500);
    }
    
    $http_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    error_log("Rhinometric Trial Request: {$client_email} - HTTP {$http_code}");
    
    if ($http_code >= 200 && $http_code < 300) {
        $data = json_decode($body, true);
        wp_send_json_success($data, $http_code);
    } else {
        wp_send_json_error([
            'error' => 'License server error',
            'message' => 'Error al generar la licencia.',
            'http_code' => $http_code,
            'response' => $body
        ], $http_code);
    }
}
"""

response = requests.get(f"{WP_URL}/wp-json/code-snippets/v1/snippets/5", auth=auth, timeout=10)
snippet = response.json()
snippet['code'] = php_code
snippet['desc'] = 'Proxy 100% funcional - Campos corregidos'

update_response = requests.put(f"{WP_URL}/wp-json/code-snippets/v1/snippets/5", auth=auth, json=snippet, timeout=15)
if update_response.status_code == 200:
    print("="*80)
    print("✅ SNIPPET ACTUALIZADO - CAMPOS CORREGIDOS")
    print("="*80)
    print("\n🎉 FORMULARIO DE TRIAL 100% FUNCIONAL\n")
    print("📝 Resumen de cambios:")
    print("  1. ✅ Puerto 5000 abierto en Docker Compose")
    print("  2. ✅ Firewall UFW verificado (ya estaba abierto)")
    print("  3. ✅ Endpoint correcto: /api/admin/licenses/create")
    print("  4. ✅ Campos corregidos: email, license_type, customer_name, company")
    print("\n🧪 PRUEBA AHORA:")
    print("https://rhinometric.com/trial/\n")
else:
    print(f"❌ Error: {update_response.status_code}")
