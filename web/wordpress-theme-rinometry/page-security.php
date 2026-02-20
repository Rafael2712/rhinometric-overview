<?php
/**
 * page-security.php — Rhinometric v3
 * Security & trust: mTLS, RBAC, EU data residency, air-gap.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Security & trust', 'es' => 'Seguridad y confianza'],
    'lead'    => ['en' => 'Security is foundational to Rhinometric — not an afterthought. Every layer is hardened from day one.', 'es' => 'La seguridad es fundamental en Rhinometric — no una ocurrencia tardía. Cada capa está reforzada desde el día uno.'],
    'c1_t'    => ['en' => 'mTLS everywhere', 'es' => 'mTLS en todas partes'],
    'c1_d'    => ['en' => 'All inter-service communication uses mutual TLS. Zero trust networking by default across every component.', 'es' => 'Toda la comunicación entre servicios usa TLS mutuo. Red zero-trust por defecto en cada componente.'],
    'c2_t'    => ['en' => 'Role-based access control', 'es' => 'Control de acceso basado en roles'],
    'c2_d'    => ['en' => 'Granular RBAC with least-privilege defaults. Audit trail for every user action and configuration change.', 'es' => 'RBAC granular con mínimos privilegios por defecto. Pista de auditoría para cada acción y cambio de configuración.'],
    'c3_t'    => ['en' => 'EU data residency', 'es' => 'Residencia de datos en la UE'],
    'c3_d'    => ['en' => 'All data stays within EU borders. GDPR-ready architecture designed for regulatory compliance.', 'es' => 'Todos los datos permanecen dentro de las fronteras de la UE. Arquitectura preparada para cumplimiento GDPR.'],
    'c4_t'    => ['en' => 'Air-gap support', 'es' => 'Soporte air-gap'],
    'c4_d'    => ['en' => 'Fully deployable in disconnected environments with offline license validation and local artifact mirrors.', 'es' => 'Completamente desplegable en entornos desconectados con validación de licencia offline y mirrors de artefactos locales.'],
    'c5_t'    => ['en' => 'Network policies', 'es' => 'Políticas de red'],
    'c5_d'    => ['en' => 'Fine-grained network segmentation and ingress/egress controls baked into every deployment template.', 'es' => 'Segmentación de red granular y controles de ingreso/egreso integrados en cada plantilla de despliegue.'],
    'c6_t'    => ['en' => 'Audit logging', 'es' => 'Auditoría de logs'],
    'c6_d'    => ['en' => 'Complete operational audit trail with structured logging, exportable for compliance reporting.', 'es' => 'Pista de auditoría operacional completa con logging estructurado, exportable para reportes de cumplimiento.'],
    'comp_t'  => ['en' => 'Compliance readiness', 'es' => 'Preparación para cumplimiento'],
    'comp_d'  => ['en' => 'Rhinometric is designed with compliance in mind. We do not claim certifications we have not earned — but the architecture is built to support your compliance journey.', 'es' => 'Rhinometric está diseñado con el cumplimiento en mente. No afirmamos certificaciones que no hemos obtenido — pero la arquitectura está construida para apoyar tu proceso de cumplimiento.'],
    'cta_t'   => ['en' => 'Questions about security?', 'es' => '¿Preguntas sobre seguridad?'],
    'cta_d'   => ['en' => 'Our team can walk you through the security architecture in detail.', 'es' => 'Nuestro equipo puede explicarte la arquitectura de seguridad en detalle.'],
    'cta_btn' => ['en' => 'Contact us', 'es' => 'Contáctanos'],
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
      $cards = [
          ['k' => 'c1', 'icon' => '🔒'],
          ['k' => 'c2', 'icon' => '👤'],
          ['k' => 'c3', 'icon' => '🇪🇺'],
          ['k' => 'c4', 'icon' => '🔌'],
          ['k' => 'c5', 'icon' => '🌐'],
          ['k' => 'c6', 'icon' => '📋'],
      ];
      foreach ($cards as $c) :
      ?>
      <div class="card">
        <div class="card-icon" aria-hidden="true"><?php echo $c['icon']; ?></div>
        <h3 class="card-title"><?php echo esc_html($__($c['k'] . '_t')); ?></h3>
        <p><?php echo esc_html($__($c['k'] . '_d')); ?></p>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container" style="text-align:center; max-width:680px;">
    <h2 class="section-title"><?php echo esc_html($__('comp_t')); ?></h2>
    <p><?php echo esc_html($__('comp_d')); ?></p>
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
