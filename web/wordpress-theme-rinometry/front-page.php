<?php get_header(); ?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div class="hero-brand" aria-hidden="true">
      <img class="hero-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="" />
    </div>
    <div class="hero-copy hero-content">
      <span class="badge" data-i18n="hero.badge">Unified Observability Platform</span>
      <h1 class="section-title" data-i18n="hero.title">Own your observability stack. On-premise. Fully controlled.</h1>
      <p class="section-lead" data-i18n="hero.lead">Deploy a curated platform for metrics, logs, and traces inside your infrastructure — without sending operational data to external SaaS. Built for regulated and on-prem environments.</p>
      <ul class="hero-bullets">
        <li data-i18n="hero.bullet1">Data stays inside your infrastructure (no SaaS ingestion).</li>
        <li data-i18n="hero.bullet2">Faster triage with guided dashboards and anomaly signals.</li>
        <li data-i18n="hero.bullet3">Predictable operations and retention under your control.</li>
      </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com" data-i18n="hero.ctaPrimary">3–6 months free for early adopters (validation program)</a>
        <a class="btn btn-secondary" href="mailto:rafael.canelon@rhinometric.com" data-i18n="hero.ctaSecondary">Guided session with the team</a>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt console-preview-section" aria-label="Rhinometric Console Preview" data-i18n="console.aria" data-i18n-attr="aria-label">
  <div class="container">
    <div class="card console-preview-card">
      <div class="mock-header" data-i18n="console.header">Rhinometric Console Preview</div>
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

<section class="section trust-strip" aria-label="Trust strip" data-i18n="trust.aria" data-i18n-attr="aria-label">
  <div class="container">
    <p class="trust-strip-text" data-i18n="trust.copy">On-premise • No SaaS lock-in • Metrics + Logs + Traces</p>
  </div>
</section>

<section class="section section-alt" id="benefits">
  <div class="container">
    <h2 class="section-title" data-i18n="benefits.title">Why teams choose Rhinometric</h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="benefits.card1.title">Data sovereignty</h3>
        <p data-i18n="benefits.card1.text">Data stays inside your infrastructure (no SaaS ingestion).</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="benefits.card2.title">Unified signals</h3>
        <p data-i18n="benefits.card2.text">Unified signals: metrics, logs, and traces in one stack.</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="benefits.card3.title">Faster triage</h3>
        <p data-i18n="benefits.card3.text">Faster triage with guided dashboards and anomaly signals. Predictable operations and retention under your control. Designed for compliance-driven and security-sensitive teams.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="how-it-works">
  <div class="container">
    <h2 class="section-title" data-i18n="deploy.title">Deploy fast. Operate with confidence.</h2>
    <div class="grid steps-grid">
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3 data-i18n="deploy.card1.title">Automated installer</h3>
        <p data-i18n="deploy.card1.text">Automated installer validates requirements and checks ports.</p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3 data-i18n="deploy.card2.title">Secure configuration</h3>
        <p data-i18n="deploy.card2.text">Generates secure credentials and configuration files.</p>
      </div>
      <div class="card">
        <span class="step-icon" aria-hidden="true"></span>
        <h3 data-i18n="deploy.card3.title">Docker Compose + health checks</h3>
        <p data-i18n="deploy.card3.text">Bootstraps the stack via Docker Compose. Runs health checks to confirm the platform is ready.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="roadmap">
  <div class="container">
    <h2 class="section-title" data-i18n="roadmap.title">Roadmap (planned)</h2>
    <div class="timeline">
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3 data-i18n="roadmap.now.title">Now</h3>
          <p data-i18n="roadmap.now.text">Early access & validation</p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3 data-i18n="roadmap.next1.title">Next</h3>
          <p data-i18n="roadmap.next1.text">Guided onboarding & dashboards</p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3 data-i18n="roadmap.next2.title">Next</h3>
          <p data-i18n="roadmap.next2.text">Automated reporting & deeper integrations</p>
        </div>
      </div>
      <div class="timeline-item">
        <span class="timeline-dot" aria-hidden="true"></span>
        <div>
          <h3 data-i18n="roadmap.later.title">Later</h3>
          <p data-i18n="roadmap.later.text">More self-serve workflows for non-expert users</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt early-access" id="early-access">
  <div class="container">
    <div class="card">
      <span class="early-access-tag" data-i18n="early.tag">Early Access</span>
      <h2 class="section-title" data-i18n="early.title">Early Adopter Program (3–6 months)</h2>
      <p class="section-lead" data-i18n="early.lead">We're onboarding a limited number of on-prem organizations to validate Rhinometric in real environments.</p>
      <ul class="early-list">
        <li data-i18n="early.item1">Full access for 3–6 months at no cost</li>
        <li data-i18n="early.item2">Priority onboarding support for installation</li>
        <li data-i18n="early.item3">Direct feedback channel with the team</li>
        <li data-i18n="early.item4">Influence upcoming roadmap priorities</li>
      </ul>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com" data-i18n="early.cta">Join the program: rafael.canelon@rhinometric.com</a>
    </div>
  </div>
</section>

