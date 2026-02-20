<?php
/**
 * page-platform.php — Rhinometric v3
 * Platform overview: unified data plane, operator-first design, enterprise governance.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Platform overview', 'es' => 'Visión general de la plataforma'],
    'lead'    => ['en' => 'Rhinometric unifies metrics, logs, and traces into a single self-hosted observability stack — pre-configured, production-ready, and fully under your control.', 'es' => 'Rhinometric unifica métricas, logs y trazas en un único stack de observabilidad autoalojado — preconfigurado, listo para producción y totalmente bajo tu control.'],
    'c1_t'    => ['en' => 'Unified data plane', 'es' => 'Plano de datos unificado'],
    'c1_d'    => ['en' => 'Metrics, logs, and traces in a single operational view with consistent retention policies.', 'es' => 'Métricas, logs y trazas en una única vista operacional con políticas de retención consistentes.'],
    'c2_t'    => ['en' => 'Operator-first design', 'es' => 'Diseño orientado al operador'],
    'c2_d'    => ['en' => 'Opinionated dashboards, alerts, and runbooks to accelerate incident response.', 'es' => 'Dashboards, alertas y runbooks prediseñados para acelerar la respuesta a incidentes.'],
    'c3_t'    => ['en' => 'Enterprise governance', 'es' => 'Gobernanza empresarial'],
    'c3_d'    => ['en' => 'Role-based access, audit visibility, and secure integrations for regulated teams.', 'es' => 'Control de acceso basado en roles, visibilidad de auditoría e integraciones seguras para equipos regulados.'],
    'comp_t'  => ['en' => 'Core components', 'es' => 'Componentes principales'],
    'comp_d'  => ['en' => 'Built on battle-tested open-source foundations.', 'es' => 'Construido sobre bases open-source probadas en producción.'],
    'cta_t'   => ['en' => 'See it in action', 'es' => 'Vélo en acción'],
    'cta_d'   => ['en' => 'Contact us for a personalized walkthrough of the Rhinometric platform.', 'es' => 'Contáctanos para una demostración personalizada de la plataforma Rhinometric.'],
    'cta_btn' => ['en' => 'Contact us', 'es' => 'Contáctanos'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };
$components = [
    ['icon' => '📊', 'name' => 'Prometheus', 'desc' => ['en' => 'Metrics collection & long-term storage', 'es' => 'Recolección de métricas y almacenamiento a largo plazo']],
    ['icon' => '📋', 'name' => 'Loki',       'desc' => ['en' => 'Log aggregation with label-based queries', 'es' => 'Agregación de logs con consultas basadas en etiquetas']],
    ['icon' => '🔗', 'name' => 'Tempo',      'desc' => ['en' => 'Distributed tracing with service maps', 'es' => 'Trazas distribuidas con mapas de servicios']],
    ['icon' => '📈', 'name' => 'Grafana',    'desc' => ['en' => 'Visualization, dashboards & alerting', 'es' => 'Visualización, dashboards y alertas']],
];
?>

<section class="page-hero">
  <div class="container">
    <h1><?php echo esc_html($__('title')); ?></h1>
    <p class="hero-lead"><?php echo esc_html($__('lead')); ?></p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="grid-3">
      <div class="card">
        <div class="card-icon" aria-hidden="true">🔄</div>
        <h3 class="card-title"><?php echo esc_html($__('c1_t')); ?></h3>
        <p><?php echo esc_html($__('c1_d')); ?></p>
      </div>
      <div class="card">
        <div class="card-icon" aria-hidden="true">🎯</div>
        <h3 class="card-title"><?php echo esc_html($__('c2_t')); ?></h3>
        <p><?php echo esc_html($__('c2_d')); ?></p>
      </div>
      <div class="card">
        <div class="card-icon" aria-hidden="true">🏛️</div>
        <h3 class="card-title"><?php echo esc_html($__('c3_t')); ?></h3>
        <p><?php echo esc_html($__('c3_d')); ?></p>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('comp_t')); ?></h2>
    <p class="section-subtitle"><?php echo esc_html($__('comp_d')); ?></p>
    <div class="grid-2">
      <?php foreach ($components as $c) : ?>
      <div class="card">
        <div class="card-icon" aria-hidden="true"><?php echo $c['icon']; ?></div>
        <h3 class="card-title"><?php echo esc_html($c['name']); ?></h3>
        <p><?php echo esc_html($c['desc'][$lang] ?? $c['desc']['en']); ?></p>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<section class="section section-dark cta-section">
  <div class="container" style="text-align:center;">
    <h2><?php echo esc_html($__('cta_t')); ?></h2>
    <p class="cta-lead"><?php echo esc_html($__('cta_d')); ?></p>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>"><?php echo esc_html($__('cta_btn')); ?></a>
  </div>
</section>

<?php get_footer(); ?>
