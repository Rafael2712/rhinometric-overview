<?php
$rinometry_frontpage_supported_languages = ['en', 'es'];
$rinometry_frontpage_lang_param = '';
if (isset($_GET['lang'])) {
  $rinometry_frontpage_lang_param = sanitize_key(wp_unslash($_GET['lang']));
  if (!in_array($rinometry_frontpage_lang_param, $rinometry_frontpage_supported_languages, true)) {
    $rinometry_frontpage_lang_param = '';
  }
}

$rinometry_frontpage_cookie_name = 'rhino_lang';
$rinometry_frontpage_legacy_cookie = 'rino_lang';
$rinometry_frontpage_language = 'en';

if ($rinometry_frontpage_lang_param) {
  $rinometry_frontpage_language = $rinometry_frontpage_lang_param;
} elseif (isset($_COOKIE[$rinometry_frontpage_cookie_name]) && in_array($_COOKIE[$rinometry_frontpage_cookie_name], $rinometry_frontpage_supported_languages, true)) {
  $rinometry_frontpage_language = sanitize_key(wp_unslash($_COOKIE[$rinometry_frontpage_cookie_name]));
} elseif (isset($_COOKIE[$rinometry_frontpage_legacy_cookie]) && in_array($_COOKIE[$rinometry_frontpage_legacy_cookie], $rinometry_frontpage_supported_languages, true)) {
  $rinometry_frontpage_language = sanitize_key(wp_unslash($_COOKIE[$rinometry_frontpage_legacy_cookie]));
}

$rinometry_frontpage_cookie_expires = time() + (DAY_IN_SECONDS * 30);
$rinometry_frontpage_cookie_path = COOKIEPATH ? COOKIEPATH : '/';
$rinometry_frontpage_cookie_domain = COOKIE_DOMAIN ? COOKIE_DOMAIN : '';
$rinometry_frontpage_cookie_secure = is_ssl();
$rinometry_frontpage_cookie_http_only = true;

if ($rinometry_frontpage_lang_param || !isset($_COOKIE[$rinometry_frontpage_cookie_name]) || $_COOKIE[$rinometry_frontpage_cookie_name] !== $rinometry_frontpage_language) {
  setcookie(
    $rinometry_frontpage_cookie_name,
    $rinometry_frontpage_language,
    $rinometry_frontpage_cookie_expires,
    $rinometry_frontpage_cookie_path,
    $rinometry_frontpage_cookie_domain,
    $rinometry_frontpage_cookie_secure,
    $rinometry_frontpage_cookie_http_only
  );
}

if ($rinometry_frontpage_lang_param || !isset($_COOKIE[$rinometry_frontpage_legacy_cookie]) || $_COOKIE[$rinometry_frontpage_legacy_cookie] !== $rinometry_frontpage_language) {
  setcookie(
    $rinometry_frontpage_legacy_cookie,
    $rinometry_frontpage_language,
    $rinometry_frontpage_cookie_expires,
    $rinometry_frontpage_cookie_path,
    $rinometry_frontpage_cookie_domain,
    $rinometry_frontpage_cookie_secure,
    $rinometry_frontpage_cookie_http_only
  );
}

