<?php
/**
 * rhinometric-leads.php — Contact form backend
 *
 * Transactional email via SendGrid HTTP API.
 * Persistent lead storage via WP CPT (contact_lead).
 * Full logging on every request + email attempt.
 *
 * Required wp_options (Settings → General):
 *   rhinometric_sendgrid_api_key   — SendGrid API key
 *   rhinometric_sender_email       — From address (default: noreply@rhinometric.com)
 */

if (!defined('ABSPATH')) {
    exit;
}

/* ==========================================================================
   1. Settings
   ========================================================================== */
function rhinometric_leads_register_settings() {
    $fields = [
        'rhinometric_sendgrid_api_key' => 'SendGrid API Key',
        'rhinometric_sender_email'     => 'Sender email (From)',
    ];
    foreach ($fields as $key => $label) {
        register_setting('general', $key, [
            'type'              => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default'           => '',
        ]);
        add_settings_field($key, $label, function () use ($key) {
            $val = esc_attr(get_option($key, ''));
            $type = strpos($key, 'api_key') !== false ? 'password' : 'text';
            echo '<input type="' . esc_attr($type) . '" id="' . esc_attr($key)
                . '" name="' . esc_attr($key) . '" value="' . $val
                . '" class="regular-text" autocomplete="off" />';
        }, 'general');
    }
}
add_action('admin_init', 'rhinometric_leads_register_settings');

/* ==========================================================================
   2. CPT: contact_lead
   ========================================================================== */
function rhinometric_register_cpt_contact_leads() {
    register_post_type('contact_lead', [
        'labels'   => [
            'name'          => 'Contact Leads',
            'singular_name' => 'Contact Lead',
        ],
        'public'   => false,
        'show_ui'  => true,
        'menu_icon'=> 'dashicons-email-alt',
        'supports' => ['title'],
    ]);
}
add_action('init', 'rhinometric_register_cpt_contact_leads');

/* ==========================================================================
   3. Request ID
   ========================================================================== */
function rhinometric_generate_request_id() {
    return 'REQ-' . strtoupper(bin2hex(random_bytes(6)));
}

/* ==========================================================================
   4. Logging helper
   ========================================================================== */
function rhinometric_log($request_id, $message, $context = []) {
    $entry = sprintf(
        '[Rhinometric Leads] [%s] %s %s',
        $request_id,
        $message,
        $context ? '| ' . wp_json_encode($context, JSON_UNESCAPED_SLASHES) : ''
    );
    error_log($entry);
}

/* ==========================================================================
   5. SendGrid HTTP API — send one email
   ========================================================================== */
function rhinometric_sendgrid_send($to, $subject, $body_text, $reply_to = '', $request_id = '') {
    $api_key = get_option('rhinometric_sendgrid_api_key', '');
    $from    = get_option('rhinometric_sender_email', '') ?: 'noreply@rhinometric.com';

    if (!$api_key) {
        rhinometric_log($request_id, 'SENDGRID_ERROR: No API key configured.');
        return ['ok' => false, 'error' => 'Email provider not configured. Contact sales@rhinometric.com'];
    }

    $payload = [
        'personalizations' => [[
            'to' => [['email' => $to]],
        ]],
        'from'    => ['email' => $from, 'name' => 'Rhinometric'],
        'subject' => $subject,
        'content' => [['type' => 'text/plain', 'value' => $body_text]],
    ];

    if ($reply_to && is_email($reply_to)) {
        $payload['reply_to'] = ['email' => $reply_to];
    }

    $response = wp_remote_post('https://api.sendgrid.com/v3/mail/send', [
        'timeout' => 15,
        'headers' => [
            'Authorization' => 'Bearer ' . $api_key,
            'Content-Type'  => 'application/json',
        ],
        'body' => wp_json_encode($payload),
    ]);

    if (is_wp_error($response)) {
        $err = $response->get_error_message();
        rhinometric_log($request_id, 'SENDGRID_ERROR: WP HTTP error', ['error' => $err]);
        return ['ok' => false, 'error' => $err];
    }

    $code = wp_remote_retrieve_response_code($response);
    $resp_body = wp_remote_retrieve_body($response);

    // SendGrid returns 202 Accepted for successful sends
    if ($code >= 200 && $code < 300) {
        rhinometric_log($request_id, 'SENDGRID_OK', ['to' => $to, 'status' => $code]);
        return ['ok' => true];
    }

    rhinometric_log($request_id, 'SENDGRID_ERROR: Non-2xx response', [
        'status' => $code,
        'body'   => $resp_body,
        'to'     => $to,
    ]);
    return ['ok' => false, 'error' => 'SendGrid HTTP ' . $code . ': ' . $resp_body];
}

