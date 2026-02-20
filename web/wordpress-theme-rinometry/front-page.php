<?php
/**
 * front-page.php — Rhinometric v3.2
 * 5-block compact homepage with full EN/ES i18n.
 * Blocks: Hero · What is it · Why on-prem · Deployment & Security · CTA final
 */

get_header();

$lang = rinometry_get_current_language();

/* ================================================================
   i18n string catalogue (compact — detail lives in child pages)
   ================================================================ */
$t = [
    /* ---- Hero ---- */
    'hero_h1'       => ['en' => 'AI-powered observability.<br>One interface. Zero integration.', 'es' => 'Observabilidad potenciada por IA.<br>Una interfaz. Cero integración.'],
    'hero_lead'     => ['en' => 'Rhinometric delivers dashboards, AI-guided anomaly detection, alerts, logs, and traces — pre-integrated and production-ready. Connect your services and operate. No glue code, no consulting projects.', 'es' => 'Rhinometric ofrece dashboards, detección de anomalías guiada por IA, alertas, logs y trazas — pre-integrado y listo para producción. Conecta tus servicios y opera. Sin código de pegamento, sin proyectos de consultoría.'],
    'hero_trust'    => ['en' => 'Single-tenant. On-premise or dedicated VM in a European cloud provider, under full customer control.', 'es' => 'Single-tenant. On-premise o VM dedicada en un proveedor cloud europeo, bajo control total del cliente.'],
    'hero_cta_1'    => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
    'hero_cta_2'    => ['en' => 'Explore the Platform', 'es' => 'Explorar la plataforma'],

    /* ---- Unified Operational Interface (7 capabilities) ---- */
    'ops_title'     => ['en' => 'Unified Operational Interface', 'es' => 'Interfaz Operativa Unificada'],
    'ops_lead'      => ['en' => 'AI-assisted anomaly detection is the core of Rhinometric. Connect your telemetry once and operate everything from one console — dashboards, alerts, logs, traces, metrics, and notifications — without months of integration work.', 'es' => 'La detección de anomalías asistida por IA es el corazón de Rhinometric. Conecta tu telemetría una vez y opera todo desde una sola consola — dashboards, alertas, logs, trazas, métricas y notificaciones — sin meses de trabajo de integración.'],
    'ops_hint'      => ['en' => 'Swipe →', 'es' => 'Desliza →'],
    'ops_1_t'       => ['en' => 'AI Anomalies', 'es' => 'Anomalías IA'],
    'ops_1_d'       => ['en' => 'Guided anomaly detection and triage built into the console.', 'es' => 'Detección de anomalías y guía de triage integradas en la consola.'],
    'ops_2_t'       => ['en' => 'Dashboards', 'es' => 'Dashboards'],
    'ops_2_d'       => ['en' => 'Dashboards powered by Grafana — ready to use.', 'es' => 'Dashboards con Grafana — listos para usar.'],
    'ops_3_t'       => ['en' => 'Alerts', 'es' => 'Alertas'],
    'ops_3_d'       => ['en' => 'Alert routing and escalation with Alertmanager.', 'es' => 'Ruteo y escalado de alertas con Alertmanager.'],
    'ops_4_t'       => ['en' => 'Logs', 'es' => 'Logs'],
    'ops_4_d'       => ['en' => 'Centralized logs with Loki for fast, label-based queries.', 'es' => 'Logs centralizados con Loki para consultas rápidas por etiquetas.'],
    'ops_5_t'       => ['en' => 'Traces', 'es' => 'Trazas'],
    'ops_5_d'       => ['en' => 'Distributed tracing with Jaeger to map service dependencies.', 'es' => 'Trazas distribuidas con Jaeger para mapear dependencias entre servicios.'],
    'ops_6_t'       => ['en' => 'Metrics', 'es' => 'Métricas'],
    'ops_6_d'       => ['en' => 'Prometheus collection + VictoriaMetrics for long-term retention and high-performance queries.', 'es' => 'Recolección con Prometheus + VictoriaMetrics para retención a largo plazo y consultas de alto rendimiento.'],
    'ops_7_t'       => ['en' => 'Notifications', 'es' => 'Notificaciones'],
    'ops_7_d'       => ['en' => 'Notifications via Email and Slack to keep teams aligned.', 'es' => 'Notificaciones por Email y Slack para mantener al equipo alineado.'],
    /* ---- Why on-prem / Single-tenant EU ---- */
    'why_title'     => ['en' => 'Why on-prem &amp; single-tenant', 'es' => 'Por qué on-prem y single-tenant'],
    'why_1'         => ['en' => 'Your telemetry never leaves your network — full data sovereignty.', 'es' => 'Tu telemetría nunca sale de tu red — soberanía de datos total.'],
    'why_2'         => ['en' => 'Built on open-source foundations — no vendor lock-in.', 'es' => 'Construido sobre bases open-source — sin vendor lock-in.'],
    'why_3'         => ['en' => 'Pre-integrated platform — no months of setup, no glue code, no consulting engagements.', 'es' => 'Plataforma pre-integrada — sin meses de configuración, sin código de pegamento, sin proyectos de consultoría.'],
    'designed_t'    => ['en' => 'Designed for', 'es' => 'Diseñado para'],
    'designed_1'    => ['en' => 'Organizations requiring infrastructure control and data sovereignty', 'es' => 'Organizaciones que requieren control de infraestructura y soberanía de datos'],
    'designed_2'    => ['en' => 'Teams operating in regulated or sensitive environments', 'es' => 'Equipos que operan en entornos regulados o sensibles'],
    'designed_3'    => ['en' => 'Engineering teams needing full observability without shared SaaS', 'es' => 'Equipos de ingeniería que necesitan observabilidad completa sin SaaS compartido'],

    /* ---- Deployment & Security (merged) ---- */
    'depsec_title'  => ['en' => 'Deployment &amp; Security', 'es' => 'Despliegue y seguridad'],
    'depsec_1'      => ['en' => 'Deploy on-premise or in a dedicated VM within a European cloud provider, under full customer control.', 'es' => 'Despliega on-premise o en una VM dedicada dentro de un proveedor cloud europeo, bajo control total del cliente.'],
    'depsec_2'      => ['en' => 'mTLS everywhere, RBAC with audit trail, EU data residency.', 'es' => 'mTLS en todas las comunicaciones, RBAC con auditoría, residencia de datos en la UE.'],
    'deploy_link'   => ['en' => 'Explore deployment', 'es' => 'Explorar despliegue'],
    'sec_link'      => ['en' => 'Learn about security', 'es' => 'Más sobre seguridad'],

    /* ---- CTA final ---- */
    'cta_title'     => ['en' => 'Ready to take control?', 'es' => '¿Listo para tomar el control?'],
    'cta_lead'      => ['en' => 'Deploy Rhinometric in your infrastructure today. No shared tenancy, no third-party data exposure.', 'es' => 'Despliega Rhinometric en tu infraestructura hoy. Sin multi-tenancy compartida, sin exposición de datos a terceros.'],
    'cta_btn'       => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],

    /* ---- Social (rendered by footer, kept for i18n JS) ---- */
    'social_title'  => ['en' => 'Follow us', 'es' => 'Síguenos'],
];