$rinometry_frontpage_strings = [
  'en' => [
    'hero.badge' => 'On-Prem Observability Engine',
    'hero.title' => 'On-Premise Observability: Your Infrastructure, Your Rules.',
    'hero.lead' => 'Own your observability. Deploy a high-performance engine for metrics, logs, and traces—fully isolated, production-ready, and with zero-data egress. Secure your infrastructure without the SaaS tax.',
    'hero.bullet1' => 'Engine installed in your data center or edge, production-ready.',
    'hero.bullet2' => 'Predictable costs: zero cloud egress, zero billing surprises.',
    'hero.bullet3' => 'Compliance and operational control on your own terms.',
    'hero.ctaPrimary' => 'Early Adopter Program',
    'hero.ctaSecondary' => 'Technical Specifications',
    'how.aria' => 'How it works',
    'how.step1.label' => 'One-Command Deploy',
    'how.step1.text' => 'Deploy the full stack on your infrastructure via Docker in minutes.',
    'how.step2.label' => 'Local Ingestion',
    'how.step2.text' => 'Your metrics and logs are collected and processed locally. Nothing leaves your network.',
    'how.step3.label' => 'Private Insights',
    'how.step3.text' => 'Visualize and analyze your data with total sovereignty and zero latency.',
    'console.aria' => 'Rhinometric Console Preview',
    'console.header' => 'Rhinometric Console Preview',
    'engine.title' => 'The Full-Stack Observability Engine.',
    'engine.lead' => 'Everything you need to monitor, trace, and secure your private infrastructure—pre-configured for production and absolute data sovereignty.',
    'engine.footnote' => 'Based on open standards. Zero vendor lock-in. Air-Gapped Ready. You own your configuration forever.',
    'tabs.aria' => 'Technical tabs',
    'tabs.metrics.label' => 'Metrics',
    'tabs.metrics.point1' => 'Infrastructure & Service Health — Prometheus: High-density monitoring based on industry standards, optimized to detect failures in milliseconds.',
    'tabs.metrics.point2' => 'High-Performance Persistence — PostgreSQL + Redis: Pre-configured storage layers for ultra-fast queries and total data reliability.',
    'tabs.metrics.caption' => 'Dark-mode Grafana dashboards with live CPU/RAM gauges tuned for private fleets.',
    'tabs.logs.label' => 'Logs',
    'tabs.logs.point1' => 'Private Log Centralization — Loki: Index terabytes of logs without a single byte leaving your network or incurring cloud egress fees.',
    'tabs.logs.point2' => 'Full-Text Intelligence: Search and filter data in real-time for audits, security, and critical troubleshooting.',
    'tabs.logs.caption' => 'Private Loki console with streaming ERROR filters and zero cloud egress.',
    'tabs.traces.label' => 'Traces',
    'tabs.traces.point1' => 'Microservices Visibility — Jaeger: Identify bottlenecks and latent failures in distributed systems with native tracing.',
    'tabs.traces.point2' => 'Dependency Mapping: Visualize service interactions to find the root cause of errors in seconds.',
    'tabs.traces.caption' => 'Jaeger dependency map connecting critical microservices across air-gapped clusters.',
    'tabs.visualization.label' => 'Visualization',
    'tabs.visual.point1' => 'Dashboards — Grafana preloaded views: Start diagnosing faster with guided dashboards and a unified navigation experience.',
    'tabs.visual.point2' => 'The Rhino Guide: Step-by-step deployment and operational documentation to keep your team autonomous from day one.',
    'tabs.visual.point3' => 'Tooling: Grafana.',
    'tabs.visual.caption' => 'Guided Grafana dashboards plus the Rhino Guide keep teams autonomous from day one.',
    'tabs.ai.label' => 'AI',
    'tabs.ai.point1' => 'AI-assisted anomaly signals (early): Surface unusual patterns across Prometheus metrics to reduce alert noise and speed up triage. Rhinometric highlights anomalies and trends so teams can investigate faster—without sending data outside your network.',
    'tabs.ai.point2' => 'Tooling: Prometheus + Rhinometric Anomaly Engine (early).',
    'tabs.ai.caption' => 'AI-assisted Prometheus anomalies with Rhino overlays for faster triage.',
    'feature.badge' => '100% Private / On-Premise',
    'critical.title' => 'Built for critical sectors',
    'critical.body' => 'Built for zero-risk tolerance sectors. If your company operates in Fintech, Health, Defense, or Industrial IoT, Rhinometric guarantees that 100% of telemetry stays on your servers. Regulatory compliance (GDPR/HIPAA) and total security in Air-Gapped environments.',
    'install.title' => 'Installation support & autonomy',
    'install.body' => 'We build the engine; you keep the keys. We guarantee a perfect setup and stack stability. With the included Rhino Guide, your team gains the knowledge to operate with full independence, eliminating reliance on external consulting.',
    'why.title' => 'Why choose Rhinometric',
    'why.item1' => 'Zero Cloud Egress Fees: Save thousands by eliminating the cost of transferring data to external clouds.',
    'why.item2' => 'No Vendor Lock-in: Based on open standards. You own the software and the configuration forever.',
    'why.item3' => 'Time-to-Market: What takes a senior team months to configure, we deliver in an afternoon.',
    'early.tag' => 'Early Access',
    'early.title' => 'Looking for the first 10 pioneers.',
    'early.lead' => 'Be part of the Rhinometric launch. We offer 3 months of full access and priority deployment support for free in exchange for your technical feedback. Secure your infrastructure today.',
    'early.cta' => 'Apply to Program - 10 Spots Available',
  ],
  'es' => [
    'hero.badge' => 'Motor de Observabilidad On-Prem',
    'hero.title' => 'Observabilidad On-Premise: Tu Infraestructura, Tus Reglas.',
    'hero.lead' => 'Toma el control absoluto de tu observabilidad. Despliega un motor de alto rendimiento para métricas, logs y trazas—totalmente aislado, listo para producción y sin costos de transferencia a la nube. Protege tu infraestructura sin pagar el “impuesto” de las plataformas SaaS.',
    'hero.bullet1' => 'Motor instalado en tu data center o edge, listo para producción.',
    'hero.bullet2' => 'Costos predecibles: cero cloud egress, cero sorpresas en la factura.',
    'hero.bullet3' => 'Cumplimiento y control operativo bajo tus propias reglas.',
    'hero.ctaPrimary' => 'Programa Early Adopter',
    'hero.ctaSecondary' => 'Especificaciones Técnicas',
    'how.aria' => 'Cómo funciona',
    'how.step1.label' => 'One-Command Deploy',
    'how.step1.text' => 'Despliega el stack completo en tu infraestructura mediante Docker en minutos.',
    'how.step2.label' => 'Ingesta Local',
    'how.step2.text' => 'Tus métricas y logs se colectan y procesan localmente. Nada sale de tu red.',
    'how.step3.label' => 'Private Insights',
    'how.step3.text' => 'Visualiza y analiza tus datos con soberanía total y cero latencia.',
    'console.aria' => 'Vista previa de Rhinometric Console',
    'console.header' => 'Vista previa de Rhinometric Console',
    'engine.title' => 'The Full-Stack Observability Engine.',
    'engine.lead' => 'Todo lo que necesitas para monitorear, trazar y asegurar tu infraestructura privada, preconfigurado para producción y con soberanía absoluta de datos.',
    'engine.footnote' => 'Basado en estándares abiertos. Cero vendor lock-in. Listo para Air-Gapped. Eres dueño de tu configuración para siempre.',
    'tabs.aria' => 'Pestañas técnicas',
    'tabs.metrics.label' => 'Métricas',
    'tabs.metrics.point1' => 'Salud de Infraestructura y Servicios — Prometheus: monitoreo de alta densidad basado en estándares, optimizado para detectar fallos en milisegundos.',
    'tabs.metrics.point2' => 'Persistencia de Alto Rendimiento — PostgreSQL + Redis: capas de almacenamiento preconfiguradas para consultas ultrarrápidas y total confiabilidad.',
    'tabs.metrics.caption' => 'Dashboards en modo oscuro con indicadores de CPU/RAM en vivo para flotas privadas.',
    'tabs.logs.label' => 'Registros',
    'tabs.logs.point1' => 'Centralización Privada de Logs — Loki: indexa terabytes sin que un solo byte salga de tu red ni genere costos de egress.',
    'tabs.logs.point2' => 'Inteligencia de Texto Completo: busca y filtra datos en tiempo real para auditorías, seguridad y resolución crítica.',
    'tabs.logs.caption' => 'Consola Loki privada con filtros de ERROR en streaming y cero egress.',
    'tabs.traces.label' => 'Trazas',
    'tabs.traces.point1' => 'Visibilidad de Microservicios — Jaeger: identifica cuellos de botella y fallos latentes en sistemas distribuidos con trazabilidad nativa.',
    'tabs.traces.point2' => 'Mapa de Dependencias: visualiza interacciones entre servicios para hallar la causa raíz en segundos.',
    'tabs.traces.caption' => 'Mapa de dependencias de Jaeger conectando microservicios críticos en clústeres air-gapped.',
    'tabs.visualization.label' => 'Visualización',
    'tabs.visual.point1' => 'Dashboards — vistas precargadas de Grafana: diagnostica más rápido con tableros guiados y una navegación unificada.',
    'tabs.visual.point2' => 'The Rhino Guide: documentación paso a paso de despliegue y operación para que tu equipo sea autónomo desde el día uno.',
    'tabs.visual.point3' => 'Herramientas: Grafana.',
    'tabs.visual.caption' => 'Dashboards guiados de Grafana más Rhino Guide para operar con autonomía desde el día uno.',
    'tabs.ai.label' => 'IA',
    'tabs.ai.point1' => 'Señales de anomalía asistidas por IA (early): detecta patrones inusuales sobre métricas de Prometheus para reducir el ruido de alertas y acelerar el triage. Rhinometric resalta anomalías y tendencias sin sacar datos de tu red.',
    'tabs.ai.point2' => 'Herramientas: Prometheus + Rhinometric Anomaly Engine (early).',
    'tabs.ai.caption' => 'Anomalías asistidas por IA sobre Prometheus con overlays Rhino para acelerar el triage.',
    'feature.badge' => '100% Privado / On-Premise',
    'critical.title' => 'Soberanía y Cumplimiento',
    'critical.body' => 'Diseñado para sectores con tolerancia cero al riesgo. Si operas en Fintech, Salud, Defensa o IoT Industrial, Rhinometric garantiza que el 100% de la telemetría permanezca en tus servidores. Cumplimiento normativo (GDPR/HIPAA) y seguridad total en entornos Air-Gapped.',
    'install.title' => 'Soporte de instalación y autonomía',
    'install.body' => 'Nosotros montamos el motor, tú mantienes las llaves. Garantizamos una instalación perfecta y estabilidad del stack. Con la Rhino Guide tu equipo opera con independencia, sin depender de consultorías externas.',
    'why.title' => 'Por qué elegir Rhinometric',
    'why.item1' => 'Cero Cloud Egress Fees: ahorra miles al eliminar el costo de transferir datos a nubes externas.',
    'why.item2' => 'Sin Vendor Lock-in: basado en estándares abiertos. Eres dueño del software y de tu configuración para siempre.',
    'why.item3' => 'Time-to-Market: lo que a un equipo senior le toma meses, lo entregamos en una tarde.',
    'early.tag' => 'Early Access',
    'early.title' => 'Buscamos a los 10 primeros pioneros.',
    'early.lead' => 'Sé parte del lanzamiento de Rhinometric. Ofrecemos 3 meses de acceso completo y soporte de despliegue prioritario gratis a cambio de tu feedback técnico. Asegura tu infraestructura hoy.',
    'early.cta' => 'Aplicar al Programa - 10 Plazas Libres',
  ],
];