/* ==========================================================================
   6. Save lead to WP (CPT)
   ========================================================================== */
function rhinometric_save_lead($data, $request_id) {
    $post_id = wp_insert_post([
        'post_type'   => 'contact_lead',
        'post_title'  => $data['company'] . ' — ' . $data['email'],
        'post_status' => 'private',
    ]);

    if (is_wp_error($post_id)) {
        rhinometric_log($request_id, 'SAVE_ERROR: wp_insert_post failed', [
            'error' => $post_id->get_error_message(),
        ]);
        return false;
    }

    $meta = [
        '_rino_request_id' => $request_id,
        '_rino_email'      => $data['email'],
        '_rino_phone'      => $data['phone'],
        '_rino_company'    => $data['company'],
        '_rino_role'       => $data['role'],
        '_rino_comments'   => $data['comments'],
        '_rino_lang'       => $data['lang'],
        '_rino_ip'         => isset($_SERVER['REMOTE_ADDR'])
            ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : '',
        '_rino_submitted_at'    => current_time('mysql'),
        '_rino_email_internal'  => 'pending',
        '_rino_email_user'      => 'pending',
    ];

    foreach ($meta as $key => $value) {
        update_post_meta($post_id, $key, $value);
    }

    rhinometric_log($request_id, 'LEAD_SAVED', ['post_id' => $post_id]);
    return $post_id;
}

/* ==========================================================================
   7. AJAX handler — form submission
   ========================================================================== */
