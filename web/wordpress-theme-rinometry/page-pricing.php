<?php
/**
 * page-pricing.php — Rhinometric v3
 * Pricing tiers: Starter, Professional, Enterprise.
 */
get_header();
$lang = rinometry_get_current_language();
$t = [
    'title'   => ['en' => 'Pricing', 'es' => 'Precios'],
    'lead'    => ['en' => 'Transparent, predictable pricing. No per-seat fees, no hidden data charges.', 'es' => 'Precios transparentes y predecibles. Sin cargos por usuario, sin tarifas ocultas por datos.'],
    's_name'  => ['en' => 'Starter', 'es' => 'Starter'],
    's_price' => ['en' => 'Free', 'es' => 'Gratis'],
    's_desc'  => ['en' => 'For evaluation and small-scale deployments.', 'es' => 'Para evaluación y despliegues a pequeña escala.'],
    's_f1'    => ['en' => 'Metrics, logs & traces', 'es' => 'Métricas, logs y trazas'],
    's_f2'    => ['en' => 'Single node', 'es' => 'Nodo único'],
    's_f3'    => ['en' => '7-day retention', 'es' => 'Retención de 7 días'],
    's_f4'    => ['en' => 'Community support', 'es' => 'Soporte comunitario'],
    'p_name'  => ['en' => 'Professional', 'es' => 'Profesional'],
    'p_price' => ['en' => 'Contact us', 'es' => 'Contáctanos'],
    'p_desc'  => ['en' => 'For teams running production workloads.', 'es' => 'Para equipos con cargas de trabajo en producción.'],
    'p_f1'    => ['en' => 'Everything in Starter', 'es' => 'Todo lo de Starter'],
    'p_f2'    => ['en' => 'High-availability mode', 'es' => 'Modo alta disponibilidad'],
    'p_f3'    => ['en' => '90-day retention', 'es' => 'Retención de 90 días'],
    'p_f4'    => ['en' => 'Email support (48h SLA)', 'es' => 'Soporte por email (SLA 48h)'],
    'e_name'  => ['en' => 'Enterprise', 'es' => 'Enterprise'],
    'e_price' => ['en' => 'Custom', 'es' => 'Personalizado'],
    'e_desc'  => ['en' => 'For organizations with compliance, scale, or air-gap requirements.', 'es' => 'Para organizaciones con requisitos de cumplimiento, escala o air-gap.'],
    'e_f1'    => ['en' => 'Everything in Professional', 'es' => 'Todo lo de Profesional'],
    'e_f2'    => ['en' => 'Air-gap & offline licensing', 'es' => 'Air-gap y licencia offline'],
    'e_f3'    => ['en' => 'Custom retention policies', 'es' => 'Políticas de retención personalizadas'],
    'e_f4'    => ['en' => 'Dedicated support (24h SLA)', 'es' => 'Soporte dedicado (SLA 24h)'],
    'cta_btn' => ['en' => 'Contact sales', 'es' => 'Contactar ventas'],
    'faq_t'   => ['en' => 'Common questions', 'es' => 'Preguntas frecuentes'],
    'faq1_q'  => ['en' => 'Is there a free trial?', 'es' => '¿Hay prueba gratuita?'],
    'faq1_a'  => ['en' => 'Yes. The Starter tier is free forever for evaluation and small workloads.', 'es' => 'Sí. El nivel Starter es gratis para siempre para evaluación y cargas pequeñas.'],
    'faq2_q'  => ['en' => 'Do you charge per seat or per GB?', 'es' => '¿Cobran por usuario o por GB?'],
    'faq2_a'  => ['en' => 'No. Pricing is based on deployment tier, not on data volume or user count.', 'es' => 'No. El precio se basa en el nivel de despliegue, no en volumen de datos ni usuarios.'],
    'faq3_q'  => ['en' => 'Can I upgrade later?', 'es' => '¿Puedo actualizar después?'],
    'faq3_a'  => ['en' => 'Absolutely. Upgrade from Starter to Professional or Enterprise at any time with zero downtime.', 'es' => 'Absolutamente. Actualiza de Starter a Profesional o Enterprise en cualquier momento sin tiempo de inactividad.'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };
$tiers = [
    ['key' => 's', 'highlight' => false],
    ['key' => 'p', 'highlight' => true],
    ['key' => 'e', 'highlight' => false],
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
      <?php foreach ($tiers as $tier) :
          $k = $tier['key'];
          $classes = 'pricing-card card' . ($tier['highlight'] ? ' is-featured' : '');
      ?>
      <div class="<?php echo esc_attr($classes); ?>">
        <h2 class="card-title"><?php echo esc_html($__("{$k}_name")); ?></h2>
        <div class="pricing-price"><?php echo esc_html($__("{$k}_price")); ?></div>
        <p><?php echo esc_html($__("{$k}_desc")); ?></p>
        <ul>
          <li><?php echo esc_html($__("{$k}_f1")); ?></li>
          <li><?php echo esc_html($__("{$k}_f2")); ?></li>
          <li><?php echo esc_html($__("{$k}_f3")); ?></li>
          <li><?php echo esc_html($__("{$k}_f4")); ?></li>
        </ul>
        <a class="btn <?php echo $tier['highlight'] ? 'btn-primary' : 'btn-outline'; ?>"
           href="<?php echo esc_url(rinometry_page_url('evaluation')); ?>">
          <?php echo esc_html($__('cta_btn')); ?>
        </a>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container" style="max-width:680px;">
    <h2 class="section-title"><?php echo esc_html($__('faq_t')); ?></h2>
    <?php for ($i = 1; $i <= 3; $i++) : ?>
    <details class="card" style="margin-bottom:1rem;">
      <summary><strong><?php echo esc_html($__("faq{$i}_q")); ?></strong></summary>
      <p style="margin-top:.5rem;"><?php echo esc_html($__("faq{$i}_a")); ?></p>
    </details>
    <?php endfor; ?>
  </div>
</section>

<?php get_footer(); ?>
