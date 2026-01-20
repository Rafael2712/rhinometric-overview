<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('Security', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('Security is built into RHINOMETRIC, from access controls to infrastructure hardening. We do not claim certifications that are not in place.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-security.svg'); ?>" alt="<?php esc_attr_e('Security icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Access control', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Role-based access and least-privilege defaults.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-logs.svg'); ?>" alt="<?php esc_attr_e('Logs icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Audit visibility', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Operational logs and audit-ready reporting for compliance teams.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-media">
          <img class="icon" src="<?php echo esc_url(get_template_directory_uri() . '/assets/icon-onprem.svg'); ?>" alt="<?php esc_attr_e('On-prem icon', 'rinometry'); ?>">
          <div>
            <h3><?php esc_html_e('Secure deployment', 'rinometry'); ?></h3>
            <p><?php esc_html_e('Support for hardened environments and on-prem controls.', 'rinometry'); ?></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
