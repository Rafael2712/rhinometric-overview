<?php
/**
 * functions.php — Rhinometric v3
 * Preserves all existing functionality + adds new nav, JS, SEO, cookie support.
 */

if (!defined('ABSPATH')) {
    exit;
}

/* ------------------------------------------------------------------
   Theme setup
   ------------------------------------------------------------------ */
function rinometry_setup() {
    load_theme_textdomain('rinometry', get_template_directory() . '/languages');
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list', 'gallery', 'caption']);

    register_nav_menus([
        'primary' => __('Primary Navigation', 'rinometry'),
        'footer'  => __('Footer Navigation', 'rinometry'),
    ]);
}
add_action('after_setup_theme', 'rinometry_setup');

/* ------------------------------------------------------------------
   Enqueue assets
   ------------------------------------------------------------------ */
function rinometry_enqueue_assets() {
    $theme_dir = get_stylesheet_directory();
    $theme_uri = get_stylesheet_directory_uri();

    wp_enqueue_style(
        'rinometry-style',
        get_stylesheet_uri(),
        [],
        filemtime($theme_dir . '/style.css')
    );

    // Navigation JS (hamburger)
    $nav_file = $theme_dir . '/assets/js/navigation.js';
    if (file_exists($nav_file)) {
        wp_enqueue_script(
            'rinometry-nav',
            $theme_uri . '/assets/js/navigation.js',
            [],
            filemtime($nav_file),
            true
        );
    }

    // Cookie banner JS
    if (rinometry_cookie_banner_enabled()) {
        $cookie_file = $theme_dir . '/assets/js/cookie-banner.js';
        if (file_exists($cookie_file)) {
            wp_enqueue_script(
                'rinometry-cookies',
                $theme_uri . '/assets/js/cookie-banner.js',
                [],
                filemtime($cookie_file),
                true
            );
        }
    }

    // Front-page i18n JS (only on front page)
    if (is_front_page()) {
        $i18n_file = $theme_dir . '/assets/js/frontpage-i18n.js';
        if (file_exists($i18n_file)) {
            wp_enqueue_script(
                'rinometry-i18n',
                $theme_uri . '/assets/js/frontpage-i18n.js',
                [],
                filemtime($i18n_file),
                true
            );
        }
    }
}
add_action('wp_enqueue_scripts', 'rinometry_enqueue_assets');

/* ------------------------------------------------------------------
   Cookie banner toggle
   ------------------------------------------------------------------ */
function rinometry_cookie_banner_enabled() {
    return true;
}

/* ------------------------------------------------------------------
   Favicon
   ------------------------------------------------------------------ */
function rinometry_output_favicon() {
    if (has_site_icon()) {
        return;
    }
    $icon = get_template_directory_uri() . '/assets/img/logo-rhinometric.png';
    echo '<link rel="icon" href="' . esc_url($icon) . '" sizes="32x32" />' . "\n";
    echo '<link rel="apple-touch-icon" href="' . esc_url($icon) . '" />' . "\n";
}
add_action('wp_head', 'rinometry_output_favicon');

/* ------------------------------------------------------------------
   SEO meta tags — per-page title & description with i18n
   ------------------------------------------------------------------ */
function rinometry_meta_tags() {
    $lang = rinometry_get_current_language();

    // Front page meta
    if (is_front_page()) {
        $titles = [
            'en' => 'Rhinometric — Single-Tenant Observability in the EU',
            'es' => 'Rhinometric — Observabilidad Single-Tenant en la UE',
        ];
        $descs = [
            'en' => 'Deploy a private observability engine for metrics, logs, and traces. On-premise or dedicated VM in a European cloud provider. No shared tenancy.',
            'es' => 'Despliega un motor de observabilidad privado para métricas, logs y trazas. On-premise o VM dedicada en proveedor cloud europeo. Sin tenencia compartida.',
        ];
        $title = $titles[$lang] ?? $titles['en'];
        $desc = $descs[$lang] ?? $descs['en'];
    } elseif (is_singular()) {
        global $post;
        $title = wp_get_document_title();
        $custom_desc = get_post_meta($post->ID, '_rino_meta_description', true);
        $desc = $custom_desc ?: wp_trim_words(get_the_excerpt($post), 28);
        if (!$desc) {
            $desc = ($lang === 'es')
                ? 'Rhinometric: observabilidad on-prem para métricas, logs y trazas con seguridad empresarial.'
                : 'Rhinometric: on-prem observability for metrics, logs, and traces with enterprise-grade security.';
        }
    } else {
        return;
    }

    $url = is_front_page() ? home_url('/') : get_permalink();
    echo '<meta name="description" content="' . esc_attr($desc) . '" />' . "\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '" />' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($desc) . '" />' . "\n";
    echo '<meta property="og:url" content="' . esc_url($url) . '" />' . "\n";
    echo '<meta property="og:type" content="website" />' . "\n";
}
add_action('wp_head', 'rinometry_meta_tags');

