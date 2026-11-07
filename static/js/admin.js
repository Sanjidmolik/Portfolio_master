/* Admin Control Center interactions. */
(function () {
  'use strict';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var csrfMeta = $('meta[name="csrf-token"]');
  var CSRF = csrfMeta ? csrfMeta.content : '';

  function postJSON(url, data) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-CSRFToken': CSRF },
      body: JSON.stringify(data || {})
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, error: 'Unexpected response (' + r.status + ')' }; })
        .then(function (j) { if (!r.ok && j.ok !== false) j.ok = false; return j; });
    });
  }

  function toast(msg, kind) {
    var t = document.createElement('div');
    t.className = 'toast toast-' + (kind || 'ok'); t.setAttribute('role', 'status'); t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('show'); });
    setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 300); }, 2600);
  }

  /* ---------- Sidebar (mobile) ---------- */
  var sideBtn = $('[data-side-toggle]'), side = $('#sidebar');
  if (sideBtn && side) {
    sideBtn.addEventListener('click', function () {
      var open = !side.classList.contains('open');
      side.classList.toggle('open', open); sideBtn.setAttribute('aria-expanded', String(open));
    });
  }

  /* ---------- Show / hide password ---------- */
  var EYE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.53 13.53 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="m2 2 20 20"/></svg>';
  $$('input[type=password]').forEach(function (input) {
    var wrap = document.createElement('span');
    wrap.className = 'pw-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pw-toggle';
    btn.setAttribute('aria-label', 'Show password');
    btn.setAttribute('aria-pressed', 'false');
    btn.innerHTML = EYE;
    wrap.appendChild(btn);
    btn.addEventListener('click', function () {
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.innerHTML = show ? EYE_OFF : EYE;
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      btn.setAttribute('aria-pressed', String(show));
      input.focus();
    });
    // never leave a password visible when the form is sent
    if (input.form) input.form.addEventListener('submit', function () { input.type = 'password'; });
  });
  // Caps Lock warning on password fields
  $$('.pw-wrap input').forEach(function (input) {
    var warn = document.createElement('p');
    warn.className = 'caps-warn'; warn.hidden = true; warn.textContent = 'Caps Lock is on';
    input.closest('.pw-wrap').after(warn);
    ['keydown', 'keyup'].forEach(function (ev) {
      input.addEventListener(ev, function (e) { if (e.getModifierState) warn.hidden = !e.getModifierState('CapsLock'); });
    });
  });

  /* ---------- Confirmations (keep the submitter's name/value) ---------- */
  document.addEventListener('submit', function (e) {
    var f = e.target, btn = e.submitter;
    var msg = (btn && btn.dataset.confirmBtn) || f.dataset.confirm;
    if (msg && !window.confirm(msg)) e.preventDefault();
  }, true);

  /* ---------- Visibility toggles via fetch ---------- */
  $$('[data-toggle-form]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      fetch(f.action, { method: 'POST', body: new FormData(f), headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) throw new Error();
          var b = $('.switch', f); b.classList.toggle('on', d.value); b.setAttribute('aria-checked', String(d.value));
          var row = f.closest('tr'); if (row) row.classList.toggle('is-hidden', !d.value);
          toast(d.value ? 'Now visible on your portfolio' : 'Hidden from your portfolio');
        }).catch(function () { toast('Could not update. Refresh and try again.', 'err'); });
    });
  });

  /* ---------- Drag-and-drop list sorting ---------- */
  function makeSortable(list, itemSel, onDrop) {
    var dragging = null;
    list.addEventListener('dragstart', function (e) {
      var item = e.target.closest(itemSel);
      if (!item || item.classList.contains('locked')) { e.preventDefault(); return; }
      dragging = item; item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      try { e.dataTransfer.setData('text/plain', ''); } catch (err) {}
      if (e.dataTransfer.setDragImage && item.tagName === 'TR') e.dataTransfer.setDragImage(item, 20, 20);
    });
    list.addEventListener('dragover', function (e) {
      if (!dragging) return;
      e.preventDefault();
      var over = e.target.closest(itemSel);
      if (!over || over === dragging || over.classList.contains('locked')) return;
      var r = over.getBoundingClientRect();
      var after = (e.clientY - r.top) > r.height / 2;
      list.insertBefore(dragging, after ? over.nextSibling : over);
    });
    list.addEventListener('dragend', function () {
      if (!dragging) return;
      dragging.classList.remove('dragging'); dragging = null; onDrop();
    });
  }

  $$('[data-sortable]').forEach(function (tbody) {
    // make the whole row draggable only while the handle is pressed
    $$('.drag', tbody).forEach(function (h) {
      var row = h.closest('tr');
      h.addEventListener('mousedown', function () { row.setAttribute('draggable', 'true'); });
      row.addEventListener('dragend', function () { row.removeAttribute('draggable'); });
    });
    makeSortable(tbody, 'tr', function () {
      var ids = $$('tr', tbody).map(function (r) { return parseInt(r.dataset.id, 10); });
      postJSON(tbody.dataset.sortable, { ids: ids }).then(function (d) {
        toast(d.ok ? 'Order saved' : (d.error || 'Could not save order'), d.ok ? 'ok' : 'err');
        $$('tr', tbody).forEach(function (r, i, all) {
          var b = $$('.move button', r); if (b.length === 2) { b[0].disabled = i === 0; b[1].disabled = i === all.length - 1; }
        });
      });
    });
  });

  /* ---------- Image upload preview ---------- */
  $$('[data-upload]').forEach(function (box) {
    var input = $('[data-upload-input]', box);
    if (!input) return;
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file || !/^image\//.test(file.type)) return;
      var holder = $('[data-upload-img]', box);
      var img = document.createElement('img'); img.setAttribute('data-upload-img', ''); img.alt = '';
      img.src = URL.createObjectURL(file);
      holder.replaceWith(img);
    });
  });

  /* ---------- Icon picker ---------- */
  function renderIconPreview(input) {
    var wrap = input.closest('.f'), prev = $('[data-icon-preview]', wrap), v = input.value.trim();
    if (!prev) return;
    if (/^si:[a-z0-9]{1,40}$/.test(v)) {
      prev.innerHTML = '';
      var m = document.createElement('span');
      m.className = 'si-mask';
      m.style.setProperty('--si', 'url(https://cdn.simpleicons.org/' + v.slice(3) + ')');
      prev.appendChild(m);
      return;
    }
    var match = $('[data-icon-choice="' + CSS.escape(v) + '"]', wrap);
    prev.innerHTML = match ? match.innerHTML : '';
  }
  $$('[data-icon-choice]').forEach(function (b) {
    b.addEventListener('click', function () {
      var input = $('[data-icon-input]', b.closest('.f'));
      input.value = b.dataset.iconChoice;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
  });
  $$('[data-icon-input]').forEach(function (input) {
    input.addEventListener('input', function () { renderIconPreview(input); });
  });

  /* ---------- Professional forms: counters, validation, dirty state ---------- */
  function updateCounter(el) {
    var c = $('[data-counter-for="' + el.id + '"]');
    var max = parseInt(el.getAttribute('maxlength'), 10);
    if (!c || !max) return;
    var n = el.value.length;
    c.textContent = n + ' / ' + max;
    c.classList.toggle('near', n >= max * 0.9 && n < max);
    c.classList.toggle('full', n >= max);
  }

  function fieldMessage(el) {
    var v = el.validity, label = (el.closest('.f') && $('label', el.closest('.f'))) ;
    var name = label ? label.textContent.replace('*', '').trim() : 'This field';
    if (v.valueMissing) return name + ' is required.';
    if (v.tooLong) return name + ' is too long.';
    if (v.typeMismatch && el.type === 'email') return 'Enter a valid email address, e.g. name@example.com.';
    if (v.typeMismatch && el.type === 'url') return 'Enter a full URL starting with https://';
    if (v.patternMismatch) return name + ': ' + (el.title || 'invalid format') + '.';
    if (v.rangeOverflow || v.rangeUnderflow || v.stepMismatch || v.badInput) return name + ' must be a number between ' + el.min + ' and ' + el.max + '.';
    return el.validationMessage;
  }

  function setFieldError(el, msg) {
    var f = el.closest('.f');
    if (!f) return;
    var p = $('.err[data-live]', f);
    if (msg) {
      f.classList.add('has-error');
      if (!p) { p = document.createElement('p'); p.className = 'err'; p.setAttribute('data-live', ''); p.setAttribute('role', 'alert'); f.appendChild(p); }
      p.textContent = msg;
    } else {
      if (p) p.remove();
      if (!$('.err:not([data-live])', f)) f.classList.remove('has-error');
    }
  }

  $$('[data-pro-form]').forEach(function (form) {
    var status = $('[data-dirty-status]', form);
    var fields = $$('input:not([type=hidden]):not([type=file]), textarea, select', form);
    var snapshot = function () { return fields.map(function (el) { return el.type === 'checkbox' ? el.checked : el.value; }).join('\u0001'); };
    var initial = snapshot(), submitting = false;

    function refreshDirty() {
      var dirty = snapshot() !== initial || $$('input[type=file]', form).some(function (i) { return i.files && i.files.length; });
      form.classList.toggle('is-dirty', dirty);
      if (status) status.textContent = dirty ? 'Unsaved changes' : 'All changes saved';
      return dirty;
    }

    fields.forEach(function (el) {
      if (el.getAttribute('maxlength')) updateCounter(el);
      el.addEventListener('input', function () { updateCounter(el); refreshDirty(); if (el.closest('.has-error') && el.checkValidity()) setFieldError(el, ''); });
      el.addEventListener('change', refreshDirty);
      el.addEventListener('blur', function () { if (el.value && !el.checkValidity()) setFieldError(el, fieldMessage(el)); });
    });
    $$('input[type=file]', form).forEach(function (i) { i.addEventListener('change', refreshDirty); });

    form.addEventListener('submit', function (e) {
      var bad = fields.filter(function (el) { return !el.disabled && !el.checkValidity(); });
      bad.forEach(function (el) { setFieldError(el, fieldMessage(el)); });
      if (bad.length) {
        e.preventDefault();
        var panel = bad[0].closest('[data-cpanel]');
        if (panel) showTab(panel.dataset.cpanel);
        bad[0].focus();
        bad[0].scrollIntoView({ block: 'center' });
        toast(bad.length + ' field' + (bad.length > 1 ? 's need' : ' needs') + ' attention', 'err');
        return;
      }
      submitting = true;
      $$('button[type=submit]', form).forEach(function (b) { b.classList.add('is-busy'); });
    });

    window.addEventListener('beforeunload', function (e) {
      if (!submitting && refreshDirty()) { e.preventDefault(); e.returnValue = ''; }
    });

    // Reset-to-default buttons (Site Content)
    $$('[data-reset-to]', form).forEach(function (b) {
      b.addEventListener('click', function () {
        var el = document.getElementById(b.dataset.resetTarget);
        el.value = b.dataset.resetTo;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.focus();
      });
    });

    var summary = $('[data-error-summary]', form);
    if (summary) summary.focus();
  });

  /* ---------- Site Content tabs ---------- */
  var tabField = $('[data-tab-field]');
  function showTab(key) {
    var found = false;
    $$('[data-ctab]').forEach(function (t) {
      var on = t.dataset.ctab === key; found = found || on;
      t.setAttribute('aria-selected', String(on)); t.classList.toggle('active', on);
    });
    if (!found) return;
    $$('[data-cpanel]').forEach(function (p) { p.hidden = p.dataset.cpanel !== key; });
    if (tabField) tabField.value = key;
    if (history.replaceState) history.replaceState(null, '', '#' + key);
  }
  $$('[data-ctab]').forEach(function (t) {
    t.addEventListener('click', function () { showTab(t.dataset.ctab); });
    t.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var tabs = $$('[data-ctab]'), i = tabs.indexOf(t) + (e.key === 'ArrowRight' ? 1 : -1);
      var next = tabs[(i + tabs.length) % tabs.length]; next.focus(); showTab(next.dataset.ctab);
    });
  });
  if ($('[data-ctab]')) {
    var firstErr = $('[data-cpanel] .has-error');
    if (firstErr) showTab(firstErr.closest('[data-cpanel]').dataset.cpanel);
    else if (location.hash) showTab(location.hash.slice(1));
    else showTab($('[data-ctab]').dataset.ctab);
  }
  $$('[data-goto]').forEach(function (a) {
    a.addEventListener('click', function () {
      var el = document.getElementById('field-' + a.dataset.goto);
      var panel = el && el.closest('[data-cpanel]');
      if (panel) showTab(panel.dataset.cpanel);
    });
  });

  /* ======================================================================
     Design Center
     ====================================================================== */
  var layout = $('.design-layout');
  if (!layout) return;
  var form = $('[data-design-form]');
  var frame = $('[data-preview-frame]');
  var stateEl = $('[data-save-state]');
  var defaults = JSON.parse($('#design-defaults').textContent);
  var current = JSON.parse($('#design-data').textContent);
  var savedSnapshot = JSON.stringify(current);
  var frameReady = false, lastCompiled = null, compileTimer = null;

  form.addEventListener('submit', function (e) { e.preventDefault(); });

  function setState(text, kind) { stateEl.textContent = text; stateEl.className = 'save-state ' + (kind || ''); }

  // Tabs
  var tabs = $$('[data-tab]', form);
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      tabs.forEach(function (x) { var on = x === t; x.classList.toggle('active', on); x.setAttribute('aria-selected', String(on)); });
      $$('[data-panel]', form).forEach(function (p) { p.hidden = p.dataset.panel !== t.dataset.tab; });
    });
  });
  if (location.hash === '#sections') { var st = $('[data-tab="sections"]'); if (st) st.click(); }

  // Read the whole form into a design object
  function collect() {
    var d = JSON.parse(JSON.stringify(current));
    $$('[name]', form).forEach(function (el) {
      var parts = el.name.split('.'); if (parts.length !== 2 || !d[parts[0]]) return;
      if (el.type === 'radio') { if (el.checked) d[parts[0]][parts[1]] = el.value; }
      else if (el.type === 'checkbox') d[parts[0]][parts[1]] = el.checked;
      else if (el.type === 'range') d[parts[0]][parts[1]] = parseFloat(el.value);
      else d[parts[0]][parts[1]] = el.value;
    });
    d.sections = $$('[data-section-list] > li').map(function (li) {
      var en = $('[data-sec-enabled]', li), t = $('[data-sec-title]', li), s = $('[data-sec-subtitle]', li);
      var prev = (current.sections || []).filter(function (x) { return x.key === li.dataset.key; })[0] || {};
      return { key: li.dataset.key, enabled: en ? en.checked : true, title: t ? t.value : (prev.title || ''), subtitle: s ? s.value : (prev.subtitle || '') };
    });
    return d;
  }

  // Write a design object back into the form
  function apply(d) {
    current = d;
    $$('[name]', form).forEach(function (el) {
      var parts = el.name.split('.'); if (parts.length !== 2 || !d[parts[0]]) return;
      var v = d[parts[0]][parts[1]];
      if (el.type === 'radio') el.checked = el.value === v;
      else if (el.type === 'checkbox') el.checked = !!v;
      else el.value = v;
    });
    var list = $('[data-section-list]');
    d.sections.forEach(function (s) {
      var li = $('li[data-key="' + s.key + '"]', list); if (!li) return;
      list.appendChild(li);
      var en = $('[data-sec-enabled]', li); if (en) en.checked = s.enabled;
      var t = $('[data-sec-title]', li); if (t) t.value = s.title;
      var sub = $('[data-sec-subtitle]', li); if (sub) sub.value = s.subtitle;
    });
    syncOutputs(); changed(true);
  }

  function syncOutputs() {
    $$('input[type=range]', form).forEach(function (r) {
      var o = $('output', r.closest('label')); if (o) o.textContent = r.value + (r.dataset.unit || '');
    });
    $$('.color-row', form).forEach(function (row) { $('[data-hex]', row).textContent = $('input', row).value; });
    contrastCheck();
  }

  // WCAG contrast hint between text and background
  function lum(hex) {
    var c = [1, 3, 5].map(function (i) { var v = parseInt(hex.substr(i, 2), 16) / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function ratio(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function contrastCheck() {
    var el = $('[data-contrast]'); if (!el) return;
    var d = collect(), warn = [];
    var r1 = ratio(d.colors.text, d.colors.background), r2 = ratio(d.colors.text_light, d.colors.background_light);
    if (r1 < 4.5) warn.push('Dark theme text contrast is ' + r1.toFixed(1) + ':1 (aim for 4.5:1+).');
    if (r2 < 4.5) warn.push('Light theme text contrast is ' + r2.toFixed(1) + ':1 (aim for 4.5:1+).');
    el.hidden = !warn.length; el.textContent = warn.join(' ');
  }

  function changed(skipState) {
    current = collect();
    if (!skipState) setState(JSON.stringify(current) === savedSnapshot ? 'Draft saved' : 'Unsaved changes', 'dirty');
    clearTimeout(compileTimer);
    compileTimer = setTimeout(pushPreview, 120);
  }

  function pushPreview() {
    postJSON(layout.dataset.compileUrl, current).then(function (res) {
      if (!res.ok) return;
      lastCompiled = res;
      send();
    });
  }
  function send() {
    if (!frameReady || !lastCompiled || !frame.contentWindow) return;
    frame.contentWindow.postMessage({
      type: 'pf-design', css: lastCompiled.css, classes: lastCompiled.classes, fontUrl: lastCompiled.font_url,
      mode: lastCompiled.mode, sections: lastCompiled.sections
    }, location.origin);
  }
  window.addEventListener('message', function (e) {
    if (e.origin === location.origin && e.source === frame.contentWindow && e.data && e.data.type === 'pf-preview-ready') {
      frameReady = true; if (lastCompiled) send(); else pushPreview();
    }
  });

  form.addEventListener('input', function (e) { if (e.target.matches('input[type=range], input[type=color]')) syncOutputs(); changed(); });
  form.addEventListener('change', function () { syncOutputs(); changed(); });

  // One-click theme presets (whole design; keeps the current sections)
  var presetData = $('#design-presets') ? JSON.parse($('#design-presets').textContent) : [];
  $$('[data-apply-preset]').forEach(function (b) {
    b.addEventListener('click', function () {
      var p = presetData.filter(function (x) { return x.key === b.dataset.applyPreset; })[0];
      if (!p) return;
      var d = JSON.parse(JSON.stringify(p.design));
      d.sections = collect().sections;
      apply(d);
      $$('[data-preset-card]').forEach(function (c) { c.classList.toggle('is-current', c.dataset.presetCard === p.key); });
      setState('Theme applied, not published', 'dirty');
      toast(p.name + ' applied to the preview. Publish to make it live.');
    });
  });

  // Palette presets
  $$('[data-preset]').forEach(function (b) {
    b.addEventListener('click', function () {
      var p = JSON.parse(b.dataset.preset);
      Object.keys(p).forEach(function (k) { var el = $('[name="colors.' + k + '"]', form); if (el) el.value = p[k]; });
      syncOutputs(); changed();
    });
  });

  // Section ordering
  var secList = $('[data-section-list]');
  makeSortable(secList, 'li', function () { changed(); });
  secList.addEventListener('click', function (e) {
    var up = e.target.closest('[data-sec-up]'), down = e.target.closest('[data-sec-down]');
    if (!up && !down) return;
    var li = e.target.closest('li');
    if (up && li.previousElementSibling && !li.previousElementSibling.classList.contains('locked')) secList.insertBefore(li, li.previousElementSibling);
    if (down && li.nextElementSibling) secList.insertBefore(li.nextElementSibling, li);
    changed();
  });

  // Device sizes
  $$('[data-device]').forEach(function (b) {
    b.addEventListener('click', function () {
      $$('[data-device]').forEach(function (x) { x.classList.toggle('active', x === b); });
      $('[data-stage]').dataset.device = b.dataset.device;
    });
  });

  // Actions
  function busy(btn, on) { btn.disabled = on; btn.classList.toggle('is-busy', on); }
  $$('[data-act]', form).forEach(function (btn) {
    btn.addEventListener('click', function () {
      var act = btn.dataset.act;
      if (act === 'reset' && !confirm('Load the default design into your draft? (Nothing is published until you click Publish.)')) return;
      if (act === 'discard' && !confirm('Discard draft changes and go back to the published design?')) return;
      if (act === 'publish' && !confirm('Publish this design to your live portfolio?')) return;
      var url = { save: layout.dataset.draftUrl, preview: layout.dataset.draftUrl, publish: layout.dataset.publishUrl,
                  reset: layout.dataset.resetUrl, discard: layout.dataset.discardUrl }[act];
      var payload = (act === 'reset' || act === 'discard') ? {} : collect();
      var win = act === 'preview' ? window.open('', '_blank') : null;  // open synchronously (popup blockers)
      busy(btn, true);
      postJSON(url, payload).then(function (res) {
        if (!res.ok) { toast(res.error || 'Something went wrong', 'err'); if (win) win.close(); return; }
        savedSnapshot = JSON.stringify(res.design);
        if (act === 'reset' || act === 'discard') apply(res.design);
        else current = res.design;
        if (act === 'publish') { setState('Published', 'ok'); toast('Published! Your live portfolio is updated.'); }
        else if (res.dirty) setState('Draft saved, not published', 'dirty');
        else setState('Published', 'ok');
        if (act === 'save') toast('Draft saved');
        if (act === 'reset') toast('Defaults loaded into draft');
        if (act === 'discard') toast('Draft discarded');
        if (win) { win.opener = null; win.location = frame.src.split('#')[0]; }
      }).catch(function () { toast('Network error', 'err'); if (win) win.close(); })
        .finally(function () { busy(btn, false); });
    });
  });

  window.addEventListener('beforeunload', function (e) {
    if (JSON.stringify(collect()) !== savedSnapshot) { e.preventDefault(); e.returnValue = ''; }
  });

  syncOutputs();
  void defaults;
})();
