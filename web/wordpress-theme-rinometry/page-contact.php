<?php
/**
 * Template Name: Contact
 *
 * 5-field lead form. Emails via SendGrid API.
 * No double opt-in. No confirmation link.
 */
get_header();

$lang = rinometry_get_current_language();

/* ── i18n ── */
$t = [
    'hero_title'    => ['en' => 'Contact Us',                            'es' => 'Contáctanos'],
    'hero_lead'     => ['en' => 'Tell us about your project. We will respond within 1–2 business days.', 'es' => 'Cuéntanos sobre tu proyecto. Te responderemos en 1–2 días laborables.'],
    'sidebar_title' => ['en' => 'What to expect',                        'es' => 'Qué esperar'],
    'sidebar_1'     => ['en' => 'A response within 1–2 business days.',  'es' => 'Respuesta en 1–2 días laborables.'],
    'sidebar_2'     => ['en' => 'Technical guidance for your use case.',  'es' => 'Orientación técnica para tu caso de uso.'],
    'sidebar_3'     => ['en' => 'No commitment required.',               'es' => 'Sin compromiso.'],

    'label_email'   => ['en' => 'Email',                                 'es' => 'Email'],
    'label_phone'   => ['en' => 'Phone',                                 'es' => 'Teléfono'],
    'label_company' => ['en' => 'Company',                               'es' => 'Empresa'],
    'label_role'    => ['en' => 'Role / Title',                          'es' => 'Cargo'],
    'label_comments'=> ['en' => 'Comments (optional)',                   'es' => 'Comentarios (opcional)'],

    'btn_submit'    => ['en' => 'Send request',                          'es' => 'Enviar solicitud'],
    'btn_sending'   => ['en' => 'Sending…',                              'es' => 'Enviando…'],
    'success_msg'   => ['en' => 'Request received. We will contact you within 1–2 business days.', 'es' => 'Solicitud recibida. Te contactaremos en 1–2 días laborables.'],
    'fallback_error'=> ['en' => 'Could not send the request. Try again or email sales@rhinometric.com', 'es' => 'No pudimos enviar la solicitud. Inténtalo de nuevo o escríbenos a sales@rhinometric.com'],
];

$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};
?>

<section class="page-hero">
  <div class="container">
    <h1><?php echo esc_html($__('hero_title')); ?></h1>
    <p class="hero-lead"><?php echo esc_html($__('hero_lead')); ?></p>
  </div>
</section>

