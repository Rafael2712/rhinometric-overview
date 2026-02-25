<?php
/**
 * rhinometric-leads.php — Contact form backend
 *
 * Email via Zoho SMTP (smtp.zoho.eu:587, STARTTLS).
 * From: rafael.canelon@rhinometric.com (real account, no alias yet).
 * No SendGrid. No sendmail. No mail().
 * Persistent lead storage via WP CPT (contact_lead).
 * GDPR consent evidence logged per submission.
 * Full logging on every request + email attempt.
 *
 * Required wp_option (Settings → General):
 *   rhinometric_zoho_smtp_password  — App Password for rafael.canelon@rhinometric.com
 */

if (!defined('ABSPATH')) {
    exit;
}

/* ==========================================================================
   1. Zoho SMTP setting (password only — host/port/user are fixed)
   ========================================================================== */
function rhinometric_leads_register_settings() {
    register_setting('general', 'rhinometric_zoho_smtp_password', [
        'type'              => 'string',
        'sanitize_callback' => 'sanitize_text_field',
        'default'           => '',
    ]);
    add_settings_field(
        'rhinometric_zoho_smtp_password',
        'Zoho SMTP Password (rafael.canelon@rhinometric.com)',
        function () {
            $val = esc_attr(get_option('rhinometric_zoho_smtp_password', ''));
            echo '<input type="password" id="rhinometric_zoho_smtp_password" '
                . 'name="rhinometric_zoho_smtp_password" value="' . $val
                . '" class="regular-text" autocomplete="off" />'
                . '<p class="description">App Password from Zoho for rafael.canelon@rhinometric.com</p>';
        },
        'general'
    );
}
add_action('admin_init', 'rhinometric_leads_register_settings');

/* ==========================================================================
   2. Force Zoho SMTP on every wp_mail() call
   ========================================================================== */
function rhinometric_configure_zoho_smtp($phpmailer) {
    // If WP Mail SMTP (or similar) plugin is active and already configured SMTP,
    // skip our custom configuration to avoid conflicts.
    if (class_exists('WPMailSMTP\\WP') || defined('WPMS_PLUGIN_VER')) {
        // WP Mail SMTP handles credentials — only force From identity
        $phpmailer->From     = 'rafael.canelon@rhinometric.com';
        $phpmailer->FromName = 'Rhinometric';
        return;
    }

    $password = get_option('rhinometric_zoho_smtp_password', '');

    if (!$password) {
        error_log('[Rhinometric SMTP] No Zoho SMTP password configured. Email will fail.');
        return;
    }

    $phpmailer->isSMTP();
    $phpmailer->Host       = 'smtp.zoho.eu';
    $phpmailer->Port       = 587;
    $phpmailer->SMTPSecure = 'tls';
    $phpmailer->SMTPAuth   = true;
    $phpmailer->Username   = 'rafael.canelon@rhinometric.com';
    $phpmailer->Password   = $password;

    $phpmailer->From     = 'rafael.canelon@rhinometric.com';
    $phpmailer->FromName = 'Rhinometric';

    $phpmailer->SMTPDebug   = 0;
    $phpmailer->Debugoutput = 'error_log';
}
add_action('phpmailer_init', 'rhinometric_configure_zoho_smtp');

/* ==========================================================================
   3. Force From header (belt + suspenders with phpmailer_init above)
   ========================================================================== */
function rhinometric_force_from_email($email) {
    return 'rafael.canelon@rhinometric.com';
}
function rhinometric_force_from_name($name) {
    return 'Rhinometric';
}
add_filter('wp_mail_from', 'rhinometric_force_from_email');
add_filter('wp_mail_from_name', 'rhinometric_force_from_name');

/* ==========================================================================
   4. CPT: contact_lead
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
   5. Request ID
   ========================================================================== */
function rhinometric_generate_request_id() {
    return 'REQ-' . strtoupper(bin2hex(random_bytes(8)));
}

/* ==========================================================================
   6. Logging helper
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
   7. Send email via wp_mail (routed through Zoho SMTP by hook above)
   ========================================================================== */
