<?php
/**
 * rhinometric-leads.php — Lead capture backend
 * Zoho CRM integration, double email validation, lead scoring.
 *
 * Required wp_options (set in WP Admin → Settings → General):
 *   rhinometric_zoho_client_id
 *   rhinometric_zoho_client_secret
 *   rhinometric_zoho_refresh_token
 *   rhinometric_recaptcha_site_key
 *   rhinometric_recaptcha_secret_key
 */

if (!defined('ABSPATH')) {
    exit;
}

/* ==========================================================================
   1. Settings registration
   ========================================================================== */
function rhinometric_leads_register_settings() {
    $fields = [
        'rhinometric_zoho_client_id'      => 'Zoho Client ID',
        'rhinometric_zoho_client_secret'   => 'Zoho Client Secret',
        'rhinometric_zoho_refresh_token'   => 'Zoho Refresh Token',
        'rhinometric_recaptcha_site_key'   => 'reCAPTCHA Site Key',
        'rhinometric_recaptcha_secret_key' => 'reCAPTCHA Secret Key',
    ];
    foreach ($fields as $key => $label) {
        register_setting('general', $key, [
            'type'              => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default'           => '',
        ]);
        add_settings_field($key, $label, function () use ($key) {
            $val = esc_attr(get_option($key, ''));
            echo '<input type="text" id="' . esc_attr($key) . '" name="' . esc_attr($key) . '" value="' . $val . '" class="regular-text" autocomplete="off" />';
        }, 'general');
    }
}
add_action('admin_init', 'rhinometric_leads_register_settings');

/* ==========================================================================
   2. Custom Post Type for lead tokens
   ========================================================================== */
function rhinometric_register_cpt_contact_leads() {
    register_post_type('contact_lead', [
        'labels'   => [
            'name'          => __('Contact Leads', 'rinometry'),
            'singular_name' => __('Contact Lead', 'rinometry'),
        ],
        'public'   => false,
        'show_ui'  => true,
        'menu_icon'=> 'dashicons-email-alt',
        'supports' => ['title'],
    ]);
}
add_action('init', 'rhinometric_register_cpt_contact_leads');

/* ==========================================================================
   3. MX domain validation
   ========================================================================== */
function rhinometric_validate_mx($email) {
    $domain = substr(strrchr($email, '@'), 1);
    if (!$domain) {
        return false;
    }
    // checkdnsrr returns true if MX records exist
    return checkdnsrr($domain, 'MX');
}

/* ==========================================================================
   4. Public domain detection
   ========================================================================== */
function rhinometric_is_public_domain($email) {
    $public = [
        'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com',
        'icloud.com','mail.com','protonmail.com','zoho.com','yandex.com',
        'gmx.com','live.com','msn.com','me.com','inbox.com',
    ];
    $domain = strtolower(substr(strrchr($email, '@'), 1));
    return in_array($domain, $public, true);
}

/* ==========================================================================
   5. reCAPTCHA verification
   ========================================================================== */
