<?php
get_header();

$errors = [];
$success = false;
$name = '';
$email = '';
$company = '';
$use_case = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['rinometry_download_nonce']) || !wp_verify_nonce($_POST['rinometry_download_nonce'], 'rinometry_download')) {
        $errors[] = __('Security check failed. Please try again.', 'rinometry');
    } else {
        $name = sanitize_text_field(wp_unslash($_POST['name'] ?? ''));
        $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
        $company = sanitize_text_field(wp_unslash($_POST['company'] ?? ''));
        $use_case = sanitize_textarea_field(wp_unslash($_POST['use_case'] ?? ''));

        if ($name === '') {
            $errors[] = __('Name is required.', 'rinometry');
        }
        if ($email === '' || !is_email($email)) {
            $errors[] = __('A valid email is required.', 'rinometry');
        }
        if ($use_case === '') {
            $errors[] = __('Please describe your primary use case.', 'rinometry');
        }

        if (empty($errors)) {
            $lead_id = wp_insert_post([
                'post_type' => 'download_lead',
                'post_title' => $name . ' <' . $email . '>',
                'post_status' => 'private',
            ]);

            if (!is_wp_error($lead_id)) {
                update_post_meta($lead_id, '_rino_email', $email);
                update_post_meta($lead_id, '_rino_company', $company);
                update_post_meta($lead_id, '_rino_use_case', $use_case);
            }

            $download_url = rinometry_get_download_url();
            $thank_you_url = get_permalink(get_page_by_path('thank-you'));

            $subject = __('Your RHINOMETRIC download link', 'rinometry');
            $message = sprintf(
                "%s\n\n%s\n%s\n\n%s",
              __('Thanks for your interest in RHINOMETRIC. Use the link below to download:', 'rinometry'),
                $download_url,
                __('Need help installing? Visit the thank you page for next steps:', 'rinometry'),
                $thank_you_url
            );

            wp_mail($email, $subject, $message);
            $success = true;
        }
    }
}
?>
<section class="section">
  <div class="container split">
    <div>
      <h1 class="section-title"><?php esc_html_e('Download RHINOMETRIC', 'rinometry'); ?></h1>
      <p class="section-lead"><?php esc_html_e('Complete the form to receive your download link and installation guidance.', 'rinometry'); ?></p>
      <div class="card">
        <h2><?php esc_html_e('What happens next', 'rinometry'); ?></h2>
        <ol>
          <li><?php esc_html_e('We send the download link to your email.', 'rinometry'); ?></li>
          <li><?php esc_html_e('You receive installation steps and quick-start guidance.', 'rinometry'); ?></li>
          <li><?php esc_html_e('We follow up to support your evaluation.', 'rinometry'); ?></li>
        </ol>
      </div>
    </div>
    <div>
      <form class="form" method="post" action="<?php echo esc_url(get_permalink()); ?>" novalidate>
        <h2><?php esc_html_e('Get the download', 'rinometry'); ?></h2>
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
            <h3><?php esc_html_e('Download sent!', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Check your inbox for the download link. You can also use the link below:', 'rinometry'); ?></p>
            <p><a class="btn btn-primary" href="<?php echo esc_url(rinometry_get_download_url()); ?>"><?php esc_html_e('Download now', 'rinometry'); ?></a></p>
            <p><a href="<?php echo esc_url(get_permalink(get_page_by_path('thank-you'))); ?>"><?php esc_html_e('View installation steps', 'rinometry'); ?></a></p>
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
          <label for="use_case"><?php esc_html_e('Primary use case', 'rinometry'); ?></label>
          <textarea id="use_case" name="use_case" required><?php echo esc_textarea($use_case); ?></textarea>
          <p class="helper"><?php esc_html_e('Example: observability for regulated on-prem workloads.', 'rinometry'); ?></p>
        </div>
        <?php wp_nonce_field('rinometry_download', 'rinometry_download_nonce'); ?>
        <button class="btn btn-primary" type="submit"><?php esc_html_e('Send download link', 'rinometry'); ?></button>
      </form>
    </div>
  </div>
</section>
<?php
get_footer();