function rhinometric_send_mail($to, $subject, $body, $reply_to = '', $request_id = '') {
    $headers = ['Content-Type: text/plain; charset=UTF-8'];

    if ($reply_to && is_email($reply_to)) {
        $headers[] = 'Reply-To: ' . $reply_to;
    }

    rhinometric_log($request_id, 'MAIL_ATTEMPT', ['to' => $to, 'subject' => $subject]);

    $sent = wp_mail($to, $subject, $body, $headers);

    if ($sent) {
        rhinometric_log($request_id, 'MAIL_OK', ['to' => $to]);
    } else {
        // Capture PHPMailer error
        global $phpmailer;
        $error_msg = '';
        if (isset($phpmailer) && is_object($phpmailer)) {
            $error_msg = $phpmailer->ErrorInfo;
        }
        rhinometric_log($request_id, 'MAIL_FAIL', [
            'to'    => $to,
            'error' => $error_msg ?: 'wp_mail returned false',
        ]);
    }

    return $sent;
}

/* ==========================================================================
   8. Save lead to WP (CPT) — ALWAYS runs before email
   ========================================================================== */
function rhinometric_save_lead($data, $request_id) {
    $title_parts = array_filter([$data['full_name'] ?? '', $data['company'] ?? '', $data['email']]);
    $post_id = wp_insert_post([
        'post_type'   => 'contact_lead',
        'post_title'  => implode(' — ', $title_parts) ?: $data['email'],
        'post_status' => 'private',
    ]);

    if (is_wp_error($post_id)) {
        rhinometric_log($request_id, 'SAVE_ERROR: wp_insert_post failed', [
            'error' => $post_id->get_error_message(),
        ]);
        return false;
    }

    $meta = [
        '_rino_request_id'      => $request_id,
        '_rino_full_name'       => $data['full_name'] ?? '',
        '_rino_email'           => $data['email'],
        '_rino_company'         => $data['company'] ?? '',
        '_rino_intention'       => $data['intention'] ?? '',
        '_rino_phone'           => $data['phone'],
        '_rino_comments'        => $data['comments'],
        '_rino_lang'            => $data['lang'],
        '_rino_ip'              => $data['ip'],
        '_rino_user_agent'      => $data['user_agent'],
        '_rino_page_url'        => $data['page_url'],
        '_rino_consent'         => $data['consent'] ? 'true' : 'false',
        '_rino_marketing'       => ($data['marketing'] ?? false) ? 'true' : 'false',
        '_rino_consent_ts'      => $data['consent_ts'],
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
   9. AJAX handler — form submission
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
    $full_name  = sanitize_text_field(wp_unslash($_POST['full_name'] ?? ''));
    $email      = sanitize_email(wp_unslash($_POST['email'] ?? ''));
    $company    = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
    $intention  = sanitize_text_field(wp_unslash($_POST['intention'] ?? ''));
    $phone      = sanitize_text_field(wp_unslash($_POST['phone'] ?? ''));
    $comments   = sanitize_textarea_field(wp_unslash($_POST['comments'] ?? ''));
    $lang       = sanitize_text_field(wp_unslash($_POST['lang'] ?? 'en'));
    $consent    = !empty($_POST['gdpr_consent']);
    $marketing  = !empty($_POST['marketing_consent']);
    $page_url   = esc_url_raw(wp_unslash($_POST['page_url'] ?? ''));

    // Evidence fields
    $ip         = isset($_SERVER['REMOTE_ADDR'])
        ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : 'unknown';
    $user_agent = isset($_SERVER['HTTP_USER_AGENT'])
        ? sanitize_text_field(wp_unslash($_SERVER['HTTP_USER_AGENT'])) : 'unknown';
    $consent_ts = gmdate('Y-m-d\TH:i:s\Z'); // UTC ISO-8601

    // --- Validate required ---
    $errors = [];
    if (!$full_name) {
        $errors['full_name'] = ($lang === 'es')
            ? 'El nombre es obligatorio.'
            : 'Full name is required.';
    }
    if (!$email || !is_email($email)) {
        $errors['email'] = ($lang === 'es')
            ? 'Introduce un email válido.'
            : 'Enter a valid email address.';
    }
    if (!$company) {
        $errors['company'] = ($lang === 'es')
            ? 'La empresa es obligatoria.'
            : 'Company is required.';
    }
    $valid_intentions = ['demo', 'evaluate', 'info'];
    if (!$intention || !in_array($intention, $valid_intentions, true)) {
        $errors['intention'] = ($lang === 'es')
            ? 'Selecciona una opción.'
            : 'Please select an option.';
    }
    if (mb_strlen($comments) > 255) {
        $errors['comments'] = ($lang === 'es')
            ? 'Máximo 255 caracteres.'
            : 'Maximum 255 characters.';
    }
    if (!$consent) {
        $errors['gdpr_consent'] = ($lang === 'es')
            ? 'Debes aceptar los Términos y la Política de Privacidad.'
            : 'You must accept the Terms and Privacy Policy.';
    }

    if (!empty($errors)) {
        rhinometric_log($request_id, 'VALIDATION_FAIL', $errors);
        wp_send_json_error(['fields' => $errors], 422);
    }

    // --- 1. Save lead FIRST (before any email attempt) ---
    $lead_data = [
        'full_name'  => $full_name,
        'email'      => $email,
        'company'    => $company,
        'intention'  => $intention,
        'phone'      => $phone,
        'comments'   => $comments,
        'lang'       => $lang,
        'ip'         => $ip,
        'user_agent' => $user_agent,
        'page_url'   => $page_url,
        'consent'    => $consent,
        'marketing'  => $marketing,
        'consent_ts' => $consent_ts,
    ];
    $post_id = rhinometric_save_lead($lead_data, $request_id);

    if (!$post_id) {
        rhinometric_log($request_id, 'SUBMIT_FAIL: Could not save lead');
        wp_send_json_error([
            'message' => ($lang === 'es')
                ? 'No pudimos procesar la solicitud. Inténtalo de nuevo o escríbenos a rafael.canelon@rhinometric.com'
                : 'Could not process the request. Try again or email rafael.canelon@rhinometric.com',
        ], 500);
    }

    // --- 2. EMAIL #1: Internal notification ---
    $internal_recipient = rinometry_get_lead_recipient(); // rafael.canelon@rhinometric.com
    $timestamp     = current_time('Y-m-d H:i:s T');
    $intention_label = ucfirst($intention ?: 'contact');
    $internal_subj = "[Rhinometric] New request — {$intention_label} — {$request_id}";
    $internal_body = implode("\n", [
        "New contact request received.",
        "",
        "Name:       {$full_name}",
        "Email:      {$email}",
        "Company:    {$company}",
        "Intention:  {$intention_label}",
        "Phone:      " . ($phone ?: '—'),
        "Comments:   " . ($comments ?: '—'),
        "",
        "Timestamp:  {$timestamp}",
        "Page:       {$page_url}",
        "IP:         {$ip}",
        "UA:         {$user_agent}",
        "Consent:    TRUE",
        "Marketing:  " . ($marketing ? 'YES' : 'NO'),
        "Consent TS: {$consent_ts}",
        "Request ID: {$request_id}",
    ]);

    $internal_ok = rhinometric_send_mail(
        $internal_recipient,
        $internal_subj,
        $internal_body,
        $email,       // Reply-To = user's email
        $request_id
    );

    update_post_meta($post_id, '_rino_email_internal', $internal_ok ? 'sent' : 'failed');
    if (!$internal_ok) {
        global $phpmailer;
        $err = (isset($phpmailer) && is_object($phpmailer)) ? $phpmailer->ErrorInfo : 'unknown';
        update_post_meta($post_id, '_rino_email_internal_error', $err);
        rhinometric_log($request_id, 'INTERNAL_SEND_FAIL', ['error' => $err]);
    }

    // --- 3. EMAIL #2: Autoreply to user (always attempted, independent of internal) ---
    $privacy_url = home_url('/privacy-cookies/');
    $user_subj   = 'We received your request — Rhinometric';
    $user_body   = implode("\n", [
        "Hi there,",
        "",
        "We've received your request. Our team will contact you within 24–48 hours.",
        "",
        "If you didn't submit this request, you can ignore this email.",
        "",
        "Privacy Policy: {$privacy_url}",
        "",
        "Request ID: {$request_id}",
        "",
        "— Rhinometric",
    ]);

    $user_ok = rhinometric_send_mail(
        $email,
        $user_subj,
        $user_body,
        'rafael.canelon@rhinometric.com',   // Reply-To
        $request_id
    );

    update_post_meta($post_id, '_rino_email_user', $user_ok ? 'sent' : 'failed');
    if (!$user_ok) {
        global $phpmailer;
        $err = (isset($phpmailer) && is_object($phpmailer)) ? $phpmailer->ErrorInfo : 'unknown';
        update_post_meta($post_id, '_rino_email_user_error', $err);
        rhinometric_log($request_id, 'AUTOREPLY_SEND_FAIL', ['error' => $err]);
    }

    // --- 4. Determine response ---
    // Internal fail = 500. Autoreply fail is logged but still returns success to user.
    if (!$internal_ok) {
        rhinometric_log($request_id, 'SUBMIT_PARTIAL_FAIL', [
            'post_id'  => $post_id,
            'internal' => 'failed',
            'user'     => $user_ok ? 'sent' : 'failed',
        ]);
        wp_send_json_error([
            'message' => ($lang === 'es')
                ? 'No pudimos enviar la solicitud. Inténtalo de nuevo o escríbenos a rafael.canelon@rhinometric.com'
                : 'Could not send the request. Try again or email rafael.canelon@rhinometric.com',
            'request_id' => $request_id,
        ], 500);
    }

    // --- 5. Success (internal sent; autoreply may or may not have sent) ---
    rhinometric_log($request_id, 'SUBMIT_OK', [
        'post_id'  => $post_id,
        'internal' => 'sent',
        'user'     => $user_ok ? 'sent' : 'failed',
    ]);

    wp_send_json_success([
        'message'    => 'ok',
        'request_id' => $request_id,
    ]);
}
add_action('wp_ajax_rhinometric_contact_submit', 'rhinometric_handle_contact_submit');
add_action('wp_ajax_nopriv_rhinometric_contact_submit', 'rhinometric_handle_contact_submit');

/* ==========================================================================
   10. Admin page — Recent leads viewer
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
        . '<th>Request ID</th><th>Name</th><th>Email</th>'
        . '<th>Company</th><th>Intention</th>'
        . '<th>Phone</th><th>Comments</th>'
        . '<th>Consent</th><th>Mktg</th><th>IP</th>'
        . '<th>Internal</th><th>User</th>'
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
            . '<td>' . $m('_rino_full_name') . '</td>'
            . '<td>' . $m('_rino_email') . '</td>'
            . '<td>' . $m('_rino_company') . '</td>'
            . '<td>' . $m('_rino_intention') . '</td>'
            . '<td>' . $m('_rino_phone') . '</td>'
            . '<td>' . $m('_rino_comments') . '</td>'
            . '<td>' . $m('_rino_consent') . '</td>'
            . '<td>' . $m('_rino_marketing') . '</td>'
            . '<td>' . $m('_rino_ip') . '</td>'
            . '<td style="' . $int_class . '">' . $int_status . '</td>'
            . '<td style="' . $usr_class . '">' . $usr_status . '</td>'
            . '<td>' . esc_html($lead->post_date) . '</td>'
            . '</tr>';
    }

    echo '</tbody></table></div>';
}

/* ==========================================================================
   11. Contact leads CSV export
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
            'request_id'     => get_post_meta($lead->ID, '_rino_request_id', true),
            'full_name'      => get_post_meta($lead->ID, '_rino_full_name', true),
            'email'          => get_post_meta($lead->ID, '_rino_email', true),
            'company'        => get_post_meta($lead->ID, '_rino_company', true),
            'intention'      => get_post_meta($lead->ID, '_rino_intention', true),
            'phone'          => get_post_meta($lead->ID, '_rino_phone', true),
            'comments'       => get_post_meta($lead->ID, '_rino_comments', true),
            'consent'        => get_post_meta($lead->ID, '_rino_consent', true),
            'marketing'      => get_post_meta($lead->ID, '_rino_marketing', true),
            'ip'             => get_post_meta($lead->ID, '_rino_ip', true),
            'page_url'       => get_post_meta($lead->ID, '_rino_page_url', true),
            'email_internal' => get_post_meta($lead->ID, '_rino_email_internal', true),
            'email_user'     => get_post_meta($lead->ID, '_rino_email_user', true),
            'date'           => $lead->post_date,
        ];
    }

    if ($format === 'json') {
        wp_send_json($rows);
    }

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename=contact-leads-' . gmdate('Y-m-d') . '.csv');
    $out = fopen('php://output', 'w');
    fputcsv($out, ['request_id','full_name','email','company','intention','phone','comments','consent','marketing','ip','page_url','email_internal','email_user','date']);
    foreach ($rows as $row) {
        fputcsv($out, $row);
    }
    fclose($out);
    exit;
}
add_action('admin_post_rhinometric_export_contact_leads', 'rhinometric_export_contact_leads_handler');
