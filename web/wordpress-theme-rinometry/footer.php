<?php
?>
</main>
<footer class="site-footer" role="contentinfo">
  <div class="container footer-grid">
    <div>
      <h2><?php esc_html_e('Rhinometric', 'rinometry'); ?></h2>
      <p><?php esc_html_e('Enterprise-grade observability for metrics, logs, and traces with on-prem control.', 'rinometry'); ?></p>
    </div>
    <div>
      <h3><?php esc_html_e('Explore', 'rinometry'); ?></h3>
      <nav aria-label="<?php esc_attr_e('Footer', 'rinometry'); ?>">
        <?php
          wp_nav_menu([
            'theme_location' => 'footer',
            'container' => false,
            'fallback_cb' => false,
            'items_wrap' => '<ul>%3$s</ul>',
          ]);
        ?>
      </nav>
    </div>
    <div>
      <h3><?php esc_html_e('Contact', 'rinometry'); ?></h3>
      <p><?php esc_html_e('Email: hello@rhinometric.com', 'rinometry'); ?></p>
      <p><?php esc_html_e('Request a demo to see the platform in action.', 'rinometry'); ?></p>
    </div>
  </div>
  <div class="container" style="margin-top: 2rem; font-size: 0.9rem; opacity: 0.8;">
    <p><?php echo esc_html(sprintf(__('© %s Rhinometric. All rights reserved.', 'rinometry'), date('Y'))); ?></p>
  </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
