<?php
/**
 * Rhinometric Trial License Request Proxy
 * 
 * Este archivo se debe subir al servidor WordPress
 * Ubicación: /var/www/html/wp-content/themes/[tu-tema]/rhinometric-trial-proxy.php
 * 
 * URL de acceso: https://rhinometric.com/wp-content/themes/[tu-tema]/rhinometric-trial-proxy.php
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://rhinometric.com');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Solo permitir POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Leer datos del request
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Validar datos requeridos
if (!isset($data['customer_name']) || !isset($data['client_email']) || !isset($data['client_company'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

// Validar email
if (!filter_var($data['client_email'], FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email format']);
    exit;
}

// Preparar request al License Server
$license_server_url = 'http://54.197.192.198:5000/api/admin/licenses';

$payload = json_encode([
    'customer_name' => $data['customer_name'],
    'client_email' => $data['client_email'],
    'client_company' => $data['client_company'],
    'license_type' => 'trial'
]);

// Hacer request al License Server usando cURL
$ch = curl_init($license_server_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Content-Length: ' . strlen($payload)
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

// Manejar errores de conexión
if ($curl_error) {
    error_log("Rhinometric Trial Proxy Error: " . $curl_error);
    http_response_code(500);
    echo json_encode([
        'error' => 'Could not connect to license server',
        'message' => 'Please try again later or contact support@rhinometric.com'
    ]);
    exit;
}

// Retornar respuesta del License Server
http_response_code($http_code);
echo $response;

// Log para debugging (opcional)
error_log("Rhinometric Trial Request: " . $data['client_email'] . " - HTTP " . $http_code);
?>
