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
            'fallback_cb' => 'rinometry_primary_menu_fallback',
            'items_wrap' => '<ul>%3$s</ul>',
          ]);
        ?>
      </nav>
    </div>
    <div>
      <h3><?php esc_html_e('Contact', 'rinometry'); ?></h3>
      <p><a href="mailto:rafael.canelon@rhinometric.com">rafael.canelon@rhinometric.com</a></p>
      <p><?php esc_html_e('Request a demo to see the platform in action.', 'rinometry'); ?></p>
    </div>
  </div>
  <div class="container" style="margin-top: 2rem; font-size: 0.9rem; opacity: 0.8;">
    <p><?php echo esc_html(sprintf(__('© %s Rhinometric. All rights reserved.', 'rinometry'), date('Y'))); ?></p>
  </div>
  <div class="container deploy-info">
    <?php
      $deploy_info_path = get_template_directory() . '/deploy-info.json';
      $deploy_line = 'Deployed: unknown';
      if (file_exists($deploy_info_path)) {
        $raw = file_get_contents($deploy_info_path);
        $data = json_decode($raw, true);
        if (is_array($data)) {
          $sha = isset($data['sha']) ? trim((string) $data['sha']) : '';
          $run_number = isset($data['run_number']) ? trim((string) $data['run_number']) : '';
          $deployed_at = isset($data['deployed_at_utc']) ? trim((string) $data['deployed_at_utc']) : '';
          if ($sha && $run_number && $deployed_at) {
            $short_sha = substr($sha, 0, 7);
            $deploy_line = sprintf('Deployed: %s · Run #%s · %s', $short_sha, $run_number, $deployed_at);
          }
        }
      }
    ?>
    <p><?php echo esc_html($deploy_line); ?></p>
  </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
