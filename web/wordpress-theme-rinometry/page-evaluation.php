<?php
/**
 * page-evaluation.php — Rhinometric Evaluation Request
 * Compact evaluation page with i18n EN/ES + lead form.
 * Template for WP page with slug "evaluation".
 */

get_header();

$errors  = [];
$success = false;
$name    = '';
$email   = '';
$company = '';
$message = '';
$lang    = rinometry_get_current_language();

/* ================================================================
   i18n string catalogue
   ================================================================ */
$t = [
    'title'       => ['en' => 'Enterprise Evaluation Session', 'es' => 'Sesión de Evaluación Empresarial'],
    'subtitle'    => ['en' => 'Assess deployment fit, architecture compatibility and operational alignment.', 'es' => 'Evalúe el encaje del despliegue, la compatibilidad arquitectónica y la alineación operativa.'],
    'covers_t'    => ['en' => 'What this session covers', 'es' => 'Qué cubre esta sesión'],
    'covers_1'    => ['en' => 'Deployment model discussion (On-premise or dedicated VM in a European public cloud environment)', 'es' => 'Discusión del modelo de despliegue (On-premise o VM dedicada en entorno de nube pública europeo)'],
    'covers_2'    => ['en' => 'Architecture walkthrough (Prometheus + VictoriaMetrics, Loki, Jaeger, Grafana)', 'es' => 'Recorrido arquitectónico (Prometheus + VictoriaMetrics, Loki, Jaeger, Grafana)'],
    'covers_3'    => ['en' => 'Security and isolation model review', 'es' => 'Revisión del modelo de seguridad y aislamiento'],
    'covers_4'    => ['en' => 'Q&A tailored to your infrastructure', 'es' => 'Preguntas y respuestas adaptadas a tu infraestructura'],
    'reassurance' => ['en' => 'This is a focused, technical and strategic session — not a generic sales pitch.', 'es' => 'Esta es una sesión enfocada, técnica y estratégica — no una charla de ventas genérica.'],
    'form_t'      => ['en' => 'Request your evaluation', 'es' => 'Solicita tu evaluación'],
];
$__ = function ($k) use ($t, $lang) { return $t[$k][$lang] ?? $t[$k]['en'] ?? $k; };

/* ================================================================
   Form processing (reuses demo_lead CPT for data continuity)
   ================================================================ */
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['rinometry_eval_nonce']) || !wp_verify_nonce($_POST['rinometry_eval_nonce'], 'rinometry_eval')) {
        $errors[] = __('Security check failed. Please try again.', 'rinometry');
    } else {
        $name     = sanitize_text_field(wp_unslash($_POST['name'] ?? ''));
        $email    = sanitize_email(wp_unslash($_POST['email'] ?? ''));
        $company  = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
        $message  = sanitize_textarea_field(wp_unslash($_POST['message'] ?? ''));
        $honeypot = sanitize_text_field(wp_unslash($_POST['website'] ?? ''));

        if ($honeypot !== '') {
            $errors[] = __('Submission rejected. Please try again.', 'rinometry');
        }
        if ($name === '') {
            $errors[] = __('Name is required.', 'rinometry');
        }
        if ($email === '' || !is_email($email)) {
            $errors[] = __('A valid email is required.', 'rinometry');
        }
        if (empty($errors) && !rinometry_check_rate_limit('demo')) {
            $errors[] = __('Please wait a moment before submitting again.', 'rinometry');
        }

        if (empty($errors)) {
            $lead_id = wp_insert_post([
                'post_type'   => 'demo_lead',
                'post_title'  => $name . ' <' . $email . '>',
                'post_status' => 'private',
            ]);

            if (!is_wp_error($lead_id)) {
                update_post_meta($lead_id, '_rino_email',   $email);
                update_post_meta($lead_id, '_rino_company', $company);
                update_post_meta($lead_id, '_rino_message', $message);
                update_post_meta($lead_id, '_rino_source',  'evaluation');
            }

            $recipient = rinometry_get_lead_recipient();
            $subject   = __('Rhinometric evaluation request', 'rinometry');
            $body      = sprintf(
                "%s\n\n%s: %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s",
                __('New evaluation request received:', 'rinometry'),
                __('Name', 'rinometry'), $name,
                __('Email', 'rinometry'), $email,
                __('Company', 'rinometry'), $company ?: __('Not provided', 'rinometry'),
                __('Message', 'rinometry'), $message ?: __('Not provided', 'rinometry'),
                __('Language', 'rinometry'), strtoupper($lang),
                __('Submitted at', 'rinometry'), current_time('mysql')
            );
            wp_mail($recipient, $subject, $body, ['Reply-To: ' . $email]);

            $user_subject = __('Your Rhinometric evaluation request', 'rinometry');
            $user_body    = sprintf(
                "%s\n\n%s\n%s\n\n%s",
                __('Thanks for requesting an evaluation session with Rhinometric.', 'rinometry'),
                __('We will reach out shortly to coordinate a session.', 'rinometry'),
                __('Submitted at:', 'rinometry') . ' ' . current_time('mysql'),
                __('Helpful links: Download, Roadmap, Contact.', 'rinometry')
            );
            wp_mail($email, $user_subject, $user_body);
            $success = true;
        }
    }
}
?>