<section class="section">
  <div class="container contact-layout">

    <!-- Sidebar -->
    <aside class="contact-sidebar">
      <div class="card">
        <h2><?php echo esc_html($__('sidebar_title')); ?></h2>
        <ul>
          <li><?php echo esc_html($__('sidebar_1')); ?></li>
          <li><?php echo esc_html($__('sidebar_2')); ?></li>
          <li><?php echo esc_html($__('sidebar_3')); ?></li>
        </ul>
      </div>
    </aside>

    <!-- Form -->
    <div class="contact-form-wrap">
      <form id="rhinoContactForm" class="contact-form" novalidate>
        <?php wp_nonce_field('rhinometric_contact_form', '_wpnonce'); ?>
        <input type="hidden" name="action" value="rhinometric_contact_submit">
        <input type="hidden" name="lang" value="<?php echo esc_attr($lang); ?>">

        <!-- Honeypot -->
        <div class="honeypot" aria-hidden="true">
          <label for="website">Website</label>
          <input id="website" name="website" type="text" autocomplete="off" tabindex="-1">
        </div>

        <!-- Global error banner -->
        <div id="formErrors" class="form-errors" role="alert" aria-live="assertive" hidden></div>

        <!-- Success state -->
        <div id="formSuccess" class="form-success" role="status" aria-live="polite" hidden>
          <p><?php echo esc_html($__('success_msg')); ?></p>
        </div>

        <div id="formFields">
          <!-- 1. Email -->
          <div class="form-field">
            <label for="email"><?php echo esc_html($__('label_email')); ?> <span aria-hidden="true">*</span></label>
            <input id="email" name="email" type="email" required autocomplete="email"
                   placeholder="you@company.com">
            <span class="field-error" data-field="email"></span>
          </div>

          <!-- 2. Phone -->
          <div class="form-field">
            <label for="phone"><?php echo esc_html($__('label_phone')); ?> <span aria-hidden="true">*</span></label>
            <input id="phone" name="phone" type="tel" required autocomplete="tel"
                   placeholder="+34 600 000 000">
            <span class="field-error" data-field="phone"></span>
          </div>

          <!-- 3. Company -->
          <div class="form-field">
            <label for="company"><?php echo esc_html($__('label_company')); ?> <span aria-hidden="true">*</span></label>
            <input id="company" name="company" type="text" required autocomplete="organization">
            <span class="field-error" data-field="company"></span>
          </div>

          <!-- 4. Role -->
          <div class="form-field">
            <label for="role"><?php echo esc_html($__('label_role')); ?> <span aria-hidden="true">*</span></label>
            <input id="role" name="role" type="text" required
                   placeholder="<?php echo esc_attr($lang === 'es' ? 'Ej.: CTO, DevOps Lead' : 'e.g. CTO, DevOps Lead'); ?>">
            <span class="field-error" data-field="role"></span>
          </div>

          <!-- 5. Comments (optional) -->
          <div class="form-field">
            <label for="comments"><?php echo esc_html($__('label_comments')); ?></label>
            <textarea id="comments" name="comments" rows="3"
                      placeholder="<?php echo esc_attr($lang === 'es' ? 'Cuéntanos sobre tu proyecto...' : 'Tell us about your project...'); ?>"></textarea>
          </div>

          <!-- Submit -->
          <button id="submitBtn" class="btn btn-primary btn-block" type="submit">
            <?php echo esc_html($__('btn_submit')); ?>
          </button>
        </div>
      </form>
    </div>

  </div>
</section>

<script>
(function(){
  'use strict';

  var form       = document.getElementById('rhinoContactForm');
  var formFields = document.getElementById('formFields');
  var errBanner  = document.getElementById('formErrors');
  var successBox = document.getElementById('formSuccess');
  var submitBtn  = document.getElementById('submitBtn');
  var ajaxUrl    = <?php echo wp_json_encode(admin_url('admin-ajax.php')); ?>;
  var sendingTxt = <?php echo wp_json_encode($__('btn_sending')); ?>;
  var fallbackErr= <?php echo wp_json_encode($__('fallback_error')); ?>;
  var originalTxt= submitBtn.textContent;

  function clearErrors(){
    errBanner.hidden = true;
    errBanner.innerHTML = '';
    var spans = document.querySelectorAll('.field-error');
    for(var i=0;i<spans.length;i++) spans[i].textContent='';
    var inv = document.querySelectorAll('.form-field--invalid');
    for(var j=0;j<inv.length;j++) inv[j].classList.remove('form-field--invalid');
  }

  function showFieldError(field, msg){
    var span = document.querySelector('.field-error[data-field="'+field+'"]');
    if(span){
      span.textContent = msg;
      span.closest('.form-field').classList.add('form-field--invalid');
    }
  }

  function resetBtn(){
    submitBtn.disabled = false;
    submitBtn.textContent = originalTxt;
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    clearErrors();

    submitBtn.disabled = true;
    submitBtn.textContent = sendingTxt;

    var fd = new FormData(form);

    fetch(ajaxUrl, { method:'POST', body: fd, credentials:'same-origin' })
      .then(function(r){ return r.json(); })
      .then(function(res){
        if(res.success){
          formFields.hidden = true;
          successBox.hidden = false;
          successBox.scrollIntoView({ behavior:'smooth', block:'center' });
        } else {
          if(res.data && res.data.fields){
            var keys = Object.keys(res.data.fields);
            for(var k=0;k<keys.length;k++){
              showFieldError(keys[k], res.data.fields[keys[k]]);
            }
          }
          if(res.data && res.data.message){
            errBanner.hidden = false;
            errBanner.textContent = res.data.message;
          }
          resetBtn();
        }
      })
      .catch(function(){
        errBanner.hidden = false;
        errBanner.textContent = fallbackErr;
        resetBtn();
      });
  });
})();
</script>

<?php get_footer(); ?>