/* ------------------------------------------------------------------
   Language handling (preserved from v2)
   ------------------------------------------------------------------ */
function rinometry_language_switcher() {
    if (function_exists('pll_the_languages')) {
        echo '<div class="language-switcher" aria-label="' . esc_attr__('Language selector', 'rinometry') . '">';
        pll_the_languages(['show_flags' => 0, 'show_names' => 1, 'display_names_as' => 'name', 'dropdown' => 0]);
        echo '</div>';
        return;
    }
    $current_lang = rinometry_get_current_language();
    $current_url = home_url(add_query_arg([]));
    echo '<div class="language-switcher" aria-label="' . esc_attr__('Language selector', 'rinometry') . '">';
    echo '<a class="' . ($current_lang === 'en' ? 'is-active' : '') . '" href="' . esc_url(add_query_arg('lang', 'en', $current_url)) . '">EN</a>';
    echo '<a class="' . ($current_lang === 'es' ? 'is-active' : '') . '" href="' . esc_url(add_query_arg('lang', 'es', $current_url)) . '">ES</a>';
    echo '</div>';
}

function rinometry_get_current_language() {
    $supported = ['en', 'es'];

    // Query param takes priority
    if (isset($_GET['lang'])) {
        $q = sanitize_text_field(wp_unslash($_GET['lang']));
        if (in_array($q, $supported, true)) {
            return $q;
        }
    }

    // Then cookie
    if (isset($_COOKIE['rino_lang'])) {
        $c = sanitize_text_field(wp_unslash($_COOKIE['rino_lang']));
        if (in_array($c, $supported, true)) {
            return $c;
        }
    }

    return 'en';
}

function rinometry_set_language_cookie() {
    if (!isset($_GET['lang'])) {
        return;
    }
    $lang = sanitize_text_field(wp_unslash($_GET['lang']));
    if (!in_array($lang, ['en', 'es'], true)) {
        return;
    }
    setcookie('rino_lang', $lang, time() + DAY_IN_SECONDS * 30, COOKIEPATH ?: '/', COOKIE_DOMAIN ?: '', is_ssl(), true);
    $_COOKIE['rino_lang'] = $lang;

    $redirect = remove_query_arg('lang');
    wp_safe_redirect($redirect);
    exit;
}
add_action('init', 'rinometry_set_language_cookie');

function rinometry_filter_locale($locale) {
    return rinometry_get_current_language() === 'es' ? 'es_ES' : 'en_US';
}
add_filter('locale', 'rinometry_filter_locale');
add_filter('determine_locale', 'rinometry_filter_locale');

/* ------------------------------------------------------------------
   Navigation helper — outputs links for both desktop & mobile
   ------------------------------------------------------------------ */
