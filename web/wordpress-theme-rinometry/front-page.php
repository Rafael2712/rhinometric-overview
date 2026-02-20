<?php
/**
 * front-page.php — Rhinometric v3
 * 6-block homepage with full EN/ES i18n.
 * Blocks: Hero · Why it matters · What you get · Deployment models · Security & trust · CTA final
 */

get_header();

$lang = rinometry_get_current_language();

/* ================================================================
   i18n string catalogue
   ================================================================ */
$t = [
    /* ---- Hero ---- */
    'hero_badge'    => ['en' => 'Single-Tenant Observability', 'es' => 'Observabilidad Single-Tenant'],
    'hero_h1'       => ['en' => 'Your infrastructure.<br>Your data.<br>Zero cloud egress.', 'es' => 'Tu infraestructura.<br>Tus datos.<br>Cero egreso a la nube.'],
    'hero_lead'     => ['en' => 'Deploy a private observability engine for metrics, logs, and traces — hosted in the EU, on your own terms.', 'es' => 'Despliega un motor de observabilidad privado para métricas, logs y trazas — alojado en la UE, bajo tus condiciones.'],
    'hero_bullet_1' => ['en' => 'Metrics, logs & traces in one stack', 'es' => 'Métricas, logs y trazas en un solo stack'],
    'hero_bullet_2' => ['en' => 'Grafana-native dashboards included', 'es' => 'Dashboards nativos de Grafana incluidos'],
    'hero_bullet_3' => ['en' => 'Docker-based, deploys in minutes', 'es' => 'Basado en Docker, despliega en minutos'],
    'hero_cta'      => ['en' => 'Get started', 'es' => 'Comenzar'],

    /* ---- Why it matters ---- */
    'why_title'     => ['en' => 'Why it matters', 'es' => 'Por qué importa'],
    'why_subtitle'  => ['en' => 'Most observability platforms require you to send telemetry to a shared, multi-tenant cloud. That means latency, vendor lock-in, and data exposure. Rhinometric keeps everything inside your perimeter.', 'es' => 'La mayoría de las plataformas de observabilidad exigen enviar telemetría a una nube compartida multi-tenant. Eso implica latencia, vendor lock-in y exposición de datos. Rhinometric mantiene todo dentro de tu perímetro.'],
    'why_card_1_t'  => ['en' => 'Data sovereignty', 'es' => 'Soberanía de datos'],
    'why_card_1_d'  => ['en' => 'Your telemetry never leaves your network. Full control, full compliance.', 'es' => 'Tu telemetría nunca sale de tu red. Control total, cumplimiento total.'],
    'why_card_2_t'  => ['en' => 'No vendor lock-in', 'es' => 'Sin vendor lock-in'],
    'why_card_2_d'  => ['en' => 'Built on open-source foundations: Prometheus, Loki, Tempo, Grafana. Own your stack.', 'es' => 'Construido sobre bases open-source: Prometheus, Loki, Tempo, Grafana. Tu stack es tuyo.'],
    'why_card_3_t'  => ['en' => 'Production-ready', 'es' => 'Listo para producción'],
    'why_card_3_d'  => ['en' => 'Pre-configured dashboards, alerting rules, and retention policies out of the box.', 'es' => 'Dashboards preconfigurados, reglas de alerta y políticas de retención listas para usar.'],

    /* ---- What you get ---- */
    'what_title'    => ['en' => 'What you get', 'es' => 'Qué obtienes'],
    'what_1_t'      => ['en' => 'Metrics', 'es' => 'Métricas'],
    'what_1_d'      => ['en' => 'Prometheus-powered metrics collection with long-term storage and pre-built Grafana dashboards.', 'es' => 'Recolección de métricas con Prometheus, almacenamiento a largo plazo y dashboards Grafana pre-configurados.'],
    'what_2_t'      => ['en' => 'Logs', 'es' => 'Logs'],
    'what_2_d'      => ['en' => 'Centralized log aggregation via Loki with label-based querying and integrated alerting.', 'es' => 'Agregación centralizada de logs con Loki, consultas basadas en etiquetas y alertas integradas.'],
    'what_3_t'      => ['en' => 'Traces', 'es' => 'Trazas'],
    'what_3_d'      => ['en' => 'Distributed tracing through Tempo with service maps, span analysis and correlation.', 'es' => 'Trazas distribuidas con Tempo, mapas de servicios, análisis de spans y correlación.'],
    'what_4_t'      => ['en' => 'Dashboards', 'es' => 'Dashboards'],
    'what_4_d'      => ['en' => 'Grafana-native panels with real-time data, flexible layout, and built-in alerting.', 'es' => 'Paneles nativos de Grafana con datos en tiempo real, diseño flexible y alertas integradas.'],
    'what_5_t'      => ['en' => 'Alerting', 'es' => 'Alertas'],
    'what_5_d'      => ['en' => 'Unified alerting engine with Slack, email, PagerDuty and webhook integrations.', 'es' => 'Motor de alertas unificado con integraciones para Slack, email, PagerDuty y webhooks.'],
    'what_6_t'      => ['en' => 'Security', 'es' => 'Seguridad'],
    'what_6_d'      => ['en' => 'mTLS, RBAC, network policies, and audit logging. Enterprise-grade from day one.', 'es' => 'mTLS, RBAC, políticas de red y auditoría de logs. Nivel empresarial desde el día uno.'],

    /* ---- Deployment models ---- */
    'deploy_title'  => ['en' => 'Deployment models', 'es' => 'Modelos de despliegue'],
    'deploy_1_t'    => ['en' => 'On-premise', 'es' => 'On-premise'],
    'deploy_1_d'    => ['en' => 'Full control on your hardware. Air-gapped support available.', 'es' => 'Control total en tu hardware. Soporte air-gapped disponible.'],
    'deploy_2_t'    => ['en' => 'Private cloud', 'es' => 'Nube privada'],
    'deploy_2_d'    => ['en' => 'Deploy on AWS, Azure, or GCP inside your own VPC. No shared tenancy.', 'es' => 'Despliega en AWS, Azure o GCP dentro de tu propio VPC. Sin tenencia compartida.'],
    'deploy_3_t'    => ['en' => 'Hybrid', 'es' => 'Híbrido'],
    'deploy_3_d'    => ['en' => 'Combine on-prem collection with cloud storage. Best of both worlds.', 'es' => 'Combina recolección on-prem con almacenamiento en la nube. Lo mejor de ambos mundos.'],

    /* ---- Security & trust ---- */
    'sec_title'     => ['en' => 'Security & trust', 'es' => 'Seguridad y confianza'],
    'sec_1_t'       => ['en' => 'mTLS everywhere', 'es' => 'mTLS en todas partes'],
    'sec_1_d'       => ['en' => 'All inter-service communication is encrypted with mutual TLS. Zero trust by default.', 'es' => 'Toda la comunicación entre servicios está cifrada con TLS mutuo. Zero trust por defecto.'],
    'sec_2_t'       => ['en' => 'RBAC & audit logs', 'es' => 'RBAC y auditoría'],
    'sec_2_d'       => ['en' => 'Granular role-based access control with complete audit trail for every action.', 'es' => 'Control de acceso basado en roles granular con pista de auditoría completa para cada acción.'],
    'sec_3_t'       => ['en' => 'EU data residency', 'es' => 'Residencia de datos en la UE'],
    'sec_3_d'       => ['en' => 'All data stays within EU borders. GDPR-ready architecture built in.', 'es' => 'Todos los datos permanecen dentro de las fronteras de la UE. Arquitectura preparada para GDPR.'],
    'sec_4_t'       => ['en' => 'Air-gap ready', 'es' => 'Preparado para air-gap'],
    'sec_4_d'       => ['en' => 'Deployable in fully disconnected environments with offline license validation.', 'es' => 'Desplegable en entornos completamente desconectados con validación de licencia offline.'],

    /* ---- CTA final ---- */
    'cta_title'     => ['en' => 'Ready to take control?', 'es' => '¿Listo para tomar el control?'],
    'cta_lead'      => ['en' => 'Deploy Rhinometric in your infrastructure today. No credit card, no shared tenancy, no data egress.', 'es' => 'Despliega Rhinometric en tu infraestructura hoy. Sin tarjeta de crédito, sin tenencia compartida, sin egreso de datos.'],
    'cta_btn_1'     => ['en' => 'Request a demo', 'es' => 'Solicitar demo'],
    'cta_btn_2'     => ['en' => 'View pricing', 'es' => 'Ver precios'],

    /* ---- Social ---- */
    'social_title'  => ['en' => 'Follow us', 'es' => 'Síguenos'],
];

