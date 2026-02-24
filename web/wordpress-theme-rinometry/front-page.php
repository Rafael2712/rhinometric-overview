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
    'hero_h1'       => ['en' => 'Detect what\'s abnormal.<br>Understand it in seconds.', 'es' => 'Detecta lo anormal.<br>Entiéndelo en segundos.'],
    'hero_lead'     => ['en' => 'Rhinometric identifies behavioral deviations across your metrics and connects them with logs and traces — so your team can diagnose faster, with full operational context in one place.', 'es' => 'Rhinometric identifica desviaciones de comportamiento en tus métricas y las conecta con logs y trazas — para que tu equipo diagnostique más rápido, con contexto operativo completo en un solo lugar.'],
    'hero_trust'    => ['en' => 'One operational interface. Correlated signals. Faster decisions.', 'es' => 'Una interfaz operativa. Señales correlacionadas. Decisiones más rápidas.'],
    'hero_cta_1'    => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
    'hero_cta_2'    => ['en' => 'Explore the Platform', 'es' => 'Explorar la plataforma'],

    /* ---- Unified Operational Interface (7 capabilities) ---- */
    'ops_title'     => ['en' => 'From scattered signals to guided investigation', 'es' => 'De señales dispersas a investigación guiada'],
    'ops_lead'      => ['en' => 'Dashboards show data. Alerts show symptoms. But when behavior starts to deviate, teams switch between tools to understand what is happening — metrics in one place, logs in another, traces somewhere else. Context gets fragmented. Investigation slows down. Rhinometric detects abnormal behavior using statistical baselines and anomaly models, then guides you through correlated metrics, logs, and traces in a single operational interface.', 'es' => 'Los dashboards muestran datos. Las alertas muestran síntomas. Pero cuando el comportamiento empieza a desviarse, los equipos alternan entre herramientas para entender qué está pasando — métricas en un lugar, logs en otro, trazas en otro. El contexto se fragmenta. La investigación se ralentiza. Rhinometric detecta comportamiento anormal usando líneas base estadísticas y modelos de anomalías, y te guía a través de métricas, logs y trazas correlacionadas en una interfaz operativa única.'],
    'ops_hint'      => ['en' => 'Swipe →', 'es' => 'Desliza →'],
    'ops_1_t'       => ['en' => 'Anomaly Detection', 'es' => 'Detección de anomalías'],
    'ops_1_d'       => ['en' => 'Identifies behavioral deviations against statistical baselines. The starting point of every investigation.', 'es' => 'Identifica desviaciones de comportamiento contra líneas base estadísticas. El punto de partida de cada investigación.'],
    'ops_2_t'       => ['en' => 'Dashboards', 'es' => 'Dashboards'],
    'ops_2_d'       => ['en' => 'See the deviation in context. Grafana dashboards show what changed and when.', 'es' => 'Visualiza la desviación en contexto. Los dashboards de Grafana muestran qué cambió y cuándo.'],
    'ops_3_t'       => ['en' => 'Alerts', 'es' => 'Alertas'],
    'ops_3_d'       => ['en' => 'Alertmanager routes threshold-based alerts. Anomaly signals add behavioral context.', 'es' => 'Alertmanager enruta alertas basadas en umbrales. Las señales de anomalía añaden contexto de comportamiento.'],
    'ops_4_t'       => ['en' => 'Logs', 'es' => 'Logs'],
    'ops_4_d'       => ['en' => 'Inspect correlated logs via Loki — filtered to the time window and services involved.', 'es' => 'Inspecciona logs correlacionados con Loki — filtrados al intervalo de tiempo y servicios involucrados.'],
    'ops_5_t'       => ['en' => 'Traces', 'es' => 'Trazas'],
    'ops_5_d'       => ['en' => 'Explore distributed traces with Jaeger to follow requests across services and pinpoint root cause.', 'es' => 'Explora trazas distribuidas con Jaeger para seguir peticiones entre servicios e identificar la causa raíz.'],
    'ops_6_t'       => ['en' => 'Metrics', 'es' => 'Métricas'],
    'ops_6_d'       => ['en' => 'Access related metrics instantly. Prometheus + VictoriaMetrics for collection and long-term retention.', 'es' => 'Accede a métricas relacionadas de inmediato. Prometheus + VictoriaMetrics para recolección y retención a largo plazo.'],
    'ops_7_t'       => ['en' => 'Notifications', 'es' => 'Notificaciones'],
    'ops_7_d'       => ['en' => 'Email and Slack notifications tied to anomaly and alert events. Keep teams aligned in real time.', 'es' => 'Notificaciones por Email y Slack vinculadas a eventos de anomalías y alertas. Mantén al equipo alineado en tiempo real.'],
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
