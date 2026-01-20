<?php
get_header();

$errors = [];
$success = false;
$name = '';
$email = '';
$company = '';
$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['rinometry_contact_nonce']) || !wp_verify_nonce($_POST['rinometry_contact_nonce'], 'rinometry_contact')) {
        $errors[] = __('Security check failed. Please try again.', 'rinometry');
    } else {
        $name = sanitize_text_field(wp_unslash($_POST['name'] ?? ''));
        $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
        $company = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
        $message = sanitize_textarea_field(wp_unslash($_POST['message'] ?? ''));

        if ($name === '') {
            $errors[] = __('Name is required.', 'rinometry');
        }
        if ($email === '' || !is_email($email)) {
            $errors[] = __('A valid email is required.', 'rinometry');
        }
        if ($message === '') {
            $errors[] = __('Please include a short message.', 'rinometry');
        }

        if (empty($errors)) {
            $subject = __('RHINOMETRIC demo request', 'rinometry');
            $body = sprintf(
                "%s\n\n%s: %s\n%s: %s\n\n%s",
                __('New demo request received:', 'rinometry'),
                __('Name', 'rinometry'),
                $name,
                __('Company', 'rinometry'),
                $company,
                $message
            );

            wp_mail(get_option('admin_email'), $subject, $body, ['Reply-To: ' . $email]);
            $success = true;
        }
    }
}
?>
<section class="section">
  <div class="container split">
    <div>
      <h1 class="section-title"><?php esc_html_e('Request a demo', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('Tell us about your environment and we will schedule a tailored walkthrough.', 'rinometry'); ?></p>
      <div class="card">
        <h2><?php esc_html_e('What to expect', 'rinometry'); ?></h2>
        <ul>
          <li><?php esc_html_e('A quick discovery call with our product team.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Demo tailored to your observability goals.', 'rinometry'); ?></li>
          <li><?php esc_html_e('Guidance on evaluation and next steps.', 'rinometry'); ?></li>
        </ul>
      </div>
    </div>
    <div>
      <form class="form" method="post" action="<?php echo esc_url(get_permalink()); ?>" novalidate>
        <h2><?php esc_html_e('Contact form', 'rinometry'); ?></h2>
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
          <label for="company"><?php esc_html_e('Company', 'rinometry'); ?></label>
          <input id="company" name="company" type="text" value="<?php echo esc_attr($company); ?>">
        </div>
        <div class="field">
          <label for="message"><?php esc_html_e('Message', 'rinometry'); ?></label>
          <textarea id="message" name="message" required><?php echo esc_textarea($message); ?></textarea>
        </div>
        <?php wp_nonce_field('rinometry_contact', 'rinometry_contact_nonce'); ?>
        <button class="btn btn-primary" type="submit"><?php esc_html_e('Send request', 'rinometry'); ?></button>
      </form>
    </div>
  </div>
</section>
<?php
get_footer();
