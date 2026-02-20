<?php
/**
 * footer.php — Rhinometric v3
 * Social section + footer grid + cookie banner
 */
?>
</main>

<!-- Social section (LinkedIn) -->
<section class="social-section">
  <div class="container social-inner">
    <h2 class="social-title" data-i18n="social_title"><?php esc_html_e('Follow us', 'rinometry'); ?></h2>
    <a class="social-link"
       href="https://www.linkedin.com/company/rhinometric/"
       target="_blank"
       rel="noopener noreferrer"
       aria-label="<?php esc_attr_e('Rhinometric on LinkedIn', 'rinometry'); ?>">
      <svg viewBox="0 0 24 24" role="img" focusable="false" xmlns="http://www.w3.org/2000/svg">
        <path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5ZM.5 8h4V24h-4V8Zm7.5 0h3.8v2.2h.05c.53-1 1.83-2.2 3.76-2.2C19.6 8 22 10.1 22 14.4V24h-4v-8.4c0-2-.04-4.6-2.8-4.6-2.8 0-3.23 2.2-3.23 4.5V24h-4V8Z"/>
      </svg>
      LinkedIn
    </a>
  </div>
</section>

<!-- Footer -->
<footer class="site-footer" role="contentinfo">
  <div class="container">
    <div class="footer-grid">

      <div class="footer-col">
        <h4><?php esc_html_e('Product', 'rinometry'); ?></h4>
        <ul>
          <li><a href="<?php echo esc_url(rinometry_page_url('platform')); ?>"><?php esc_html_e('Platform', 'rinometry'); ?></a></li>
          <li><a href="<?php echo esc_url(rinometry_page_url('deployment')); ?>"><?php esc_html_e('Deployment', 'rinometry'); ?></a></li>
          <li><a href="<?php echo esc_url(rinometry_page_url('security')); ?>"><?php esc_html_e('Security', 'rinometry'); ?></a></li>
          <li><a href="<?php echo esc_url(rinometry_page_url('pricing')); ?>"><?php esc_html_e('Pricing', 'rinometry'); ?></a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h4><?php esc_html_e('Company', 'rinometry'); ?></h4>
        <ul>
          <li><a href="<?php echo esc_url(rinometry_page_url('resources')); ?>"><?php esc_html_e('Resources', 'rinometry'); ?></a></li>
          <li><a href="<?php echo esc_url(rinometry_page_url('contact')); ?>"><?php esc_html_e('Contact', 'rinometry'); ?></a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h4><?php esc_html_e('Legal', 'rinometry'); ?></h4>
        <ul>
          <li><a href="<?php echo esc_url(rinometry_page_url('privacy-cookies')); ?>"><?php esc_html_e('Privacy & Cookies', 'rinometry'); ?></a></li>
          <li><a href="<?php echo esc_url(rinometry_page_url('terms')); ?>"><?php esc_html_e('Terms', 'rinometry'); ?></a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h4><?php esc_html_e('Connect', 'rinometry'); ?></h4>
        <ul>
          <li><a href="https://www.linkedin.com/company/rhinometric/" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
          <li><a href="mailto:rafael.canelon@rhinometric.com">rafael.canelon@rhinometric.com</a></li>
        </ul>
      </div>

    </div>

    <div class="footer-bottom">
      <p>&copy; <?php echo esc_html(date('Y')); ?> Rhinometric. <?php esc_html_e('All rights reserved.', 'rinometry'); ?></p>
    </div>
  </div>
</footer>

<!-- Cookie Banner -->
<?php if (rinometry_cookie_banner_enabled()) : ?>
<div class="cookie-banner" id="cookie-banner" role="region" aria-label="<?php esc_attr_e('Cookie notice', 'rinometry'); ?>">
  <div class="cookie-banner-inner">
    <p>
      <?php esc_html_e('We use essential cookies only to ensure the website functions properly.', 'rinometry'); ?>
      <a href="<?php echo esc_url(rinometry_page_url('privacy-cookies')); ?>"><?php esc_html_e('Cookie policy', 'rinometry'); ?></a>
    </p>
    <button class="btn btn-primary btn-sm" id="cookie-accept"><?php esc_html_e('Accept', 'rinometry'); ?></button>
  </div>
</div>
<?php endif; ?>

<?php wp_footer(); ?>
</body>
</html>
