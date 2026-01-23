(function () {
  var storageKey = 'rhino_lang';
  var translations = {
    en: {
      'hero.badge': 'On-Prem Observability Engine',
      'hero.title': 'On-Premise Observability: Your Infrastructure, Your Rules.',
      'hero.lead': 'Deploy a professional stack of metrics, logs, and traces in minutes. No data leaving your network, no cloud egress fees, and total sovereignty.',
      'hero.bullet1': 'Engine installed in your data center or edge, production-ready.',
      'hero.bullet2': 'Predictable costs: zero cloud egress, zero billing surprises.',
      'hero.bullet3': 'Compliance and operational control on your own terms.',
      'hero.ctaPrimary': 'Early Adopter Program',
      'hero.ctaSecondary': 'Technical Specifications',
      'console.aria': 'Rhinometric Console Preview',
      'console.header': 'Rhinometric Console Preview',
      'engine.title': 'The Full-Stack Observability Engine.',
      'engine.lead': 'Everything you need to monitor, trace, and secure your private infrastructure—pre-configured for production and absolute data sovereignty.',
      'engine.footnote': 'Based on open standards. Zero vendor lock-in. Air-Gapped Ready. You own your configuration forever.',
      'tabs.aria': 'Technical tabs',
      'critical.title': 'Built for critical sectors',
      'critical.body': 'Built for zero-risk tolerance sectors. If your company operates in Fintech, Health, Defense, or Industrial IoT, Rhinometric guarantees that 100% of telemetry stays on your servers. Regulatory compliance (GDPR/HIPAA) and total security in Air-Gapped environments.',
      'install.title': 'Installation support & autonomy',
      'install.body': 'We build the engine; you keep the keys. We guarantee a perfect setup and stack stability. With the included Rhino Guide, your team gains the knowledge to operate with full independence, eliminating reliance on external consulting.',
      'why.title': 'Why choose Rhinometric',
      'why.item1': 'Zero Cloud Egress Fees: Save thousands by eliminating the cost of transferring data to external clouds.',
      'why.item2': 'No Vendor Lock-in: Based on open standards. You own the software and the configuration forever.',
      'why.item3': 'Time-to-Market: What takes a senior team months to configure, we deliver in an afternoon.',
      'early.tag': 'Early Access',
      'early.title': 'Looking for the first 10 pioneers.',
      'early.lead': 'Be part of the Rhinometric launch. We offer 3 months of full access and priority deployment support for free in exchange for your technical feedback. Secure your infrastructure today.',
      'early.cta': 'Apply to Program - 10 Spots Available',
      'tabs.metrics.label': 'Metrics',
      'tabs.metrics.point1': 'Infrastructure & Service Health — Prometheus: High-density monitoring based on industry standards, optimized to detect failures in milliseconds.',
      'tabs.metrics.point2': 'High-Performance Persistence — PostgreSQL + Redis: Pre-configured storage layers for ultra-fast queries and total data reliability.',
      'tabs.metrics.caption': 'Dark-mode Grafana dashboards with live CPU/RAM gauges tuned for private fleets.',
      'tabs.logs.label': 'Logs',
      'tabs.logs.point1': 'Private Log Centralization — Loki: Index terabytes of logs without a single byte leaving your network or incurring cloud egress fees.',
      'tabs.logs.point2': 'Full-Text Intelligence: Search and filter data in real-time for audits, security, and critical troubleshooting.',
      'tabs.logs.caption': 'Private Loki console with streaming ERROR filters and zero cloud egress.',
      'tabs.traces.label': 'Traces',
      'tabs.traces.point1': 'Microservices Visibility — Jaeger: Identify bottlenecks and latent failures in distributed systems with native tracing.',
      'tabs.traces.point2': 'Dependency Mapping: Visualize service interactions to find the root cause of errors in seconds.',
      'tabs.traces.caption': 'Jaeger dependency map connecting critical microservices across air-gapped clusters.',
      'tabs.visualization.label': 'Visualization',
      'tabs.visual.point1': 'Decision-Ready Dashboards — Grafana: Visual intelligence with factory-optimized panels for instant visibility.',
      'tabs.visual.caption': 'Factory-optimized Grafana layouts with Rhinometric navigation and theming.',
      'tabs.ai.label': 'AI',
      'tabs.ai.point1': 'Proactive Anomaly Detection: Smart engine that identifies deviations and unusual patterns before they turn into service outages.',
      'tabs.ai.caption': 'Signal baselines with highlighted anomaly spikes and Rhino alert overlays.',
      'feature.badge': '100% Private / On-Premise'
    },
    es: {
      'hero.badge': 'Motor de Observabilidad On-Prem',
      'hero.title': 'Observabilidad On-Premise: Tu Infraestructura, Tus Reglas.',
      'hero.lead': 'Despliega en minutos un stack profesional de métricas, logs y trazas. Sin datos saliendo de tu red, sin cargos por transferencia de nube y con soberanía total.',
      'hero.bullet1': 'Motor instalado en tu data center o edge, listo para producción.',
      'hero.bullet2': 'Costos predecibles: cero cloud egress, cero sorpresas en la factura.',
      'hero.bullet3': 'Cumplimiento y control operativo bajo tus propias reglas.',
      'hero.ctaPrimary': 'Programa Early Adopter',
      'hero.ctaSecondary': 'Especificaciones Técnicas',
      'console.aria': 'Vista previa de Rhinometric Console',
      'console.header': 'Vista previa de Rhinometric Console',
      'engine.title': 'The Full-Stack Observability Engine.',
      'engine.lead': 'Todo lo que necesitas para monitorear, trazar y asegurar tu infraestructura privada, preconfigurado para producción y con soberanía absoluta de datos.',
      'engine.footnote': 'Based on open standards. Zero vendor lock-in. Air-Gapped Ready. You own your configuration forever.',
      'tabs.aria': 'Pestañas técnicas',
      'critical.title': 'Soberanía y Cumplimiento',
      'critical.body': 'Diseñado para sectores con tolerancia cero al riesgo. Si tu empresa opera en Fintech, Salud, Defensa o IoT Industrial, Rhinometric garantiza que el 100% de la telemetría permanezca en tus servidores. Cumplimiento normativo (GDPR/HIPAA) y seguridad total en entornos Air-Gapped.',
      'install.title': 'Soporte de instalación y autonomía',
      'install.body': 'Nosotros montamos el motor, tú mantienes las llaves. Garantizamos una instalación perfecta y la estabilidad del stack. Con la Rhino Guide incluida, tu equipo obtiene el conocimiento para operar con total independencia, eliminando la dependencia de consultorías externas.',
      'why.title': 'Por qué elegir Rhinometric',
      'why.item1': 'Cero Cloud Egress Fees: ahorra miles al eliminar el costo de transferir datos a nubes externas.',
      'why.item2': 'Sin Vendor Lock-in: basado en estándares abiertos. Eres dueño del software y de tu configuración para siempre.',
      'why.item3': 'Time-to-Market: lo que a un equipo senior le toma meses, lo entregamos en una tarde.',
      'early.tag': 'Early Access',
      'early.title': 'Buscamos a los 10 primeros pioneros.',
      'early.lead': 'Sé parte del lanzamiento de Rhinometric. Ofrecemos 3 meses de acceso completo y soporte de despliegue prioritario gratis a cambio de tu feedback técnico. Asegura tu infraestructura hoy.',
      'early.cta': 'Aplicar al Programa - 10 Plazas Libres',
      'tabs.metrics.label': 'Métricas',
      'tabs.metrics.point1': 'Salud de Infraestructura & Servicios — Prometheus: Monitoreo de alta densidad basado en estándares de la industria, optimizado para detectar fallos en milisegundos.',
      'tabs.metrics.point2': 'Persistencia de Alto Rendimiento — PostgreSQL + Redis: Capas de almacenamiento pre-configuradas para consultas ultrarrápidas y una fiabilidad de datos total.',
      'tabs.metrics.caption': 'Dashboards en modo oscuro con indicadores de CPU/RAM en vivo para flotas privadas.',
      'tabs.logs.label': 'Registros',
      'tabs.logs.point1': 'Centralización Privada de Logs — Loki: Indexa terabytes de registros sin que un solo byte salga de tu red ni generar costos por transferencia de nube (Egress Fees).',
      'tabs.logs.point2': 'Inteligencia de Texto Completo: Busca y filtra datos en tiempo real para auditorías, seguridad y resolución de problemas críticos.',
      'tabs.logs.caption': 'Consola Loki privada con filtros de ERROR en streaming y cero egress.',
      'tabs.traces.label': 'Trazas',
      'tabs.traces.point1': 'Visibilidad de Microservicios — Jaeger: Identifica cuellos de botella y fallos latentes en sistemas distribuidos con trazabilidad nativa.',
      'tabs.traces.point2': 'Mapa de Dependencias: Visualiza la interacción entre servicios para hallar la causa raíz de errores en segundos.',
      'tabs.traces.caption': 'Mapa de dependencias de Jaeger conectando microservicios críticos en clústeres air-gapped.',
      'tabs.visualization.label': 'Visualización',
      'tabs.visual.point1': 'Dashboards Listos para la Decisión — Grafana: Inteligencia visual con paneles optimizados de fábrica para una visibilidad inmediata.',
      'tabs.visual.caption': 'Paneles Grafana optimizados con la navegación y el tema de Rhinometric.',
      'tabs.ai.label': 'IA',
      'tabs.ai.point1': 'Detección Proactiva de Anomalías: Motor inteligente que identifica desviaciones y patrones inusuales antes de que se conviertan en caídas de servicio.',
      'tabs.ai.caption': 'Líneas base de señal con picos de anomalía resaltados y alertas Rhino.',
      'feature.badge': '100% Private / On-Premise'
    }
  };

  function parseHashLanguage() {
    var hash = window.location.hash || '';
    var match = hash.match(/lang=([a-z]{2})/i);
    if (match && translations[match[1].toLowerCase()]) {
      return match[1].toLowerCase();
    }
    return null;
  }

  function getPreferredLanguage() {
    var fromHash = parseHashLanguage();
    if (fromHash) {
      return fromHash;
    }
    try {
      var stored = localStorage.getItem(storageKey);
      if (stored && translations[stored]) {
        return stored;
      }
    } catch (err) {}
    return 'en';
  }

  function persistLanguage(lang) {
    try {
      localStorage.setItem(storageKey, lang);
    } catch (err) {}
    var base = window.location.pathname + window.location.search;
    if (lang === 'en') {
      history.replaceState(null, '', base);
    } else {
      history.replaceState(null, '', base + '#lang=' + lang);
    }
  }

  function translateDocument(lang) {
    var fallback = translations.en;
    var dict = translations[lang] || fallback;
    document.querySelectorAll('[data-i18n]').forEach(function (node) {
      var key = node.getAttribute('data-i18n');
      if (!key) {
        return;
      }
      var text = dict[key] || fallback[key];
      var wantsText = !node.hasAttribute('data-i18n-attr') || node.getAttribute('data-i18n-text') === 'true';
      if (wantsText && typeof text === 'string') {
        node.textContent = text;
      }
    });
    document.querySelectorAll('[data-i18n-attr]').forEach(function (node) {
      var attrs = (node.getAttribute('data-i18n-attr') || '').split(',');
      var key = node.getAttribute('data-i18n');
      var attrValue = dict[key] || fallback[key];
      attrs.forEach(function (attr) {
        var name = attr.trim();
        if (name && typeof attrValue === 'string') {
          node.setAttribute(name, attrValue);
        }
      });
    });
  }

  function updateLanguageToggle(lang) {
    document.querySelectorAll('.language-switcher a').forEach(function (anchor) {
      var anchorLang = anchor.getAttribute('data-lang');
      if (!anchorLang) {
        var href = anchor.getAttribute('href') || '';
        var match = href.match(/lang=([a-z]{2})/i);
        if (match) {
          anchorLang = match[1].toLowerCase();
        }
      }
      if (!anchorLang) {
        return;
      }
      anchor.setAttribute('data-lang', anchorLang);
      anchor.setAttribute('href', '#lang=' + anchorLang);
      anchor.classList.toggle('lang-active', anchorLang === lang);
    });
  }

  function setLanguage(lang, shouldPersist) {
    var normalized = translations[lang] ? lang : 'en';
    document.documentElement.setAttribute('lang', normalized);
    translateDocument(normalized);
    updateLanguageToggle(normalized);
    if (shouldPersist) {
      persistLanguage(normalized);
    }
  }

  function initI18n() {
    var currentLang = getPreferredLanguage();
    setLanguage(currentLang, false);

    document.querySelectorAll('.language-switcher a').forEach(function (anchor) {
      anchor.addEventListener('click', function (event) {
        var lang = anchor.getAttribute('data-lang');
        if (!lang) {
          var match = (anchor.getAttribute('href') || '').match(/lang=([a-z]{2})/i);
          lang = match ? match[1].toLowerCase() : null;
        }
        if (!lang) {
          return;
        }
        event.preventDefault();
        setLanguage(lang, true);
      });
    });

    window.addEventListener('hashchange', function () {
      var langFromHash = parseHashLanguage();
      if (langFromHash) {
        setLanguage(langFromHash, true);
      } else {
        setLanguage('en', true);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initI18n);
  } else {
    initI18n();
  }
})();
