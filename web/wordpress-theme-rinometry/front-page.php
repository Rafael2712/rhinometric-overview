<?php
get_header();
?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div class="hero-brand" aria-hidden="true">
      <img class="hero-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="" />
    </div>
    <div class="hero-copy hero-content">
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
      <h1 class="section-title"><?php esc_html_e('Own your observability stack. On-premise. Fully controlled.', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('Deploy a curated platform for metrics, logs, and traces inside your infrastructure — without sending operational data to external SaaS. Built for regulated and on-prem environments.', 'rinometry'); ?></p>
      <ul class="hero-bullets">
        <li><?php esc_html_e('Data stays inside your infrastructure (no SaaS ingestion).', 'rinometry'); ?></li>
        <li><?php esc_html_e('Faster triage with guided dashboards and anomaly signals.', 'rinometry'); ?></li>
        <li><?php esc_html_e('Predictable operations and retention under your control.', 'rinometry'); ?></li>
      </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Get Early Access (3–6 months)', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="mailto:rafael.canelon@rhinometric.com">
          <?php esc_html_e('Request a Demo', 'rinometry'); ?>
        </a>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt console-preview-section" aria-label="<?php esc_attr_e('Rhinometric Console Preview', 'rinometry'); ?>">
  <div class="container">
    <div class="card console-preview-card">
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

<section class="section trust-strip" aria-label="<?php esc_attr_e('Trust strip', 'rinometry'); ?>">
  <div class="container">
    <p class="trust-strip-text"><?php esc_html_e('On-premise • No SaaS lock-in • Metrics + Logs + Traces', 'rinometry'); ?></p>
  </div>
</section>

<section class="section section-alt" id="benefits">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Why teams choose Rhinometric', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Data sovereignty', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Data stays inside your infrastructure (no SaaS ingestion).', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Unified signals', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Unified signals: metrics, logs, and traces in one stack.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Faster triage', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Faster triage with guided dashboards and anomaly signals. Predictable operations and retention under your control. Designed for compliance-driven and security-sensitive teams.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="how-it-works">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Deploy fast. Operate with confidence.', 'rinometry'); ?></h2>
    <div class="grid steps-grid">
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Automated installer', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Automated installer validates requirements and checks ports.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Secure configuration', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Generates secure credentials and configuration files.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Docker Compose + health checks', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Bootstraps the stack via Docker Compose. Runs health checks to confirm the platform is ready.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="roadmap">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Roadmap (planned)', 'rinometry'); ?></h2>
    <div class="timeline">
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Now', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Early access & validation', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Next', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Guided onboarding & dashboards', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Next', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Automated reporting & deeper integrations', 'rinometry'); ?></p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3><?php esc_html_e('Later', 'rinometry'); ?></h3>
          <p><?php esc_html_e('More self-serve workflows for non-expert users', 'rinometry'); ?></p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt early-access" id="early-access">
  <div class="container">
    <div class="card">
      <span class="early-access-tag"><?php esc_html_e('Early Access', 'rinometry'); ?></span>
      <h2 class="section-title"><?php esc_html_e('Early Adopter Program (3–6 months)', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('We’re onboarding a limited number of on-prem organizations to validate Rhinometric in real environments.', 'rinometry'); ?></p>
      <ul class="early-list">
        <li><?php esc_html_e('Full access for 3–6 months at no cost', 'rinometry'); ?></li>
        <li><?php esc_html_e('Priority onboarding support for installation', 'rinometry'); ?></li>
        <li><?php esc_html_e('Direct feedback channel with the team', 'rinometry'); ?></li>
        <li><?php esc_html_e('Influence upcoming roadmap priorities', 'rinometry'); ?></li>
      </ul>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com">
        <?php esc_html_e('Join the program: rafael.canelon@rhinometric.com', 'rinometry'); ?>
      </a>
    </div>
  </div>
</section>

<section class="section" id="who-its-for">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Built for teams that can’t compromise on control', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Regulated industries', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Finance, healthcare, government', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('DevOps/SRE teams', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Operating on-prem infrastructure', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3><?php esc_html_e('Data sovereignty', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Organizations avoiding SaaS observability due to data sovereignty', 'rinometry'); ?></p>
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
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-alerts" id="tab-btn-alerts"><?php esc_html_e('Visualization', 'rinometry'); ?></button>
      </div>
      <div class="tab-panel is-active" role="tabpanel" id="tab-metrics" aria-labelledby="tab-btn-metrics">
        <ul>
          <li><?php esc_html_e('Metrics — Prometheus + exporters with ready dashboards.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Ready dashboards for faster adoption.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Prometheus.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-logs" aria-labelledby="tab-btn-logs">
        <ul>
          <li><?php esc_html_e('Logs — Loki + Promtail for centralized troubleshooting.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Centralized log review across services.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Loki.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-traces" aria-labelledby="tab-btn-traces">
        <ul>
          <li><?php esc_html_e('Traces — Jaeger for distributed request visibility.', 'rinometry'); ?></li>
          <li><?php esc_html_e('See request paths across services.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Jaeger.', 'rinometry'); ?></p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-alerts" aria-labelledby="tab-btn-alerts">
        <ul>
          <li><?php esc_html_e('Visualization — Grafana with preloaded views for faster diagnosis.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Rhinometric Console — simplified status, license visibility, and quick access to the stack.', 'rinometry'); ?></li>
        </ul>
        <p class="section-note"><?php esc_html_e('Tooling: Grafana.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="expected-outcomes">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Anomaly detection without the learning curve', 'rinometry'); ?></h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Rhinometric includes an anomaly engine that surfaces unusual behavior.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Spikes in latency, CPU, or errors are highlighted from Prometheus metrics.', 'rinometry'); ?></p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p><?php esc_html_e('Detect incidents earlier with less manual investigation.', 'rinometry'); ?></p>
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