/**
 * Translate helper: returns the string for the current language.
 */
$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};

/* ================================================================
   Trust strip logos
   ================================================================ */
$trust_logos = [
    ['label' => 'Prometheus',  'file' => 'logo-prometheus.svg'],
    ['label' => 'Grafana',     'file' => 'logo-grafana.svg'],
    ['label' => 'Loki',        'file' => 'logo-loki.svg'],
    ['label' => 'Tempo',       'file' => 'logo-tempo.svg'],
    ['label' => 'Docker',      'file' => 'logo-docker.svg'],
];
$asset_uri = get_template_directory_uri() . '/assets/';
?>

<!-- ============================================================
     BLOCK 1 — Hero
     ============================================================ -->
<section class="hero">
  <div class="container hero-inner">
    <span class="badge" data-i18n="hero_badge"><?php echo $__('hero_badge'); ?></span>
    <h1 data-i18n="hero_h1"><?php echo $__('hero_h1'); ?></h1>
    <p class="hero-lead" data-i18n="hero_lead"><?php echo esc_html($__('hero_lead')); ?></p>
    <ul class="hero-bullets" aria-label="<?php echo esc_attr($__('hero_badge')); ?>">
      <li data-i18n="hero_bullet_1"><?php echo esc_html($__('hero_bullet_1')); ?></li>
      <li data-i18n="hero_bullet_2"><?php echo esc_html($__('hero_bullet_2')); ?></li>
      <li data-i18n="hero_bullet_3"><?php echo esc_html($__('hero_bullet_3')); ?></li>
    </ul>
    <a class="btn btn-primary btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>" data-i18n="hero_cta">
      <?php echo esc_html($__('hero_cta')); ?>
    </a>
  </div>
