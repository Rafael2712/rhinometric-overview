<?php

if (!defined('ABSPATH')) {
    exit;
}

function rinometry_setup() {
    load_theme_textdomain('rinometry', get_template_directory() . '/languages');

    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list', 'gallery', 'caption']);

    register_nav_menus([
        'primary' => __('Primary Navigation', 'rinometry'),
        'footer' => __('Footer Navigation', 'rinometry'),
    ]);
}
add_action('after_setup_theme', 'rinometry_setup');

function rinometry_enqueue_assets() {
    wp_enqueue_style(
        'rinometry-style',
        get_stylesheet_uri(),
        [],
        filemtime(get_stylesheet_directory() . '/style.css')
    );
}
add_action('wp_enqueue_scripts', 'rinometry_enqueue_assets');

function rinometry_output_favicon() {
    if (has_site_icon()) {
        return;
    }

    $icon = get_template_directory_uri() . '/assets/img/logo-rhinometric.png';
    $icon_svg = get_template_directory_uri() . '/assets/img/logo-rhinometric.svg';
    echo '<link rel="icon" href="' . esc_url($icon) . '" sizes="32x32" />' . "\n";
    echo '<link rel="icon" href="' . esc_url($icon_svg) . '" type="image/svg+xml" />' . "\n";
    echo '<link rel="apple-touch-icon" href="' . esc_url($icon) . '" />' . "\n";
}
add_action('wp_head', 'rinometry_output_favicon');

function rinometry_register_cpt_download_leads() {
    register_post_type('download_lead', [
        'labels' => [
            'name' => __('Download Leads', 'rinometry'),
            'singular_name' => __('Download Lead', 'rinometry'),
        ],
        'public' => false,
        'show_ui' => true,
        'menu_icon' => 'dashicons-download',
        'supports' => ['title'],
    ]);
}
add_action('init', 'rinometry_register_cpt_download_leads');

function rinometry_register_cpt_demo_leads() {
    register_post_type('demo_lead', [
        'labels' => [
            'name' => __('Demo Leads', 'rinometry'),
            'singular_name' => __('Demo Lead', 'rinometry'),
        ],
        'public' => false,
        'show_ui' => true,
        'menu_icon' => 'dashicons-video-alt3',
        'supports' => ['title'],
    ]);
}
add_action('init', 'rinometry_register_cpt_demo_leads');

function rinometry_meta_tags() {
    if (!is_singular()) {
        return;
    }

    global $post;
    $custom_description = get_post_meta($post->ID, '_rino_meta_description', true);
    $description = $custom_description ? $custom_description : wp_trim_words(get_the_excerpt($post), 28);
    if (!$description) {
        $description = __('Rhinometric is an on-prem observability suite for metrics, logs, and traces with enterprise-grade security.', 'rinometry');
    }

    $title = wp_get_document_title();
    $url = get_permalink($post);
    $image = get_site_icon_url(512);

    echo '<meta name="description" content="' . esc_attr($description) . '" />' . "\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '" />' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($description) . '" />' . "\n";
    echo '<meta property="og:url" content="' . esc_url($url) . '" />' . "\n";
    echo '<meta property="og:type" content="website" />' . "\n";
    if ($image) {
        echo '<meta property="og:image" content="' . esc_url($image) . '" />' . "\n";
    }
}
add_action('wp_head', 'rinometry_meta_tags');

