<?php
/**
 * page-deployment.php — Rhinometric v3
 * Deployment models: on-premise, private cloud, hybrid.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Deployment models', 'es' => 'Modelos de despliegue'],
    'lead'    => ['en' => 'Run Rhinometric wherever your data lives — on your hardware, in your cloud, or both.', 'es' => 'Ejecuta Rhinometric donde vivan tus datos — en tu hardware, en tu nube, o ambos.'],
    'op_t'    => ['en' => 'On-premise', 'es' => 'On-premise'],
    'op_d'    => ['en' => 'Full control on your hardware. Air-gapped environments supported. Ideal for regulated industries.', 'es' => 'Control total en tu hardware. Entornos air-gapped soportados. Ideal para industrias reguladas.'],
    'op_f1'   => ['en' => 'Docker-based deployment', 'es' => 'Despliegue basado en Docker'],
    'op_f2'   => ['en' => 'Offline license validation', 'es' => 'Validación de licencia offline'],
    'op_f3'   => ['en' => 'Air-gap ready', 'es' => 'Preparado para air-gap'],
    'pc_t'    => ['en' => 'Private cloud', 'es' => 'Nube privada'],
    'pc_d'    => ['en' => 'Deploy on AWS, Azure, or GCP inside your own VPC. No shared tenancy, no data egress.', 'es' => 'Despliega en AWS, Azure o GCP dentro de tu propio VPC. Sin tenencia compartida, sin egreso de datos.'],
    'pc_f1'   => ['en' => 'AWS / Azure / GCP support', 'es' => 'Soporte AWS / Azure / GCP'],
    'pc_f2'   => ['en' => 'VPC-only networking', 'es' => 'Red solo VPC'],
    'pc_f3'   => ['en' => 'Auto-scaling capable', 'es' => 'Auto-escalado disponible'],
    'hy_t'    => ['en' => 'Hybrid', 'es' => 'Híbrido'],
    'hy_d'    => ['en' => 'Combine on-prem collection with cloud storage and visualization. Best of both worlds.', 'es' => 'Combina recolección on-prem con almacenamiento y visualización en la nube. Lo mejor de ambos mundos.'],
    'hy_f1'   => ['en' => 'Local collectors, remote storage', 'es' => 'Colectores locales, almacenamiento remoto'],
    'hy_f2'   => ['en' => 'Edge-to-cloud telemetry', 'es' => 'Telemetría edge-to-cloud'],
    'hy_f3'   => ['en' => 'Centralized dashboards', 'es' => 'Dashboards centralizados'],
    'cta_t'   => ['en' => 'Not sure which model fits?', 'es' => '¿No sabes qué modelo encaja?'],
    'cta_d'   => ['en' => 'We can help you evaluate the best deployment strategy for your infrastructure.', 'es' => 'Podemos ayudarte a evaluar la mejor estrategia de despliegue para tu infraestructura.'],
    'cta_btn' => ['en' => 'Talk to us', 'es' => 'Habla con nosotros'],
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
      $models = [
          ['key' => 'op', 'icon' => '🏢'],
          ['key' => 'pc', 'icon' => '☁️'],
          ['key' => 'hy', 'icon' => '🔄'],
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
          <li><?php echo esc_html($__("{$k}_f3")); ?></li>
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
