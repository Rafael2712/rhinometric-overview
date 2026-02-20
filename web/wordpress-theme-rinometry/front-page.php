<?php
/**
 * front-page.php — Rhinometric v3.1
 * 6-block compact homepage with full EN/ES i18n.
 * Blocks: Hero · What is it · Why on-prem · Deployment summary · Security summary · CTA final
 */

get_header();

$lang = rinometry_get_current_language();

/* ================================================================
   i18n string catalogue (compact — detail lives in child pages)
   ================================================================ */
$t = [
    /* ---- Hero ---- */
    'hero_h1'       => ['en' => 'Your infrastructure.<br>Your data.<br>Zero cloud egress.', 'es' => 'Tu infraestructura.<br>Tus datos.<br>Cero egreso a la nube.'],
    'hero_lead'     => ['en' => 'Private observability for metrics, logs, and traces — single-tenant, EU-hosted, Docker-based.', 'es' => 'Observabilidad privada para métricas, logs y trazas — single-tenant, alojado en la UE, basado en Docker.'],
    'hero_cta_1'    => ['en' => 'Request a demo', 'es' => 'Solicitar demo'],
    'hero_cta_2'    => ['en' => 'View platform', 'es' => 'Ver plataforma'],

    /* ---- What is it ---- */
    'what_title'    => ['en' => 'What is Rhinometric', 'es' => 'Qué es Rhinometric'],
    'what_lead'     => ['en' => 'A self-hosted observability stack built on Prometheus, Loki, Jaeger, and Grafana.', 'es' => 'Un stack de observabilidad autoalojado basado en Prometheus, Loki, Jaeger y Grafana.'],
    'what_1_t'      => ['en' => 'Metrics', 'es' => 'Métricas'],
    'what_1_d'      => ['en' => 'Prometheus-powered collection with long-term storage and Grafana dashboards.', 'es' => 'Recolección con Prometheus, almacenamiento a largo plazo y dashboards Grafana.'],
    'what_2_t'      => ['en' => 'Logs', 'es' => 'Logs'],
    'what_2_d'      => ['en' => 'Centralized aggregation via Loki with label-based querying.', 'es' => 'Agregación centralizada con Loki y consultas basadas en etiquetas.'],
    'what_3_t'      => ['en' => 'Traces', 'es' => 'Trazas'],
    'what_3_d'      => ['en' => 'Distributed tracing through Jaeger with service maps and span analysis.', 'es' => 'Trazas distribuidas con Jaeger, mapas de servicios y análisis de spans.'],
    'what_link'     => ['en' => 'See full platform details', 'es' => 'Ver detalles completos de la plataforma'],

    /* ---- Why on-prem / Single-tenant EU ---- */
    'why_title'     => ['en' => 'Why on-prem &amp; single-tenant', 'es' => 'Por qué on-prem y single-tenant'],
    'why_1'         => ['en' => 'Your telemetry never leaves your network — full data sovereignty.', 'es' => 'Tu telemetría nunca sale de tu red — soberanía de datos total.'],
    'why_2'         => ['en' => 'Built on open-source foundations — no vendor lock-in.', 'es' => 'Construido sobre bases open-source — sin vendor lock-in.'],
    'why_3'         => ['en' => 'Pre-configured dashboards, alerting, and retention policies included.', 'es' => 'Dashboards, alertas y políticas de retención preconfigurados incluidos.'],

    /* ---- Deployment summary ---- */
    'deploy_title'  => ['en' => 'Deployment options', 'es' => 'Opciones de despliegue'],
    'deploy_1'      => ['en' => 'On-premise or private cloud (AWS, Azure, GCP) — your VPC, your rules.', 'es' => 'On-premise o nube privada (AWS, Azure, GCP) — tu VPC, tus reglas.'],
    'deploy_2'      => ['en' => 'Hybrid mode available — on-prem collectors with cloud storage.', 'es' => 'Modo híbrido disponible — colectores on-prem con almacenamiento en la nube.'],
    'deploy_link'   => ['en' => 'Explore deployment models', 'es' => 'Explorar modelos de despliegue'],

    /* ---- Security summary ---- */
    'sec_title'     => ['en' => 'Security &amp; trust', 'es' => 'Seguridad y confianza'],
    'sec_1'         => ['en' => 'mTLS on all inter-service communication — zero trust by default.', 'es' => 'mTLS en toda la comunicación entre servicios — zero trust por defecto.'],
    'sec_2'         => ['en' => 'Role-based access control with full audit trail.', 'es' => 'Control de acceso basado en roles con auditoría completa.'],
    'sec_3'         => ['en' => 'EU data residency — GDPR-ready architecture.', 'es' => 'Residencia de datos en la UE — arquitectura preparada para GDPR.'],
    'sec_link'      => ['en' => 'Learn more about security', 'es' => 'Más sobre seguridad'],

    /* ---- CTA final ---- */
    'cta_title'     => ['en' => 'Ready to take control?', 'es' => '¿Listo para tomar el control?'],
    'cta_lead'      => ['en' => 'Deploy Rhinometric in your infrastructure today. No shared tenancy, no data egress.', 'es' => 'Despliega Rhinometric en tu infraestructura hoy. Sin tenencia compartida, sin egreso de datos.'],
    'cta_btn'       => ['en' => 'Contact us', 'es' => 'Contáctanos'],

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
    <div class="hero-cta">
      <a class="btn btn-primary btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>" data-i18n="hero_cta_1">
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
    <p class="section-link"><a href="<?php echo esc_url(rinometry_page_url('platform')); ?>" data-i18n="what_link"><?php echo esc_html($__('what_link')); ?> &rarr;</a></p>
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
  </div>
</section>

<!-- ============================================================
     BLOCK 4 — Deployment summary (2 bullets + link)
     ============================================================ -->
<section class="section section-compact">
  <div class="container">
    <h2 class="section-title" data-i18n="deploy_title"><?php echo $__('deploy_title'); ?></h2>
    <ul class="check-list">
      <li data-i18n="deploy_1"><?php echo esc_html($__('deploy_1')); ?></li>
      <li data-i18n="deploy_2"><?php echo esc_html($__('deploy_2')); ?></li>
    </ul>
    <p class="section-link"><a href="<?php echo esc_url(rinometry_page_url('deployment')); ?>" data-i18n="deploy_link"><?php echo esc_html($__('deploy_link')); ?> &rarr;</a></p>
  </div>
</section>

<!-- ============================================================
     BLOCK 5 — Security summary (3 bullets + link)
     ============================================================ -->
<section class="section section-compact section-alt">
  <div class="container">
    <h2 class="section-title" data-i18n="sec_title"><?php echo $__('sec_title'); ?></h2>
    <ul class="check-list">
      <li data-i18n="sec_1"><?php echo esc_html($__('sec_1')); ?></li>
      <li data-i18n="sec_2"><?php echo esc_html($__('sec_2')); ?></li>
      <li data-i18n="sec_3"><?php echo esc_html($__('sec_3')); ?></li>
    </ul>
    <p class="section-link"><a href="<?php echo esc_url(rinometry_page_url('security')); ?>" data-i18n="sec_link"><?php echo esc_html($__('sec_link')); ?> &rarr;</a></p>
  </div>
</section>

<!-- ============================================================
     BLOCK 6 — CTA final
     ============================================================ -->
<section class="section section-compact section-dark cta-section">
  <div class="container" style="text-align:center;">
    <h2 data-i18n="cta_title"><?php echo esc_html($__('cta_title')); ?></h2>
    <p class="cta-lead" data-i18n="cta_lead"><?php echo esc_html($__('cta_lead')); ?></p>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>" data-i18n="cta_btn">
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
