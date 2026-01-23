<?php get_header(); ?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div class="hero-brand" aria-hidden="true">
      <img class="hero-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="" />
    </div>
    <div class="hero-copy hero-content">
      <span class="badge" data-i18n="hero.badge">Motor On-Prem Observability</span>
      <h1 class="section-title" data-i18n="hero.title">Observabilidad On-Premise: Tu Infraestructura, Tus Reglas.</h1>
      <p class="section-lead" data-i18n="hero.lead">Despliega en minutos un stack profesional de métricas, logs y trazas. Sin datos saliendo de tu red, sin cargos por transferencia de nube y con soberanía total.</p>
      <ul class="hero-bullets">
        <li data-i18n="hero.bullet1">Motor instalado en tu DC o edge, listo para producción.</li>
        <li data-i18n="hero.bullet2">Costos predecibles: cero cloud egress, cero sorpresas.</li>
        <li data-i18n="hero.bullet3">Cumplimiento y control operativo bajo tus propias reglas.</li>
      </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="#early-access" data-i18n="hero.ctaPrimary">Programa Early Adopter</a>
        <a class="btn btn-secondary" href="#out-of-the-box" data-i18n="hero.ctaSecondary">Especificaciones Técnicas</a>
      </div>
    </div>
  </div>
</section>

<section class="how-it-works" id="how-it-works" aria-label="How it works" data-i18n="how.aria" data-i18n-attr="aria-label">
  <div class="container">
    <div class="how-steps" role="list">
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--deploy" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step1.label">One-Command Deploy</p>
          <p class="how-step-text" data-i18n="how.step1.text">Deploy the full stack on your infrastructure via Docker in minutes.</p>
        </div>
      </div>
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--ingest" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step2.label">Local Ingestion</p>
          <p class="how-step-text" data-i18n="how.step2.text">Your metrics and logs are collected and processed locally. Nothing leaves your network.</p>
        </div>
      </div>
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--insight" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step3.label">Private Insights</p>
          <p class="how-step-text" data-i18n="how.step3.text">Visualize and analyze your data with total sovereignty and zero latency.</p>
        </div>
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

<section class="section section-alt" id="out-of-the-box">
  <div class="container">
    <h2 class="section-title" data-i18n="engine.title">The Full-Stack Observability Engine.</h2>
    <p class="section-lead" data-i18n="engine.lead">Everything you need to monitor, trace, and secure your private infrastructure—pre-configured for production and absolute data sovereignty.</p>
    <div class="feature-showcase" data-feature-tabs>
      <div class="feature-nav" role="tablist" aria-label="Technical tabs" data-i18n="tabs.aria" data-i18n-attr="aria-label">
        <button type="button" class="feature-tab is-active" role="tab" aria-selected="true" aria-controls="feature-panel-metrics" id="feature-tab-metrics" data-feature-tab="feature-panel-metrics">
          <span class="feature-tab-icon feature-tab-icon--metrics" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.metrics.label">Metrics</span>
            <span class="feature-tab-point" data-i18n="tabs.metrics.point1">Infrastructure & Service Health — Prometheus: High-density monitoring based on industry standards, optimized to detect failures in milliseconds.</span>
            <span class="feature-tab-point" data-i18n="tabs.metrics.point2">High-Performance Persistence — PostgreSQL + Redis: Pre-configured storage layers for ultra-fast queries and total data reliability.</span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-logs" id="feature-tab-logs" data-feature-tab="feature-panel-logs">
          <span class="feature-tab-icon feature-tab-icon--logs" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.logs.label">Logs</span>
            <span class="feature-tab-point" data-i18n="tabs.logs.point1">Private Log Centralization — Loki: Index terabytes of logs without a single byte leaving your network or incurring cloud egress fees.</span>
            <span class="feature-tab-point" data-i18n="tabs.logs.point2">Full-Text Intelligence: Search and filter data in real-time for audits, security, and critical troubleshooting.</span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-traces" id="feature-tab-traces" data-feature-tab="feature-panel-traces">
          <span class="feature-tab-icon feature-tab-icon--traces" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.traces.label">Traces</span>
            <span class="feature-tab-point" data-i18n="tabs.traces.point1">Microservices Visibility — Jaeger: Identify bottlenecks and latent failures in distributed systems with native tracing.</span>
            <span class="feature-tab-point" data-i18n="tabs.traces.point2">Dependency Mapping: Visualize service interactions to find the root cause of errors in seconds.</span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-visual" id="feature-tab-visual" data-feature-tab="feature-panel-visual">
          <span class="feature-tab-icon feature-tab-icon--visual" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.visualization.label">Visualization</span>
            <span class="feature-tab-point" data-i18n="tabs.visual.point1">Decision-Ready Dashboards — Grafana: Visual intelligence with factory-optimized panels for instant visibility.</span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-ai" id="feature-tab-ai" data-feature-tab="feature-panel-ai">
          <span class="feature-tab-icon feature-tab-icon--ai" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.ai.label">AI</span>
            <span class="feature-tab-point" data-i18n="tabs.ai.point1">Proactive Anomaly Detection: Smart engine that identifies deviations and unusual patterns before they turn into service outages.</span>
          </div>
        </button>
      </div>
      <div class="feature-display">
        <div class="feature-panel is-active" id="feature-panel-metrics" role="tabpanel" aria-labelledby="feature-tab-metrics">
          <div class="feature-badge" data-i18n="feature.badge">100% Private / On-Premise</div>
          <div class="feature-visual feature-visual--metrics">
            <div class="visual-dashboard">
              <div class="visual-gauge"></div>
              <div class="visual-gauge visual-gauge--secondary"></div>
              <div class="visual-bars">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.metrics.caption">Dark-mode Grafana dashboards with live CPU/RAM gauges tuned for private fleets.</p>
        </div>
        <div class="feature-panel" id="feature-panel-logs" role="tabpanel" aria-labelledby="feature-tab-logs">
          <div class="feature-badge" data-i18n="feature.badge">100% Private / On-Premise</div>
          <div class="feature-visual feature-visual--logs">
            <div class="visual-terminal">
              <div class="terminal-line"></div>
              <div class="terminal-line"></div>
              <div class="terminal-line terminal-line--highlight"></div>
              <div class="terminal-line"></div>
              <div class="terminal-line"></div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.logs.caption">Private Loki console with streaming ERROR filters and zero cloud egress.</p>
        </div>
        <div class="feature-panel" id="feature-panel-traces" role="tabpanel" aria-labelledby="feature-tab-traces">
          <div class="feature-badge" data-i18n="feature.badge">100% Private / On-Premise</div>
          <div class="feature-visual feature-visual--traces">
            <div class="visual-graph">
              <span class="graph-node graph-node--main"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.traces.caption">Jaeger dependency map connecting critical microservices across air-gapped clusters.</p>
        </div>
        <div class="feature-panel" id="feature-panel-visual" role="tabpanel" aria-labelledby="feature-tab-visual">
          <div class="feature-badge" data-i18n="feature.badge">100% Private / On-Premise</div>
          <div class="feature-visual feature-visual--visual">
            <div class="visual-panels">
              <div class="panel-row">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="panel-row panel-row--wide"></div>
              <div class="panel-row">
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.visual.caption">Factory-optimized Grafana layouts with Rhinometric navigation and theming.</p>
        </div>
        <div class="feature-panel" id="feature-panel-ai" role="tabpanel" aria-labelledby="feature-tab-ai">
          <div class="feature-badge" data-i18n="feature.badge">100% Private / On-Premise</div>
          <div class="feature-visual feature-visual--ai">
            <div class="visual-anomaly">
              <span class="anomaly-baseline"></span>
              <span class="anomaly-spike"></span>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.ai.caption">Baseline signals with highlighted anomaly spikes and Rhino alert overlays.</p>
        </div>
      </div>
    </div>
    <p class="engine-footnote" data-i18n="engine.footnote">Based on open standards. Zero vendor lock-in. Air-Gapped Ready. You own your configuration forever.</p>
  </div>
