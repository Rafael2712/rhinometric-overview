/**
 * cookie-banner.js — Rhinometric v3
 * Shows cookie banner if not yet accepted; stores consent in localStorage.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'rino_cookies_accepted';
  var banner = document.getElementById('cookie-banner');
  var acceptBtn = document.getElementById('cookie-accept');
  if (!banner || !acceptBtn) return;

  // Already accepted?
  if (localStorage.getItem(STORAGE_KEY) === '1') return;

  // Show banner
  banner.classList.add('is-visible');

  acceptBtn.addEventListener('click', function () {
    localStorage.setItem(STORAGE_KEY, '1');
    banner.classList.remove('is-visible');
  });
})();