function rhinometric_handle_contact_submit() {
    $request_id = rhinometric_generate_request_id();
    rhinometric_log($request_id, 'SUBMIT_START');

    // --- Nonce ---
    if (!isset($_POST['_wpnonce']) ||
        !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_wpnonce'])), 'rhinometric_contact_form')) {
        rhinometric_log($request_id, 'NONCE_FAIL');
        wp_send_json_error(['message' => 'Security check failed.'], 403);
    }

    // --- Honeypot ---
    if (!empty($_POST['website'])) {
        rhinometric_log($request_id, 'HONEYPOT_TRIGGERED');
        wp_send_json_error(['message' => 'Submission rejected.'], 403);
    }

    // --- Rate limit ---
    if (!rinometry_check_rate_limit('contact_lead', 15)) {
        rhinometric_log($request_id, 'RATE_LIMITED');
        wp_send_json_error(['message' => 'Please wait before submitting again.'], 429);
    }

    // --- Sanitize ---
    $email    = sanitize_email(wp_unslash($_POST['email'] ?? ''));
    $phone    = sanitize_text_field(wp_unslash($_POST['phone'] ?? ''));
    $company  = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
    $role     = sanitize_text_field(wp_unslash($_POST['role'] ?? ''));
    $comments = sanitize_textarea_field(wp_unslash($_POST['comments'] ?? ''));
    $lang     = sanitize_text_field(wp_unslash($_POST['lang'] ?? 'en'));

    // --- Validate required ---
    $errors = [];
    if (!$email || !is_email($email)) {
        $errors['email'] = ($lang === 'es')
            ? 'Introduce un email válido.'
            : 'Enter a valid email address.';
    }
    if (!$phone) {
        $errors['phone'] = ($lang === 'es')
            ? 'El teléfono es obligatorio.'
            : 'Phone number is required.';
    }
    if (!$company) {
        $errors['company'] = ($lang === 'es')
            ? 'La empresa es obligatoria.'
            : 'Company is required.';
    }
    if (!$role) {
        $errors['role'] = ($lang === 'es')
            ? 'El cargo es obligatorio.'
            : 'Role is required.';
    }

    if (!empty($errors)) {
        rhinometric_log($request_id, 'VALIDATION_FAIL', $errors);
        wp_send_json_error(['fields' => $errors], 422);
    }

    // --- 1. Save lead FIRST (before any email attempt) ---
    $lead_data = [
        'email'    => $email,
        'phone'    => $phone,
        'company'  => $company,
        'role'     => $role,
        'comments' => $comments,
        'lang'     => $lang,
    ];
    $post_id = rhinometric_save_lead($lead_data, $request_id);

    if (!$post_id) {
        rhinometric_log($request_id, 'SUBMIT_FAIL: Could not save lead');
        wp_send_json_error([
            'message' => ($lang === 'es')
                ? 'No pudimos procesar la solicitud. Inténtalo de nuevo o escríbenos a sales@rhinometric.com'
                : 'Could not process the request. Try again or email sales@rhinometric.com',
        ], 500);
    }

    // --- 2. Send internal email to sales@rhinometric.com ---
    $timestamp    = current_time('Y-m-d H:i:s T');
    $internal_subj = "[Rhinometric] New contact request — {$company} — {$role}";
    $internal_body = implode("\n", [
        "New contact request received.",
        "",
        "Email:      {$email}",
        "Phone:      {$phone}",
        "Company:    {$company}",
        "Role:       {$role}",
        "Comments:   " . ($comments ?: '—'),
        "",
        "Timestamp:  {$timestamp}",
        "Request ID: {$request_id}",
    ]);

    $sales_result = rhinometric_sendgrid_send(
        'sales@rhinometric.com',
        $internal_subj,
        $internal_body,
        $email,   // reply-to = user's email
        $request_id
    );

    update_post_meta($post_id, '_rino_email_internal', $sales_result['ok'] ? 'sent' : 'failed');
    if (!$sales_result['ok']) {
        update_post_meta($post_id, '_rino_email_internal_error', $sales_result['error'] ?? 'unknown');
    }

    // --- 3. Send acknowledgment email to user ---
    $user_subj = 'We received your request — Rhinometric';
    if ($lang === 'es') {
        $user_subj = 'Hemos recibido tu solicitud — Rhinometric';
    }

    $user_body_en = implode("\n", [
        "Thank you for contacting Rhinometric.",
        "",
        "We have received your request and will contact you within 1–2 business days.",
        "If you need to add information, reply to this email.",
        "",
        "— Rhinometric Team",
    ]);
    $user_body_es = implode("\n", [
        "Gracias por contactar con Rhinometric.",
        "",
        "Hemos recibido tu solicitud y te contactaremos en 1–2 días laborables.",
        "Si necesitas añadir información, responde a este correo.",
        "",
        "— Equipo Rhinometric",
    ]);

    $user_result = rhinometric_sendgrid_send(
        $email,
        $user_subj,
        ($lang === 'es') ? $user_body_es : $user_body_en,
        'sales@rhinometric.com',   // reply-to = sales
        $request_id
    );

    update_post_meta($post_id, '_rino_email_user', $user_result['ok'] ? 'sent' : 'failed');
    if (!$user_result['ok']) {
        update_post_meta($post_id, '_rino_email_user_error', $user_result['error'] ?? 'unknown');
    }

    // --- 4. Check if BOTH emails failed ---
    if (!$sales_result['ok'] && !$user_result['ok']) {
        rhinometric_log($request_id, 'SUBMIT_EMAIL_FAIL: Both emails failed', [
            'internal_error' => $sales_result['error'] ?? '',
            'user_error'     => $user_result['error'] ?? '',
        ]);
        wp_send_json_error([
            'message' => ($lang === 'es')
                ? 'No pudimos enviar la solicitud. Inténtalo de nuevo o escríbenos a sales@rhinometric.com'
                : 'Could not send the request. Try again or email sales@rhinometric.com',
            'request_id' => $request_id,
        ], 500);
    }

    // --- 5. Success (lead saved, at least one email sent) ---
    rhinometric_log($request_id, 'SUBMIT_OK', [
        'post_id'  => $post_id,
        'internal' => $sales_result['ok'] ? 'sent' : 'failed',
        'user'     => $user_result['ok'] ? 'sent' : 'failed',
    ]);

    wp_send_json_success([
        'message'    => 'ok',
        'request_id' => $request_id,
    ]);
}
add_action('wp_ajax_rhinometric_contact_submit', 'rhinometric_handle_contact_submit');
add_action('wp_ajax_nopriv_rhinometric_contact_submit', 'rhinometric_handle_contact_submit');