</section>

<section class="section" id="critical-sectors">
  <div class="container">
    <h2 class="section-title" data-i18n="critical.title">Built for critical sectors</h2>
    <p class="section-lead" data-i18n="critical.body">Built for zero-risk tolerance sectors. If your company operates in Fintech, Health, Defense, or Industrial IoT, Rhinometric guarantees that 100% of telemetry stays on your servers. Regulatory compliance (GDPR/HIPAA) and total security in Air-Gapped environments.</p>
  </div>
</section>

<section class="section section-alt" id="installation-support">
  <div class="container">
    <h2 class="section-title" data-i18n="install.title">Installation support & autonomy</h2>
    <p class="section-lead" data-i18n="install.body">We build the engine; you keep the keys. We guarantee a perfect setup and stack stability. With the included Rhino Guide, your team gains the knowledge to operate with full independence, eliminating reliance on external consulting.</p>
  </div>
</section>

<section class="section" id="why-rhinometric">
  <div class="container">
    <h2 class="section-title" data-i18n="why.title">Why choose Rhinometric</h2>
    <ul class="early-list">
      <li data-i18n="why.item1">Zero Cloud Egress Fees: Save thousands by eliminating the cost of transferring data to external clouds.</li>
      <li data-i18n="why.item2">No Vendor Lock-in: Based on open standards. You own the software and the configuration forever.</li>
      <li data-i18n="why.item3">Time-to-Market: What takes a senior team months to configure, we deliver in an afternoon.</li>
    </ul>
  </div>
</section>

<section class="section section-alt early-access" id="early-access">
  <div class="container">
    <div class="card">
      <span class="early-access-tag" data-i18n="early.tag">Early Access</span>
      <h2 class="section-title" data-i18n="early.title">Looking for the first 10 pioneers.</h2>
      <p class="section-lead" data-i18n="early.lead">Be part of the Rhinometric launch. We offer 3 months of full access and priority deployment support for free in exchange for your technical feedback. Secure your infrastructure today.</p>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com" data-i18n="early.cta">Apply to Program - 10 Spots Available</a>
    </div>
  </div>
</section>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-feature-tabs]').forEach(function (container) {
      var tabs = container.querySelectorAll('.feature-tab');
      var panels = container.querySelectorAll('.feature-panel');

      function activate(tab) {
        if (!tab || tab.classList.contains('is-active')) {
          return;
        }
        tabs.forEach(function (btn) {
          btn.classList.remove('is-active');
          btn.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('is-active');
        tab.setAttribute('aria-selected', 'true');

        var targetId = tab.getAttribute('data-feature-tab');
        panels.forEach(function (panel) {
          if (panel.id === targetId) {
            panel.classList.add('is-active');
            panel.removeAttribute('aria-hidden');
          } else {
            panel.classList.remove('is-active');
            panel.setAttribute('aria-hidden', 'true');
          }
        });
      }

      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          activate(tab);
        });
        tab.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            activate(tab);
          }
        });
      });

      panels.forEach(function (panel) {
        if (!panel.classList.contains('is-active')) {
          panel.setAttribute('aria-hidden', 'true');
        }
      });
    });
  });
</script>

<script src="<?php echo esc_url(get_template_directory_uri() . '/assets/js/frontpage-i18n.js'); ?>"></script>
<?php get_footer(); ?>
