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
      <li><span class="benefit-icon" aria-hidden="true"></span><?php esc_html_e('On-prem control and data sovereignty.', 'rinometry'); ?></li>
      <li><span class="benefit-icon" aria-hidden="true"></span><?php esc_html_e('Unified metrics, logs, and traces for faster triage.', 'rinometry'); ?></li>
      <li><span class="benefit-icon" aria-hidden="true"></span><?php esc_html_e('Operational visibility with clear dashboards.', 'rinometry'); ?></li>
      <li><span class="benefit-icon" aria-hidden="true"></span><?php esc_html_e('Reduce noise and focus on high-impact issues.', 'rinometry'); ?></li>
    </ul>

    <div class="tabs" data-tabs>
      <div class="tab-list" role="tablist" aria-label="<?php esc_attr_e('Telemetry tabs', 'rinometry'); ?>">
        <button class="tab-button is-active" role="tab" aria-selected="true" aria-controls="tab-metrics" id="tab-btn-metrics"><?php esc_html_e('Metrics', 'rinometry'); ?></button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-logs" id="tab-btn-logs"><?php esc_html_e('Logs', 'rinometry'); ?></button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-traces" id="tab-btn-traces"><?php esc_html_e('Traces', 'rinometry'); ?></button>
      </div>
      <div class="tab-panel is-active" role="tabpanel" id="tab-metrics" aria-labelledby="tab-btn-metrics">
        <p><?php esc_html_e('Capture system and service performance with Prometheus-style metrics and clear dashboards.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-logs" aria-labelledby="tab-btn-logs">
        <p><?php esc_html_e('Centralize logs for faster investigations and cross-signal context.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-traces" aria-labelledby="tab-btn-traces">
        <p><?php esc_html_e('Trace requests end-to-end with OTLP-compatible pipelines.', 'rinometry'); ?></p>
      </div>
    </div>

    <div class="accordion">
      <details>
        <summary><?php esc_html_e('On-premise security', 'rinometry'); ?></summary>
        <p><?php esc_html_e('Keep telemetry inside your environment with controlled access and audit-ready operations.', 'rinometry'); ?></p>
      </details>
      <details>
        <summary><?php esc_html_e('Integrations', 'rinometry'); ?></summary>
        <p><?php esc_html_e('Connect existing telemetry sources without re-architecting your stack.', 'rinometry'); ?></p>
      </details>
    </div>
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
    <div class="grid placeholders-grid" aria-label="<?php esc_attr_e('Product placeholders', 'rinometry'); ?>">
      <div class="card placeholder-card">
        <div class="placeholder-frame" aria-hidden="true"></div>
        <h3><?php esc_html_e('Grafana dashboard', 'rinometry'); ?></h3>
      </div>
      <div class="card placeholder-card">
        <div class="placeholder-frame" aria-hidden="true"></div>
        <h3><?php esc_html_e('Logs / Traces / Metrics', 'rinometry'); ?></h3>
      </div>
      <div class="card placeholder-card">
        <div class="placeholder-frame" aria-hidden="true"></div>
        <h3><?php esc_html_e('Rhinometric console', 'rinometry'); ?></h3>
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

<script>
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-tabs]').forEach(function (tabs) {
      var buttons = tabs.querySelectorAll('.tab-button');
      var panels = tabs.querySelectorAll('.tab-panel');
      buttons.forEach(function (button) {
        button.addEventListener('click', function () {
          buttons.forEach(function (btn) {
            btn.classList.remove('is-active');
            btn.setAttribute('aria-selected', 'false');
          });
          panels.forEach(function (panel) {
            panel.classList.remove('is-active');
          });
          button.classList.add('is-active');
          button.setAttribute('aria-selected', 'true');
          var target = tabs.querySelector('#' + button.getAttribute('aria-controls'));
          if (target) {
            target.classList.add('is-active');
          }
        });
      });
    });
  });
</script>
<?php
get_footer();