/**
 * Translate helper.
 */
$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};
?>

<!-- ============================================================
     BLOCK 1 — Hero (compact: H1 + lead + 2 CTAs)
     ============================================================ -->
<section class="hero hero-compact">
  <div class="container hero-inner">
    <h1 data-i18n="hero_h1"><?php echo $__('hero_h1'); ?></h1>
    <p class="hero-lead" data-i18n="hero_lead"><?php echo esc_html($__('hero_lead')); ?></p>
    <p class="hero-trust" data-i18n="hero_trust"><?php echo esc_html($__('hero_trust')); ?></p>
    <div class="hero-cta">
      <a class="btn btn-primary btn-lg" href="<?php echo esc_url(rinometry_page_url('evaluation')); ?>" data-i18n="hero_cta_1">
        <?php echo esc_html($__('hero_cta_1')); ?>
      </a>
      <a class="btn btn-ghost btn-lg" href="<?php echo esc_url(rinometry_page_url('platform')); ?>" data-i18n="hero_cta_2">
        <?php echo esc_html($__('hero_cta_2')); ?>
      </a>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 2 — Unified Operational Interface (carousel / grid)
     ============================================================ -->
<section class="ops-unified">
  <div class="container">
    <h2 class="ops-title" data-i18n="ops_title"><?php echo esc_html($__('ops_title')); ?></h2>
    <p class="ops-lead" data-i18n="ops_lead"><?php echo esc_html($__('ops_lead')); ?></p>
    <p class="ops-swipe-hint" data-i18n="ops_hint"><?php echo esc_html($__('ops_hint')); ?></p>
    <div class="ops-cards">
      <?php
      $ops_icons = ['🤖', '📈', '🔔', '📋', '🔗', '📊', '📧'];
      for ($i = 1; $i <= 7; $i++) : ?>
      <article class="ops-card">
        <div class="ops-icon" aria-hidden="true"><?php echo $ops_icons[$i - 1]; ?></div>
        <h3 data-i18n="ops_<?php echo $i; ?>_t"><?php echo esc_html($__("ops_{$i}_t")); ?></h3>
        <p data-i18n="ops_<?php echo $i; ?>_d"><?php echo esc_html($__("ops_{$i}_d")); ?></p>
      </article>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 3 — Why on-prem / Single-tenant EU (3 bullets)
     ============================================================ -->
