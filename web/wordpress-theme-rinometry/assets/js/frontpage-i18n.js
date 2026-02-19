(function () {
  'use strict';

  var config = window.__RHINO_I18N__ || {};
  var translations = config.translations || {};
  var fallbackLang = config.fallbackLang && translations[config.fallbackLang] ? config.fallbackLang : 'en';
  if (!translations[fallbackLang]) {
    fallbackLang = Object.keys(translations)[0] || fallbackLang;
  }
  var supportedLanguages = Object.keys(translations);
  if (!supportedLanguages.length) {
    return;
  }

  var storageKey = config.storageKey || 'rhino_lang';
  var cookieName = config.cookieName || storageKey;
  var queryParam = config.queryParam || 'lang';
  var initialLang = config.initialLang;
  var currentLang = null;
  var warned = new Set();

  function isSupported(lang) {
    return typeof lang === 'string' && supportedLanguages.indexOf(lang) !== -1;
  }

  function escapeForRegex(str) {
    return str.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
  }

  function getLangFromQuery() {
    try {
      var params = new URLSearchParams(window.location.search);
      var value = params.get(queryParam);
      return isSupported(value) ? value : null;
    } catch (err) {
      var regex = new RegExp(queryParam + '=([a-z]{2})', 'i');
      var match = window.location.search.match(regex);
      if (match && isSupported(match[1].toLowerCase())) {
        return match[1].toLowerCase();
      }
    }
    return null;
  }

  function getLangFromCookie() {
    var pattern = new RegExp('(?:^|; )' + escapeForRegex(cookieName) + '=([^;]*)');
    var match = document.cookie.match(pattern);
    if (match) {
      var value = decodeURIComponent(match[1]);
      return isSupported(value) ? value : null;
    }
    return null;
  }

  function getLangFromStorage() {
    try {
      var value = localStorage.getItem(storageKey);
      return isSupported(value) ? value : null;
    } catch (err) {
      return null;
    }
  }

  function persistLanguage(lang) {
    try {
      localStorage.setItem(storageKey, lang);
    } catch (err) {}
    var maxAge = 60 * 60 * 24 * 30;
    document.cookie = cookieName + '=' + encodeURIComponent(lang) + ';path=/;max-age=' + maxAge + ';SameSite=Lax';
  }

  function syncUrl(lang) {
    if (typeof URL === 'undefined' || typeof history.replaceState !== 'function') {
      return;
    }
    var url = new URL(window.location.href);
    if (lang === fallbackLang) {
      url.searchParams.delete(queryParam);
    } else {
      url.searchParams.set(queryParam, lang);
    }
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  function getDict(lang) {
    return translations[lang] || translations[fallbackLang] || {};
  }
  function t(lang, key) {
    if (!key) return null;
    var langDict = translations[lang] || {};
    if (typeof langDict[key] === 'string' && langDict[key] !== '') {
      return langDict[key];
    }

    var enDict = translations['en'] || {};
    if (typeof enDict[key] === 'string' && enDict[key] !== '') {
      if (!warned.has(key)) {
        console.warn('[i18n] Missing "' + key + '" for ' + lang + '. Falling back to EN.');
        warned.add(key);
      }
      return enDict[key];
    }

    if (!warned.has(key)) {
      console.warn('[i18n] Missing "' + key + '" for ' + lang + ' and EN. Keeping existing content.');
      warned.add(key);
    }
    return null;
  }

  function translateNodes(lang) {
    document.querySelectorAll('[data-i18n]').forEach(function (node) {
      var key = node.getAttribute('data-i18n');
      if (!key) return;
      var wantsText = !node.hasAttribute('data-i18n-attr') || node.getAttribute('data-i18n-text') === 'true';
      var value = t(lang, key);
      if (value === null) return; // keep existing content
      if (wantsText) {
        node.textContent = value;
      }
    });

    document.querySelectorAll('[data-i18n-attr]').forEach(function (node) {
      var attrs = (node.getAttribute('data-i18n-attr') || '').split(',');
      var key = node.getAttribute('data-i18n');
      if (!key) return;
      var value = t(lang, key);
      if (value === null) return;
      attrs.forEach(function (attr) {
        var name = attr.trim();
        if (name) {
          node.setAttribute(name, value);
        }
      });
    });
  }

  function updateLanguageToggle(lang) {
    document.querySelectorAll('.language-switcher a').forEach(function (anchor) {
      var anchorLang = (anchor.getAttribute('data-lang') || '').toLowerCase();
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
      anchor.classList.toggle('lang-active', anchorLang === lang);
      if (anchorLang === lang) {
        anchor.setAttribute('aria-current', 'true');
      } else {
        anchor.removeAttribute('aria-current');
      }
    });
  }

  function updateModalDataset(lang) {
    var form = document.querySelector('.elite-modal-form');
    if (!form) {
      return;
    }
    var datasetMap = [
      ['errorRequired', 'modal.error.required'],
      ['errorEmail', 'modal.error.email'],
      ['errorServer', 'modal.error.server'],
      ['errorsTitle', 'modal.error.listTitle'],
      ['loadingLabel', 'modal.loading'],
      ['submitLabel', 'modal.submit'],
      ['successTitle', 'modal.success.title']
    ];
    datasetMap.forEach(function (entry) {
      var key = entry[1];
      var value = t(lang, key);
      if (typeof value === 'string') {
        form.dataset[entry[0]] = value;
      }
    });
    var submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
      var submitLabel = form.dataset.submitLabel || submitButton.textContent || '';
      var loadingLabel = form.dataset.loadingLabel || submitLabel;
      submitButton.setAttribute('data-default-label', submitLabel);
      submitButton.setAttribute('data-loading-label', loadingLabel);
      if (!form.classList.contains('is-submitted')) {
        submitButton.textContent = submitLabel;
      }
    }
    var langField = form.querySelector('input[name="current_lang"]');
    if (langField) {
      langField.value = lang;
    }
  }

  function setLanguage(lang, options) {
    options = options || {};
    var normalized = isSupported(lang) ? lang : fallbackLang;
    var previous = currentLang;
    currentLang = normalized;
    document.documentElement.setAttribute('lang', normalized);
    translateNodes(normalized);
    updateLanguageToggle(normalized);
    updateModalDataset(normalized);
    if (options.persist !== false) {
      persistLanguage(normalized);
    }
    if (options.updateUrl) {
      syncUrl(normalized);
    }
    if (previous !== normalized) {
      try {
        window.dispatchEvent(new CustomEvent('rinometry:language-change', { detail: { lang: normalized } }));
      } catch (err) {}
    }
  }

  function bindSwitchers() {
    document.querySelectorAll('.language-switcher a').forEach(function (anchor) {
      anchor.addEventListener('click', function (event) {
        var lang = anchor.getAttribute('data-lang');
        if (!lang) {
          var match = (anchor.getAttribute('href') || '').match(/lang=([a-z]{2})/i);
          lang = match ? match[1].toLowerCase() : null;
        }
        if (!isSupported(lang)) {
          return;
        }
        event.preventDefault();
        setLanguage(lang, { persist: true, updateUrl: true });
      });
    });
  }

  function init() {
    bindSwitchers();
    var langFromQuery = getLangFromQuery();
    var langFromCookie = getLangFromCookie();
    var langFromStorage = getLangFromStorage();
    var fallbackInitial = isSupported(initialLang) ? initialLang : null;
    var startingLang = langFromQuery || langFromCookie || langFromStorage || fallbackInitial || fallbackLang;
    setLanguage(startingLang, {
      persist: Boolean(langFromQuery),
      updateUrl: false
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
