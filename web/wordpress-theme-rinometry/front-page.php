<?php
get_header();
?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div>
      <span class="badge"><?php esc_html_e('Unified Observability Platform', 'rinometry'); ?></span>
        <h1 class="section-title"><?php esc_html_e('Own your observability stack — fully on-premise', 'rinometry'); ?></h1>
        <p class="section-lead"><?php esc_html_e('Unify metrics, logs, and traces inside your infrastructure with full control, fast time-to-value, and no SaaS lock-in.', 'rinometry'); ?></p>
        <p class="section-note"><?php esc_html_e('On-prem. Unified metrics, logs, and traces. No vendor lock-in.', 'rinometry'); ?></p>
        <ul class="hero-bullets">
          <li><?php esc_html_e('Data sovereignty: nothing leaves your network.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Fast time-to-value: dashboards from day one.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Predictable cost: no SaaS billing surprises.', 'rinometry'); ?></li>
        </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
          <?php esc_html_e('Download Rhinometric', 'rinometry'); ?>
        </a>
        <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('request-demo'))); ?>">
          <?php esc_html_e('Request a demo', 'rinometry'); ?>
        </a>
      </div>
      <p class="trust-strip">
        <?php esc_html_e('On-premise • No SaaS lock-in • Metrics + Logs + Traces • Prometheus • Grafana • Loki • Jaeger • OpenTelemetry', 'rinometry'); ?>
      </p>
    </div>
    <div class="hero-card hero-visual" aria-label="<?php esc_attr_e('Rhinometric hero logo', 'rinometry'); ?>">
      <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="<?php esc_attr_e('Rhinometric logo illustration', 'rinometry'); ?>" onerror="this.onerror=null;this.src='<?php echo esc_url(get_template_directory_uri() . '/assets/img/hero-illustration.svg'); ?>';">
      <h2><?php esc_html_e('Why teams choose Rhinometric', 'rinometry'); ?></h2>
      <div class="mini-card-grid">
        <div class="mini-card">
          <span class="mini-icon" aria-hidden="true"></span>
            <span><?php esc_html_e('Unified signals across metrics, logs, and traces.', 'rinometry'); ?></span>
        </div>
        <div class="mini-card">
          <span class="mini-icon" aria-hidden="true"></span>
            <span><?php esc_html_e('On-prem by design for regulated environments.', 'rinometry'); ?></span>
        </div>
        <div class="mini-card">
          <span class="mini-icon" aria-hidden="true"></span>
            <span><?php esc_html_e('Operational clarity with Grafana + License UI.', 'rinometry'); ?></span>
        </div>
        <div class="mini-card">
          <span class="mini-icon" aria-hidden="true"></span>
            <span><?php esc_html_e('Anomaly detection to reduce noise and speed triage.', 'rinometry'); ?></span>
          </div>
          <div class="mini-card">
            <span class="mini-icon" aria-hidden="true"></span>
            <span><?php esc_html_e('Safe by architecture: observes, not in the transaction path.', 'rinometry'); ?></span>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="features">
  <div class="container">
      <h2 class="section-title"><?php esc_html_e('What you get out of the box', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('A production-ready stack with core observability services and operational tooling included.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
          <h3><?php esc_html_e('Metrics', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Prometheus + Node Exporter + cAdvisor for host and container visibility.', 'rinometry'); ?></p>
      </div>
      <div class="card">
          <h3><?php esc_html_e('Logs', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Loki + Promtail for centralized, queryable logs.', 'rinometry'); ?></p>
      </div>
      <div class="card">
          <h3><?php esc_html_e('Traces', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Jaeger for tracing (OTLP compatible).', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Dashboards', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Grafana dashboards for infrastructure, containers, and stack health.', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Operational UI', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Grafana UI + License UI for access and operational status.', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Anomaly engine', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Local ML service to flag unusual behavior and reduce alert fatigue.', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Automated backups', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Scheduled backups for Prometheus, Loki, Jaeger, Grafana, and Postgres.', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Compose packaging', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Docker Compose packaging with healthchecks and secure .env defaults.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="deployment">
  <div class="container split">
    <div>
        <h2 class="section-title"><?php esc_html_e('Deployment', 'rinometry'); ?></h2>
        <p class="section-lead"><?php esc_html_e('Deploy in your environment, not ours. Use compose-based installs with healthchecks and secure .env configuration.', 'rinometry'); ?></p>
      <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('observability-suite'))); ?>">
        <?php esc_html_e('Explore the suite', 'rinometry'); ?>
      </a>
    </div>
    <div class="card">
        <h3><?php esc_html_e('Who it’s for', 'rinometry'); ?></h3>
      <ul>
          <li><?php esc_html_e('DevOps, SRE, and platform teams.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Regulated organizations with data sovereignty needs.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Teams replacing SaaS monitoring with on-prem control.', 'rinometry'); ?></li>
      </ul>
    </div>
  </div>
</section>

<section class="section" id="integrations">
  <div class="container">
      <h2 class="section-title"><?php esc_html_e('Download vs. request a demo', 'rinometry'); ?></h2>
      <p class="section-lead"><?php esc_html_e('Choose the path that fits your evaluation needs—hands-on access or guided review.', 'rinometry'); ?></p>
      <div class="grid">
        <div class="card">
          <h3><?php esc_html_e('Download (Early Access)', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Get early access. Deploy on-prem and share feedback to shape the roadmap.', 'rinometry'); ?></p>
          <a class="btn btn-primary" href="<?php echo esc_url(get_permalink(get_page_by_path('download'))); ?>">
            <?php esc_html_e('Download Rhinometric', 'rinometry'); ?>
          </a>
          <p class="section-note"><?php esc_html_e('Early access (3–6 months) + feedback-driven validation', 'rinometry'); ?></p>
        </div>
        <div class="card">
          <h3><?php esc_html_e('Request a demo', 'rinometry'); ?></h3>
          <p><?php esc_html_e('Guided evaluation for enterprise, security, and compliance stakeholders.', 'rinometry'); ?></p>
          <a class="btn btn-secondary" href="<?php echo esc_url(get_permalink(get_page_by_path('request-demo'))); ?>">
            <?php esc_html_e('Request a demo', 'rinometry'); ?>
          </a>
          <p class="section-note"><?php esc_html_e('Guided evaluation for security/compliance and enterprise fit', 'rinometry'); ?></p>
        </div>
      </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Integrations & tooling', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Out of the box: Prometheus + Grafana + Loki + Jaeger (Traces: Jaeger, OTLP compatible).', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-otel.svg'); ?>" alt="<?php esc_attr_e('OpenTelemetry icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('OpenTelemetry pipelines', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Ingest standardized telemetry through OpenTelemetry collectors to preserve context across metrics, logs, and traces.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-prometheus.svg'); ?>" alt="<?php esc_attr_e('Prometheus icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Metrics ecosystems', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Connect Prometheus-style metrics pipelines and reuse existing alerting rules when appropriate.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/integration-logging.svg'); ?>" alt="<?php esc_attr_e('Logging icon placeholder', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Logs and traces stack', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Stream logs and traces into Rhinometric to unify troubleshooting and retention governance.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('Roadmap (planned)', 'rinometry'); ?></h2>
    <p class="section-lead"><?php esc_html_e('Planned improvements without fixed dates or pricing commitments.', 'rinometry'); ?></p>
    <ul>
      <li><?php esc_html_e('Guided dashboards and operational playbooks.', 'rinometry'); ?></li>
      <li><?php esc_html_e('Reporting automation and executive summaries.', 'rinometry'); ?></li>
      <li><?php esc_html_e('Expanded integrations for regulated environments.', 'rinometry'); ?></li>
    </ul>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php esc_html_e('FAQ', 'rinometry'); ?></h2>
    <div class="grid">
      <div class="card">
        <h3><?php esc_html_e('Is Rhinometric SaaS?', 'rinometry'); ?></h3>
        <p><?php esc_html_e('No. Rhinometric is deployed on-premise within your environment.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('What data leaves the environment?', 'rinometry'); ?></h3>
        <p><?php esc_html_e('By default, nothing. Telemetry stays inside your network.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('How long does deployment take?', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Deployment time depends on your environment. The compose package is designed for fast setup.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('Can I start small and scale?', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Yes. Start with core services and expand when ready.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h3><?php esc_html_e('What’s included in early access?', 'rinometry'); ?></h3>
        <p><?php esc_html_e('Hands-on deployment, direct feedback loop, and roadmap influence.', 'rinometry'); ?></p>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
