<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('Platform Overview', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('Rhinometric unifies observability workflows with secure, on-prem deployment options and enterprise-grade governance.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-platform.svg'); ?>" alt="<?php esc_attr_e('Platform icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Unified data plane', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Metrics, logs, and traces in a single operational view with consistent retention policies.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-dashboards.svg'); ?>" alt="<?php esc_attr_e('Dashboards icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Operator-first design', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Opinionated dashboards, alerts, and runbooks to accelerate incident response.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-security.svg'); ?>" alt="<?php esc_attr_e('Security icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Enterprise governance', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Role-based access, audit visibility, and secure integrations for regulated teams.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Product views', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Placeholder visuals for product screens. Replace with real screenshots when available.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-dashboard.png'); ?>" alt="<?php esc_attr_e('Rhinometric dashboard screenshot placeholder', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-dashboard.svg'); ?>';">
        <h3><?php esc_html_e('Executive dashboard', 'rinometry'); ?></h3>
        <p><?php esc_html_e('High-level SLIs, SLO status, and incident posture.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-logs.png'); ?>" alt="<?php esc_attr_e('Rhinometric logs screenshot placeholder', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-logs.svg'); ?>';">
        <h3><?php esc_html_e('Logs explorer', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Search, filter, and correlate logs with trace context.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-traces.png'); ?>" alt="<?php esc_attr_e('Rhinometric traces screenshot placeholder', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-traces.svg'); ?>';">
        <h3><?php esc_html_e('Trace analysis', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Identify latency hotspots and service dependencies.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-alerts.png'); ?>" alt="<?php esc_attr_e('Rhinometric alerts screenshot placeholder', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/product-alerts.svg'); ?>';">
        <h3><?php esc_html_e('Alert center', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Route alerts with context to reduce MTTR.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container split">
    <div>
      <h2 class="section-title"><?php esc_html_e('Deployment flexibility', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('Run fully on-premise or in a hybrid configuration while keeping sensitive data in your control.', 'rinometry'); ?></p>
    </div>
    <div class="card">
      <h3><?php esc_html_e('Integration-ready', 'rinometry'); ?></h3>
      <p><?php esc_html_e('Aligned with common telemetry standards and compatible with existing alerting workflows.', 'rinometry'); ?></p>
    </div>
  </div>
</section>
<?php
get_footer();