function rhinometric_verify_recaptcha($token) {
    $secret = get_option('rhinometric_recaptcha_secret_key', '');
    if (!$secret) {
        // If no reCAPTCHA configured, pass (allows deployment without keys)
        return true;
    }
    $response = wp_remote_post('https://www.google.com/recaptcha/api/siteverify', [
        'body' => [
            'secret'   => $secret,
            'response' => $token,
            'remoteip' => isset($_SERVER['REMOTE_ADDR']) ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : '',
        ],
    ]);
    if (is_wp_error($response)) {
        return false;
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return !empty($body['success']) && ($body['score'] ?? 0) >= 0.5;
}

/* ==========================================================================
   6. Zoho CRM — OAuth token
   ========================================================================== */
function rhinometric_zoho_get_access_token() {
    $client_id     = get_option('rhinometric_zoho_client_id', '');
    $client_secret = get_option('rhinometric_zoho_client_secret', '');
    $refresh_token = get_option('rhinometric_zoho_refresh_token', '');

    if (!$client_id || !$client_secret || !$refresh_token) {
        return false;
    }

    // Cache access token for 50 minutes (Zoho tokens last 60 min)
    $cached = get_transient('rhinometric_zoho_access_token');
    if ($cached) {
        return $cached;
    }

    $response = wp_remote_post('https://accounts.zoho.eu/oauth/v2/token', [
        'body' => [
            'grant_type'    => 'refresh_token',
            'client_id'     => $client_id,
            'client_secret' => $client_secret,
            'refresh_token' => $refresh_token,
        ],
    ]);

    if (is_wp_error($response)) {
        error_log('[Rhinometric Leads] Zoho token error: ' . $response->get_error_message());
        return false;
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);
    if (empty($body['access_token'])) {
        error_log('[Rhinometric Leads] Zoho token response: ' . wp_json_encode($body));
        return false;
    }

    set_transient('rhinometric_zoho_access_token', $body['access_token'], 50 * MINUTE_IN_SECONDS);
    return $body['access_token'];
}

/* ==========================================================================
   7. Zoho CRM — Create Lead
   ========================================================================== */
function rhinometric_zoho_create_lead($data) {
    $token = rhinometric_zoho_get_access_token();
    if (!$token) {
        error_log('[Rhinometric Leads] Zoho: no access token, skipping CRM push.');
        return false;
    }

    $payload = [
        'data' => [[
            'Email'              => $data['email'],
            'Company'            => $data['company'],
            'Designation'        => $data['role'] ?? '',
            'Description'        => sprintf(
                "Infra: %s | Stack: %s | Challenge: %s | On-prem: %s",
                $data['infra'] ?? '',
                $data['stack'] ?? '',
                $data['challenge'] ?? '',
                $data['onprem'] ?? ''
            ),
            'Lead_Status'        => 'Pendiente Confirmación',
            'Lead_Source'        => 'Web – Evaluación Técnica',
            'Email_Validated'    => false,
        ]],
    ];

    $response = wp_remote_post('https://www.zohoapis.eu/crm/v5/Leads', [
        'headers' => [
            'Authorization' => 'Zoho-oauthtoken ' . $token,
            'Content-Type'  => 'application/json',
        ],
        'body' => wp_json_encode($payload),
    ]);

    if (is_wp_error($response)) {
        error_log('[Rhinometric Leads] Zoho create lead error: ' . $response->get_error_message());
        return false;
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);
    if (!empty($body['data'][0]['details']['id'])) {
        return $body['data'][0]['details']['id'];
    }

    error_log('[Rhinometric Leads] Zoho create lead response: ' . wp_json_encode($body));
    return false;
}

/* ==========================================================================
   8. Zoho CRM — Update Lead
   ========================================================================== */
function rhinometric_zoho_update_lead($zoho_id, $fields) {
    $token = rhinometric_zoho_get_access_token();
    if (!$token) {
        return false;
    }

    $payload = [
        'data' => [array_merge(['id' => $zoho_id], $fields)],
    ];

    $response = wp_remote_request('https://www.zohoapis.eu/crm/v5/Leads', [
        'method'  => 'PUT',
        'headers' => [
            'Authorization' => 'Zoho-oauthtoken ' . $token,
            'Content-Type'  => 'application/json',
        ],
        'body' => wp_json_encode($payload),
    ]);

    if (is_wp_error($response)) {
        error_log('[Rhinometric Leads] Zoho update error: ' . $response->get_error_message());
        return false;
    }

    return true;
}

/* ==========================================================================
   9. Lead scoring
   ========================================================================== */
function rhinometric_calculate_lead_score($data) {
    $score = 0;

    // Domain
    $score += rhinometric_is_public_domain($data['email']) ? 5 : 20;

    // Role
    $role_scores = [
        'CTO'                     => 30,
        'VP Engineering'          => 25,
        'Head of Infrastructure'  => 25,
        'DevOps Lead'             => 20,
        'SRE Lead'                => 20,
        'Platform Engineer'       => 15,
        'IT Manager'              => 15,
        'Security Lead'           => 15,
        'Other'                   => 5,
    ];
    $score += $role_scores[$data['role'] ?? ''] ?? 5;

    // Infrastructure
    $infra_scores = [
        'On-Premise'              => 25,
        'Hybrid (On-Prem + Cloud)'=> 20,
        'AWS'                     => 15,
        'Azure'                   => 15,
        'GCP'                     => 15,
        'Other Cloud'             => 10,
    ];
    $score += $infra_scores[$data['infra'] ?? ''] ?? 5;

    // Challenge
    $challenge_scores = [
        'Regulatory compliance'                     => 30,
        'Observability consolidation'               => 20,
        'Cost reduction'                            => 15,
        'Incident response time'                    => 20,
        'Migrating from existing tool'              => 15,
        'Data sovereignty / on-prem requirement'    => 30,
    ];
    $score += $challenge_scores[$data['challenge'] ?? ''] ?? 5;

    // On-prem requirement
    $onprem_scores = [
        'yes'           => 30,
        'evaluating'    => 15,
        'no'            => 5,
    ];
    $score += $onprem_scores[$data['onprem'] ?? ''] ?? 5;

    return $score;
}

function rhinometric_classify_lead($score) {
    if ($score >= 101) {
        return 'Enterprise Estratégico';
    }
    if ($score >= 61) {
        return 'Técnico Calificado';
    }
    return 'Exploratorio';
}

/* ==========================================================================
   10. Token management
   ========================================================================== */
function rhinometric_generate_confirmation_token() {
    return bin2hex(random_bytes(32)); // 64-char hex string
}

function rhinometric_hash_token($token) {
    return hash('sha256', $token);
}

/* ==========================================================================
   11. Send confirmation email
   ========================================================================== */
function rhinometric_send_confirmation_email($email, $token, $lang = 'en') {
    $confirm_url = add_query_arg('token', $token, home_url('/confirm/'));

    $subjects = [
        'en' => 'Rhinometric — Confirm your evaluation request',
        'es' => 'Rhinometric — Confirma tu solicitud de evaluación',
    ];
    $bodies = [
        'en' => sprintf(
            "Thank you for your interest in Rhinometric.\n\n" .
            "Please confirm your request by clicking the link below:\n%s\n\n" .
            "This link expires in 48 hours.\n\n" .
            "If you did not submit this request, you can ignore this email.\n\n" .
            "— Rhinometric Team",
            $confirm_url
        ),
        'es' => sprintf(
            "Gracias por tu interés en Rhinometric.\n\n" .
            "Confirma tu solicitud haciendo clic en el siguiente enlace:\n%s\n\n" .
            "Este enlace expira en 48 horas.\n\n" .
            "Si no enviaste esta solicitud, puedes ignorar este correo.\n\n" .
            "— Equipo Rhinometric",
            $confirm_url
        ),
    ];

    $subject = $subjects[$lang] ?? $subjects['en'];
    $body    = $bodies[$lang] ?? $bodies['en'];

    return wp_mail($email, $subject, $body);
}

/* ==========================================================================
   12. Send sales notification (post-confirmation only)
   ========================================================================== */
function rhinometric_notify_sales($post_id) {
    $meta = function ($key) use ($post_id) {
        return get_post_meta($post_id, $key, true);
    };

    $score    = (int) $meta('_rino_lead_score');
    $category = $meta('_rino_lead_category');
    $email    = $meta('_rino_email');
    $company  = $meta('_rino_company');
    $role     = $meta('_rino_role');
    $infra    = $meta('_rino_infra');
    $stack    = $meta('_rino_stack');
    $challenge= $meta('_rino_challenge');
    $onprem   = $meta('_rino_onprem');

    $recipient = rinometry_get_lead_recipient();
    $subject   = sprintf('[Rhinometric] Nuevo lead confirmado — %s (%s)', $company, $category);
    $body      = sprintf(
        "Lead confirmado y validado:\n\n" .
        "Email: %s\nEmpresa: %s\nCargo: %s\n" .
        "Infraestructura: %s\nStack actual: %s\nReto principal: %s\n" .
        "Requiere on-prem: %s\n\n" .
        "Score: %d\nCategoría: %s\n\n" .
        "Fecha de confirmación: %s\n" .
        "WP Post ID: %d",
        $email, $company, $role,
        $infra, $stack, $challenge,
        $onprem,
        $score, $category,
        current_time('mysql'),
        $post_id
    );

    wp_mail($recipient, $subject, $body);
}

/* ==========================================================================
   13. AJAX: Form submission handler
   ========================================================================== */
function rhinometric_handle_lead_submission() {
    // Verify nonce
    if (!isset($_POST['_wpnonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['_wpnonce'])), 'rhinometric_lead_form')) {
        wp_send_json_error(['message' => 'Security check failed.'], 403);
    }

    // Honeypot
    $honeypot = sanitize_text_field(wp_unslash($_POST['website'] ?? ''));
    if ($honeypot !== '') {
        wp_send_json_error(['message' => 'Submission rejected.'], 403);
    }

    // Rate limit
    if (!rinometry_check_rate_limit('contact_lead', 15)) {
        wp_send_json_error(['message' => 'Please wait before submitting again.'], 429);
    }

    // reCAPTCHA
    $recaptcha_token = sanitize_text_field(wp_unslash($_POST['recaptcha_token'] ?? ''));
    if (!rhinometric_verify_recaptcha($recaptcha_token)) {
        wp_send_json_error(['message' => 'Verification failed. Please try again.'], 403);
    }

    // Sanitize fields
    $email     = sanitize_email(wp_unslash($_POST['email'] ?? ''));
    $company   = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
    $role      = sanitize_text_field(wp_unslash($_POST['role'] ?? ''));
    $infra     = sanitize_text_field(wp_unslash($_POST['infra'] ?? ''));
    $stack     = sanitize_text_field(wp_unslash($_POST['stack'] ?? ''));
    $challenge = sanitize_text_field(wp_unslash($_POST['challenge'] ?? ''));
    $onprem    = sanitize_text_field(wp_unslash($_POST['onprem'] ?? ''));
    $gdpr      = sanitize_text_field(wp_unslash($_POST['gdpr'] ?? ''));
    $lang      = sanitize_text_field(wp_unslash($_POST['lang'] ?? 'en'));

    // Validate required
    $errors = [];
    if (!$email || !is_email($email)) {
        $errors['email'] = 'A valid email is required.';
    }
    if (!$company) {
        $errors['company'] = 'Company is required.';
    }
    if (!$role) {
        $errors['role'] = 'Please select your role.';
    }
    if (!$infra) {
        $errors['infra'] = 'Please select your infrastructure.';
    }
    if (!$stack) {
        $errors['stack'] = 'Please select your current stack.';
    }
    if (!$challenge) {
        $errors['challenge'] = 'Please select your main challenge.';
    }
    if (!$onprem) {
        $errors['onprem'] = 'Please select an option.';
    }
    if ($gdpr !== '1') {
        $errors['gdpr'] = 'You must accept the data processing terms.';
    }

    // MX validation
    if ($email && empty($errors['email']) && !rhinometric_validate_mx($email)) {
        $errors['email'] = 'Email domain does not have valid mail servers.';
    }

    if (!empty($errors)) {
        wp_send_json_error(['fields' => $errors], 422);
    }

    // Generate token
    $token      = rhinometric_generate_confirmation_token();
    $token_hash = rhinometric_hash_token($token);

    // Create WP post
    $post_id = wp_insert_post([
        'post_type'   => 'contact_lead',
        'post_title'  => $company . ' — ' . $email,
        'post_status' => 'private',
    ]);

    if (is_wp_error($post_id)) {
        wp_send_json_error(['message' => 'An internal error occurred.'], 500);
    }

    // Store metadata
    $meta_fields = [
        '_rino_email'           => $email,
        '_rino_company'         => $company,
        '_rino_role'            => $role,
        '_rino_infra'           => $infra,
        '_rino_stack'           => $stack,
        '_rino_challenge'       => $challenge,
        '_rino_onprem'          => $onprem,
        '_rino_lang'            => $lang,
        '_rino_token_hash'      => $token_hash,
        '_rino_token_expires'   => time() + (48 * HOUR_IN_SECONDS),
        '_rino_confirmed'       => '0',
        '_rino_is_public_email' => rhinometric_is_public_domain($email) ? '1' : '0',
        '_rino_submitted_at'    => current_time('mysql'),
        '_rino_ip'              => isset($_SERVER['REMOTE_ADDR']) ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : '',
    ];
    foreach ($meta_fields as $key => $value) {
        update_post_meta($post_id, $key, $value);
    }

    // Push to Zoho CRM
    $zoho_id = rhinometric_zoho_create_lead([
        'email'     => $email,
        'company'   => $company,
        'role'      => $role,
        'infra'     => $infra,
        'stack'     => $stack,
        'challenge' => $challenge,
        'onprem'    => $onprem,
    ]);
    if ($zoho_id) {
        update_post_meta($post_id, '_rino_zoho_id', $zoho_id);
    }

    // Send confirmation email (NOT sales notification)
    rhinometric_send_confirmation_email($email, $token, $lang);

    wp_send_json_success(['message' => 'confirmation_sent']);
}
add_action('wp_ajax_rhinometric_lead_submit', 'rhinometric_handle_lead_submission');
add_action('wp_ajax_nopriv_rhinometric_lead_submit', 'rhinometric_handle_lead_submission');

/* ==========================================================================
   14. AJAX: Token confirmation handler
   ========================================================================== */
function rhinometric_handle_lead_confirmation($token_param = null) {
    $token = $token_param ?: sanitize_text_field(wp_unslash($_GET['token'] ?? ''));

    if (!$token || strlen($token) < 64) {
        return ['status' => 'invalid'];
    }

    $token_hash = rhinometric_hash_token($token);

    // Find the lead by token hash
    $leads = get_posts([
        'post_type'   => 'contact_lead',
        'post_status' => 'private',
        'meta_key'    => '_rino_token_hash',
        'meta_value'  => $token_hash,
        'numberposts' => 1,
    ]);

    if (empty($leads)) {
        return ['status' => 'invalid'];
    }

    $post_id = $leads[0]->ID;

    // Check already confirmed
    if (get_post_meta($post_id, '_rino_confirmed', true) === '1') {
        return ['status' => 'already_confirmed'];
    }

    // Check expiration
    $expires = (int) get_post_meta($post_id, '_rino_token_expires', true);
    if (time() > $expires) {
        return ['status' => 'expired'];
    }

    // Mark confirmed
    update_post_meta($post_id, '_rino_confirmed', '1');
    update_post_meta($post_id, '_rino_confirmed_at', current_time('mysql'));

    // Calculate lead score
    $lead_data = [
        'email'     => get_post_meta($post_id, '_rino_email', true),
        'role'      => get_post_meta($post_id, '_rino_role', true),
        'infra'     => get_post_meta($post_id, '_rino_infra', true),
        'challenge' => get_post_meta($post_id, '_rino_challenge', true),
        'onprem'    => get_post_meta($post_id, '_rino_onprem', true),
    ];

    $score    = rhinometric_calculate_lead_score($lead_data);
    $category = rhinometric_classify_lead($score);

    update_post_meta($post_id, '_rino_lead_score', $score);
    update_post_meta($post_id, '_rino_lead_category', $category);

    // Update Zoho CRM
    $zoho_id = get_post_meta($post_id, '_rino_zoho_id', true);
    if ($zoho_id) {
        rhinometric_zoho_update_lead($zoho_id, [
            'Email_Validated' => true,
            'Lead_Status'     => 'Nuevo – Revisión Técnica',
            'Lead_Score'      => $score,
            'Lead_Category'   => $category,
        ]);
    }

    // NOW notify sales
    rhinometric_notify_sales($post_id);

    return ['status' => 'confirmed', 'category' => $category];
}
