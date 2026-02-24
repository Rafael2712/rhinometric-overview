<?php
/**
 * page-deployment.php — Rhinometric v3
 * Deployment models: on-premise and dedicated VM (single-tenant).
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Deployment models', 'es' => 'Modelos de despliegue'],
    'lead'    => ['en' => 'Two deployment options — both single-tenant, both under your full control.', 'es' => 'Dos opciones de despliegue — ambas single-tenant, ambas bajo tu control total.'],
    'ps_t'    => ['en' => 'Private SaaS (Dedicated VM)', 'es' => 'SaaS privado (VM dedicada)'],
    'ps_d'    => ['en' => 'A dedicated virtual machine per customer within a European cloud provider. No shared resources, no multi-tenancy.', 'es' => 'Una máquina virtual dedicada por cliente en un proveedor cloud europeo. Sin recursos compartidos, sin multi-tenancy.'],
    'ps_f1'   => ['en' => 'Dedicated VM — no shared resources', 'es' => 'VM dedicada — sin recursos compartidos'],
    'ps_f2'   => ['en' => 'European cloud provider', 'es' => 'Proveedor cloud europeo'],
    'op_t'    => ['en' => 'On-premise', 'es' => 'On-premise'],
    'op_d'    => ['en' => 'Full installation on your own physical servers. Air-gapped environments supported. Ideal for regulated industries.', 'es' => 'Instalación completa en tus propios servidores físicos. Entornos air-gapped soportados. Ideal para industrias reguladas.'],
    'op_f1'   => ['en' => 'Docker-based deployment on your hardware', 'es' => 'Despliegue basado en Docker en tu hardware'],
    'op_f2'   => ['en' => 'Offline license validation, air-gap ready', 'es' => 'Validación de licencia offline, preparado para air-gap'],
    'cta_t'   => ['en' => 'Not sure which model fits?', 'es' => '¿No sabes qué modelo encaja?'],
    'cta_d'   => ['en' => 'We can help you evaluate the best deployment strategy for your infrastructure.', 'es' => 'Podemos ayudarte a evaluar la mejor estrategia de despliegue para tu infraestructura.'],
    'cta_btn' => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
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
    <div class="grid-2">
      <?php
      $models = [
          ['key' => 'ps', 'icon' => '☁️'],
          ['key' => 'op', 'icon' => '🏢'],
      ];
      foreach ($models as $m) :
          $k = $m['key'];
      ?>
      <div class="deployment-card card">
        <div class="card-icon" aria-hidden="true"><?php echo $m['icon']; ?></div>
        <h2 class="card-title"><?php echo esc_html($__("{$k}_t")); ?></h2>
        <p><?php echo esc_html($__("{$k}_d")); ?></p>
        <ul>
          <li><?php echo esc_html($__("{$k}_f1")); ?></li>
          <li><?php echo esc_html($__("{$k}_f2")); ?></li>
        </ul>
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
