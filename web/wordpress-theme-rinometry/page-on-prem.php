<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('On-Prem & Data Sovereignty', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('Deploy Rhinometric on your infrastructure to keep telemetry, retention, and access under your control.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-onprem.svg'); ?>" alt="<?php esc_attr_e('On-prem icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Data residency', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Maintain full ownership of telemetry and retention policies.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-platform.svg'); ?>" alt="<?php esc_attr_e('Platform icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Hybrid-ready', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Connect edge environments while centralizing governance and reporting.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-security.svg'); ?>" alt="<?php esc_attr_e('Security icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Operational control', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Tune retention, encryption, and access to meet regulatory requirements.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
