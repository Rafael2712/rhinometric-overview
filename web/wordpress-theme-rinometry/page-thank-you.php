<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('Thank you for downloading Rhinometric', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('Your download link is on its way. Use the steps below to get started.', 'rinometry'); ?></p>
    <p><a class="btn btn-primary" href="<?php echo esc_url(rinometry_get_download_url()); ?>"><?php esc_html_e('Download Rhinometric', 'rinometry'); ?></a></p>
    <div class="grid">
      <div class="card">
        <h2><?php esc_html_e('1. Prepare your environment', 'rinometry'); ?></h2>
        <p><?php esc_html_e('Verify your infrastructure prerequisites and network access. Placeholder: add specific requirements.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h2><?php esc_html_e('2. Install Rhinometric', 'rinometry'); ?></h2>
        <p><?php esc_html_e('Follow the installation guide to deploy services securely. Placeholder: link to install guide.', 'rinometry'); ?></p>
      </div>
      <div class="card">
        <h2><?php esc_html_e('3. Validate telemetry', 'rinometry'); ?></h2>
        <p><?php esc_html_e('Connect your data sources and validate dashboards. Placeholder: link to quick start.', 'rinometry'); ?></p>
      </div>
    </div>
    <div style="margin-top: 2rem;">
      <a class="btn btn-secondary" href="<?php echo esc_url(rinometry_page_url('contact')); ?>">
        <?php esc_html_e('Need help? Request an evaluation', 'rinometry'); ?>
      </a>
    </div>
  </div>
</section>
<?php
get_footer();
