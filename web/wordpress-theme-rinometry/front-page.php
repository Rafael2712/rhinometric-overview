<?php
get_header();
?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div class="hero-copy">
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
      <h1 class="section-title"><?php esc_html_e('Own your observability stack — fully on-premise', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('A unified, on-prem observability platform built for modern infrastructure teams.', 'rinometry'); ?></p>
      <ul class="hero-bullets">
        <li><?php esc_html_e('Data stays in your environment.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Unified signals for faster triage.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Clear operational visibility.', 'rinometry'); ?></li>
      </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Get Early Access', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Request a Demo', 'rinometry'); ?>
        </a>
      </div>
    </div>
    <div class="hero-card hero-visual" aria-label="<?php esc_attr_e('Rhinometric product preview', 'rinometry'); ?>">
      <div class="mock-header"><?php esc_html_e('Rhinometric Console Preview', 'rinometry'); ?></div>
      <div class="mock-line"></div>
      <div class="mock-line"></div>
      <div class="mock-line"></div>
      <div class="mock-widgets">
        <div class="mock-widget"></div>
        <div class="mock-widget"></div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="benefits">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Why teams choose Rhinometric', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('On‑premise control', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Keep data inside your environment with full sovereignty.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Unified signals', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Bring metrics, logs, and traces into one view.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Operational clarity', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Focus on what matters with clean dashboards.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="how-it-works">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('How it works', 'rinometry'); ?></h2>
    <div class="grid steps-grid">
      <div class="card">
        <h3><?php esc_html_e('Deploy on‑prem', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Install inside your environment with full control.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Connect telemetry sources', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Ingest metrics, logs, and traces quickly.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Monitor + alert', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Detect issues fast and respond with confidence.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section early-access" id="early-access">
  <div class="container">
    <div class="card">
      <h2 class="section-title"><?php esc_html_e('Early Adopter Program', 'rinometry'); ?></h2>
      <ul class="early-list">
        <li><?php esc_html_e('Early access to the platform.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Direct input into the roadmap.', 'rinometry'); ?></li>
      </ul>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
        <?php esc_html_e('Get Early Access', 'rinometry'); ?>
      </a>
    </div>
  </div>
</section>
<?php
get_footer();
