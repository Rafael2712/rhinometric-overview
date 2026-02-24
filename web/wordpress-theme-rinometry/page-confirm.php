<?php
/**
 * Template Name: Confirm — Double Opt-In
 * Slug: confirm
 *
 * Validates a confirmation token sent via email.
 * If valid: marks lead confirmed, scores, pushes to Zoho, notifies sales.
 */
get_header();

$lang = rinometry_get_current_language();

/* ── i18n ── */
$t = [
    'confirmed_title'      => ['en' => 'Email Confirmed',                     'es' => 'Email Confirmado'],
    'confirmed_text'       => ['en' => 'Your evaluation request is active. Our team will contact you within 1–2 business days.', 'es' => 'Tu solicitud de evaluación está activa. Nuestro equipo te contactará en 1–2 días hábiles.'],
    'already_title'        => ['en' => 'Already Confirmed',                   'es' => 'Ya Confirmado'],
    'already_text'         => ['en' => 'This request was already confirmed. Our team has been notified.', 'es' => 'Esta solicitud ya fue confirmada. Nuestro equipo ha sido notificado.'],
    'expired_title'        => ['en' => 'Link Expired',                        'es' => 'Enlace Expirado'],
    'expired_text'         => ['en' => 'This confirmation link has expired. Please submit a new request.', 'es' => 'Este enlace de confirmación ha expirado. Por favor, envía una nueva solicitud.'],
    'invalid_title'        => ['en' => 'Invalid Link',                        'es' => 'Enlace Inválido'],
    'invalid_text'         => ['en' => 'This confirmation link is not valid. If you submitted a request, check your email for the correct link.', 'es' => 'Este enlace de confirmación no es válido. Si enviaste una solicitud, revisa tu email para el enlace correcto.'],
    'back_contact'         => ['en' => 'Request a new evaluation',            'es' => 'Solicitar nueva evaluación'],
    'back_home'            => ['en' => 'Return to homepage',                  'es' => 'Volver al inicio'],
];

$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};

/* ── Process token ── */
$result = rhinometric_handle_lead_confirmation();
$status = $result['status'] ?? 'invalid';

/* ── Map status to display ── */
$icon_map = [
    'confirmed'         => '✓',
    'already_confirmed' => '✓',
    'expired'           => '⏱',
    'invalid'           => '✗',
];
$title_key = [
    'confirmed'         => 'confirmed_title',
    'already_confirmed' => 'already_title',
    'expired'           => 'expired_title',
    'invalid'           => 'invalid_title',
];
$text_key = [
    'confirmed'         => 'confirmed_text',
    'already_confirmed' => 'already_text',
    'expired'           => 'expired_text',
    'invalid'           => 'invalid_text',
];
$css_class = [
    'confirmed'         => 'confirm-ok',
    'already_confirmed' => 'confirm-ok',
    'expired'           => 'confirm-warn',
    'invalid'           => 'confirm-err',
];

$icon  = $icon_map[$status] ?? '✗';
$title = $__($title_key[$status] ?? 'invalid_title');
$text  = $__($text_key[$status] ?? 'invalid_text');
$cls   = $css_class[$status] ?? 'confirm-err';
?>

<section class="page-hero">
  <div class="container">
    <h1><?php echo esc_html($title); ?></h1>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="confirm-card <?php echo esc_attr($cls); ?>">
      <div class="confirm-icon"><?php echo esc_html($icon); ?></div>
      <h2><?php echo esc_html($title); ?></h2>
      <p><?php echo esc_html($text); ?></p>
      <div class="confirm-actions">
        <?php if ($status === 'expired' || $status === 'invalid') : ?>
          <a href="<?php echo esc_url(home_url('/contact/')); ?>" class="btn btn-primary"><?php echo esc_html($__('back_contact')); ?></a>
        <?php endif; ?>
        <a href="<?php echo esc_url(home_url('/')); ?>" class="btn btn-outline"><?php echo esc_html($__('back_home')); ?></a>
      </div>
    </div>
  </div>
</section>

<?php get_footer(); ?>
