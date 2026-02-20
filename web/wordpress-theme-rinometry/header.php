<?php
/**
 * header.php — Rhinometric v3
 * Desktop: horizontal nav + CTA + lang switcher
 * Mobile: hamburger → overlay
 */
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

    <!-- Brand -->
    <a class="brand" href="<?php echo esc_url(home_url('/')); ?>">
      <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>"
           alt="<?php esc_attr_e('Rhinometric', 'rinometry'); ?>" />
      <span>Rhinometric</span>
    </a>

    <!-- Desktop nav -->
    <nav class="main-nav" role="navigation" aria-label="<?php esc_attr_e('Primary navigation', 'rinometry'); ?>">
      <?php rinometry_v3_nav_links(); ?>
    </nav>

    <!-- Header actions: lang + CTA -->
    <div class="header-actions">
      <?php rinometry_language_switcher(); ?>
      <a class="btn btn-primary btn-sm" href="<?php echo esc_url(rinometry_page_url('contact')); ?>">
        <?php esc_html_e('Contact us', 'rinometry'); ?>
      </a>
    </div>

    <!-- Hamburger (mobile only) -->
    <button class="nav-toggle" aria-label="<?php esc_attr_e('Open menu', 'rinometry'); ?>" aria-expanded="false" aria-controls="mobile-nav">
      <span></span><span></span><span></span>
    </button>

  </div>
</header>

<!-- Mobile overlay -->
<div class="mobile-nav-overlay" id="mobile-nav" aria-hidden="true">
  <nav aria-label="<?php esc_attr_e('Mobile navigation', 'rinometry'); ?>">
    <?php rinometry_v3_nav_links(); ?>
  </nav>
  <div class="mobile-nav-actions">
    <a class="btn btn-primary" href="<?php echo esc_url(rinometry_page_url('contact')); ?>">
      <?php esc_html_e('Contact us', 'rinometry'); ?>
    </a>
  </div>
</div>

<main id="main" class="site-main" role="main">
