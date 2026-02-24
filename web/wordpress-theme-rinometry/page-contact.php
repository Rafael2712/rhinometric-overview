<?php
/**
 * Template Name: Contact — Lead Capture
 * Slug: contact
 *
 * Structured evaluation-request form with Zoho CRM push,
 * double-opt-in email validation, and lead scoring.
 */
get_header();

$lang = rinometry_get_current_language();
$recaptcha_site_key = esc_attr(get_option('rhinometric_recaptcha_site_key', ''));

/* ── i18n ── */
$t = [
    'hero_title'        => ['en' => 'Request a Technical Evaluation',            'es' => 'Solicitar una Evaluación Técnica'],
    'hero_lead'         => ['en' => 'Complete the form below and we will contact you within 1–2 business days to discuss your infrastructure requirements.', 'es' => 'Completa el formulario y te contactaremos en 1–2 días hábiles para analizar tus requisitos de infraestructura.'],
    'sidebar_title'     => ['en' => 'What to expect',                            'es' => 'Qué esperar'],
    'sidebar_1'         => ['en' => 'Email confirmation link within minutes.',    'es' => 'Enlace de confirmación por email en minutos.'],
    'sidebar_2'         => ['en' => 'Technical review of your requirements.',     'es' => 'Revisión técnica de tus requisitos.'],
    'sidebar_3'         => ['en' => 'Guided evaluation plan tailored to your stack.', 'es' => 'Plan de evaluación adaptado a tu stack.'],
    'sidebar_4'         => ['en' => 'All data processed within the EU.',         'es' => 'Todos los datos procesados dentro de la UE.'],

    'label_email'       => ['en' => 'Corporate email',                           'es' => 'Email corporativo'],
    'label_company'     => ['en' => 'Company',                                   'es' => 'Empresa'],
    'label_role'        => ['en' => 'Role',                                      'es' => 'Cargo'],
    'label_infra'       => ['en' => 'Primary infrastructure',                    'es' => 'Infraestructura principal'],
    'label_stack'       => ['en' => 'Current observability stack',               'es' => 'Stack de observabilidad actual'],
    'label_challenge'   => ['en' => 'Primary challenge',                         'es' => 'Reto principal'],
    'label_onprem'      => ['en' => 'On-premises requirement',                   'es' => 'Requisito on-premises'],
    'label_gdpr'        => ['en' => 'I accept that Rhinometric processes my data to respond to this request, per the <a href="/privacy-cookies/" target="_blank">Privacy Policy</a>.', 'es' => 'Acepto que Rhinometric procese mis datos para responder a esta solicitud, según la <a href="/privacy-cookies/" target="_blank">Política de Privacidad</a>.'],
    'btn_submit'        => ['en' => 'Send evaluation request',                   'es' => 'Enviar solicitud de evaluación'],
    'btn_sending'       => ['en' => 'Sending request…',                          'es' => 'Enviando solicitud…'],
    'success_title'     => ['en' => 'Check your inbox',                          'es' => 'Revisa tu bandeja de entrada'],
    'success_text'      => ['en' => 'We sent a confirmation link to your email. Click it within 48 hours to activate your request.', 'es' => 'Enviamos un enlace de confirmación a tu email. Haz clic dentro de las 48 horas para activar tu solicitud.'],
    'select_default'    => ['en' => '— Select —',                                'es' => '— Seleccionar —'],
];

$__ = function ($key) use ($t, $lang) {
    return $t[$key][$lang] ?? $t[$key]['en'] ?? $key;
};