</section>

<!-- Trust strip -->
<div class="trust-strip">
  <div class="container trust-strip-inner">
    <?php foreach ($trust_logos as $logo) :
        $path = $asset_uri . $logo['file'];
    ?>
      <img src="<?php echo esc_url($path); ?>" alt="<?php echo esc_attr($logo['label']); ?>" loading="lazy" />
    <?php endforeach; ?>
  </div>
</div>

<!-- ============================================================
     BLOCK 2 — Why it matters
     ============================================================ -->
<section class="section">
  <div class="container">
    <h2 class="section-title" data-i18n="why_title"><?php echo esc_html($__('why_title')); ?></h2>
    <p class="section-subtitle" data-i18n="why_subtitle"><?php echo esc_html($__('why_subtitle')); ?></p>
    <div class="grid-3">
      <?php for ($i = 1; $i <= 3; $i++) : ?>
      <div class="card">
        <h3 class="card-title" data-i18n="why_card_<?php echo $i; ?>_t"><?php echo esc_html($__("why_card_{$i}_t")); ?></h3>
        <p data-i18n="why_card_<?php echo $i; ?>_d"><?php echo esc_html($__("why_card_{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 3 — What you get
     ============================================================ -->
<section class="section section-alt">
  <div class="container">
    <h2 class="section-title" data-i18n="what_title"><?php echo esc_html($__('what_title')); ?></h2>
    <div class="grid-3">
      <?php for ($i = 1; $i <= 6; $i++) : ?>
      <div class="card">
        <div class="card-icon" aria-hidden="true">
          <?php
          $icons = ['📊', '📋', '🔗', '📈', '🔔', '🛡️'];
          echo $icons[$i - 1];
          ?>
        </div>
        <h3 class="card-title" data-i18n="what_<?php echo $i; ?>_t"><?php echo esc_html($__("what_{$i}_t")); ?></h3>
        <p data-i18n="what_<?php echo $i; ?>_d"><?php echo esc_html($__("what_{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 4 — Deployment models
     ============================================================ -->
<section class="section">
  <div class="container">
    <h2 class="section-title" data-i18n="deploy_title"><?php echo esc_html($__('deploy_title')); ?></h2>
    <div class="grid-3">
      <?php
      $deploy_icons = ['🏢', '☁️', '🔄'];
      for ($i = 1; $i <= 3; $i++) : ?>
      <div class="deployment-card card">
        <div class="card-icon" aria-hidden="true"><?php echo $deploy_icons[$i - 1]; ?></div>
        <h3 class="card-title" data-i18n="deploy_<?php echo $i; ?>_t"><?php echo esc_html($__("deploy_{$i}_t")); ?></h3>
        <p data-i18n="deploy_<?php echo $i; ?>_d"><?php echo esc_html($__("deploy_{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 5 — Security & trust
     ============================================================ -->
<section class="section section-alt">
  <div class="container">
    <h2 class="section-title" data-i18n="sec_title"><?php echo esc_html($__('sec_title')); ?></h2>
    <div class="grid-2">
      <?php
      $sec_icons = ['🔒', '👤', '🇪🇺', '🔌'];
      for ($i = 1; $i <= 4; $i++) : ?>
      <div class="card">
        <div class="card-icon" aria-hidden="true"><?php echo $sec_icons[$i - 1]; ?></div>
        <h3 class="card-title" data-i18n="sec_<?php echo $i; ?>_t"><?php echo esc_html($__("sec_{$i}_t")); ?></h3>
        <p data-i18n="sec_<?php echo $i; ?>_d"><?php echo esc_html($__("sec_{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
    </div>
  </div>
</section>

<!-- ============================================================
     BLOCK 6 — CTA final
     ============================================================ -->
<section class="section section-dark cta-section">
  <div class="container" style="text-align:center;">
    <h2 data-i18n="cta_title"><?php echo esc_html($__('cta_title')); ?></h2>
    <p class="cta-lead" data-i18n="cta_lead"><?php echo esc_html($__('cta_lead')); ?></p>
    <div class="cta-buttons">
      <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>" data-i18n="cta_btn_1">
        <?php echo esc_html($__('cta_btn_1')); ?>
      </a>
      <a class="btn btn-outline btn-lg" href="<?php echo esc_url(rinometry_page_url('pricing')); ?>" data-i18n="cta_btn_2">
        <?php echo esc_html($__('cta_btn_2')); ?>
      </a>
    </div>
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