function rinometry_language_switcher() {
    if (function_exists('pll_the_languages')) {
        echo '<div class="language-switcher" aria-label="' . esc_attr__('Language selector', 'rinometry') . '">';
        pll_the_languages([
            'show_flags' => 0,
            'show_names' => 1,
            'display_names_as' => 'name',
            'dropdown' => 0,
        ]);
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

function rinometry_home_anchor_url($anchor) {
    return esc_url(home_url('/#' . ltrim($anchor, '#')));
}

function rinometry_primary_menu_fallback() {
    $items = [
        [
            'label' => __('Platform', 'rinometry'),
            'url' => get_permalink(get_page_by_path('platform')),
        ],
        [
            'label' => __('Features', 'rinometry'),
            'url' => rinometry_home_anchor_url('features'),
        ],
        [
            'label' => __('Integrations', 'rinometry'),
            'url' => rinometry_home_anchor_url('integrations'),
        ],
        [
            'label' => __('Security', 'rinometry'),
            'url' => get_permalink(get_page_by_path('security')),
        ],
        [
            'label' => __('Roadmap', 'rinometry'),
            'url' => get_permalink(get_page_by_path('roadmap')),
        ],
        [
            'label' => __('Download', 'rinometry'),
            'url' => get_permalink(get_page_by_path('download')),
        ],
    ];

    echo '<ul>';
    foreach ($items as $item) {
        if (!$item['url']) {
            continue;
        }
        echo '<li><a href="' . esc_url($item['url']) . '">' . esc_html($item['label']) . '</a></li>';
    }
    echo '</ul>';
}

function rinometry_get_current_language() {
    $lang = isset($_COOKIE['rino_lang']) ? sanitize_text_field(wp_unslash($_COOKIE['rino_lang'])) : '';
    return $lang === 'es' ? 'es' : 'en';
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
    register_setting('general', 'rinometry_download_url', [
        'type' => 'string',
        'sanitize_callback' => 'esc_url_raw',
        'default' => '',
    ]);

    register_setting('general', 'rinometry_lead_recipient', [
        'type' => 'string',
        'sanitize_callback' => 'sanitize_email',
        'default' => 'rafael.canelon@rhinometric.com',
    ]);

    add_settings_field(
        'rinometry_download_url',
        __('Rhinometric download URL', 'rinometry'),
        'rinometry_download_url_field',
        'general'
    );

    add_settings_field(
        'rinometry_lead_recipient',
        __('Rhinometric lead recipient email', 'rinometry'),
        'rinometry_lead_recipient_field',
        'general'
    );
}
add_action('admin_init', 'rinometry_register_settings');

function rinometry_download_url_field() {
    $value = esc_url(get_option('rinometry_download_url'));
    echo '<input type="url" id="rinometry_download_url" name="rinometry_download_url" value="' . esc_attr($value) . '" class="regular-text" />';
    echo '<p class="description">' . esc_html__('Public download link used in emails and the download page.', 'rinometry') . '</p>';
}

function rinometry_lead_recipient_field() {
    $value = esc_attr(get_option('rinometry_lead_recipient', 'rafael.canelon@rhinometric.com'));
    echo '<input type="email" id="rinometry_lead_recipient" name="rinometry_lead_recipient" value="' . $value . '" class="regular-text" />';
    echo '<p class="description">' . esc_html__('Lead notifications will be sent to this email.', 'rinometry') . '</p>';
}

function rinometry_register_lead_exports() {
    add_management_page(
        __('Rhinometric Leads Export', 'rinometry'),
        __('Rhinometric Leads Export', 'rinometry'),
        'manage_options',
        'rhinometric-leads-export',
        'rinometry_render_lead_export_page'
    );
}
add_action('admin_menu', 'rinometry_register_lead_exports');

function rinometry_render_lead_export_page() {
    if (!current_user_can('manage_options')) {
        return;
    }

    $base_url = admin_url('admin-post.php');
    $nonce = wp_create_nonce('rinometry_export_leads');

    $links = [
        'download_csv' => add_query_arg([
            'action' => 'rinometry_export_leads',
            'type' => 'download',
            'format' => 'csv',
            '_wpnonce' => $nonce,
        ], $base_url),
        'download_json' => add_query_arg([
            'action' => 'rinometry_export_leads',
            'type' => 'download',
            'format' => 'json',
            '_wpnonce' => $nonce,
        ], $base_url),
        'demo_csv' => add_query_arg([
            'action' => 'rinometry_export_leads',
            'type' => 'demo',
            'format' => 'csv',
            '_wpnonce' => $nonce,
        ], $base_url),
        'demo_json' => add_query_arg([
            'action' => 'rinometry_export_leads',
            'type' => 'demo',
            'format' => 'json',
            '_wpnonce' => $nonce,
        ], $base_url),
    ];

    echo '<div class="wrap">';
    echo '<h1>' . esc_html__('Rhinometric Leads Export', 'rinometry') . '</h1>';
    echo '<p>' . esc_html__('Download leads in CSV or JSON format.', 'rinometry') . '</p>';
    echo '<ul>';
    echo '<li><a href="' . esc_url($links['download_csv']) . '">' . esc_html__('Download leads (CSV)', 'rinometry') . '</a></li>';
    echo '<li><a href="' . esc_url($links['download_json']) . '">' . esc_html__('Download leads (JSON)', 'rinometry') . '</a></li>';
    echo '<li><a href="' . esc_url($links['demo_csv']) . '">' . esc_html__('Demo leads (CSV)', 'rinometry') . '</a></li>';
    echo '<li><a href="' . esc_url($links['demo_json']) . '">' . esc_html__('Demo leads (JSON)', 'rinometry') . '</a></li>';
    echo '</ul>';
    echo '</div>';
}

function rinometry_export_leads_handler() {
    if (!current_user_can('manage_options')) {
        wp_die(__('Unauthorized request.', 'rinometry'));
    }

    check_admin_referer('rinometry_export_leads');

    $type = sanitize_text_field(wp_unslash($_GET['type'] ?? 'download'));
    $format = sanitize_text_field(wp_unslash($_GET['format'] ?? 'csv'));
    $post_type = $type === 'demo' ? 'demo_lead' : 'download_lead';

    $posts = get_posts([
        'post_type' => $post_type,
        'post_status' => ['private', 'publish', 'draft'],
        'numberposts' => -1,
        'orderby' => 'date',
        'order' => 'DESC',
    ]);

    $rows = [];
    foreach ($posts as $post) {
        $rows[] = [
            'name' => $post->post_title,
            'email' => get_post_meta($post->ID, '_rino_email', true),
            'company' => get_post_meta($post->ID, '_rino_company', true),
            'use_case' => get_post_meta($post->ID, '_rino_use_case', true),
            'message' => get_post_meta($post->ID, '_rino_message', true),
            'created_at' => $post->post_date,
        ];
    }

    if ($format === 'json') {
        wp_send_json($rows);
    }

    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename=' . $post_type . '.csv');
    $output = fopen('php://output', 'w');
    fputcsv($output, ['name', 'email', 'company', 'use_case', 'message', 'created_at']);
    foreach ($rows as $row) {
        fputcsv($output, $row);
    }
    fclose($output);
    exit;
}
add_action('admin_post_rinometry_export_leads', 'rinometry_export_leads_handler');

function rinometry_check_rate_limit($key, $seconds = 10) {
        $ip = isset($_SERVER['REMOTE_ADDR']) ? sanitize_text_field(wp_unslash($_SERVER['REMOTE_ADDR'])) : 'unknown';
        $transient_key = 'rino_rate_' . md5($key . '|' . $ip);
        if (get_transient($transient_key)) {
                return false;
        }
        set_transient($transient_key, 1, $seconds);
        return true;
}

function rinometry_render_form_js() {
        ?>
        <script>
            document.addEventListener('submit', function (event) {
                var form = event.target;
                if (!form || !form.classList.contains('js-disable-on-submit')) {
                    return;
                }
                var button = form.querySelector('button[type="submit"]');
                if (button) {
                    button.setAttribute('disabled', 'disabled');
                    button.setAttribute('aria-disabled', 'true');
                    button.classList.add('is-loading');
                }
                form.setAttribute('aria-busy', 'true');
            });
        </script>
        <?php
}
add_action('wp_footer', 'rinometry_render_form_js');