$rinometry_frontpage_translate = function ($key) use ($rinometry_frontpage_language, $rinometry_frontpage_strings) {
  $fallback = $rinometry_frontpage_strings['en'];
  $dictionary = isset($rinometry_frontpage_strings[$rinometry_frontpage_language]) ? $rinometry_frontpage_strings[$rinometry_frontpage_language] : $fallback;
  return $dictionary[$key] ?? ($fallback[$key] ?? $key);
};

?>
<?php get_header(); ?>
<section class="hero" id="home">
  <div class="container hero-grid">
    <div class="hero-brand" aria-hidden="true">
      <img class="hero-logo" src="<?php echo esc_url(get_template_directory_uri() . '/assets/img/logo-rhinometric.png'); ?>" alt="" />
    </div>
    <div class="hero-copy hero-content">
      <span class="badge" data-i18n="hero.badge"><?php echo esc_html($rinometry_frontpage_translate('hero.badge')); ?></span>
      <h1 class="section-title" data-i18n="hero.title"><?php echo esc_html($rinometry_frontpage_translate('hero.title')); ?></h1>
      <p class="section-lead" data-i18n="hero.lead"><?php echo esc_html($rinometry_frontpage_translate('hero.lead')); ?></p>
      <ul class="hero-bullets">
        <li data-i18n="hero.bullet1"><?php echo esc_html($rinometry_frontpage_translate('hero.bullet1')); ?></li>
        <li data-i18n="hero.bullet2"><?php echo esc_html($rinometry_frontpage_translate('hero.bullet2')); ?></li>
        <li data-i18n="hero.bullet3"><?php echo esc_html($rinometry_frontpage_translate('hero.bullet3')); ?></li>
      </ul>
      <div class="header-actions" style="margin-top: 1.5rem;">
        <a class="btn btn-primary" href="#early-access" data-i18n="hero.ctaPrimary"><?php echo esc_html($rinometry_frontpage_translate('hero.ctaPrimary')); ?></a>
        <a class="btn btn-secondary" href="#out-of-the-box" data-i18n="hero.ctaSecondary"><?php echo esc_html($rinometry_frontpage_translate('hero.ctaSecondary')); ?></a>
      </div>
    </div>
  </div>
