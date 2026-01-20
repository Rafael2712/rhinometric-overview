<?php
get_header();
?>
<section class="section">
  <div class="container">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
      <h1 class="section-title"><?php the_title(); ?></h1>
      <?php the_content(); ?>
    <?php endwhile; else : ?>
      <h1 class="section-title"><?php esc_html_e('Content not found', 'rinometry'); ?></h1>
    <?php endif; ?>
  </div>
</section>
<?php
get_footer();
