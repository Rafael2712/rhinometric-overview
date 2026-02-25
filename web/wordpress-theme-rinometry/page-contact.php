<?php
/**
 * Template Name: Contact
 *
 * B2B qualifying lead form — mobile-first, i18n ES/EN.
 * Emails via Zoho SMTP (unchanged flow).
 */
get_header();

$lang = rinometry_get_current_language();

/* ── i18n ── */
$t = [
    'hero_title'    => [
        'en' => 'Talk to our team',
        'es' => 'Habla con nuestro equipo',
    ],
    'intro'         => [
        'en' => 'Rhinometric is an on-premise observability platform with AI-assisted anomaly detection, built for infrastructure and SRE teams that need to correlate metrics, logs, and traces within a single operational interface.<br><br>If you\'re evaluating a solution for mission-critical systems, share your technical context.',
        'es' => 'Rhinometric es una plataforma de observabilidad on-premise con detección de anomalías asistida por IA, diseñada para equipos de infraestructura y SRE que necesitan correlacionar métricas, logs y trazas en una única interfaz operativa.<br><br>Si estás evaluando una solución para entornos críticos, compártenos tu contexto técnico.',
    ],
    'sidebar_title' => [
        'en' => 'What to expect',
        'es' => 'Qué esperar',
    ],
    'sidebar_1'     => ['en' => 'A response within 24–48 hours.',       'es' => 'Respuesta en 24–48 horas.'],
    'sidebar_2'     => ['en' => 'Technical guidance for your use case.', 'es' => 'Orientación técnica para tu caso de uso.'],
    'sidebar_3'     => ['en' => 'No commitment required.',              'es' => 'Sin compromiso.'],

    /* Section headers */
    'section_id'       => ['en' => 'Identification',            'es' => 'Identificación'],
    'section_intent'   => ['en' => 'What are you looking for?', 'es' => '¿Qué estás buscando?'],
    'section_context'  => ['en' => 'Technical context',         'es' => 'Contexto técnico'],
    'section_message'  => ['en' => 'Additional details',        'es' => 'Detalles adicionales'],

    /* Fields */
    'label_fullname'   => ['en' => 'Full name',                 'es' => 'Nombre y apellido'],
    'label_email'      => ['en' => 'Email',                     'es' => 'Email'],
    'label_company'    => ['en' => 'Company',                   'es' => 'Empresa'],
    'label_role'       => ['en' => 'Role in the company',       'es' => 'Rol en la empresa'],
    'label_env_size'   => ['en' => 'Approximate environment size', 'es' => 'Tamaño aproximado del entorno'],
    'label_phone'      => ['en' => 'Phone (optional)',          'es' => 'Teléfono (opcional)'],
    'label_message'    => ['en' => 'Message (optional)',         'es' => 'Mensaje (opcional)'],

    /* Intention radios */
    'intent_demo'    => ['en' => 'Request a demo',                  'es' => 'Solicitar una demo'],
    'intent_eval'    => ['en' => 'Evaluate Rhinometric for my team','es' => 'Evaluar Rhinometric para mi equipo'],
    'intent_info'    => ['en' => 'Receive more information',        'es' => 'Recibir más información'],

    /* Env size options */
    'env_placeholder' => ['en' => 'Select…',        'es' => 'Seleccionar…'],
    'env_1_10'        => ['en' => '1–10 servers',    'es' => '1–10 servidores'],
    'env_10_50'       => ['en' => '10–50 servers',   'es' => '10–50 servidores'],
    'env_50_200'      => ['en' => '50–200 servers',  'es' => '50–200 servidores'],
    'env_200_plus'    => ['en' => '200+ servers',    'es' => '200+ servidores'],

    /* Legal */
    'label_gdpr' => [
        'en' => 'I confirm that I have read and accept the <a href="/terms/" target="_blank">Terms</a> and the <a href="/privacy-cookies/" target="_blank">Privacy Policy</a>.',
        'es' => 'Declaro que he leído y acepto los <a href="/terms/" target="_blank">Términos</a> y la <a href="/privacy-cookies/" target="_blank">Política de Privacidad</a>.',
    ],
    'label_marketing' => [
        'en' => 'I would like to receive occasional updates and product communications from Rhinometric.',
        'es' => 'Quiero recibir comunicaciones ocasionales sobre novedades y actualizaciones de Rhinometric.',
    ],

    /* Button / states */
    'btn_submit'    => ['en' => 'Send request',   'es' => 'Enviar solicitud'],
    'btn_sending'   => ['en' => 'Sending…',       'es' => 'Enviando…'],
    'success_msg'   => ['en' => 'Request received. We will contact you within 24–48 hours.', 'es' => 'Solicitud recibida. Te contactaremos en 24–48 horas.'],
    'fallback_error'=> ['en' => 'Could not send the request. Try again or email rafael.canelon@rhinometric.com', 'es' => 'No pudimos enviar la solicitud. Inténtalo de nuevo o escríbenos a rafael.canelon@rhinometric.com'],

    /* Char counter */
    'chars_remaining' => ['en' => 'characters remaining', 'es' => 'caracteres restantes'],
];

