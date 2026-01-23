(function () {
  'use strict';

  var backdrop = document.querySelector('[data-elite-modal]');
  if (!backdrop) {
    return;
  }

  var container = backdrop.querySelector('.elite-modal-container');
  var form = backdrop.querySelector('.elite-modal-form');
  var successPanel = backdrop.querySelector('.elite-modal-success');
  var feedback = backdrop.querySelector('.elite-modal-feedback');
  var errorsBox = backdrop.querySelector('.elite-modal-errors');
  var submitButton = form ? form.querySelector('button[type="submit"]') : null;
  var triggers = document.querySelectorAll('[data-elite-modal-trigger]');
  var closeButtons = backdrop.querySelectorAll('[data-elite-modal-close]');
  var focusableSelectors = 'a[href], button:not([disabled]), textarea, input:not([type="hidden"]), select, [tabindex]:not([tabindex="-1"])';
  var lastFocusedElement = null;
  var submitting = false;
  function getDefaultSubmitLabel() {
    if (!submitButton) {
      return '';
    }
    return submitButton.getAttribute('data-default-label') || submitButton.textContent || '';
  }

  function getLoadingSubmitLabel() {
    if (!submitButton) {
      return '';
    }
    return submitButton.getAttribute('data-loading-label') || submitButton.textContent || '';
  }

  function getServerErrorMessage() {
    if (!form) {
      return '';
    }
    return form.dataset.errorServer || '';
  }

  function lockScroll() {
    document.documentElement.classList.add('modal-open');
    document.body.classList.add('modal-open');
  }

  function unlockScroll() {
    document.documentElement.classList.remove('modal-open');
    document.body.classList.remove('modal-open');
  }

  function getFocusableElements() {
    if (!container) {
      return [];
    }
    return Array.prototype.slice.call(container.querySelectorAll(focusableSelectors)).filter(function (el) {
      return !el.hasAttribute('disabled') && el.getAttribute('aria-hidden') !== 'true';
    });
  }

  function trapFocus(event) {
    if (event.key !== 'Tab' || backdrop.hidden) {
      return;
    }
    var focusable = getFocusableElements();
    if (!focusable.length) {
      return;
    }
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    var isShift = event.shiftKey;
    if (isShift && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!isShift && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function resetFeedback() {
    if (feedback) {
      feedback.textContent = '';
    }
  }

  function clearErrorSummary() {
    if (!errorsBox) {
      return;
    }
    errorsBox.classList.remove('is-visible');
    errorsBox.innerHTML = '';
  }

  function hideErrors() {
    clearErrorSummary();
    if (!form) {
      return;
    }
    Array.prototype.forEach.call(form.elements, function (field) {
      field.classList.remove('is-invalid');
      field.removeAttribute('aria-invalid');
    });
  }

  function showErrors(summary, fieldErrors) {
    if (!errorsBox) {
      return;
    }
    errorsBox.innerHTML = '';
    if (summary) {
      var title = document.createElement('strong');
      title.textContent = summary;
      errorsBox.appendChild(title);
    }
    if (fieldErrors && fieldErrors.length) {
      var list = document.createElement('ul');
      fieldErrors.forEach(function (message) {
        var item = document.createElement('li');
        item.textContent = message;
        list.appendChild(item);
      });
      errorsBox.appendChild(list);
    }
    errorsBox.classList.add('is-visible');
  }

  function markFieldError(fieldName, message) {
    if (!form) {
      return;
    }
    var field = form.elements.namedItem(fieldName);
    if (field) {
      field.classList.add('is-invalid');
      field.setAttribute('aria-invalid', 'true');
    }
    if (errorsBox && message) {
      errorsBox.classList.add('is-visible');
    }
  }

  function updateSubmitState() {
    if (!submitButton || !form) {
      return;
    }
    if (submitting) {
      submitButton.disabled = true;
      return;
    }
    submitButton.disabled = !form.checkValidity();
  }

  function syncSubmitButtonCopy() {
    if (!submitButton) {
      return;
    }
    submitButton.textContent = submitting ? getLoadingSubmitLabel() : getDefaultSubmitLabel();
    submitButton.disabled = submitting || (form ? !form.checkValidity() : false);
  }

  function setSubmittingState(isSubmitting) {
    submitting = isSubmitting;
    syncSubmitButtonCopy();
  }

  function resetFormState() {
    if (!form) {
      return;
    }
    form.classList.remove('is-submitted');
    form.removeAttribute('aria-hidden');
    if (successPanel) {
      successPanel.hidden = true;
    }
    form.reset();
    setSubmittingState(false);
    hideErrors();
    resetFeedback();
  }

  function openModal(event) {
    if (event) {
      event.preventDefault();
    }
    if (!backdrop || !container) {
      return;
    }
    if (!backdrop.hidden) {
      return;
    }
    resetFormState();
    lastFocusedElement = document.activeElement;
    backdrop.hidden = false;
    lockScroll();
    window.requestAnimationFrame(function () {
      backdrop.classList.add('is-visible');
      setTimeout(function () {
        container.focus();
      }, 20);
    });
  }

  function closeModal(event) {
    if (event) {
      event.preventDefault();
    }
    if (!backdrop) {
      return;
    }
    backdrop.classList.remove('is-visible');
    unlockScroll();
    setTimeout(function () {
      backdrop.hidden = true;
      if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
        lastFocusedElement.focus();
      }
    }, 220);
  }

  function onBackdropClick(event) {
    if (event.target === backdrop) {
      closeModal(event);
    }
  }

  function onKeyDown(event) {
    if (backdrop.hidden) {
      return;
    }
    if (event.key === 'Escape') {
      closeModal(event);
    } else if (event.key === 'Tab') {
      trapFocus(event);
    }
  }

  function handleFieldInput(event) {
    if (!form) {
      return;
    }
    var target = event.target;
    if (!target || !form.contains(target)) {
      return;
    }
    target.classList.remove('is-invalid');
    target.removeAttribute('aria-invalid');
    clearErrorSummary();
    resetFeedback();
    updateSubmitState();
  }

  function handleSuccess(message) {
    if (!form || !successPanel) {
      return;
    }
    form.classList.add('is-submitted');
    form.setAttribute('aria-hidden', 'true');
    successPanel.hidden = false;
    var textNode = successPanel.querySelector('.elite-modal-success-text');
    if (message && textNode) {
      textNode.textContent = message;
    }
    if (feedback) {
      feedback.textContent = message || '';
    }
  }

  function handleSubmissionError(serverMessage, fieldMap) {
    if (feedback) {
      feedback.textContent = serverMessage || '';
    }
    var errorList = [];
    if (fieldMap) {
      Object.keys(fieldMap).forEach(function (name) {
        markFieldError(name, fieldMap[name]);
        if (fieldMap[name]) {
          errorList.push(fieldMap[name]);
        }
      });
    }
    showErrors(serverMessage, errorList);
    var focusField = fieldMap ? Object.keys(fieldMap)[0] : null;
    if (focusField) {
      var el = form.elements.namedItem(focusField);
      if (el && typeof el.focus === 'function') {
        el.focus();
      }
    }
  }

  function submitForm(event) {
    if (!form) {
      return;
    }
    event.preventDefault();
    if (submitting || !form.checkValidity()) {
      updateSubmitState();
      return;
    }
    setSubmittingState(true);
    resetFeedback();
    hideErrors();
    var formData = new FormData(form);
    fetch(form.action, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: formData
    })
      .then(function (response) {
        return response.json().catch(function () {
          throw new Error('invalid-json');
        }).then(function (payload) {
          return {
            ok: response.ok,
            status: response.status,
            payload: payload
          };
        });
      })
      .then(function (result) {
        setSubmittingState(false);
        var data = result.payload ? result.payload.data : null;
        if (result.ok && result.payload && result.payload.success) {
          var message = data && data.message ? data.message : '';
          handleSuccess(message);
          return;
        }
        var errors = data && data.errors ? data.errors : null;
        var message = data && data.message ? data.message : getServerErrorMessage();
        handleSubmissionError(message, errors);
      })
      .catch(function () {
        setSubmittingState(false);
        handleSubmissionError(getServerErrorMessage());
      });
  }

  function init() {
    if (!container || !form || !submitButton) {
      return;
    }
    syncSubmitButtonCopy();
    triggers.forEach(function (trigger) {
      trigger.addEventListener('click', openModal);
    });
    closeButtons.forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });
    backdrop.addEventListener('click', onBackdropClick);
    document.addEventListener('keydown', onKeyDown);
    form.addEventListener('submit', submitForm);
    form.addEventListener('input', handleFieldInput);
    form.addEventListener('change', handleFieldInput);
    window.addEventListener('rinometry:language-change', syncSubmitButtonCopy);
  }

  init();
})();
