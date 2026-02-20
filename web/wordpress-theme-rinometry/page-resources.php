<?php
/**
 * page-resources.php — Rhinometric v3
 * Resources hub: documentation, guides, changelog.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Resources', 'es' => 'Recursos'],
    'lead'    => ['en' => 'Guides, documentation, and reference material to help you get the most out of Rhinometric.', 'es' => 'Guías, documentación y material de referencia para ayudarte a aprovechar al máximo Rhinometric.'],
    'r1_t'    => ['en' => 'Getting started guide', 'es' => 'Guía de inicio'],
    'r1_d'    => ['en' => 'Step-by-step instructions for your first Rhinometric deployment, from Docker pull to first dashboard.', 'es' => 'Instrucciones paso a paso para tu primer despliegue de Rhinometric, desde Docker pull hasta el primer dashboard.'],
    'r2_t'    => ['en' => 'Architecture overview', 'es' => 'Visión general de la arquitectura'],
    'r2_d'    => ['en' => 'Understand the component layout, data flow, and networking model behind Rhinometric.', 'es' => 'Entiende el diseño de componentes, flujo de datos y modelo de red detrás de Rhinometric.'],
    'r3_t'    => ['en' => 'API reference', 'es' => 'Referencia de API'],
    'r3_d'    => ['en' => 'Configuration endpoints, metrics exporters, and log/trace ingestion APIs.', 'es' => 'Endpoints de configuración, exportadores de métricas y APIs de ingesta de logs/trazas.'],
    'r4_t'    => ['en' => 'Changelog', 'es' => 'Registro de cambios'],
    'r4_d'    => ['en' => 'Track every release, improvement, and fix across all Rhinometric versions.', 'es' => 'Sigue cada versión, mejora y corrección en todas las versiones de Rhinometric.'],
    'r5_t'    => ['en' => 'FAQ', 'es' => 'Preguntas frecuentes'],
    'r5_d'    => ['en' => 'Answers to the most common questions about licensing, deployment, and support.', 'es' => 'Respuestas a las preguntas más comunes sobre licenciamiento, despliegue y soporte.'],
    'r6_t'    => ['en' => 'Community', 'es' => 'Comunidad'],
    'r6_d'    => ['en' => 'Connect with other Rhinometric operators, share best practices, and contribute feedback.', 'es' => 'Conéctate con otros operadores de Rhinometric, comparte buenas prácticas y contribuye con retroalimentación.'],
    'cta_t'   => ['en' => 'Need help?', 'es' => '¿Necesitas ayuda?'],
    'cta_d'   => ['en' => 'Our team is here to help you evaluate and deploy Rhinometric.', 'es' => 'Nuestro equipo está aquí para ayudarte a evaluar y desplegar Rhinometric.'],
    'cta_btn' => ['en' => 'Contact support', 'es' => 'Contactar soporte'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };
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
      <?php
      $icons = ['📖', '🏗️', '⚙️', '📝', '❓', '💬'];
      for ($i = 1; $i <= 6; $i++) : ?>
      <div class="card">
        <div class="card-icon" aria-hidden="true"><?php echo $icons[$i - 1]; ?></div>
        <h3 class="card-title"><?php echo esc_html($__("r{$i}_t")); ?></h3>
        <p><?php echo esc_html($__("r{$i}_d")); ?></p>
      </div>
      <?php endfor; ?>
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