<section class="section" id="who-its-for">
  <div class="container">
    <h2 class="section-title" data-i18n="audience.title">Built for teams that can't compromise on control</h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="audience.card1.title">Regulated industries</h3>
        <p data-i18n="audience.card1.text">Finance, healthcare, government.</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="audience.card2.title">DevOps/SRE teams</h3>
        <p data-i18n="audience.card2.text">Operating on-prem infrastructure.</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <h3 data-i18n="audience.card3.title">Data sovereignty</h3>
        <p data-i18n="audience.card3.text">Organizations avoiding SaaS observability due to data sovereignty.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="out-of-the-box">
  <div class="container">
    <h2 class="section-title" data-i18n="ootb.title">What you get out of the box</h2>
    <p class="section-lead" data-i18n="ootb.lead">A curated on-prem observability stack — packaged, configured, and ready to run inside your infrastructure.</p>
    <div class="tabs" data-tabs>
      <div class="tab-list" role="tablist" aria-label="Technical tabs" data-i18n="tabs.aria" data-i18n-attr="aria-label">
        <button class="tab-button is-active" role="tab" aria-selected="true" aria-controls="tab-metrics" id="tab-btn-metrics" data-i18n="tabs.metrics.label">Metrics</button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-logs" id="tab-btn-logs" data-i18n="tabs.logs.label">Logs</button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-traces" id="tab-btn-traces" data-i18n="tabs.traces.label">Traces</button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-alerts" id="tab-btn-alerts" data-i18n="tabs.visualization.label">Visualization</button>
        <button class="tab-button" role="tab" aria-selected="false" aria-controls="tab-ai" id="tab-btn-ai" data-i18n="tabs.ai.label">AI</button>
      </div>
      <div class="tab-panel is-active" role="tabpanel" id="tab-metrics" aria-labelledby="tab-btn-metrics">
        <ul>
          <li data-i18n="tabs.metrics.item1">Metrics — Prometheus + exporters: Collect infrastructure and service metrics with proven standards, ready for Grafana dashboards.</li>
          <li data-i18n="tabs.metrics.item2">Storage & performance layer — PostgreSQL + Redis: Reliable persistence and performance foundations included as part of the stack.</li>
        </ul>
        <p class="section-note" data-i18n="tabs.metrics.tooling">Tooling: Prometheus.</p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-logs" aria-labelledby="tab-btn-logs">
        <ul>
          <li data-i18n="tabs.logs.item1">Logs — Loki + Promtail: Centralize and query logs across services without jumping between servers.</li>
          <li data-i18n="tabs.logs.item2">Automated backups (platform-level): Backup mechanisms included to protect your observability data and configuration.</li>
        </ul>
        <p class="section-note" data-i18n="tabs.logs.tooling">Tooling: Loki.</p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-traces" aria-labelledby="tab-btn-traces">
        <ul>
          <li data-i18n="tabs.traces.item1">Traces — Jaeger distributed tracing: Follow a request across microservices and pinpoint latency bottlenecks or failing components.</li>
          <li data-i18n="tabs.traces.item2">Rhinometric Console: A simplified control plane for platform health, license visibility, and quick access to the stack.</li>
        </ul>
        <p class="section-note" data-i18n="tabs.traces.tooling">Tooling: Jaeger.</p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-alerts" aria-labelledby="tab-btn-alerts">
        <ul>
          <li data-i18n="tabs.visual.item1">Dashboards — Grafana preloaded views: Start diagnosing faster with guided dashboards and a unified navigation experience.</li>
          <li data-i18n="tabs.visual.item2">The Rhino Guide: Step-by-step deployment and operational documentation to keep your team autonomous from day one.</li>
        </ul>
        <p class="section-note" data-i18n="tabs.visual.tooling">Tooling: Grafana.</p>
      </div>
      <div class="tab-panel" role="tabpanel" id="tab-ai" aria-labelledby="tab-btn-ai">
        <ul>
          <li data-i18n="tabs.ai.item1">AI-assisted anomaly signals (early): Surface unusual patterns across Prometheus metrics to reduce alert noise and speed up triage.</li>
          <li data-i18n="tabs.ai.item2">Rhinometric highlights anomalies and trends so teams can investigate faster — without sending data outside your network.</li>
        </ul>
        <p class="section-note" data-i18n="tabs.ai.tooling">Tooling: Prometheus (signals) + Grafana (visualization).</p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="expected-outcomes">
  <div class="container">
    <h2 class="section-title" data-i18n="outcomes.title">Installation support. Operational autonomy.</h2>
    <div class="grid benefits-grid">
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p data-i18n="outcomes.card1.text">Our commitment is to keep your observability platform functional and stable.</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p data-i18n="outcomes.card2.text">We provide expert support for the initial deployment and Rhinometric stack reliability. Since Rhinometric is fully on-premise, we don't access customer data.</p>
      </div>
      <div class="card benefit-card">
        <span class="benefit-icon" aria-hidden="true"></span>
        <p data-i18n="outcomes.card3.text">Application-level debugging and incident resolution remain customer-owned — Rhinometric provides the visibility your team needs to act independently.</p>
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

<script src="<?php echo esc_url(get_template_directory_uri() . '/assets/js/frontpage-i18n.js'); ?>"></script>
<?php get_footer(); ?>