/* ==========================================================================
   8. Admin page — Recent leads viewer
   ========================================================================== */
function rhinometric_register_leads_admin_page() {
    add_management_page(
        'Recent Contact Leads',
        'Contact Leads',
        'manage_options',
        'rhinometric-recent-leads',
        'rhinometric_render_recent_leads_page'
    );
}
add_action('admin_menu', 'rhinometric_register_leads_admin_page');

function rhinometric_render_recent_leads_page() {
    if (!current_user_can('manage_options')) {
        return;
    }

    $leads = get_posts([
        'post_type'   => 'contact_lead',
        'post_status' => 'private',
        'numberposts' => 50,
        'orderby'     => 'date',
        'order'       => 'DESC',
    ]);

    echo '<div class="wrap">';
    echo '<h1>Recent Contact Leads (last 50)</h1>';

    if (empty($leads)) {
        echo '<p>No leads yet.</p></div>';
        return;
    }

    echo '<table class="widefat striped"><thead><tr>'
        . '<th>Request ID</th><th>Email</th><th>Phone</th>'
        . '<th>Company</th><th>Role</th><th>Comments</th>'
        . '<th>Internal Email</th><th>User Email</th>'
        . '<th>Date</th>'
        . '</tr></thead><tbody>';

    foreach ($leads as $lead) {
        $m = function ($key) use ($lead) {
            return esc_html(get_post_meta($lead->ID, $key, true));
        };
        $int_status = $m('_rino_email_internal');
        $usr_status = $m('_rino_email_user');
        $int_class  = $int_status === 'sent' ? 'color:green' : 'color:red;font-weight:bold';
        $usr_class  = $usr_status === 'sent' ? 'color:green' : 'color:red;font-weight:bold';

        echo '<tr>'
            . '<td><code>' . $m('_rino_request_id') . '</code></td>'
            . '<td>' . $m('_rino_email') . '</td>'
            . '<td>' . $m('_rino_phone') . '</td>'
            . '<td>' . $m('_rino_company') . '</td>'
            . '<td>' . $m('_rino_role') . '</td>'
            . '<td>' . $m('_rino_comments') . '</td>'
            . '<td style="' . $int_class . '">' . $int_status . '</td>'
            . '<td style="' . $usr_class . '">' . $usr_status . '</td>'
            . '<td>' . esc_html($lead->post_date) . '</td>'
            . '</tr>';
    }

    echo '</tbody></table></div>';
}

/* ==========================================================================
   9. Contact leads CSV export
   ========================================================================== */
function rhinometric_export_contact_leads_handler() {
    if (!current_user_can('manage_options')) {
        wp_die('Unauthorized.');
    }
    check_admin_referer('rhinometric_export_contact_leads');

    $leads = get_posts([
        'post_type'   => 'contact_lead',
        'post_status' => 'private',
        'numberposts' => -1,
        'orderby'     => 'date',
        'order'       => 'DESC',
    ]);

    $format = sanitize_text_field(wp_unslash($_GET['format'] ?? 'csv'));

    $rows = [];
    foreach ($leads as $lead) {
        $rows[] = [
            'request_id' => get_post_meta($lead->ID, '_rino_request_id', true),
            'email'      => get_post_meta($lead->ID, '_rino_email', true),
            'phone'      => get_post_meta($lead->ID, '_rino_phone', true),
            'company'    => get_post_meta($lead->ID, '_rino_company', true),
            'role'       => get_post_meta($lead->ID, '_rino_role', true),
            'comments'   => get_post_meta($lead->ID, '_rino_comments', true),
            'email_internal' => get_post_meta($lead->ID, '_rino_email_internal', true),
            'email_user'     => get_post_meta($lead->ID, '_rino_email_user', true),
            'date'       => $lead->post_date,
        ];
    }

    if ($format === 'json') {
        wp_send_json($rows);
    }

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename=contact-leads-' . gmdate('Y-m-d') . '.csv');
    $out = fopen('php://output', 'w');
    fputcsv($out, ['request_id','email','phone','company','role','comments','email_internal','email_user','date']);
    foreach ($rows as $row) {
        fputcsv($out, $row);
    }
    fclose($out);
    exit;
}
add_action('admin_post_rhinometric_export_contact_leads', 'rhinometric_export_contact_leads_handler');
