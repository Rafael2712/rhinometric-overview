<?php
get_header();
?>
<section class="section">
  <div class="container">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
      <h1 class="section-title"><?php the_title(); ?></h1>
      <div class="section-lead">
        <?php the_content(); ?>
      </div>
    <?php endwhile; endif; ?>
  </div>
</section>
<?php
get_footer();
