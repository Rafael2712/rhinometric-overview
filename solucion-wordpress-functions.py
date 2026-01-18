#!/usr/bin/env python3
"""
SOLUCIÓN DEFINITIVA: Crear el proxy usando WordPress Code Snippets o Functions
"""
import requests
import json

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"

# Código PHP del proxy como función que se puede ejecutar via AJAX
proxy_code = '''
// Rhinometric Trial Proxy - Añadir al functions.php del tema

add_action('wp_ajax_nopriv_rhinometric_trial', 'rhinometric_trial_proxy');
add_action('wp_ajax_rhinometric_trial', 'rhinometric_trial_proxy');

function rhinometric_trial_proxy() {
    header('Content-Type: application/json');
    
    // Leer datos del request
    $data = json_decode(file_get_contents('php://input'), true);
    
    // Validar datos requeridos
    if (!isset($data['customer_name']) || !isset($data['client_email']) || !isset($data['client_company'])) {
        wp_send_json_error(['message' => 'Missing required fields'], 400);
        return;
    }
    
    // Validar email
    if (!is_email($data['client_email'])) {
        wp_send_json_error(['message' => 'Invalid email format'], 400);
        return;
    }
    
    // Hacer request al License Server
    $license_server_url = 'http://54.197.192.198:5000/api/admin/licenses';
    
    $payload = json_encode([
        'customer_name' => sanitize_text_field($data['customer_name']),
        'client_email' => sanitize_email($data['client_email']),
        'client_company' => sanitize_text_field($data['client_company']),
        'license_type' => 'trial'
    ]);
    
    $response = wp_remote_post($license_server_url, array(
        'headers' => array('Content-Type' => 'application/json'),
        'body' => $payload,
        'timeout' => 30
    ));
    
    if (is_wp_error($response)) {
        wp_send_json_error([
            'message' => 'Could not connect to license server',
            'error' => $response->get_error_message()
        ], 500);
        return;
    }
    
    $body = wp_remote_retrieve_body($response);
    $code = wp_remote_retrieve_response_code($response);
    
    status_header($code);
    echo $body;
    wp_die();
}
'''

print("=" * 80)
print("SOLUCIÓN RÁPIDA: Copiar y pegar código en WordPress")
print("=" * 80)
print("\n1. Ve a: https://rhinometric.com/wp-admin/theme-editor.php")
print("2. Selecciona: functions.php del tema activo")
print("3. Pega este código AL FINAL del archivo:\n")
print("-" * 80)
print(proxy_code)
print("-" * 80)
print("\n4. Guarda los cambios (Update File)")
print("\n5. Actualiza el formulario para usar este endpoint:\n")

# Generar el JavaScript actualizado
js_code = '''
// Reemplazar el fetch en 02-trial-linux-page.html por:
const response = await fetch('/wp-admin/admin-ajax.php', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
        action: 'rhinometric_trial',
        ...{
            customer_name: name,
            client_email: email,
            client_company: company,
            license_type: 'trial'
        }
    })
});
'''

print("JavaScript actualizado para el formulario:")
print("-" * 80)
print(js_code)
print("-" * 80)

print("\n✅ Esta solución NO requiere SSH ni FTP")
print("✅ Usa la funcionalidad nativa de WordPress (AJAX)")
print("✅ Es más segura y mantenible\n")