</section>

<section class="how-it-works" id="how-it-works" aria-label="<?php echo esc_attr($rinometry_frontpage_translate('how.aria')); ?>" data-i18n="how.aria" data-i18n-attr="aria-label">
  <div class="container">
    <div class="how-steps" role="list">
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--deploy" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step1.label"><?php echo esc_html($rinometry_frontpage_translate('how.step1.label')); ?></p>
          <p class="how-step-text" data-i18n="how.step1.text"><?php echo esc_html($rinometry_frontpage_translate('how.step1.text')); ?></p>
        </div>
      </div>
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--ingest" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step2.label"><?php echo esc_html($rinometry_frontpage_translate('how.step2.label')); ?></p>
          <p class="how-step-text" data-i18n="how.step2.text"><?php echo esc_html($rinometry_frontpage_translate('how.step2.text')); ?></p>
        </div>
      </div>
      <div class="how-step" role="listitem">
        <span class="how-icon how-icon--insight" aria-hidden="true"></span>
        <div class="how-copy">
          <p class="how-step-label" data-i18n="how.step3.label"><?php echo esc_html($rinometry_frontpage_translate('how.step3.label')); ?></p>
          <p class="how-step-text" data-i18n="how.step3.text"><?php echo esc_html($rinometry_frontpage_translate('how.step3.text')); ?></p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt console-preview-section" aria-label="<?php echo esc_attr($rinometry_frontpage_translate('console.aria')); ?>" data-i18n="console.aria" data-i18n-attr="aria-label">
  <div class="container">
    <div class="card console-preview-card">
      <div class="mock-header" data-i18n="console.header"><?php echo esc_html($rinometry_frontpage_translate('console.header')); ?></div>
      <div class="mock-line"></div>
      <div class="mock-line"></div>
      <div class="mock-line"></div>
      <div class="mock-widgets">
        <div class="mock-widget"></div>
        <div class="mock-widget"></div>
      </div>
    </div>
  </div>