/* ── Dropdown options ── */
$roles = [
    'CTO', 'VP Engineering', 'Head of Infrastructure', 'DevOps Lead',
    'SRE Lead', 'Platform Engineer', 'IT Manager', 'Security Lead', 'Other',
];
$infras = [
    ['en' => 'On-Premise',                'es' => 'On-Premise'],
    ['en' => 'Hybrid (On-Prem + Cloud)',   'es' => 'Híbrido (On-Prem + Cloud)'],
    ['en' => 'AWS',                        'es' => 'AWS'],
    ['en' => 'Azure',                      'es' => 'Azure'],
    ['en' => 'GCP',                        'es' => 'GCP'],
    ['en' => 'Other Cloud',                'es' => 'Otro Cloud'],
];
$stacks = [
    ['en' => 'Prometheus + Grafana',       'es' => 'Prometheus + Grafana'],
    ['en' => 'Datadog',                    'es' => 'Datadog'],
    ['en' => 'New Relic',                  'es' => 'New Relic'],
    ['en' => 'Elastic / ELK',             'es' => 'Elastic / ELK'],
    ['en' => 'Splunk',                     'es' => 'Splunk'],
    ['en' => 'No solution in place',       'es' => 'Sin solución actual'],
    ['en' => 'Other',                      'es' => 'Otro'],
];
$challenges = [
    ['en' => 'Regulatory compliance',                  'es' => 'Cumplimiento normativo'],
    ['en' => 'Observability consolidation',            'es' => 'Consolidación de observabilidad'],
    ['en' => 'Cost reduction',                         'es' => 'Reducción de costes'],
    ['en' => 'Incident response time',                 'es' => 'Tiempo de respuesta a incidentes'],
    ['en' => 'Migrating from existing tool',           'es' => 'Migración desde herramienta actual'],
    ['en' => 'Data sovereignty / on-prem requirement', 'es' => 'Soberanía de datos / requisito on-prem'],
];
$onprems = [
    ['val' => 'yes',        'en' => 'Yes — 100% on-premises required',       'es' => 'Sí — 100% on-premises requerido'],
    ['val' => 'evaluating', 'en' => 'Evaluating — considering on-prem',      'es' => 'En evaluación — considerando on-prem'],
    ['val' => 'no',         'en' => 'No — cloud or hybrid is acceptable',    'es' => 'No — cloud o híbrido es aceptable'],
];
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
          <li><?php echo esc_html($__('sidebar_4')); ?></li>
        </ul>
      </div>
    </aside>

    <!-- Form -->
    <div class="contact-form-wrap">
      <form id="rhinoLeadForm" class="contact-form" novalidate>
        <?php wp_nonce_field('rhinometric_lead_form', '_wpnonce'); ?>
        <input type="hidden" name="action" value="rhinometric_lead_submit">
        <input type="hidden" name="lang" value="<?php echo esc_attr($lang); ?>">

        <!-- Honeypot -->
        <div class="honeypot" aria-hidden="true">
          <label for="website">Website</label>
          <input id="website" name="website" type="text" autocomplete="off" tabindex="-1">
        </div>

        <!-- Global error banner (populated by JS) -->
        <div id="formErrors" class="form-errors" role="alert" aria-live="assertive" hidden></div>

        <!-- Success state -->
        <div id="formSuccess" class="form-success" role="status" aria-live="polite" hidden>
          <h3><?php echo esc_html($__('success_title')); ?></h3>
          <p><?php echo esc_html($__('success_text')); ?></p>
        </div>

        <div id="formFields">
          <!-- Email -->
          <div class="form-field">
            <label for="email"><?php echo esc_html($__('label_email')); ?> <span aria-hidden="true">*</span></label>
            <input id="email" name="email" type="email" required autocomplete="email">
            <span class="field-error" data-field="email"></span>
          </div>

          <!-- Company -->
          <div class="form-field">
            <label for="company"><?php echo esc_html($__('label_company')); ?> <span aria-hidden="true">*</span></label>
            <input id="company" name="company" type="text" required autocomplete="organization">
            <span class="field-error" data-field="company"></span>
          </div>

          <!-- Role -->
          <div class="form-field">
            <label for="role"><?php echo esc_html($__('label_role')); ?> <span aria-hidden="true">*</span></label>
            <select id="role" name="role" required>
              <option value=""><?php echo esc_html($__('select_default')); ?></option>
              <?php foreach ($roles as $r) : ?>
                <option value="<?php echo esc_attr($r); ?>"><?php echo esc_html($r); ?></option>
              <?php endforeach; ?>
            </select>
            <span class="field-error" data-field="role"></span>
          </div>

          <!-- Infrastructure -->
          <div class="form-field">
            <label for="infra"><?php echo esc_html($__('label_infra')); ?> <span aria-hidden="true">*</span></label>
            <select id="infra" name="infra" required>
              <option value=""><?php echo esc_html($__('select_default')); ?></option>
              <?php foreach ($infras as $i) : ?>
                <option value="<?php echo esc_attr($i['en']); ?>"><?php echo esc_html($i[$lang] ?? $i['en']); ?></option>
              <?php endforeach; ?>
            </select>
            <span class="field-error" data-field="infra"></span>
          </div>

          <!-- Stack -->
          <div class="form-field">
            <label for="stack"><?php echo esc_html($__('label_stack')); ?> <span aria-hidden="true">*</span></label>
            <select id="stack" name="stack" required>
              <option value=""><?php echo esc_html($__('select_default')); ?></option>
              <?php foreach ($stacks as $s) : ?>
                <option value="<?php echo esc_attr($s['en']); ?>"><?php echo esc_html($s[$lang] ?? $s['en']); ?></option>
              <?php endforeach; ?>
            </select>
            <span class="field-error" data-field="stack"></span>
          </div>

          <!-- Challenge -->
          <div class="form-field">
            <label for="challenge"><?php echo esc_html($__('label_challenge')); ?> <span aria-hidden="true">*</span></label>
            <select id="challenge" name="challenge" required>
              <option value=""><?php echo esc_html($__('select_default')); ?></option>
              <?php foreach ($challenges as $c) : ?>
                <option value="<?php echo esc_attr($c['en']); ?>"><?php echo esc_html($c[$lang] ?? $c['en']); ?></option>
              <?php endforeach; ?>
            </select>
            <span class="field-error" data-field="challenge"></span>
          </div>

          <!-- On-prem -->
          <div class="form-field">
            <label for="onprem"><?php echo esc_html($__('label_onprem')); ?> <span aria-hidden="true">*</span></label>
            <select id="onprem" name="onprem" required>
              <option value=""><?php echo esc_html($__('select_default')); ?></option>
              <?php foreach ($onprems as $o) : ?>
                <option value="<?php echo esc_attr($o['val']); ?>"><?php echo esc_html($o[$lang] ?? $o['en']); ?></option>
              <?php endforeach; ?>
            </select>
            <span class="field-error" data-field="onprem"></span>
          </div>

          <!-- GDPR -->
          <div class="form-field form-field--checkbox">
            <label>
              <input id="gdpr" name="gdpr" type="checkbox" value="1" required>
              <span><?php echo wp_kses_post($__('label_gdpr')); ?></span>
            </label>
            <span class="field-error" data-field="gdpr"></span>
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

  var form      = document.getElementById('rhinoLeadForm');
  var formFields= document.getElementById('formFields');
  var errBanner = document.getElementById('formErrors');
  var successBox= document.getElementById('formSuccess');
  var submitBtn = document.getElementById('submitBtn');
  var ajaxUrl   = <?php echo wp_json_encode(admin_url('admin-ajax.php')); ?>;
  var sendingTxt= <?php echo wp_json_encode($__('btn_sending')); ?>;
  var originalTxt= submitBtn.textContent;

  function clearErrors(){
    errBanner.hidden = true;
    errBanner.innerHTML = '';
    document.querySelectorAll('.field-error').forEach(function(el){ el.textContent=''; });
    document.querySelectorAll('.form-field--invalid').forEach(function(el){ el.classList.remove('form-field--invalid'); });
  }

  function showFieldError(field, msg){
    var span = document.querySelector('.field-error[data-field="'+field+'"]');
    if(span){
      span.textContent = msg;
      span.closest('.form-field').classList.add('form-field--invalid');
    }
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    clearErrors();

    submitBtn.disabled = true;
    submitBtn.textContent = sendingTxt;

    var recaptchaSiteKey = <?php echo wp_json_encode($recaptcha_site_key); ?>;

    function doSubmit(recaptchaToken){
      var fd = new FormData(form);
      if(recaptchaToken) fd.set('recaptcha_token', recaptchaToken);

      fetch(ajaxUrl, { method:'POST', body: fd, credentials:'same-origin' })
        .then(function(r){ return r.json(); })
        .then(function(res){
          if(res.success){
            formFields.hidden = true;
            successBox.hidden = false;
            successBox.scrollIntoView({ behavior:'smooth', block:'center' });
          } else {
            if(res.data && res.data.fields){
              Object.keys(res.data.fields).forEach(function(k){
                showFieldError(k, res.data.fields[k]);
              });
            }
            if(res.data && res.data.message){
              errBanner.hidden = false;
              errBanner.textContent = res.data.message;
            }
            submitBtn.disabled = false;
            submitBtn.textContent = originalTxt;
          }
        })
        .catch(function(){
          errBanner.hidden = false;
          errBanner.textContent = 'Network error. Please try again.';
          submitBtn.disabled = false;
          submitBtn.textContent = originalTxt;
        });
    }

    if(recaptchaSiteKey && typeof grecaptcha !== 'undefined'){
      grecaptcha.ready(function(){
        grecaptcha.execute(recaptchaSiteKey, {action:'lead_submit'}).then(doSubmit);
      });
    } else {
      doSubmit('');
    }
  });
})();
</script>

<?php get_footer(); ?>
