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
    'hero_h1'       => ['en' => 'Your infrastructure.<br>Your data.<br>Your control.', 'es' => 'Tu infraestructura.<br>Tus datos.<br>Tu control.'],
    'hero_lead'     => ['en' => 'Deploy on-premise or in a dedicated VM within a European public cloud environment, under full customer control.', 'es' => 'Despliega on-premise o en una VM dedicada dentro de un entorno de nube pública europeo, bajo control total del cliente.'],
    'hero_trust'    => ['en' => 'No shared tenancy. No third-party SaaS data exposure.', 'es' => 'Sin multi-tenancy compartida. Sin exposición de datos a un SaaS de terceros.'],
    'hero_cta_1'    => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
    'hero_cta_2'    => ['en' => 'Explore the Platform', 'es' => 'Explorar la plataforma'],

    /* ---- What is it ---- */
    'what_title'    => ['en' => 'What is Rhinometric', 'es' => 'Qué es Rhinometric'],
    'what_lead'     => ['en' => 'Rhinometric unifies metrics, logs, and traces in one operational view. Built on Prometheus + VictoriaMetrics (metrics), Loki (logs), Jaeger (traces), and Grafana (visualization).', 'es' => 'Rhinometric unifica métricas, logs y trazas en una sola vista operativa. Construido sobre Prometheus + VictoriaMetrics (métricas), Loki (logs), Jaeger (trazas) y Grafana (visualización).'],
    'what_1_t'      => ['en' => 'Metrics', 'es' => 'Métricas'],
    'what_1_d'      => ['en' => 'Prometheus + VictoriaMetrics collection with Grafana dashboards.', 'es' => 'Recolección con Prometheus + VictoriaMetrics y dashboards Grafana.'],
    'what_2_t'      => ['en' => 'Logs', 'es' => 'Logs'],
    'what_2_d'      => ['en' => 'Centralized log aggregation via Loki.', 'es' => 'Agregación centralizada de logs con Loki.'],
    'what_3_t'      => ['en' => 'Traces', 'es' => 'Trazas'],
    'what_3_d'      => ['en' => 'Distributed tracing with Jaeger service maps. AI-assisted anomaly detection to surface unusual patterns and reduce alert noise.', 'es' => 'Trazas distribuidas con mapas de servicios Jaeger. Detección de anomalías asistida por IA para identificar patrones inusuales y reducir el ruido de alertas.'],
    /* ---- Why on-prem / Single-tenant EU ---- */
    'why_title'     => ['en' => 'Why on-prem &amp; single-tenant', 'es' => 'Por qué on-prem y single-tenant'],
    'why_1'         => ['en' => 'Your telemetry never leaves your network — full data sovereignty.', 'es' => 'Tu telemetría nunca sale de tu red — soberanía de datos total.'],
    'why_2'         => ['en' => 'Built on open-source foundations — no vendor lock-in.', 'es' => 'Construido sobre bases open-source — sin vendor lock-in.'],
    'designed_t'    => ['en' => 'Designed for', 'es' => 'Diseñado para'],
    'designed_1'    => ['en' => 'Organizations requiring infrastructure control and data sovereignty', 'es' => 'Organizaciones que requieren control de infraestructura y soberanía de datos'],
    'designed_2'    => ['en' => 'Teams operating in regulated or sensitive environments', 'es' => 'Equipos que operan en entornos regulados o sensibles'],
    'designed_3'    => ['en' => 'Engineering teams needing full observability without shared SaaS', 'es' => 'Equipos de ingeniería que necesitan observabilidad completa sin SaaS compartido'],

    /* ---- Deployment & Security (merged) ---- */
    'depsec_title'  => ['en' => 'Deployment &amp; Security', 'es' => 'Despliegue y seguridad'],
    'depsec_1'      => ['en' => 'On-premise or dedicated VM in a European public cloud environment — your infrastructure, your rules.', 'es' => 'On-premise o VM dedicada en un entorno de nube pública europeo — tu infraestructura, tus reglas.'],
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
     BLOCK 2 — What is Rhinometric (1 sentence + 3 cards)
     ============================================================ -->
<section class="section section-compact">
  <div class="container">
    <h2 class="section-title" data-i18n="what_title"><?php echo esc_html($__('what_title')); ?></h2>
    <p class="section-subtitle" data-i18n="what_lead"><?php echo esc_html($__('what_lead')); ?></p>
    <div class="grid-3">
      <?php
      $what_icons = ['📊', '📋', '🔗'];
      for ($i = 1; $i <= 3; $i++) : ?>
      <div class="card card-compact">
        <div class="card-icon" aria-hidden="true"><?php echo $what_icons[$i - 1]; ?></div>
        <h3 class="card-title" data-i18n="what_<?php echo $i; ?>_t"><?php echo esc_html($__("what_{$i}_t")); ?></h3>
        <p data-i18n="what_<?php echo $i; ?>_d"><?php echo esc_html($__("what_{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 3 — Why on-prem / Single-tenant EU (2 bullets)
     ============================================================ -->
<section class="section section-compact section-alt">
  <div class="container">
    <h2 class="section-title" data-i18n="why_title"><?php echo $__('why_title'); ?></h2>
    <ul class="check-list">
      <li data-i18n="why_1"><?php echo esc_html($__('why_1')); ?></li>
      <li data-i18n="why_2"><?php echo esc_html($__('why_2')); ?></li>
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
