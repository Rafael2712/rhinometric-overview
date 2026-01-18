/**
 * RHINOMETRIC TRIAL PROXY - CÓDIGO PARA FUNCTIONS.PHP
 * 
 * INSTRUCCIONES:
 * 1. Ve a https://rhinometric.com/wp-admin/theme-editor.php
 * 2. Selecciona "functions.php" del tema activo (normalmente el primero de la lista)
 * 3. Scroll hasta el FINAL del archivo
 * 4. Pega TODO el código de abajo
 * 5. Click en "Update File" para guardar
 * 6. Recarga la página https://rhinometric.com/trial/ y prueba el formulario
 */

// Hook AJAX para usuarios no logueados y logueados
add_action('wp_ajax_nopriv_rhinometric_trial', 'rhinometric_trial_proxy');
add_action('wp_ajax_rhinometric_trial', 'rhinometric_trial_proxy');

function rhinometric_trial_proxy() {
    // Configuración de headers
    header('Content-Type: application/json');
    
    // Validar datos requeridos
    if (empty($_POST['customer_name']) || empty($_POST['client_email']) || empty($_POST['client_company'])) {
        wp_send_json_error([
            'error' => 'Missing required fields',
            'message' => 'Por favor completa todos los campos requeridos'
        ], 400);
    }
    
    // Sanitizar y validar datos
    $customer_name = sanitize_text_field($_POST['customer_name']);
    $client_email = sanitize_email($_POST['client_email']);
    $client_company = sanitize_text_field($_POST['client_company']);
    
    // Validar formato de email
    if (!is_email($client_email)) {
        wp_send_json_error([
            'error' => 'Invalid email format',
            'message' => 'El email proporcionado no es válido'
        ], 400);
    }
    
    // Preparar datos para el License Server
    $payload = json_encode([
        'customer_name' => $customer_name,
        'client_email' => $client_email,
        'client_company' => $client_company,
        'license_type' => 'trial'
    ]);
    
    // URL del License Server (servidor interno, no bloqueado por firewall)
    $license_server_url = 'http://54.197.192.198:5000/api/admin/licenses';
    
    // Hacer request usando wp_remote_post (más seguro que cURL)
    $response = wp_remote_post($license_server_url, [
        'headers' => ['Content-Type' => 'application/json'],
        'body' => $payload,
        'timeout' => 30,
        'sslverify' => false
    ]);
    
    // Manejar errores de conexión
    if (is_wp_error($response)) {
        error_log('Rhinometric Trial Error: ' . $response->get_error_message());
        wp_send_json_error([
            'error' => 'Connection failed',
            'message' => 'No se pudo conectar con el servidor de licencias. Por favor intenta más tarde o contacta soporte.',
            'details' => $response->get_error_message()
        ], 500);
    }
    
    // Obtener código de respuesta y body
    $http_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    // Log para debugging
    error_log("Rhinometric Trial Request: {$client_email} - HTTP {$http_code}");
    
    // Si fue exitoso (200-299)
    if ($http_code >= 200 && $http_code < 300) {
        $data = json_decode($body, true);
        wp_send_json_success($data, $http_code);
    } else {
        // Error del License Server
        wp_send_json_error([
            'error' => 'License server error',
            'message' => 'Error al generar la licencia. Por favor contacta con soporte.',
            'http_code' => $http_code,
            'response' => $body
        ], $http_code);
    }
}

/**
 * NOTAS TÉCNICAS:
 * 
 * - Este código usa admin-ajax.php de WordPress (estándar para AJAX)
 * - No requiere crear archivos adicionales en el servidor
 * - Funciona tanto para usuarios logueados como no logueados
 * - Usa wp_remote_post() que es más seguro que cURL directo
 * - Sanitiza todos los inputs para prevenir XSS
 * - Logs automáticos en /var/log/nginx/error.log o /var/log/apache2/error.log
 * 
 * VERIFICACIÓN:
 * Una vez guardado, prueba manualmente con:
 * 
 * curl -X POST 'https://rhinometric.com/wp-admin/admin-ajax.php' \
 *   -d 'action=rhinometric_trial' \
 *   -d 'customer_name=Test User' \
 *   -d 'client_email=test@example.com' \
 *   -d 'client_company=Test Corp'
 * 
 * Deberías recibir un JSON con la licencia creada.
 */
