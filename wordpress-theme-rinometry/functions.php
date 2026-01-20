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
    wp_enqueue_style('rinometry-style', get_stylesheet_uri(), [], '1.0.0');
}
add_action('wp_enqueue_scripts', 'rinometry_enqueue_assets');

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

    $current_locale = determine_locale();
    $is_spanish = strpos($current_locale, 'es') === 0;

    echo '<div class="language-switcher" aria-label="' . esc_attr__('Language selector', 'rinometry') . '">';
    echo '<a class="' . ($is_spanish ? '' : 'is-active') . '" href="' . esc_url(home_url('/')) . '">EN</a>';
    echo '<a class="' . ($is_spanish ? 'is-active' : '') . '" href="' . esc_url(home_url('/es/')) . '">ES</a>';
    echo '</div>';
}

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