function rinometry_v3_nav_links() {
    $lang = rinometry_get_current_language();
    $items = [
        ['slug' => 'platform',   'en' => 'Platform',   'es' => 'Plataforma'],
        ['slug' => 'deployment', 'en' => 'Deployment', 'es' => 'Despliegue'],
        ['slug' => 'security',   'en' => 'Security',   'es' => 'Seguridad'],
        ['slug' => 'pricing',    'en' => 'Pricing',    'es' => 'Precios'],
        ['slug' => 'resources',  'en' => 'Resources',  'es' => 'Recursos'],
        ['slug' => 'contact',    'en' => 'Contact',    'es' => 'Contacto'],
    ];
    foreach ($items as $item) {
        $url = rinometry_page_url($item['slug']);
        $label = $item[$lang] ?? $item['en'];
        $current = is_page($item['slug']) ? ' aria-current="page"' : '';
        echo '<a href="' . esc_url($url) . '"' . $current . '>' . esc_html($label) . '</a>';
    }
}

/**
 * Get the URL for a page by slug, with fallback to /#slug.
 */
function rinometry_page_url($slug) {
    $page = get_page_by_path($slug);
    if ($page) {
        return get_permalink($page);
    }
    return home_url('/' . $slug . '/');
}

/* ------------------------------------------------------------------
   Fallback menu (kept for backwards compat)
   ------------------------------------------------------------------ */
function rinometry_primary_menu_fallback() {
    rinometry_v3_nav_links();
}

/* ------------------------------------------------------------------
   Custom post types (preserved)
   ------------------------------------------------------------------ */
function rinometry_register_cpt_download_leads() {
    register_post_type('download_lead', [
        'labels' => ['name' => __('Download Leads', 'rinometry'), 'singular_name' => __('Download Lead', 'rinometry')],
        'public' => false, 'show_ui' => true, 'menu_icon' => 'dashicons-download', 'supports' => ['title'],
    ]);
}
add_action('init', 'rinometry_register_cpt_download_leads');

function rinometry_register_cpt_demo_leads() {
    register_post_type('demo_lead', [
        'labels' => ['name' => __('Demo Leads', 'rinometry'), 'singular_name' => __('Demo Lead', 'rinometry')],
        'public' => false, 'show_ui' => true, 'menu_icon' => 'dashicons-video-alt3', 'supports' => ['title'],
    ]);
}
add_action('init', 'rinometry_register_cpt_demo_leads');

/* ------------------------------------------------------------------
   Settings (preserved)
   ------------------------------------------------------------------ */
function rinometry_get_download_url() {
    $configured = get_option('rinometry_download_url');
    if ($configured) {
        return esc_url_raw($configured);
    }
    return 'https://rhinometric.com/download';
}

function rinometry_get_lead_recipient() {
    $configured = get_option('rinometry_lead_recipient');
    if ($configured && is_email($configured)) {
        return $configured;
    }
    return 'rafael.canelon@rhinometric.com';
}

function rinometry_register_settings() {
    register_setting('general', 'rinometry_download_url', ['type' => 'string', 'sanitize_callback' => 'esc_url_raw', 'default' => '']);
    register_setting('general', 'rinometry_lead_recipient', ['type' => 'string', 'sanitize_callback' => 'sanitize_email', 'default' => 'rafael.canelon@rhinometric.com']);
    add_settings_field('rinometry_download_url', __('Rhinometric download URL', 'rinometry'), 'rinometry_download_url_field', 'general');
    add_settings_field('rinometry_lead_recipient', __('Rhinometric lead recipient email', 'rinometry'), 'rinometry_lead_recipient_field', 'general');
}
add_action('admin_init', 'rinometry_register_settings');

function rinometry_download_url_field() {
    $value = esc_url(get_option('rinometry_download_url'));
    echo '<input type="url" id="rinometry_download_url" name="rinometry_download_url" value="' . esc_attr($value) . '" class="regular-text" />';
}

function rinometry_lead_recipient_field() {
    $value = esc_attr(get_option('rinometry_lead_recipient', 'rafael.canelon@rhinometric.com'));
    echo '<input type="email" id="rinometry_lead_recipient" name="rinometry_lead_recipient" value="' . $value . '" class="regular-text" />';
}

/* ------------------------------------------------------------------
   Lead export (preserved)
   ------------------------------------------------------------------ */
function rinometry_register_lead_exports() {
    add_management_page(
        __('Rhinometric Leads Export', 'rinometry'),
        __('Rhinometric Leads Export', 'rinometry'),
        'manage_options', 'rhinometric-leads-export', 'rinometry_render_lead_export_page'
    );
}
add_action('admin_menu', 'rinometry_register_lead_exports');