$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};
?>

<section class="page-hero">
  <div class="container">
    <h1><?php echo esc_html($__('hero_title')); ?></h1>
  </div>
</section>

<section class="section">
  <div class="container contact-layout">

    <!-- Sidebar -->
    <aside class="contact-sidebar">
      <!-- Intro text -->
      <div class="contact-intro">
        <p><?php echo wp_kses($__('intro'), ['br' => []]); ?></p>
      </div>
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
        <input type="hidden" name="page_url" value="<?php echo esc_url(get_permalink()); ?>">

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

          <!-- ═══ A) IDENTIFICATION ═══ -->
          <fieldset class="form-section">
            <legend class="form-section__title"><?php echo esc_html($__('section_id')); ?></legend>

            <div class="form-row form-row--2col">
              <!-- Full name -->
              <div class="form-field">
                <label for="full_name"><?php echo esc_html($__('label_fullname')); ?> <span aria-hidden="true">*</span></label>
                <input id="full_name" name="full_name" type="text" required autocomplete="name"
                       placeholder="<?php echo esc_attr($lang === 'es' ? 'Ej.: María López' : 'e.g. Jane Smith'); ?>">
                <span class="field-error" data-field="full_name"></span>
              </div>

              <!-- Email -->
              <div class="form-field">
                <label for="email"><?php echo esc_html($__('label_email')); ?> <span aria-hidden="true">*</span></label>
                <input id="email" name="email" type="email" required autocomplete="email"
                       placeholder="you@company.com">
                <span class="field-error" data-field="email"></span>
              </div>
            </div>

            <!-- Company -->
            <div class="form-field">
              <label for="company"><?php echo esc_html($__('label_company')); ?> <span aria-hidden="true">*</span></label>
              <input id="company" name="company" type="text" required autocomplete="organization"
                     placeholder="<?php echo esc_attr($lang === 'es' ? 'Nombre de la empresa' : 'Company name'); ?>">
              <span class="field-error" data-field="company"></span>
            </div>
          </fieldset>

          <!-- ═══ B) INTENTION ═══ -->
          <fieldset class="form-section">
            <legend class="form-section__title"><?php echo esc_html($__('section_intent')); ?> <span aria-hidden="true">*</span></legend>

            <div class="form-field form-field--radios" id="intentionGroup">
              <label class="radio-label">
                <input type="radio" name="intention" value="demo" required>
                <span><?php echo esc_html($__('intent_demo')); ?></span>
              </label>
              <label class="radio-label">
                <input type="radio" name="intention" value="evaluate">
                <span><?php echo esc_html($__('intent_eval')); ?></span>
              </label>
              <label class="radio-label">
                <input type="radio" name="intention" value="info">
                <span><?php echo esc_html($__('intent_info')); ?></span>
              </label>
              <span class="field-error" data-field="intention"></span>
            </div>
          </fieldset>

          <!-- ═══ C) CONTEXT ═══ -->
          <fieldset class="form-section">
            <legend class="form-section__title"><?php echo esc_html($__('section_context')); ?></legend>

            <div class="form-row form-row--2col">
              <!-- Role (optional) -->
              <div class="form-field">
                <label for="role"><?php echo esc_html($__('label_role')); ?></label>
                <input id="role" name="role" type="text"
                       placeholder="<?php echo esc_attr($lang === 'es' ? 'Ej.: CTO, DevOps Lead' : 'e.g. CTO, DevOps Lead'); ?>">
                <span class="field-error" data-field="role"></span>
              </div>

              <!-- Env size (conditionally required) -->
              <div class="form-field" id="envSizeField">
                <label for="env_size">
                  <?php echo esc_html($__('label_env_size')); ?>
                  <span class="env-required-star" aria-hidden="true" hidden>*</span>
                </label>
                <select id="env_size" name="env_size">
                  <option value=""><?php echo esc_html($__('env_placeholder')); ?></option>
                  <option value="1-10"><?php echo esc_html($__('env_1_10')); ?></option>
                  <option value="10-50"><?php echo esc_html($__('env_10_50')); ?></option>
                  <option value="50-200"><?php echo esc_html($__('env_50_200')); ?></option>
                  <option value="200+"><?php echo esc_html($__('env_200_plus')); ?></option>
                </select>
                <span class="field-error" data-field="env_size"></span>
              </div>
            </div>
          </fieldset>

          <!-- ═══ D) PHONE ═══ -->
          <div class="form-field">
            <label for="phone"><?php echo esc_html($__('label_phone')); ?></label>
            <input id="phone" name="phone" type="tel" autocomplete="tel"
                   placeholder="+34 600 000 000">
            <span class="field-error" data-field="phone"></span>
          </div>

          <!-- ═══ E) MESSAGE ═══ -->
          <div class="form-field">
            <label for="comments"><?php echo esc_html($__('label_message')); ?></label>
            <textarea id="comments" name="comments" rows="3" maxlength="255"
                      placeholder="<?php echo esc_attr($lang === 'es' ? 'Cuéntanos sobre tu proyecto...' : 'Tell us about your project...'); ?>"></textarea>
            <div class="char-counter"><span id="charCount">255</span>/255 <?php echo esc_html($__('chars_remaining')); ?></div>
            <span class="field-error" data-field="comments"></span>
          </div>

          <!-- ═══ LEGAL ═══ -->
          <div class="form-section form-section--legal">
            <!-- GDPR consent (required) -->
            <div class="form-field form-field--checkbox">
              <label class="gdpr-label">
                <input id="gdpr_consent" name="gdpr_consent" type="checkbox" value="1" required>
                <span><?php echo wp_kses($__('label_gdpr'), ['a' => ['href' => [], 'target' => []]]); ?></span>
              </label>
              <span class="field-error" data-field="gdpr_consent"></span>
            </div>

            <!-- Marketing consent (optional) -->
            <div class="form-field form-field--checkbox">
              <label class="gdpr-label">
                <input id="marketing_consent" name="marketing_consent" type="checkbox" value="1">
                <span><?php echo esc_html($__('label_marketing')); ?></span>
              </label>
            </div>
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

  var form        = document.getElementById('rhinoContactForm');
  var formFields  = document.getElementById('formFields');
  var errBanner   = document.getElementById('formErrors');
  var successBox  = document.getElementById('formSuccess');
  var submitBtn   = document.getElementById('submitBtn');
  var ajaxUrl     = <?php echo wp_json_encode(admin_url('admin-ajax.php')); ?>;
  var sendingTxt  = <?php echo wp_json_encode($__('btn_sending')); ?>;
  var fallbackErr = <?php echo wp_json_encode($__('fallback_error')); ?>;
  var originalTxt = submitBtn.textContent;

  /* ── Character counter ── */
  var textarea  = document.getElementById('comments');
  var charCount = document.getElementById('charCount');
  var maxLen    = 255;

  textarea.addEventListener('input', function(){
    var remaining = maxLen - this.value.length;
    if (remaining < 0) remaining = 0;
    charCount.textContent = remaining;
    charCount.parentElement.classList.toggle('char-counter--warn', remaining <= 30);
    charCount.parentElement.classList.toggle('char-counter--limit', remaining === 0);
  });

  /* ── Conditional env_size requirement ── */
  var radios   = document.querySelectorAll('input[name="intention"]');
  var envSelect= document.getElementById('env_size');
  var envStar  = document.querySelector('.env-required-star');

  function updateEnvRequired(){
    var selected = document.querySelector('input[name="intention"]:checked');
    var needsEnv = selected && (selected.value === 'demo' || selected.value === 'evaluate');
    if (needsEnv) {
      envSelect.setAttribute('required', '');
      envStar.hidden = false;
    } else {
      envSelect.removeAttribute('required');
      envStar.hidden = true;
    }
  }
  for (var r = 0; r < radios.length; r++) {
    radios[r].addEventListener('change', updateEnvRequired);
  }

  /* ── Error helpers ── */
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
      var parent = span.closest('.form-field');
      if(parent) parent.classList.add('form-field--invalid');
    }
  }

  function resetBtn(){
    submitBtn.disabled = false;
    submitBtn.textContent = originalTxt;
  }

  /* ── Client-side validation ── */
  function validateClient(){
    var ok = true;
    var fullName = document.getElementById('full_name');
    var email    = document.getElementById('email');
    var company  = document.getElementById('company');
    var consent  = document.getElementById('gdpr_consent');
    var intentSel= document.querySelector('input[name="intention"]:checked');

    if (!fullName.value.trim()) {
      showFieldError('full_name', <?php echo wp_json_encode($lang === 'es' ? 'El nombre es obligatorio.' : 'Full name is required.'); ?>);
      ok = false;
    }
    if (!email.value.trim() || !email.validity.valid) {
      showFieldError('email', <?php echo wp_json_encode($lang === 'es' ? 'Introduce un email válido.' : 'Enter a valid email address.'); ?>);
      ok = false;
    }
    if (!company.value.trim()) {
      showFieldError('company', <?php echo wp_json_encode($lang === 'es' ? 'La empresa es obligatoria.' : 'Company is required.'); ?>);
      ok = false;
    }
    if (!intentSel) {
      showFieldError('intention', <?php echo wp_json_encode($lang === 'es' ? 'Selecciona una opción.' : 'Please select an option.'); ?>);
      ok = false;
    }
    if (intentSel && (intentSel.value === 'demo' || intentSel.value === 'evaluate') && !envSelect.value) {
      showFieldError('env_size', <?php echo wp_json_encode($lang === 'es' ? 'Este campo es obligatorio para demo/evaluación.' : 'This field is required for demo/evaluation requests.'); ?>);
      ok = false;
    }
    if (textarea.value.length > maxLen) {
      showFieldError('comments', <?php echo wp_json_encode($lang === 'es' ? 'Máximo 255 caracteres.' : 'Maximum 255 characters.'); ?>);
      ok = false;
    }
    if (!consent.checked) {
      showFieldError('gdpr_consent', <?php echo wp_json_encode($lang === 'es' ? 'Debes aceptar los Términos y la Política de Privacidad.' : 'You must accept the Terms and Privacy Policy.'); ?>);
      ok = false;
    }
    return ok;
  }

  /* ── Submit ── */
  form.addEventListener('submit', function(e){
    e.preventDefault();
    clearErrors();

    if (!validateClient()) return;

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
