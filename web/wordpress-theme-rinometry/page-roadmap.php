<?php
get_header();
?>
<section class="section">
  <div class="container">
    <h1 class="section-title"><?php esc_html_e('Product Roadmap', 'rinometry'); ?></h1>
    <p class="section-lead"><?php esc_html_e('A transparent view of where Rhinometric is headed. Timelines are indicative and may evolve.', 'rinometry'); ?></p>
    <div class="grid">
      <div class="card">
        <span class="badge"><?php esc_html_e('Now', 'rinometry'); ?></span>
        <h3><?php esc_html_e('Validation & acquisition', 'rinometry'); ?></h3>
        <ul>
          <li><?php esc_html_e('Download gate with email delivery', 'rinometry'); ?></li>
          <li><?php esc_html_e('On-prem deployment documentation', 'rinometry'); ?></li>
          <li><?php esc_html_e('Observability dashboards and alerts', 'rinometry'); ?></li>
        </ul>
      </div>
      <div class="card">
        <span class="badge"><?php esc_html_e('Next', 'rinometry'); ?></span>
        <h3><?php esc_html_e('Commercial scale', 'rinometry'); ?></h3>
        <ul>
          <li><?php esc_html_e('Pricing and checkout workflow', 'rinometry'); ?></li>
          <li><?php esc_html_e('Customer portal and license management', 'rinometry'); ?></li>
          <li><?php esc_html_e('Expanded integration library', 'rinometry'); ?></li>
        </ul>
      </div>
      <div class="card">
        <span class="badge"><?php esc_html_e('Later', 'rinometry'); ?></span>
        <h3><?php esc_html_e('Ecosystem expansion', 'rinometry'); ?></h3>
        <ul>
          <li><?php esc_html_e('Automated compliance reporting', 'rinometry'); ?></li>
          <li><?php esc_html_e('Partner marketplace', 'rinometry'); ?></li>
          <li><?php esc_html_e('Advanced AI operations workflows', 'rinometry'); ?></li>
        </ul>
      </div>
    </div>
  </div>
</section>
<?php
get_footer();
