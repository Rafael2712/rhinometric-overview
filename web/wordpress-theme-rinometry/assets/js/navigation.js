/**
 * navigation.js — Rhinometric v3
 * Handles mobile hamburger toggle + overlay.
 */
(function () {
  'use strict';

  var toggle  = document.querySelector('.nav-toggle');
  var overlay = document.getElementById('mobile-nav');
  if (!toggle || !overlay) return;

  function open() {
    toggle.classList.add('is-active');
    toggle.setAttribute('aria-expanded', 'true');
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    toggle.classList.remove('is-active');
    toggle.setAttribute('aria-expanded', 'false');
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function isOpen() {
    return overlay.classList.contains('is-open');
  }

  toggle.addEventListener('click', function () {
    isOpen() ? close() : open();
  });

  // Close on ESC
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen()) close();
  });

  // Close when clicking a link inside the overlay
  overlay.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', close);
  });

  // Close on overlay background click
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) close();
  });

  // Close on resize above mobile breakpoint
  var mql = window.matchMedia('(min-width: 769px)');
  mql.addEventListener('change', function (e) {
    if (e.matches && isOpen()) close();
  });
})();
