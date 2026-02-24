<?php
/**
 * page-security.php — Rhinometric v3
 * Security posture: deployment isolation, data handling, encryption, access control.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'    => ['en' => 'Security and operational isolation by design', 'es' => 'Seguridad y aislamiento operativo por diseño'],
    'lead'     => ['en' => 'Rhinometric runs within customer-controlled environments with no shared runtime and no automatic export of telemetry to third-party services.', 'es' => 'Rhinometric se ejecuta dentro de entornos controlados por el cliente, sin runtime compartido y sin exportación automática de telemetría a servicios de terceros.'],

    'iso_t'    => ['en' => 'Deployment isolation', 'es' => 'Aislamiento de despliegue'],
    'iso_items'=> [
        'en' => ['On-premise or single-tenant VM deployment', 'Isolated instance per customer installation (no shared runtime)', 'Data remains within infrastructure controlled by the customer'],
        'es' => ['Despliegue on-premise o VM single-tenant', 'Instancia aislada por instalación de cliente (sin runtime compartido)', 'Los datos permanecen en la infraestructura controlada por el cliente'],
    ],

    'data_t'   => ['en' => 'Data handling and privacy', 'es' => 'Manejo de datos y privacidad'],
    'data_d1'  => ['en' => 'Rhinometric is not designed to process personal data as a primary use case. It processes technical telemetry: metrics, logs and operational events.', 'es' => 'Rhinometric no está diseñado para procesar datos personales como caso de uso principal. Procesa telemetría técnica: métricas, logs y eventos operativos.'],
    'data_d2'  => ['en' => 'Logs may contain personal data indirectly if customers include it in log content.', 'es' => 'Los logs pueden contener datos personales indirectamente si los clientes los incluyen en el contenido de los logs.'],
    'data_d3'  => ['en' => 'Data remains under full customer control within the deployment environment. Retention and deletion policies are managed at the infrastructure level by the customer — for example through Loki retention for logs, metrics retention policies and internal database management.', 'es' => 'Los datos permanecen bajo el control total del cliente dentro del entorno de despliegue. Las políticas de retención y eliminación se gestionan a nivel de infraestructura por el cliente — por ejemplo, a través de la retención de Loki para logs, políticas de retención de métricas y gestión interna de base de datos.'],

    'exp_t'    => ['en' => 'No external export by default', 'es' => 'Sin exportación externa por defecto'],
    'exp_d1'   => ['en' => 'Rhinometric does not export metrics or logs to external services by default.', 'es' => 'Rhinometric no exporta métricas ni logs a servicios externos por defecto.'],
    'exp_d2'   => ['en' => 'Notifications are sent only when explicitly configured by the customer (Slack and/or email).', 'es' => 'Las notificaciones se envían solo cuando son configuradas explícitamente por el cliente (Slack y/o email).'],

    'enc_t'    => ['en' => 'Encryption and transport security', 'es' => 'Cifrado y seguridad de transporte'],
    'enc_items'=> [
        'en' => ['TLS 1.2 / 1.3 enforced', 'HTTPS end-to-end using Cloudflare + Origin TLS (Full Strict)', 'HSTS enabled', 'No plaintext traffic allowed in production environments'],
        'es' => ['TLS 1.2 / 1.3 obligatorio', 'HTTPS extremo a extremo usando Cloudflare + Origin TLS (Full Strict)', 'HSTS habilitado', 'Sin tráfico en texto plano permitido en entornos de producción'],
    ],

    'ac_t'     => ['en' => 'Access control', 'es' => 'Control de acceso'],
    'ac_d1'    => ['en' => 'Rhinometric provides basic role-based access control: Owner, Admin and User. Permissions are differentiated by role.', 'es' => 'Rhinometric proporciona control de acceso básico basado en roles: Owner, Admin y User. Los permisos se diferencian por rol.'],
    'ac_d2'    => ['en' => 'No SSO integration is available today (no OAuth, SAML or OIDC).', 'es' => 'No hay integración SSO disponible actualmente (ni OAuth, SAML ni OIDC).'],

    'resp_t'   => ['en' => 'Responsibility model', 'es' => 'Modelo de responsabilidad'],
    'resp_d1'  => ['en' => 'Rhinometric secures the application layer and enforces encrypted communication.', 'es' => 'Rhinometric asegura la capa de aplicación e impone comunicación cifrada.'],
    'resp_d2'  => ['en' => 'In on-premise deployments, infrastructure hardening, network perimeter configuration and host-level security controls remain under customer responsibility.', 'es' => 'En despliegues on-premise, el endurecimiento de infraestructura, la configuración del perímetro de red y los controles de seguridad a nivel de host son responsabilidad del cliente.'],
    'resp_d3'  => ['en' => 'In single-tenant VM deployments, environment isolation is preserved and infrastructure governance is defined with the customer.', 'es' => 'En despliegues de VM single-tenant, el aislamiento del entorno se preserva y la gobernanza de infraestructura se define con el cliente.'],

    'cta_t'    => ['en' => 'Questions about security?', 'es' => '¿Preguntas sobre seguridad?'],
    'cta_btn'  => ['en' => 'Request an Evaluation', 'es' => 'Solicitar evaluación'],
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
    <h2 class="section-title"><?php echo esc_html($__('iso_t')); ?></h2>
    <ul class="check-list">
      <?php foreach ($t['iso_items'][$lang] ?? $t['iso_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('data_t')); ?></h2>
    <p><?php echo esc_html($__('data_d1')); ?></p>
    <p><?php echo esc_html($__('data_d2')); ?></p>
    <p><?php echo esc_html($__('data_d3')); ?></p>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('exp_t')); ?></h2>
    <p><?php echo esc_html($__('exp_d1')); ?></p>
    <p><?php echo esc_html($__('exp_d2')); ?></p>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('enc_t')); ?></h2>
    <ul class="check-list">
      <?php foreach ($t['enc_items'][$lang] ?? $t['enc_items']['en'] as $item) : ?>
      <li><?php echo esc_html($item); ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('ac_t')); ?></h2>
    <p><?php echo esc_html($__('ac_d1')); ?></p>
    <p><?php echo esc_html($__('ac_d2')); ?></p>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <h2 class="section-title"><?php echo esc_html($__('resp_t')); ?></h2>
    <p><?php echo esc_html($__('resp_d1')); ?></p>
    <p><?php echo esc_html($__('resp_d2')); ?></p>
    <p><?php echo esc_html($__('resp_d3')); ?></p>
  </div>
</section>

<section class="section section-dark cta-section">
  <div class="container" style="text-align:center;">
    <h2><?php echo esc_html($__('cta_t')); ?></h2>
    <a class="btn btn-white btn-lg" href="<?php echo esc_url(rinometry_page_url('evaluation')); ?>"><?php echo esc_html($__('cta_btn')); ?></a>
  </div>
</section>

<?php get_footer(); ?>
