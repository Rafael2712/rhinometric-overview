<?php
?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip-link" href="#main"><?php esc_html_e('Skip to content', 'rinometry'); ?></a>
<header class="site-header" role="banner">
  <div class="container header-inner">
    <a class="brand" href="<?php echo esc_url(home_url('/')); ?>">
      <img class="brand-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="<?php esc_attr_e('Rhinometric logo', 'rinometry'); ?>" width="32" height="32" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.svg'); ?>';">
      <span class="brand-text">Rhinometric</span>
    </a>
    <nav class="nav" role="navigation" aria-label="<?php esc_attr_e('Primary', 'rinometry'); ?>">
      <?php
        wp_nav_menu([
          'theme_location' => 'primary',
          'container' => false,
          'fallback_cb' => 'rinometry_primary_menu_fallback',
          'items_wrap' => '<ul>%3$s</ul>',
        ]);
      ?>
    </nav>
    <div class="header-actions">
      <?php rinometry_language_switcher(); ?>
      <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('request-demo'))); ?>">
        <?php esc_html_e('Request a demo', 'rinometry'); ?>
      </a>
      <a class="btn btn-primary" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
        <?php esc_html_e('Download Rhinometric', 'rinometry'); ?>
      </a>
    </div>
  </div>
</header>
<main id="main" class="site-main" role="main">