<section class="section section-compact section-alt">
  <div class="container">
    <h2 class="section-title" data-i18n="why_title"><?php echo $__('why_title'); ?></h2>
    <ul class="check-list">
      <li data-i18n="why_1"><?php echo esc_html($__('why_1')); ?></li>
      <li data-i18n="why_2"><?php echo esc_html($__('why_2')); ?></li>
      <li data-i18n="why_3"><?php echo esc_html($__('why_3')); ?></li>
    </ul>
    <h3 class="subsection-title" data-i18n="designed_t"><?php echo esc_html($__('designed_t')); ?></h3>
    <ul class="check-list">
      <li data-i18n="designed_1"><?php echo esc_html($__('designed_1')); ?></li>
      <li data-i18n="designed_2"><?php echo esc_html($__('designed_2')); ?></li>
      <li data-i18n="designed_3"><?php echo esc_html($__('designed_3')); ?></li>
    </ul>
  </div>
</section>

<!-- ============================================================
     BLOCK 4 — Deployment & Security (merged)
     ============================================================ -->
<section class="section section-compact">
  <div class="container">
    <h2 class="section-title" data-i18n="depsec_title"><?php echo $__('depsec_title'); ?></h2>
    <ul class="check-list">
      <li data-i18n="depsec_1"><?php echo esc_html($__('depsec_1')); ?></li>
      <li data-i18n="depsec_2"><?php echo esc_html($__('depsec_2')); ?></li>
    </ul>
    <div class="section-links">
      <a class="btn btn-outline btn-sm" href="<?php echo esc_url(rinometry_page_url('deployment')); ?>" data-i18n="deploy_link"><?php echo esc_html($__('deploy_link')); ?> &rarr;</a>
      <a class="btn btn-outline btn-sm" href="<?php echo esc_url(rinometry_page_url('security')); ?>" data-i18n="sec_link"><?php echo esc_html($__('sec_link')); ?> &rarr;</a>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 5 — CTA final
     ============================================================ -->
<section class="section section-compact section-dark cta-section">
  <div class="container text-center">
    <h2 data-i18n="cta_title"><?php echo esc_html($__('cta_title')); ?></h2>
    <p class="cta-lead" data-i18n="cta_lead"><?php echo esc_html($__('cta_lead')); ?></p>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('evaluation')); ?>" data-i18n="cta_btn">
      <?php echo esc_html($__('cta_btn')); ?>
    </a>
  </div>
</section>

<!-- ============================================================
     i18n bootstrap: expose strings to JS for dynamic language switch
     ============================================================ -->
<script>
window.__RHINO_I18N__ = window.__RHINO_I18N__ || {};
window.__RHINO_I18N__.currentLang = <?php echo wp_json_encode($lang); ?>;
window.__RHINO_I18N__.strings = <?php echo wp_json_encode(
    array_map(function ($v) { return $v; }, $t)
); ?>;
</script>

<?php get_footer(); ?>
