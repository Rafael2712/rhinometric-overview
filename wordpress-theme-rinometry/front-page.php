<?php
get_header();
?>
<section class="hero">
  <div class="container hero-grid">
    <div>
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
      <h1 class="section-title"><?php esc_html_e('Own your observability stack with on-prem control and enterprise-grade insights.', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('Rhinometric brings metrics, logs, traces, and AI-assisted insights into a single, secure platform built for regulated industries and modern infrastructure teams.', 'rinometry'); ?></p>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
          <?php esc_html_e('Download Rhinometric', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('request-demo'))); ?>">
          <?php esc_html_e('Request a demo', 'rinometry'); ?>
        </a>
      </div>
    </div>
    <div class="hero-card hero-visual" aria-label="<?php esc_attr_e('Platform highlights', 'rinometry'); ?>">
      <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/hero-illustration.svg'); ?>" alt="<?php esc_attr_e('Rhinometric platform hero illustration', 'rinometry'); ?>">
      <h2><?php esc_html_e('Why teams choose Rhinometric', 'rinometry'); ?></h2>
      <ul>
        <li><?php esc_html_e('Full visibility across metrics, logs, traces, and alerts.', 'rinometry'); ?></li>
        <li><?php esc_html_e('On-prem or hybrid deployment with data sovereignty.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Enterprise security controls and audit-ready observability.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Fast time-to-value with guided dashboards and playbooks.', 'rinometry'); ?></li>
      </ul>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Built for validation and acquisition', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Start with a trial download today and scale to enterprise licensing, checkout, and customer portal when you are ready.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <h3><?php esc_html_e('Fast evaluation', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Deploy in your environment with quick-start assets and secure defaults.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Prove ROI early', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Validate performance, incident response, and compliance readiness in days—not months.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Enterprise path', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Upgrade to commercial licensing, SLA support, and managed services when you scale.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container split">
    <div>
      <h2 class="section-title"><?php esc_html_e('Observability suite designed for ops teams', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('Monitor your estate with curated dashboards, alerts, and anomaly detection tuned for enterprise reliability.', 'rinometry'); ?></p>
      <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('observability-suite'))); ?>">
        <?php esc_html_e('Explore the suite', 'rinometry'); ?>
      </a>
    </div>
    <div class="card">
      <h3><?php esc_html_e('What you get', 'rinometry'); ?></h3>
      <ul>
        <li><?php esc_html_e('Dashboards for services, infrastructure, and SLAs.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Alerting with noise reduction and routing.', 'rinometry'); ?></li>
        <li><?php esc_html_e('AI-assisted anomaly detection and triage.', 'rinometry'); ?></li>
      </ul>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Ready to deploy?', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Download Rhinometric and receive installation guidance immediately.', 'rinometry'); ?></p>
    <a class="btn btn-accent" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
      <?php esc_html_e('Download Rhinometric', 'rinometry'); ?>
    </a>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Integrations & tooling', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Rhinometric is designed to work alongside common observability tooling without forcing a rip-and-replace. Mentioned tools are provided as context, not guaranteed integrations.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-otel.svg'); ?>" alt="<?php esc_attr_e('OpenTelemetry icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('OpenTelemetry pipelines', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Ingest standardized telemetry to preserve context across metrics, logs, and traces. [REVIEW]', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-prometheus.svg'); ?>" alt="<?php esc_attr_e('Prometheus icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Metrics ecosystems', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Positioned to coexist with Prometheus-style metrics and alerting workflows. [REVIEW]', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-logging.svg'); ?>" alt="<?php esc_attr_e('Logging icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Logs and traces stack', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Aligns with logging and tracing backends used by platform teams. [REVIEW]', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
