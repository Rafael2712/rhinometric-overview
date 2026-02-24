<?php
/**
 * page-platform.php — Rhinometric v3
 * Platform overview: architecture, anomaly detection, operational workflow.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Platform Architecture', 'es' => 'Arquitectura de la plataforma'],
    'lead'    => ['en' => 'Rhinometric combines proven open-source observability components with statistical anomaly detection and a unified operational console. It is built for SRE and Platform teams responsible for uptime and incident response.', 'es' => 'Rhinometric combina componentes de observabilidad open-source probados con detección estadística de anomalías y una consola operativa unificada. Está diseñado para equipos SRE y de Plataforma responsables del uptime y la respuesta a incidentes.'],
    'hero_caption' => ['en' => 'Unified operational console integrating metrics, anomalies and alerts in a single view.', 'es' => 'Consola operativa unificada que integra métricas, anomalías y alertas en una sola vista.'],
    'hero_img_alt' => ['en' => 'Rhinometric unified operational console overview', 'es' => 'Vista general de la consola operativa unificada de Rhinometric'],

    'arch_t'  => ['en' => 'Architecture Overview', 'es' => 'Visión general de la arquitectura'],
    'arch_d'  => ['en' => 'Rhinometric integrates established technologies for metrics, logs and tracing, and connects them through a single operational interface.', 'es' => 'Rhinometric integra tecnologías establecidas para métricas, logs y trazado, y las conecta a través de una interfaz operativa única.'],
    'arch_items' => [
        'en' => ['Prometheus for metrics', 'Loki for log aggregation', 'Jaeger for distributed tracing', 'Grafana for dashboards'],
        'es' => ['Prometheus para métricas', 'Loki para agregación de logs', 'Jaeger para trazado distribuido', 'Grafana para dashboards'],
    ],
    'arch_note' => ['en' => 'These components are not presented as isolated tools. These layers operate as a unified operational system.', 'es' => 'Estos componentes no se presentan como herramientas aisladas. Estas capas operan como un sistema operativo unificado.'],
    'ph_arch' => ['en' => 'Correlated investigation view — metrics → logs → traces (image will be inserted here)', 'es' => 'Vista de investigación correlacionada — métricas → logs → trazas (imagen pendiente)'],

    'anom_t'  => ['en' => 'Anomaly Detection', 'es' => 'Detección de anomalías'],
    'anom_d1' => ['en' => 'Rhinometric analyzes time-series behavior using statistical baselines and established anomaly detection models such as Isolation Forest, LOF and Z-score.', 'es' => 'Rhinometric analiza el comportamiento de series temporales utilizando líneas base estadísticas y modelos de detección de anomalías establecidos como Isolation Forest, LOF y Z-score.'],
    'anom_d2' => ['en' => 'When a deviation from expected behavior is identified, the platform highlights it and connects the anomaly to the relevant metrics, logs and traces required for investigation.', 'es' => 'Cuando se identifica una desviación del comportamiento esperado, la plataforma la destaca y conecta la anomalía con las métricas, logs y trazas relevantes necesarias para la investigación.'],
    'anom_d3' => ['en' => 'The goal is not guaranteed prediction. The objective is faster, structured understanding of abnormal behavior.', 'es' => 'El objetivo no es predicción garantizada. El objetivo es una comprensión más rápida y estructurada del comportamiento anormal.'],
    'ph_anom' => ['en' => 'AI anomaly view — baseline vs deviation (image will be inserted here)', 'es' => 'Vista de anomalía IA — línea base vs desviación (imagen pendiente)'],

    'wf_t'    => ['en' => 'Operational Workflow', 'es' => 'Flujo de trabajo operativo'],
    'wf_intro'=> ['en' => 'When an anomaly appears:', 'es' => 'Cuando aparece una anomalía:'],
    'wf_items'=> [
        'en' => ['The deviation is shown against its behavioral baseline', 'Related metrics are accessible immediately', 'Logs can be inspected without switching systems', 'Relevant traces can be explored within the same context'],
        'es' => ['La desviación se muestra contra su línea base de comportamiento', 'Las métricas relacionadas son accesibles de inmediato', 'Los logs se pueden inspeccionar sin cambiar de sistema', 'Las trazas relevantes se pueden explorar en el mismo contexto'],
    ],
    'wf_close'=> ['en' => 'The workflow is consistent and contained within one interface. This reduces context switching and cognitive overhead during incident response.', 'es' => 'El flujo de trabajo es consistente y está contenido en una sola interfaz. Esto reduce el cambio de contexto y la carga cognitiva durante la respuesta a incidentes.'],

    'why_t'   => ['en' => 'Operational Complexity', 'es' => 'Complejidad operativa'],
    'why_intro'=> ['en' => 'Installing observability tools is straightforward. Operating them coherently over time is not. What becomes challenging is not setup, but operational cohesion:', 'es' => 'Instalar herramientas de observabilidad es sencillo. Operarlas de forma coherente a lo largo del tiempo no lo es. Lo que se vuelve desafiante no es la configuración, sino la cohesión operativa:'],
    'why_items'=> [
        'en' => ['Maintaining ingestion, storage and retention policies', 'Correlating signals across different systems', 'Tuning anomaly detection and thresholds', 'Managing access control and security', 'Validating performance at scale', 'Keeping the stack stable as infrastructure evolves'],
        'es' => ['Mantener políticas de ingesta, almacenamiento y retención', 'Correlacionar señales entre diferentes sistemas', 'Ajustar detección de anomalías y umbrales', 'Gestionar control de acceso y seguridad', 'Validar rendimiento a escala', 'Mantener el stack estable a medida que la infraestructura evoluciona'],
    ],
    'why_close1'=> ['en' => 'Rhinometric packages these elements into a validated and cohesive system built on open standards.', 'es' => 'Rhinometric empaqueta estos elementos en un sistema validado y cohesivo construido sobre estándares abiertos.'],
    'why_close2'=> ['en' => 'It is not a replacement for open-source tools. It is an operational layer that integrates them with structured detection and workflow logic.', 'es' => 'No es un reemplazo de las herramientas open-source. Es una capa operativa que las integra con detección estructurada y lógica de flujo de trabajo.'],

    'perf_t'  => ['en' => 'Performance &amp; Validation', 'es' => 'Rendimiento y validación'],
    'perf_d'  => ['en' => 'Rhinometric v2.6.0 has been validated under sustained workload conditions:', 'es' => 'Rhinometric v2.6.0 ha sido validado bajo condiciones de carga sostenida:'],
    'perf_items'=> [
        'en' => ['Up to 100 hosts at 15-second scrape intervals', '100 MB/s log ingestion', '10,000 spans per second tracing', '50+ concurrent console users'],
        'es' => ['Hasta 100 hosts con intervalos de scrape de 15 segundos', 'Ingesta de logs a 100 MB/s', '10.000 spans por segundo en trazado', 'Más de 50 usuarios concurrentes en consola'],
    ],
    'perf_note'=> ['en' => 'These figures reflect the performance of the integrated platform, not isolated components.', 'es' => 'Estas cifras reflejan el rendimiento de la plataforma integrada, no de componentes aislados.'],

    'dep_t'   => ['en' => 'Deployment', 'es' => 'Despliegue'],
    'dep_d'   => ['en' => 'Rhinometric supports two deployment models depending on operational requirements.', 'es' => 'Rhinometric soporta dos modelos de despliegue según los requisitos operativos.'],
    'dep_1_t' => ['en' => 'On-premise', 'es' => 'On-premise'],
    'dep_1_d' => ['en' => 'Deployed within customer-managed infrastructure, preserving full data locality and network isolation.', 'es' => 'Desplegado en infraestructura gestionada por el cliente, preservando la localidad total de datos y el aislamiento de red.'],
    'dep_2_t' => ['en' => 'Single-tenant VM (EU)', 'es' => 'VM single-tenant (UE)'],
    'dep_2_d' => ['en' => 'Deployed in a dedicated and isolated virtual machine, with full data control and no shared runtime.', 'es' => 'Desplegado en una máquina virtual dedicada y aislada, con control total de datos y sin runtime compartido.'],
    'dep_note'=> ['en' => 'Platform updates and maintenance are coordinated to ensure stability while preserving operational continuity.', 'es' => 'Las actualizaciones y el mantenimiento de la plataforma se coordinan para garantizar estabilidad preservando la continuidad operativa.'],

    'close_d' => ['en' => 'Rhinometric is not a monitoring dashboard. It is a detection and operational workflow layer built on proven observability foundations, designed to reduce investigation time and improve clarity during incident response.', 'es' => 'Rhinometric no es un dashboard de monitorización. Es una capa de detección y flujo de trabajo operativo construida sobre fundamentos de observabilidad probados, diseñada para reducir el tiempo de investigación y mejorar la claridad durante la respuesta a incidentes.'],

    'cta_t'   => ['en' => 'See it in action', 'es' => 'Vélo en acción'],
    'cta_d'   => ['en' => 'Request an evaluation session for a personalized walkthrough of the Rhinometric platform.', 'es' => 'Solicita una sesión de evaluación para un recorrido personalizado de la plataforma Rhinometric.'],
    'cta_btn' => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };
?>

<section class="page-hero">
  <div class="container">
    <div class="platform-hero-container">
      <div class="platform-hero-text">
        <h1><?php echo esc_html($__('title')); ?></h1>
        <p class="hero-lead"><?php echo esc_html($__('lead')); ?></p>
      </div>
      <div class="platform-hero-image-wrapper">
        <img src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/platform-console-overview.png'); ?>" alt="<?php echo esc_attr($__('hero_img_alt')); ?>" class="platform-hero-image" loading="eager">
        <p class="platform-image-caption"><?php echo esc_html($__('hero_caption')); ?></p>
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
    <div class="platform-image-placeholder"><?php echo esc_html($__('ph_arch')); ?></div>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('anom_t')); ?></h2>
    <p><?php echo esc_html($__('anom_d1')); ?></p>
    <p><?php echo esc_html($__('anom_d2')); ?></p>
    <p><?php echo esc_html($__('anom_d3')); ?></p>
    <div class="platform-image-placeholder"><?php echo esc_html($__('ph_anom')); ?></div>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('wf_t')); ?></h2>
    <p><?php echo esc_html($__('wf_intro')); ?></p>
    <ul class="check-list">
      <?php foreach ($t['wf_items'][$lang] ?? $t['wf_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
    <p><?php echo esc_html($__('wf_close')); ?></p>
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
    <p><?php echo esc_html($__('why_close1')); ?></p>
    <p><?php echo esc_html($__('why_close2')); ?></p>
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
    <p><?php echo esc_html($__('dep_d')); ?></p>
    <div class="grid-2">
      <div class="card">
        <h3 class="card-title"><?php echo esc_html($__('dep_1_t')); ?></h3>
        <p><?php echo esc_html($__('dep_1_d')); ?></p>
      </div>
      <div class="card">
        <h3 class="card-title"><?php echo esc_html($__('dep_2_t')); ?></h3>
        <p><?php echo esc_html($__('dep_2_d')); ?></p>
      </div>
    </div>
    <p style="margin-top:1rem;"><?php echo esc_html($__('dep_note')); ?></p>
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
    <p class="cta-lead"><?php echo esc_html($__('cta_d')); ?></p>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('evaluation')); ?>"><?php echo esc_html($__('cta_btn')); ?></a>
  </div>
</section>

<?php get_footer(); ?>