function rinometry_render_lead_export_page() {
    if (!current_user_can('manage_options')) { return; }
    $base_url = admin_url('admin-post.php');
    $nonce = wp_create_nonce('rinometry_export_leads');
    $links = [
        'download_csv'  => add_query_arg(['action' => 'rinometry_export_leads', 'type' => 'download', 'format' => 'csv', '_wpnonce' => $nonce], $base_url),
        'download_json' => add_query_arg(['action' => 'rinometry_export_leads', 'type' => 'download', 'format' => 'json', '_wpnonce' => $nonce], $base_url),
        'demo_csv'      => add_query_arg(['action' => 'rinometry_export_leads', 'type' => 'demo', 'format' => 'csv', '_wpnonce' => $nonce], $base_url),
        'demo_json'     => add_query_arg(['action' => 'rinometry_export_leads', 'type' => 'demo', 'format' => 'json', '_wpnonce' => $nonce], $base_url),
    ];
    echo '<div class="wrap"><h1>' . esc_html__('Rhinometric Leads Export', 'rinometry') . '</h1><ul>';
    foreach ($links as $label => $url) {
        echo '<li><a href="' . esc_url($url) . '">' . esc_html(ucfirst(str_replace('_', ' ', $label))) . '</a></li>';
    }
    echo '</ul></div>';
}

function rinometry_export_leads_handler() {
    if (!current_user_can('manage_options')) { wp_die(__('Unauthorized request.', 'rinometry')); }
    check_admin_referer('rinometry_export_leads');
    $type = sanitize_text_field(wp_unslash($_GET['type'] ?? 'download'));
    $format = sanitize_text_field(wp_unslash($_GET['format'] ?? 'csv'));
    $post_type = $type === 'demo' ? 'demo_lead' : 'download_lead';
    $posts = get_posts(['post_type' => $post_type, 'post_status' => ['private', 'publish', 'draft'], 'numberposts' => -1, 'orderby' => 'date', 'order' => 'DESC']);
    $rows = [];
    foreach ($posts as $post) {
        $rows[] = [
            'name' => $post->post_title, 'email' => get_post_meta($post->ID, '_rino_email', true),
            'company' => get_post_meta($post->ID, '_rino_company', true), 'use_case' => get_post_meta($post->ID, '_rino_use_case', true),
            'message' => get_post_meta($post->ID, '_rino_message', true), 'created_at' => $post->post_date,
        ];
    }
    if ($format === 'json') { wp_send_json($rows); }
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename=' . $post_type . '.csv');
    $output = fopen('php://output', 'w');
    fputcsv($output, ['name', 'email', 'company', 'use_case', 'message', 'created_at']);
    foreach ($rows as $row) { fputcsv($output, $row); }
    fclose($output);
    exit;
}
add_action('admin_post_rinometry_export_leads', 'rinometry_export_leads_handler');

/* ------------------------------------------------------------------
   Rate limiting (preserved)
   ------------------------------------------------------------------ */
function rinometry_check_rate_limit($key, $seconds = 10) {
    $ip = isset($_SERVER['REMOTE_ADDR']) ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : 'unknown';
    $transient_key = 'rino_rate_' . md5($key . '|' . $ip);
    if (get_transient($transient_key)) { return false; }
    set_transient($transient_key, 1, $seconds);
    return true;
}

/* ------------------------------------------------------------------
   Form submit disable JS (preserved)
   ------------------------------------------------------------------ */
function rinometry_render_form_js() {
    ?>
    <script>
    document.addEventListener('submit', function(e) {
        var f = e.target;
        if (!f || !f.classList.contains('js-disable-on-submit')) return;
        var btn = f.querySelector('button[type="submit"]');
        if (btn) { btn.disabled = true; btn.setAttribute('aria-disabled','true'); btn.classList.add('is-loading'); }
        f.setAttribute('aria-busy','true');
    });
    </script>
    <?php
}
add_action('wp_footer', 'rinometry_render_form_js');
