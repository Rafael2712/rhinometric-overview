<?php
/**
 * page-platform.php — Rhinometric v3
 * Platform overview: architecture, anomaly detection, operational workflow.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Unified operational view across metrics, logs and traces.', 'es' => 'Vista operativa unificada de métricas, logs y trazas.'],
    'lead'    => ['en' => 'Single investigation flow. Statistical anomaly detection. On-prem control.', 'es' => 'Flujo de investigación único. Detección estadística de anomalías. Control on-prem.'],
    'hero_caption' => ['en' => 'Unified operational console integrating metrics, anomalies and alerts in a single view.', 'es' => 'Consola operativa unificada que integra métricas, anomalías y alertas en una sola vista.'],
    'hero_img_alt' => ['en' => 'Rhinometric unified operational console overview', 'es' => 'Vista general de la consola operativa unificada de Rhinometric'],
    'hero_cta'=> ['en' => 'Request technical evaluation', 'es' => 'Solicitar evaluación técnica'],
    'hero_sandbox' => ['en' => 'Explore the sandbox', 'es' => 'Explorar el sandbox'],

    'arch_t'  => ['en' => 'Architecture Overview', 'es' => 'Visión general de la arquitectura'],
    'arch_d'  => ['en' => 'Rhinometric integrates established technologies for metrics, logs and tracing, and connects them through a single operational interface.', 'es' => 'Rhinometric integra tecnologías establecidas para métricas, logs y trazado, y las conecta a través de una interfaz operativa única.'],
    'arch_items' => [
        'en' => ['Prometheus for metrics', 'Loki for log aggregation', 'Jaeger for distributed tracing', 'Grafana for dashboards'],
        'es' => ['Prometheus para métricas', 'Loki para agregación de logs', 'Jaeger para trazado distribuido', 'Grafana para dashboards'],
    ],
    'arch_note' => ['en' => 'These components are not presented as isolated tools. These layers operate as a unified operational system.', 'es' => 'Estos componentes no se presentan como herramientas aisladas. Estas capas operan como un sistema operativo unificado.'],
    'ph_arch' => ['en' => 'Correlated investigation view — metrics → logs → traces (image will be inserted here)', 'es' => 'Vista de investigación correlacionada — métricas → logs → trazas (imagen pendiente)'],

    'anom_t'  => ['en' => 'Anomaly Detection', 'es' => 'Detección de anomalías'],
    'anom_d1' => ['en' => 'Rhinometric uses statistical baselines and models such as Isolation Forest, LOF and Z-score to detect deviations in time-series behavior and connect them to the relevant metrics, logs and traces.', 'es' => 'Rhinometric utiliza líneas base estadísticas y modelos como Isolation Forest, LOF y Z-score para detectar desviaciones en el comportamiento de series temporales y conectarlas con las métricas, logs y trazas relevantes.'],
    'anom_d3' => ['en' => 'The goal is not guaranteed prediction.', 'es' => 'El objetivo no es predicción garantizada.'],
    'ph_anom' => ['en' => 'AI anomaly view — baseline vs deviation (image will be inserted here)', 'es' => 'Vista de anomalía IA — línea base vs desviación (imagen pendiente)'],

    'wf_t'    => ['en' => 'Operational Workflow', 'es' => 'Flujo de trabajo operativo'],
    'wf_intro'=> ['en' => 'When an anomaly appears:', 'es' => 'Cuando aparece una anomalía:'],
    'wf_items'=> [
        'en' => ['Baseline deviation surfaced automatically', 'Related metrics accessible in context', 'Logs inspected without switching tools', 'Traces explored within the same flow'],
        'es' => ['Desviación de línea base detectada automáticamente', 'Métricas relacionadas accesibles en contexto', 'Logs inspeccionados sin cambiar de herramienta', 'Trazas exploradas en el mismo flujo'],
    ],
    'wf_example_t' => ['en' => 'Example scenario:', 'es' => 'Escenario de ejemplo:'],
    'wf_example'   => ['en' => 'A latency deviation is detected in a production service. Related metrics and recent logs surface automatically. A trace confirms the upstream dependency causing the spike.', 'es' => 'Se detecta una desviación de latencia en un servicio en producción. Las métricas relacionadas y los logs recientes aparecen automáticamente. Una traza confirma la dependencia upstream que causa el pico.'],

    'why_t'   => ['en' => 'Operational Complexity', 'es' => 'Complejidad operativa'],
    'why_intro'=> ['en' => 'Installing tools is straightforward. Operating them coherently is not:', 'es' => 'Instalar herramientas es sencillo. Operarlas de forma coherente no lo es:'],
    'why_items'=> [
        'en' => ['Maintaining ingestion, storage and retention policies', 'Correlating signals across different systems', 'Tuning anomaly detection and thresholds', 'Managing access control and security', 'Keeping the stack stable as infrastructure evolves'],
        'es' => ['Mantener políticas de ingesta, almacenamiento y retención', 'Correlacionar señales entre diferentes sistemas', 'Ajustar detección de anomalías y umbrales', 'Gestionar control de acceso y seguridad', 'Mantener el stack estable a medida que la infraestructura evoluciona'],
    ],

    'perf_t'  => ['en' => 'Performance &amp; Validation', 'es' => 'Rendimiento y validación'],
    'perf_d'  => ['en' => 'Rhinometric v2.6.0 has been validated under sustained workload conditions:', 'es' => 'Rhinometric v2.6.0 ha sido validado bajo condiciones de carga sostenida:'],
    'perf_items'=> [
        'en' => ['Validated with up to 100 hosts at 15-second scrape intervals', '100 MB/s log ingestion', '10,000 spans per second tracing', '50+ concurrent console users'],
        'es' => ['Validado con hasta 100 hosts con intervalos de scrape de 15 segundos', 'Ingesta de logs a 100 MB/s', '10.000 spans por segundo en trazado', 'Más de 50 usuarios concurrentes en consola'],
    ],
    'perf_note'=> ['en' => 'These figures reflect sustained validation of the integrated platform under load.', 'es' => 'Estas cifras reflejan la validación sostenida de la plataforma integrada bajo carga.'],

    'dep_t'   => ['en' => 'Deployment', 'es' => 'Despliegue'],
    'dep_body'=> ['en' => 'Deployment options for Rhinometric are documented separately.', 'es' => 'Las opciones de despliegue de Rhinometric están documentadas por separado.'],
    'dep_link'=> ['en' => 'See Deployment', 'es' => 'Ver Despliegue'],
    'dep_link_after'=> ['en' => 'for installation and operational details.', 'es' => 'para detalles de instalación y operación.'],

    'close_d' => ['en' => 'For SRE, Platform and DevOps teams responsible for uptime — especially in regulated or on-prem environments.', 'es' => 'Para equipos SRE, Plataforma y DevOps responsables del uptime — especialmente en entornos regulados u on-prem.'],

    'cta_t'   => ['en' => 'See it in action', 'es' => 'Vélo en acción'],
    'cta_btn' => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };
?>

<style>
/* Platform page scoped styles */
.platform-hero-cta-wrap{margin-top:1rem;text-align:center}
.platform-hero-cta-wrap .btn{display:inline-block}
.platform-hero-cta-wrap .platform-secondary-link{display:block;margin-top:.65rem;font-size:.9rem;color:var(--gray-500,#64748b);text-decoration:none;opacity:.85;transition:opacity .15s}
.platform-hero-cta-wrap .platform-secondary-link:hover{opacity:1;text-decoration:underline}
.platform-frame{width:100%;aspect-ratio:16/9;border-radius:var(--radius-sm,8px);border:1px dashed var(--gray-300,#cbd5e1);background:var(--gray-100,#f1f5f9);display:flex;align-items:center;justify-content:center;padding:1rem;margin-top:1.25rem}
.platform-frame-label{font-size:.88rem;color:var(--gray-400,#94a3b8);text-align:center;line-height:1.35}
@media(max-width:768px){
  .page-hero{padding-top:1.25rem;padding-bottom:1rem}
  .platform-hero-text h1{font-size:1.35rem;margin-bottom:.5rem}
  .platform-hero-text .hero-lead{font-size:.95rem;margin-bottom:.25rem}
  .platform-hero-cta-wrap{margin-top:.75rem}
  .platform-hero-image{margin-top:.75rem}
}
</style>

<section class="page-hero">
  <div class="container">
    <div class="platform-hero-container">
      <div class="platform-hero-text">
        <h1><?php echo esc_html($__('title')); ?></h1>
        <p class="hero-lead"><?php echo esc_html($__('lead')); ?></p>
        <div class="platform-hero-cta-wrap">
          <a class="btn btn-primary btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>"><?php echo esc_html($__('hero_cta')); ?></a>
          <a class="platform-secondary-link" href="<?php echo esc_url(rinometry_page_url('resources')); ?>"><?php echo esc_html($__('hero_sandbox')); ?></a>
        </div>
      </div>
      <div class="platform-hero-image-wrapper">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/platform-console-overview.png'); ?>" alt="<?php echo esc_attr($__('hero_img_alt')); ?>" class="platform-hero-image" loading="eager">
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('arch_t')); ?></h2>
    <p class="section-subtitle"><?php echo esc_html($__('arch_d')); ?></p>
    <ul class="check-list">
      <?php foreach ($t['arch_items'][$lang] ?? $t['arch_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
    <p><?php echo esc_html($__('arch_note')); ?></p>
    <div class="platform-frame">
      <span class="platform-frame-label"><?php echo esc_html($__('ph_arch')); ?></span>
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('anom_t')); ?></h2>
    <p><?php echo esc_html($__('anom_d1')); ?></p>
    <p><?php echo esc_html($__('anom_d3')); ?></p>
    <div class="platform-frame">
      <span class="platform-frame-label"><?php echo esc_html($__('ph_anom')); ?></span>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('wf_t')); ?></h2>
    <ul class="check-list">
      <?php foreach ($t['wf_items'][$lang] ?? $t['wf_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
    <p><strong><?php echo esc_html($__('wf_example_t')); ?></strong><br><?php echo esc_html($__('wf_example')); ?></p>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('why_t')); ?></h2>
    <p><?php echo esc_html($__('why_intro')); ?></p>
    <ul class="check-list">
      <?php foreach ($t['why_items'][$lang] ?? $t['why_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo $__('perf_t'); ?></h2>
    <p><?php echo esc_html($__('perf_d')); ?></p>
    <ul class="check-list">
      <?php foreach ($t['perf_items'][$lang] ?? $t['perf_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
    <p><?php echo esc_html($__('perf_note')); ?></p>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('dep_t')); ?></h2>
    <p><?php echo esc_html($__('dep_body')); ?> <a href="<?php echo esc_url(rinometry_page_url('deployment')); ?>"><?php echo esc_html($__('dep_link')); ?></a> <?php echo esc_html($__('dep_link_after')); ?></p>
  </div>
</section>

<section class="section">
  <div class="container">
    <p class="section-subtitle" style="max-width:720px;"><?php echo esc_html($__('close_d')); ?></p>
  </div>
</section>

<section class="section section-dark cta-section">
  <div class="container" style="text-align:center;">
    <h2><?php echo esc_html($__('cta_t')); ?></h2>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('contact')); ?>"><?php echo esc_html($__('cta_btn')); ?></a>
  </div>
</section>

<?php get_footer(); ?>