<section class="page-hero">
  <div class="container">
    <h1><?php echo esc_html($__('title')); ?></h1>
    <p class="hero-lead"><?php echo esc_html($__('subtitle')); ?></p>
  </div>
</section>

<section class="section">
  <div class="container split">
    <div>
      <h2><?php echo esc_html($__('covers_t')); ?></h2>
      <ul class="check-list">
        <li><?php echo esc_html($__('covers_1')); ?></li>
        <li><?php echo esc_html($__('covers_2')); ?></li>
        <li><?php echo esc_html($__('covers_3')); ?></li>
        <li><?php echo esc_html($__('covers_4')); ?></li>
      </ul>
      <p class="text-muted"><em><?php echo esc_html($__('reassurance')); ?></em></p>
    </div>
    <div>
      <form class="form js-disable-on-submit" method="post" action="<?php echo esc_url(get_permalink()); ?>" novalidate>
        <h2><?php echo esc_html($__('form_t')); ?></h2>
        <?php if (!empty($errors)) : ?>
          <div class="error-list" role="alert" aria-live="assertive">
            <strong><?php esc_html_e('Please fix the following:', 'rinometry'); ?></strong>
            <ul>
              <?php foreach ($errors as $error) : ?>
                <li><?php echo esc_html($error); ?></li>
              <?php endforeach; ?>
            </ul>
          </div>
        <?php endif; ?>
        <?php if ($success) : ?>
          <div class="card" role="status" aria-live="polite">
            <h3><?php esc_html_e('Thank you!', 'rinometry'); ?></h3>
            <p><?php esc_html_e('We received your request and will reach out shortly.', 'rinometry'); ?></p>
          </div>
        <?php endif; ?>
        <div class="field">
          <label for="name"><?php esc_html_e('Name', 'rinometry'); ?></label>
          <input id="name" name="name" type="text" value="<?php echo esc_attr($name); ?>" required>
        </div>
        <div class="field">
          <label for="email"><?php esc_html_e('Work email', 'rinometry'); ?></label>
          <input id="email" name="email" type="email" value="<?php echo esc_attr($email); ?>" required>
        </div>
        <div class="field">
          <label for="company"><?php esc_html_e('Company (optional)', 'rinometry'); ?></label>
          <input id="company" name="company" type="text" value="<?php echo esc_attr($company); ?>">
        </div>
        <div class="field">
          <label for="message"><?php esc_html_e('Message (optional)', 'rinometry'); ?></label>
          <textarea id="message" name="message"><?php echo esc_textarea($message); ?></textarea>
        </div>
        <div class="field honeypot" aria-hidden="true">
          <label for="website"><?php esc_html_e('Website', 'rinometry'); ?></label>
          <input id="website" name="website" type="text" autocomplete="off" tabindex="-1">
        </div>
        <?php wp_nonce_field('rinometry_eval', 'rinometry_eval_nonce'); ?>
        <button class="btn btn-primary" type="submit"><?php esc_html_e('Send request', 'rinometry'); ?></button>
      </form>
    </div>
  </div>
</section>

<?php get_footer(); ?>
