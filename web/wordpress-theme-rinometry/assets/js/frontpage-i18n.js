(function () {
  var storageKey = 'rhino_lang';
  var translations = {
    en: {
      'hero.badge': 'Unified Observability Platform',
      'hero.title': 'Own your observability stack. On-premise. Fully controlled.',
      'hero.lead': 'Deploy a curated platform for metrics, logs, and traces inside your infrastructure — without sending operational data to external SaaS. Built for regulated and on-prem environments.',
      'hero.bullet1': 'Data stays inside your infrastructure (no SaaS ingestion).',
      'hero.bullet2': 'Faster triage with guided dashboards and anomaly signals.',
      'hero.bullet3': 'Predictable operations and retention under your control.',
      'hero.ctaPrimary': '3–6 months free for early adopters (validation program)',
      'hero.ctaSecondary': 'Guided session with the team',
      'console.aria': 'Rhinometric Console Preview',
      'console.header': 'Rhinometric Console Preview',
      'trust.aria': 'Trust strip',
      'trust.copy': 'On-premise • No SaaS lock-in • Metrics + Logs + Traces',
      'benefits.title': 'Why teams choose Rhinometric',
      'benefits.card1.title': 'Data sovereignty',
      'benefits.card1.text': 'Data stays inside your infrastructure (no SaaS ingestion).',
      'benefits.card2.title': 'Unified signals',
      'benefits.card2.text': 'Unified signals: metrics, logs, and traces in one stack.',
      'benefits.card3.title': 'Faster triage',
      'benefits.card3.text': 'Faster triage with guided dashboards and anomaly signals. Predictable operations and retention under your control. Designed for compliance-driven and security-sensitive teams.',
      'deploy.title': 'Deploy fast. Operate with confidence.',
      'deploy.card1.title': 'Automated installer',
      'deploy.card1.text': 'Automated installer validates requirements and checks ports.',
      'deploy.card2.title': 'Secure configuration',
      'deploy.card2.text': 'Generates secure credentials and configuration files.',
      'deploy.card3.title': 'Docker Compose + health checks',
      'deploy.card3.text': 'Bootstraps the stack via Docker Compose. Runs health checks to confirm the platform is ready.',
      'roadmap.title': 'Roadmap (planned)',
      'roadmap.now.title': 'Now',
      'roadmap.now.text': 'Early access & validation',
      'roadmap.next1.title': 'Next',
      'roadmap.next1.text': 'Guided onboarding & dashboards',
      'roadmap.next2.title': 'Next',
      'roadmap.next2.text': 'Automated reporting & deeper integrations',
      'roadmap.later.title': 'Later',
      'roadmap.later.text': 'More self-serve workflows for non-expert users',
      'early.tag': 'Early Access',
      'early.title': 'Early Adopter Program (3–6 months)',
      'early.lead': 'We\'re onboarding a limited number of on-prem organizations to validate Rhinometric in real environments.',
      'early.item1': 'Full access for 3–6 months at no cost',
      'early.item2': 'Priority onboarding support for installation',
      'early.item3': 'Direct feedback channel with the team',
      'early.item4': 'Influence upcoming roadmap priorities',
      'early.cta': 'Join the program: rafael.canelon@rhinometric.com',
      'audience.title': 'Built for teams that can\'t compromise on control',
      'audience.card1.title': 'Regulated industries',
      'audience.card1.text': 'Finance, healthcare, government.',
      'audience.card2.title': 'DevOps/SRE teams',
      'audience.card2.text': 'Operating on-prem infrastructure.',
      'audience.card3.title': 'Data sovereignty',
      'audience.card3.text': 'Organizations avoiding SaaS observability due to data sovereignty.',
      'ootb.title': 'What you get out of the box',
      'ootb.lead': 'A curated on-prem observability stack — packaged, configured, and ready to run inside your infrastructure.',
      'tabs.aria': 'Technical tabs',
      'tabs.metrics.label': 'Metrics',
      'tabs.logs.label': 'Logs',
      'tabs.traces.label': 'Traces',
      'tabs.visualization.label': 'Visualization',
      'tabs.ai.label': 'AI',
      'tabs.metrics.item1': 'Metrics — Prometheus + exporters: Collect infrastructure and service metrics with proven standards, ready for Grafana dashboards.',
      'tabs.metrics.item2': 'Storage & performance layer — PostgreSQL + Redis: Reliable persistence and performance foundations included as part of the stack.',
      'tabs.metrics.tooling': 'Tooling: Prometheus.',
      'tabs.logs.item1': 'Logs — Loki + Promtail: Centralize and query logs across services without jumping between servers.',
      'tabs.logs.item2': 'Automated backups (platform-level): Backup mechanisms included to protect your observability data and configuration.',
      'tabs.logs.tooling': 'Tooling: Loki.',
      'tabs.traces.item1': 'Traces — Jaeger distributed tracing: Follow a request across microservices and pinpoint latency bottlenecks or failing components.',
      'tabs.traces.item2': 'Rhinometric Console: A simplified control plane for platform health, license visibility, and quick access to the stack.',
      'tabs.traces.tooling': 'Tooling: Jaeger.',
      'tabs.visual.item1': 'Dashboards — Grafana preloaded views: Start diagnosing faster with guided dashboards and a unified navigation experience.',
      'tabs.visual.item2': 'The Rhino Guide: Step-by-step deployment and operational documentation to keep your team autonomous from day one.',
      'tabs.visual.tooling': 'Tooling: Grafana.',
      'tabs.ai.item1': 'AI-assisted anomaly signals (early): Surface unusual patterns across Prometheus metrics to reduce alert noise and speed up triage.',
      'tabs.ai.item2': 'Rhinometric highlights anomalies and trends so teams can investigate faster — without sending data outside your network.',
      'tabs.ai.tooling': 'Tooling: Prometheus (signals) + Grafana (visualization).',
      'outcomes.title': 'Installation support. Operational autonomy.',
      'outcomes.card1.text': 'Our commitment is to keep your observability platform functional and stable.',
      'outcomes.card2.text': 'We provide expert support for the initial deployment and Rhinometric stack reliability. Since Rhinometric is fully on-premise, we don\'t access customer data.',
      'outcomes.card3.text': 'Application-level debugging and incident resolution remain customer-owned — Rhinometric provides the visibility your team needs to act independently.'
    },
    es: {
      'hero.badge': 'Plataforma de observabilidad unificada',
      'hero.title': 'Controla tu stack de observabilidad. On-premise y bajo tu mando.',
      'hero.lead': 'Despliega una plataforma curada para métricas, logs y trazas dentro de tu infraestructura, sin enviar datos operativos a SaaS externos. Diseñada para entornos regulados y on-prem.',
      'hero.bullet1': 'Los datos permanecen en tu infraestructura (sin ingesta SaaS).',
      'hero.bullet2': 'Triage más rápido con dashboards guiados y señales de anomalías.',
      'hero.bullet3': 'Operaciones y retención predecibles bajo tu control.',
      'hero.ctaPrimary': '3–6 meses sin costo para early adopters (programa de validación)',
      'hero.ctaSecondary': 'Sesión guiada con el equipo',
      'console.aria': 'Vista previa de Rhinometric Console',
      'console.header': 'Vista previa de Rhinometric Console',
      'trust.aria': 'Franja de confianza',
      'trust.copy': 'On-premise • Sin lock-in SaaS • Métricas + Logs + Trazas',
      'benefits.title': 'Por qué los equipos eligen Rhinometric',
      'benefits.card1.title': 'Soberanía de datos',
      'benefits.card1.text': 'Los datos permanecen dentro de tu infraestructura (sin ingesta SaaS).',
      'benefits.card2.title': 'Señales unificadas',
      'benefits.card2.text': 'Señales unificadas: métricas, logs y trazas en un solo stack.',
      'benefits.card3.title': 'Triage acelerado',
      'benefits.card3.text': 'Triage más rápido con dashboards guiados y señales de anomalías. Operaciones y retención predecibles bajo tu control. Diseñado para equipos con requisitos de cumplimiento y seguridad.',
      'deploy.title': 'Despliega rápido. Opera con confianza.',
      'deploy.card1.title': 'Instalador automatizado',
      'deploy.card1.text': 'El instalador automatizado valida requisitos y revisa puertos.',
      'deploy.card2.title': 'Configuración segura',
      'deploy.card2.text': 'Genera credenciales seguras y archivos de configuración.',
      'deploy.card3.title': 'Docker Compose + verificaciones de salud',
      'deploy.card3.text': 'Inicializa el stack vía Docker Compose y ejecuta health checks para confirmar que la plataforma está lista.',
      'roadmap.title': 'Roadmap (planificado)',
      'roadmap.now.title': 'Ahora',
      'roadmap.now.text': 'Acceso temprano y validación',
      'roadmap.next1.title': 'Próximo',
      'roadmap.next1.text': 'Onboarding guiado y dashboards',
      'roadmap.next2.title': 'Próximo',
      'roadmap.next2.text': 'Reportes automatizados e integraciones más profundas',
      'roadmap.later.title': 'Después',
      'roadmap.later.text': 'Más flujos self-serve para usuarios no expertos',
      'early.tag': 'Early Access',
      'early.title': 'Programa Early Adopter (3–6 meses)',
      'early.lead': 'Estamos incorporando un número limitado de organizaciones on-prem para validar Rhinometric en entornos reales.',
      'early.item1': 'Acceso completo por 3–6 meses sin costo',
      'early.item2': 'Soporte prioritario para la instalación',
      'early.item3': 'Canal directo de feedback con el equipo',
      'early.item4': 'Influye en las prioridades del roadmap',
      'early.cta': 'Únete al programa: rafael.canelon@rhinometric.com',
      'audience.title': 'Diseñado para equipos que no pueden ceder control',
      'audience.card1.title': 'Industrias reguladas',
      'audience.card1.text': 'Finanzas, salud, gobierno.',
      'audience.card2.title': 'Equipos DevOps/SRE',
      'audience.card2.text': 'Operan infraestructura on-premise.',
      'audience.card3.title': 'Soberanía de datos',
      'audience.card3.text': 'Organizaciones que evitan SaaS de observabilidad por soberanía de datos.',
      'ootb.title': 'Lo que recibes desde el día uno',
      'ootb.lead': 'Un stack de observabilidad on-prem, empacado y listo para correr dentro de tu infraestructura.',
      'tabs.aria': 'Pestañas técnicas',
      'tabs.metrics.label': 'Métricas',
      'tabs.logs.label': 'Logs',
      'tabs.traces.label': 'Trazas',
      'tabs.visualization.label': 'Visualización',
      'tabs.ai.label': 'IA',
      'tabs.metrics.item1': 'Métricas — Prometheus + exporters: recolecta métricas de infraestructura y servicios con estándares probados, listas para dashboards en Grafana.',
      'tabs.metrics.item2': 'Capa de almacenamiento y performance — PostgreSQL + Redis: bases confiables incluidas como parte del stack.',
      'tabs.metrics.tooling': 'Tooling: Prometheus.',
      'tabs.logs.item1': 'Logs — Loki + Promtail: centraliza y consulta logs entre servicios sin saltar entre servidores.',
      'tabs.logs.item2': 'Respaldos automatizados (nivel plataforma): mecanismos incluidos para proteger tus datos de observabilidad y configuración.',
      'tabs.logs.tooling': 'Tooling: Loki.',
      'tabs.traces.item1': 'Trazas — Jaeger distributed tracing: sigue una petición entre microservicios e identifica cuellos de botella o componentes fallando.',
      'tabs.traces.item2': 'Rhinometric Console: un plano de control simplificado para salud de la plataforma, licencias y accesos rápidos.',
      'tabs.traces.tooling': 'Tooling: Jaeger.',
      'tabs.visual.item1': 'Dashboards — Vistas precargadas en Grafana: diagnostica más rápido con dashboards guiados y navegación unificada.',
      'tabs.visual.item2': 'The Rhino Guide: documentación paso a paso para despliegue y operación, manteniendo al equipo autónomo desde el día uno.',
      'tabs.visual.tooling': 'Tooling: Grafana.',
      'tabs.ai.item1': 'Señales de anomalías asistidas por IA (temprano): resalta patrones inusuales sobre métricas de Prometheus para reducir ruido de alertas y acelerar el triage.',
      'tabs.ai.item2': 'Rhinometric resalta anomalías y tendencias para que tu equipo investigue más rápido sin sacar datos de tu red.',
      'tabs.ai.tooling': 'Tooling: Prometheus (señales) + Grafana (visualización).',
      'outcomes.title': 'Acompañamos la instalación. La operación queda en tus manos.',
      'outcomes.card1.text': 'Nuestro compromiso es mantener tu plataforma de observabilidad funcional y estable.',
      'outcomes.card2.text': 'Brindamos soporte experto para el despliegue inicial y la confiabilidad del stack Rhinometric. Como es totalmente on-premise, no accedemos a datos del cliente.',
      'outcomes.card3.text': 'El debugging a nivel aplicación y la resolución de incidentes siguen siendo responsabilidad del cliente: Rhinometric entrega la visibilidad para que tu equipo actúe de forma independiente.'
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
