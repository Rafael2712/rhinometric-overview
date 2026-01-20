<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('Observability Suite', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('Monitor system health across metrics, logs, traces, curated dashboards, and alerting workflows.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-metrics.svg'); ?>" alt="<?php esc_attr_e('Metrics icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Metrics', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Service-level indicators and infrastructure KPIs with long-term retention controls.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-logs.svg'); ?>" alt="<?php esc_attr_e('Logs icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Logs', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Centralized log search with governance and noise reduction.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-traces.svg'); ?>" alt="<?php esc_attr_e('Traces icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Traces', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Distributed tracing to pinpoint latency, bottlenecks, and dependency issues.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container split">
    <div>
      <h2 class="section-title"><?php esc_html_e('Dashboards and alerts', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('Prebuilt dashboards and alert rules reduce setup time and improve response consistency.', 'rinometry'); ?></p>
    </div>
    <div class="card">
      <div class="card-media">
        <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-alerts.svg'); ?>" alt="<?php esc_attr_e('Alerts icon', 'rinometry'); ?>">
        <div>
          <h3><?php esc_html_e('Operational readiness', 'rinometry'); ?></h3>
          <ul>
            <li><?php esc_html_e('Executive visibility on uptime and SLAs.', 'rinometry'); ?></li>
            <li><?php esc_html_e('Alert routing for on-call response.', 'rinometry'); ?></li>
            <li><?php esc_html_e('Custom dashboards for product teams.', 'rinometry'); ?></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