</section>

<section class="section section-alt" id="out-of-the-box">
  <div class="container">
    <h2 class="section-title" data-i18n="engine.title"><?php echo esc_html($rinometry_frontpage_translate('engine.title')); ?></h2>
    <p class="section-lead" data-i18n="engine.lead"><?php echo esc_html($rinometry_frontpage_translate('engine.lead')); ?></p>
    <div class="feature-showcase" data-feature-tabs>
      <div class="feature-nav" role="tablist" aria-label="<?php echo esc_attr($rinometry_frontpage_translate('tabs.aria')); ?>" data-i18n="tabs.aria" data-i18n-attr="aria-label">
        <button type="button" class="feature-tab is-active" role="tab" aria-selected="true" aria-controls="feature-panel-metrics" id="feature-tab-metrics" data-feature-tab="feature-panel-metrics">
          <span class="feature-tab-icon feature-tab-icon--metrics" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.metrics.label"><?php echo esc_html($rinometry_frontpage_translate('tabs.metrics.label')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.metrics.point1"><?php echo esc_html($rinometry_frontpage_translate('tabs.metrics.point1')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.metrics.point2"><?php echo esc_html($rinometry_frontpage_translate('tabs.metrics.point2')); ?></span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-logs" id="feature-tab-logs" data-feature-tab="feature-panel-logs">
          <span class="feature-tab-icon feature-tab-icon--logs" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.logs.label"><?php echo esc_html($rinometry_frontpage_translate('tabs.logs.label')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.logs.point1"><?php echo esc_html($rinometry_frontpage_translate('tabs.logs.point1')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.logs.point2"><?php echo esc_html($rinometry_frontpage_translate('tabs.logs.point2')); ?></span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-traces" id="feature-tab-traces" data-feature-tab="feature-panel-traces">
          <span class="feature-tab-icon feature-tab-icon--traces" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.traces.label"><?php echo esc_html($rinometry_frontpage_translate('tabs.traces.label')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.traces.point1"><?php echo esc_html($rinometry_frontpage_translate('tabs.traces.point1')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.traces.point2"><?php echo esc_html($rinometry_frontpage_translate('tabs.traces.point2')); ?></span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-visual" id="feature-tab-visual" data-feature-tab="feature-panel-visual">
          <span class="feature-tab-icon feature-tab-icon--visual" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.visualization.label"><?php echo esc_html($rinometry_frontpage_translate('tabs.visualization.label')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.visual.point1"><?php echo esc_html($rinometry_frontpage_translate('tabs.visual.point1')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.visual.point2"><?php echo esc_html($rinometry_frontpage_translate('tabs.visual.point2')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.visual.point3"><?php echo esc_html($rinometry_frontpage_translate('tabs.visual.point3')); ?></span>
          </div>
        </button>
        <button type="button" class="feature-tab" role="tab" aria-selected="false" aria-controls="feature-panel-ai" id="feature-tab-ai" data-feature-tab="feature-panel-ai">
          <span class="feature-tab-icon feature-tab-icon--ai" aria-hidden="true"></span>
          <div class="feature-tab-copy">
            <span class="feature-tab-label" data-i18n="tabs.ai.label"><?php echo esc_html($rinometry_frontpage_translate('tabs.ai.label')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.ai.point1"><?php echo esc_html($rinometry_frontpage_translate('tabs.ai.point1')); ?></span>
            <span class="feature-tab-point" data-i18n="tabs.ai.point2"><?php echo esc_html($rinometry_frontpage_translate('tabs.ai.point2')); ?></span>
          </div>
        </button>
      </div>
      <div class="feature-display">
        <div class="feature-panel is-active" id="feature-panel-metrics" role="tabpanel" aria-labelledby="feature-tab-metrics">
          <div class="feature-badge" data-i18n="feature.badge"><?php echo esc_html($rinometry_frontpage_translate('feature.badge')); ?></div>
          <div class="feature-visual feature-visual--metrics">
            <div class="visual-dashboard">
              <div class="visual-gauge"></div>
              <div class="visual-gauge visual-gauge--secondary"></div>
              <div class="visual-bars">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.metrics.caption"><?php echo esc_html($rinometry_frontpage_translate('tabs.metrics.caption')); ?></p>
        </div>
        <div class="feature-panel" id="feature-panel-logs" role="tabpanel" aria-labelledby="feature-tab-logs">
          <div class="feature-badge" data-i18n="feature.badge"><?php echo esc_html($rinometry_frontpage_translate('feature.badge')); ?></div>
          <div class="feature-visual feature-visual--logs">
            <div class="visual-terminal">
              <div class="terminal-line"></div>
              <div class="terminal-line"></div>
              <div class="terminal-line terminal-line--highlight"></div>
              <div class="terminal-line"></div>
              <div class="terminal-line"></div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.logs.caption"><?php echo esc_html($rinometry_frontpage_translate('tabs.logs.caption')); ?></p>
        </div>
        <div class="feature-panel" id="feature-panel-traces" role="tabpanel" aria-labelledby="feature-tab-traces">
          <div class="feature-badge" data-i18n="feature.badge"><?php echo esc_html($rinometry_frontpage_translate('feature.badge')); ?></div>
          <div class="feature-visual feature-visual--traces">
            <div class="visual-graph">
              <span class="graph-node graph-node--main"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
              <span class="graph-node"></span>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.traces.caption"><?php echo esc_html($rinometry_frontpage_translate('tabs.traces.caption')); ?></p>
        </div>
        <div class="feature-panel" id="feature-panel-visual" role="tabpanel" aria-labelledby="feature-tab-visual">
          <div class="feature-badge" data-i18n="feature.badge"><?php echo esc_html($rinometry_frontpage_translate('feature.badge')); ?></div>
          <div class="feature-visual feature-visual--visual">
            <div class="visual-panels">
              <div class="panel-row">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="panel-row panel-row--wide"></div>
              <div class="panel-row">
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.visual.caption"><?php echo esc_html($rinometry_frontpage_translate('tabs.visual.caption')); ?></p>
        </div>
        <div class="feature-panel" id="feature-panel-ai" role="tabpanel" aria-labelledby="feature-tab-ai">
          <div class="feature-badge" data-i18n="feature.badge"><?php echo esc_html($rinometry_frontpage_translate('feature.badge')); ?></div>
          <div class="feature-visual feature-visual--ai">
            <div class="visual-anomaly">
              <span class="anomaly-baseline"></span>
              <span class="anomaly-spike"></span>
            </div>
          </div>
          <p class="feature-caption" data-i18n="tabs.ai.caption"><?php echo esc_html($rinometry_frontpage_translate('tabs.ai.caption')); ?></p>
        </div>
      </div>
    </div>
    <p class="engine-footnote" data-i18n="engine.footnote"><?php echo esc_html($rinometry_frontpage_translate('engine.footnote')); ?></p>
  </div>
</section>

<section class="section" id="critical-sectors">
  <div class="container">
    <h2 class="section-title" data-i18n="critical.title"><?php echo esc_html($rinometry_frontpage_translate('critical.title')); ?></h2>
    <p class="section-lead" data-i18n="critical.body"><?php echo esc_html($rinometry_frontpage_translate('critical.body')); ?></p>
  </div>
</section>

<section class="section section-alt" id="installation-support">
  <div class="container">
    <h2 class="section-title" data-i18n="install.title"><?php echo esc_html($rinometry_frontpage_translate('install.title')); ?></h2>
    <p class="section-lead" data-i18n="install.body"><?php echo esc_html($rinometry_frontpage_translate('install.body')); ?></p>
  </div>
</section>

<section class="section" id="why-rhinometric">
  <div class="container">
    <h2 class="section-title" data-i18n="why.title"><?php echo esc_html($rinometry_frontpage_translate('why.title')); ?></h2>
    <ul class="early-list">
      <li data-i18n="why.item1"><?php echo esc_html($rinometry_frontpage_translate('why.item1')); ?></li>
      <li data-i18n="why.item2"><?php echo esc_html($rinometry_frontpage_translate('why.item2')); ?></li>
      <li data-i18n="why.item3"><?php echo esc_html($rinometry_frontpage_translate('why.item3')); ?></li>
    </ul>
  </div>
</section>

<section class="section section-alt early-access" id="early-access">
  <div class="container">
    <div class="card">
      <span class="early-access-tag" data-i18n="early.tag"><?php echo esc_html($rinometry_frontpage_translate('early.tag')); ?></span>
      <h2 class="section-title" data-i18n="early.title"><?php echo esc_html($rinometry_frontpage_translate('early.title')); ?></h2>
      <p class="section-lead" data-i18n="early.lead"><?php echo esc_html($rinometry_frontpage_translate('early.lead')); ?></p>
      <a class="btn btn-primary" href="mailto:rafael.canelon@rhinometric.com" data-i18n="early.cta"><?php echo esc_html($rinometry_frontpage_translate('early.cta')); ?></a>
    </div>
  </div>
</section>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-feature-tabs]').forEach(function (container) {
      var tabs = container.querySelectorAll('.feature-tab');
      var panels = container.querySelectorAll('.feature-panel');

      function activate(tab) {
        if (!tab || tab.classList.contains('is-active')) {
          return;
        }
        tabs.forEach(function (btn) {
          btn.classList.remove('is-active');
          btn.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('is-active');
        tab.setAttribute('aria-selected', 'true');

        var targetId = tab.getAttribute('data-feature-tab');
        panels.forEach(function (panel) {
          if (panel.id === targetId) {
            panel.classList.add('is-active');
            panel.removeAttribute('aria-hidden');
          } else {
            panel.classList.remove('is-active');
            panel.setAttribute('aria-hidden', 'true');
          }
        });
      }

      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          activate(tab);
        });
        tab.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            activate(tab);
          }
        });
      });

      panels.forEach(function (panel) {
        if (!panel.classList.contains('is-active')) {
          panel.setAttribute('aria-hidden', 'true');
        }
      });
    });
  });
</script>
<?php get_footer(); ?>
