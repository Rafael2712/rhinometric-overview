<?php
?>
</main>
<footer class="site-footer" role="contentinfo">
  <div class="container footer-simple">
    <img class="footer-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-footer.png'); ?>" alt="<?php esc_attr_e('Rhinometric', 'rinometry'); ?>" />
    <p><?php esc_html_e('© Rhinometric. All rights reserved.', 'rinometry'); ?></p>
    <p><?php esc_html_e('Contact: ', 'rinometry'); ?><a href="mailto:rafael.canelon@rhinometric.com">rafael.canelon@rhinometric.com</a></p>
  </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
