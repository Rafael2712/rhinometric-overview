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

<section class="section section-alt" id="benefits">
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
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Deploy on‑prem', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Install inside your environment with full control.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Connect telemetry sources', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Ingest metrics, logs, and traces quickly.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Monitor + alert', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Detect issues fast and respond with confidence.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="roadmap">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Roadmap', 'rinometry'); ?></h2>
    <div class="timeline">
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Early Access & Validation (current)', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Feedback-driven adoption with fast onboarding.', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Beta release with guided dashboards', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Faster time-to-value for operations teams.', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Automated reporting & integrations', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Operational summaries and integrations.', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Enterprise features & executive summaries', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Leadership-ready insights with governance focus.', 'rinometry'); ?></p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt early-access" id="early-access">
  <div class="container">
    <div class="card">
      <span class="early-access-tag"><?php esc_html_e('Early Access', 'rinometry'); ?></span>
      <h2 class="section-title"><?php esc_html_e('Early Adopter Program', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('We are validating with a small group of enterprise teams to shape the product and onboarding experience.', 'rinometry'); ?></p>
      <ul class="early-list">
        <li><?php esc_html_e('Full access free for 3–6 months.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Priority contact with the team.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Influence roadmap and priorities.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Early documentation and onboarding support.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Invitations to feedback sessions/webinars.', 'rinometry'); ?></li>
      </ul>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
        <?php esc_html_e('Get Early Access', 'rinometry'); ?>
      </a>
    </div>
  </div>
</section>

<section class="section" id="who-its-for">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Who it’s for', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Regulated organizations', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Finance, healthcare, and government environments.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('DevOps & SRE teams', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Operational teams managing reliability at scale.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('SaaS to on‑prem migrations', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Companies bringing telemetry back in‑house.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="out-of-the-box">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('What you get out of the box', 'rinometry'); ?></h2>
    <div class="tabs" data-tabs>
      <div class="tab-list" role="tablist" aria-label="<?php esc_attr_e('Technical tabs', 'rinometry'); ?>">
        <button class="tab-button is-active" role="tab" aria-selected="true" aria-controls="tab-metrics" id="tab-btn-metrics"><?php esc_html_e('Metrics', 'rinometry'); ?></button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-logs" id="tab-btn-logs"><?php esc_html_e('Logs', 'rinometry'); ?></button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-traces" id="tab-btn-traces"><?php esc_html_e('Traces', 'rinometry'); ?></button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-alerts" id="tab-btn-alerts"><?php esc_html_e('Alerts', 'rinometry'); ?></button>
      </div>
      <div class="tab-panel is-active" role="tabpanel" id="tab-metrics" aria-labelledby="tab-btn-metrics">
        <ul>
          <li><?php esc_html_e('Track system health with clear performance baselines.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Faster capacity planning and anomaly spotting.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Prometheus.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-logs" aria-labelledby="tab-btn-logs">
        <ul>
          <li><?php esc_html_e('Centralize operational logs for faster investigations.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Correlate incidents across services quickly.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Loki.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-traces" aria-labelledby="tab-btn-traces">
        <ul>
          <li><?php esc_html_e('Trace critical paths to reduce MTTR.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Understand latency across service boundaries.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Jaeger.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-alerts" aria-labelledby="tab-btn-alerts">
        <ul>
          <li><?php esc_html_e('Alert on what matters with tuned thresholds.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Reduce noise and improve on‑call focus.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Grafana.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="expected-outcomes">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Expected Outcomes (typical benefits)', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Faster incident triage and clearer root‑cause paths.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Improved visibility across teams and services.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Reduced blind spots without SaaS lock‑in.', 'rinometry'); ?></p>
      </div>
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
