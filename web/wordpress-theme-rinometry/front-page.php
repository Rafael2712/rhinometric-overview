<?php
get_header();
?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div>
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
      <h1 class="section-title"><?php esc_html_e('Own your observability stack — fully on-premise', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('Unified metrics, logs, and traces in one secure platform built for modern infrastructure teams.', 'rinometry'); ?></p>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Request a Demo', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Get Early Access', 'rinometry'); ?>
        </a>
      </div>
    </div>
    <div class="hero-card hero-visual" aria-label="<?php esc_attr_e('Rhinometric hero logo', 'rinometry'); ?>">
      <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="<?php esc_attr_e('Rhinometric logo illustration', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/hero-illustration.svg'); ?>';">
    </div>
  </div>
</section>

<section class="section" id="benefits">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Key benefits', 'rinometry'); ?></h2>
    <ul class="benefits-list">
      <li><?php esc_html_e('On-prem control and data sovereignty.', 'rinometry'); ?></li>
      <li><?php esc_html_e('Unified metrics, logs, and traces for faster triage.', 'rinometry'); ?></li>
      <li><?php esc_html_e('Operational visibility with clear dashboards.', 'rinometry'); ?></li>
      <li><?php esc_html_e('Reduce noise and focus on high-impact issues.', 'rinometry'); ?></li>
    </ul>
  </div>
</section>

<section class="section" id="how-it-works">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('How it works', 'rinometry'); ?></h2>
    <div class="grid steps-grid">
      <div class="card">
        <h3><?php esc_html_e('Connect', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Deploy the platform inside your environment and connect telemetry sources.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Unify', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Bring metrics, logs, and traces into a single operational view.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Act', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Identify issues quickly and respond with confidence.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section early-access" id="early-access">
  <div class="container">
    <div class="card">
      <h2 class="section-title"><?php esc_html_e('Early Adopter Program', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('We are validating the platform with a small group of teams. Get early access and help shape the roadmap.', 'rinometry'); ?></p>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
        <?php esc_html_e('Get Early Access', 'rinometry'); ?>
      </a>
    </div>
  </div>
</section>
<?php
get_footer();
