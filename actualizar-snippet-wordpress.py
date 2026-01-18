#!/usr/bin/env python3
"""
Actualizar el snippet en WordPress para usar localhost:5000 
ya que el formulario se ejecuta DENTRO del servidor de WordPress
"""
import requests

WP_URL = "https://rhinometric.com"
WP_USER = "user"
WP_PASSWORD = "C8tUQIzW9DEc e8mFFVrA0Nx9"

auth = (WP_USER, WP_PASSWORD)

# Nuevo código PHP que usa conexión interna
php_code_updated = """
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
    
    // TEMPORAL: Crear licencia directamente en la base de datos hasta que abramos puerto 5000
    // Por ahora, registrar el request y enviar email de confirmación
    error_log("Rhinometric Trial Request received: {$client_email} from {$client_company}");
    
    // Enviar email al admin avisando que hay un nuevo trial request
    wp_mail(
        'rafael.canelon@rhinometric.com',
        'Nuevo Trial Request - Rhinometric',
        "Nombre: {$customer_name}\\nEmail: {$client_email}\\nEmpresa: {$client_company}\\n\\nPor favor procesa manualmente hasta que se abra el puerto 5000.",
        ['Content-Type: text/plain; charset=UTF-8']
    );
    
    // Devolver respuesta al usuario
    wp_send_json_success([
        'message' => 'Solicitud recibida correctamente',
        'customer_email' => $client_email,
        'note' => 'Recibirás tu licencia por email en las próximas horas'
    ], 200);
}
"""

print("🔄 Actualizando snippet en WordPress...\n")

try:
    # Obtener el snippet ID=5
    response = requests.get(
        f"{WP_URL}/wp-json/code-snippets/v1/snippets/5",
        auth=auth,
        timeout=10
    )
    
    if response.status_code == 200:
        snippet = response.json()
        print(f"✅ Snippet encontrado: {snippet['name']}\n")
        
        # Actualizar con el nuevo código
        snippet['code'] = php_code_updated
        snippet['desc'] = 'Proxy temporal que notifica por email hasta que se abra puerto 5000'
        
        update_response = requests.put(
            f"{WP_URL}/wp-json/code-snippets/v1/snippets/5",
            auth=auth,
            json=snippet,
            timeout=15
        )
        
        if update_response.status_code == 200:
            print("✅ Snippet actualizado correctamente!")
            print("\n⚠️  NOTA: Por ahora el formulario enviará un email a rafael.canelon@rhinometric.com")
            print("    para procesar manualmente hasta que se solucione el puerto 5000\n")
        else:
            print(f"❌ Error al actualizar: HTTP {update_response.status_code}")
            print(update_response.text)
    else:
        print(f"❌ No se pudo obtener snippet: HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎯 PRÓXIMO PASO CRÍTICO:")
print("=" * 80)
print("Necesitas abrir el puerto 5000 INTERNAMENTE en el License Server")
print("\nConéctate al servidor:")
print("ssh ubuntu@54.197.192.198")
print("\nVerifica firewall interno:")
print("sudo ufw status")
print("\nSi está bloqueado, permite el puerto:")
print("sudo ufw allow 5000/tcp")
print("sudo ufw reload")
print("\nO desactiva temporalmente para probar:")
print("sudo ufw disable")
print("=" * 80)
