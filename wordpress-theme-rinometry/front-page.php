<?php
get_header();
?>
<section class="hero">
  <div class="container hero-grid">
    <div>
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
      <h1 class="section-title"><?php esc_html_e('Own your observability stack with on-prem control and enterprise-grade insights.', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('RHINOMETRIC brings metrics, logs, traces, and AI-assisted insights into a single, secure platform built for regulated industries and modern infrastructure teams.', 'rinometry'); ?></p>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
          <?php esc_html_e('Download RHINOMETRIC', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('contact'))); ?>">
          <?php esc_html_e('Request a demo', 'rinometry'); ?>
        </a>
      </div>
    </div>
    <div class="hero-card hero-visual" aria-label="<?php esc_attr_e('Platform highlights', 'rinometry'); ?>">
      <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/rhino-mark.svg'); ?>" alt="<?php esc_attr_e('RHINOMETRIC rhino mark', 'rinometry'); ?>">
      <h2><?php esc_html_e('Why teams choose RHINOMETRIC', 'rinometry'); ?></h2>
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
    <p class="section-lead"><?php esc_html_e('Download Rinometry and receive installation guidance immediately.', 'rinometry'); ?></p>
    <a class="btn btn-accent" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
      <?php esc_html_e('Download RHINOMETRIC', 'rinometry'); ?>
    </a>
  </div>
</section>
<?php
get_footer();
