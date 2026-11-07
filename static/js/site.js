/* Public portfolio interactions. Vanilla JS, no dependencies.
   Every effect checks `motionOK()` so reduced-motion preferences and the
   admin "disable animations" switch are always respected. */
(function () {
  'use strict';
  var root = document.documentElement;
  var body = document.body;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  function motionOK() { return !root.classList.contains('reduce-motion') && !body.classList.contains('no-motion'); }

  /* ---------- Loader ---------- */
  // The script is deferred, so the DOM is ready here. Show the loader briefly
  // (or wait for web fonts, whichever is first) but never block on slow assets.
  var loaded = false;
  function revealPage() { if (!loaded) { loaded = true; body.classList.add('is-loaded'); } }
  if ($('.loader') && motionOK()) {
    setTimeout(revealPage, 1100);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { setTimeout(revealPage, 350); });
  } else revealPage();

  /* ---------- Theme toggle (visitor preference only) ---------- */
  var themeBtn = $('[data-theme-toggle]');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = root.dataset.theme === 'light' ? 'dark' : 'light';
      root.dataset.theme = next;
      store.set('pf-theme', next);
    });
  }
  if (root.dataset.themeMode === 'system' && !store.get('pf-theme')) {
    matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
      root.dataset.theme = e.matches ? 'light' : 'dark';
    });
  }

  /* ---------- Motion toggle ---------- */
  var motionBtn = $('[data-motion-toggle]');
  function syncMotionBtn() {
    if (!motionBtn) return;
    var off = root.classList.contains('reduce-motion');
    motionBtn.setAttribute('aria-pressed', String(off));
    motionBtn.setAttribute('aria-label', off ? 'Resume animations' : 'Pause animations');
    motionBtn.title = motionBtn.getAttribute('aria-label');
  }
  if (motionBtn) {
    syncMotionBtn();
    motionBtn.addEventListener('click', function () {
      var off = !root.classList.contains('reduce-motion');
      root.classList.toggle('reduce-motion', off);
      store.set('pf-motion', off ? 'off' : 'on');
      syncMotionBtn();
      if (off) $$('[data-reveal]').forEach(function (el) { el.classList.add('is-visible'); });
    });
  }

  /* ---------- Header: scrolled state, hide on scroll down ---------- */
  var header = $('[data-header]');
  var lastY = window.scrollY, ticking = false;
  function onScroll() {
    var y = window.scrollY;
    if (header) {
      header.classList.toggle('is-scrolled', y > 24);
      var menuOpen = $('#nav-links.is-open');
      header.classList.toggle('is-hidden', !menuOpen && y > 400 && y > lastY + 4);
      if (y < lastY - 4) header.classList.remove('is-hidden');
    }
    lastY = y;
    updateTimeline();
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });

  /* ---------- Mobile menu ---------- */
  var burger = $('[data-menu-toggle]'), links = $('#nav-links');
  function setMenu(open) {
    if (!burger || !links) return;
    links.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }
  if (burger) {
    burger.addEventListener('click', function () { setMenu(!links.classList.contains('is-open')); });
    links.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
    document.addEventListener('click', function (e) {
      if (links.classList.contains('is-open') && !e.target.closest('.nav')) setMenu(false);
    });
  }

  /* ---------- Active section in nav ---------- */
  var navMap = {};
  $$('[data-nav]').forEach(function (a) { navMap[a.dataset.nav] = a; });
  if ('IntersectionObserver' in window && Object.keys(navMap).length) {
    var secObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        Object.keys(navMap).forEach(function (k) { navMap[k].classList.toggle('is-active', k === en.target.id); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    $$('section[id]').forEach(function (s) { secObs.observe(s); });
  }

  /* ---------- Scroll reveal ---------- */
  var revealEls = $$('[data-reveal]');
  if (!('IntersectionObserver' in window) || body.classList.contains('reveal-none')) {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var rObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-visible'); rObs.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { rObs.observe(el); });
  }

  /* ---------- Hero: timecode + rotating titles ---------- */
  var tc = $('[data-timecode]');
  if (tc) {
    var t0 = Date.now();
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    setInterval(function () {
      var ms = Date.now() - t0, s = Math.floor(ms / 1000);
      tc.textContent = pad(Math.floor(s / 3600)) + ':' + pad(Math.floor(s / 60) % 60) + ':' + pad(s % 60) + ':' + pad(Math.floor((ms % 1000) / 40));
    }, motionOK() ? 40 : 1000);
  }

  var rot = $('[data-rotator]');
  if (rot) {
    var items = [];
    try { items = JSON.parse(rot.dataset.items || '[]'); } catch (e) {}
    if (items.length > 1) {
      var idx = 0, ch = items[0].length, deleting = false;
      var tick = function () {
        if (!motionOK()) {
          idx = (idx + 1) % items.length; rot.textContent = items[idx];
          return setTimeout(tick, 3000);
        }
        var word = items[idx];
        if (!deleting) {
          ch++; rot.textContent = word.slice(0, ch);
          if (ch >= word.length) { deleting = true; return setTimeout(tick, 2200); }
          return setTimeout(tick, 55);
        }
        ch--; rot.textContent = word.slice(0, ch);
        if (ch <= 0) { deleting = false; idx = (idx + 1) % items.length; return setTimeout(tick, 320); }
        setTimeout(tick, 28);
      };
      setTimeout(function () { deleting = true; tick(); }, 2600);
    }
  }

  /* ---------- Pointer effects: glow, spotlight, tilt, magnetic, parallax, bot ---------- */
  var glow = $('.cursor-glow');
  var visual = $('[data-parallax]');
  var pupils = $$('.bot .pupil');
  var mouse = { x: innerWidth / 2, y: innerHeight / 2 }, glowPos = { x: mouse.x, y: mouse.y }, glowRunning = false;

  function glowLoop() {
    glowPos.x += (mouse.x - glowPos.x) * 0.12;
    glowPos.y += (mouse.y - glowPos.y) * 0.12;
    glow.style.transform = 'translate3d(' + glowPos.x + 'px,' + glowPos.y + 'px,0)';
    if (Math.abs(mouse.x - glowPos.x) + Math.abs(mouse.y - glowPos.y) > 0.5) requestAnimationFrame(glowLoop);
    else glowRunning = false;
  }

  if (finePointer) {
    document.addEventListener('pointermove', function (e) {
      mouse.x = e.clientX; mouse.y = e.clientY;
      if (!motionOK()) return;
      if (glow && !body.classList.contains('no-cursor-fx')) {
        body.classList.add('has-cursor');
        if (!glowRunning) { glowRunning = true; requestAnimationFrame(glowLoop); }
      }
      if (visual) {
        var r = visual.getBoundingClientRect();
        if (r.bottom > 0) {
          visual.style.setProperty('--px', ((e.clientX / innerWidth) - 0.5) * -14 + 'px');
          visual.style.setProperty('--py', ((e.clientY / innerHeight) - 0.5) * -14 + 'px');
        }
      }
      pupils.forEach(function (p) {
        var b = p.ownerSVGElement.getBoundingClientRect();
        var cx = b.left + b.width / 2, cy = b.top + b.height / 2;
        var a = Math.atan2(e.clientY - cy, e.clientX - cx);
        p.style.transform = 'translate(' + Math.cos(a) * 4 + 'px,' + Math.sin(a) * 4 + 'px)';
      });
    }, { passive: true });
    document.addEventListener('pointerleave', function () { body.classList.remove('has-cursor'); });

    $$('[data-spotlight]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        el.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });

    $$('[data-tilt]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        if (!motionOK()) return;
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
        el.style.setProperty('--ry', (x * 10) + 'deg');
        el.style.setProperty('--rx', (y * -10) + 'deg');
      });
      el.addEventListener('pointerleave', function () { el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg'); });
    });

    $$('[data-magnetic]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        if (!motionOK()) return;
        var r = el.getBoundingClientRect();
        el.style.setProperty('--bx', ((e.clientX - r.left - r.width / 2) * 0.18) + 'px');
        el.style.setProperty('--by', ((e.clientY - r.top - r.height / 2) * 0.25) + 'px');
      });
      el.addEventListener('pointerleave', function () { el.style.setProperty('--bx', '0px'); el.style.setProperty('--by', '0px'); });
    });
  }

  /* ---------- Journey timeline: progress + filter ---------- */
  var timeline = $('[data-timeline]');
  function updateTimeline() {
    if (!timeline) return;
    var r = timeline.getBoundingClientRect();
    var p = (innerHeight * 0.6 - r.top) / r.height;
    timeline.style.setProperty('--progress', Math.max(0, Math.min(1, p)).toFixed(3));
  }
  updateTimeline();

  function bindFilter(selector, attr, items, match) {
    var chips = $$(selector);
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        var val = chip.getAttribute(attr);
        chips.forEach(function (c) { var on = c === chip; c.classList.toggle('is-active', on); c.setAttribute('aria-pressed', String(on)); });
        var n = 0;
        items().forEach(function (el) {
          var show = val === 'all' || match(el, val);
          el.classList.toggle('is-hidden', !show);
          el.classList.toggle('is-filtered', !show);
          if (show) {
            el.classList.add('is-visible');
            el.classList.remove('is-entering'); void el.offsetWidth;
            if (motionOK()) { el.style.setProperty('--n', n++); el.classList.add('is-entering'); }
          }
        });
        updateTimeline();
      });
    });
  }
  bindFilter('[data-filter]', 'data-filter', function () { return $$('.tl-item'); },
    function (el, v) { return el.dataset.kind === v; });
  bindFilter('[data-skill-filter]', 'data-skill-filter', function () { return $$('.skill-card'); },
    function (el, v) { return el.dataset.category === v; });
  bindFilter('[data-cert-filter]', 'data-cert-filter', function () { return $$('.cert-card'); },
    function (el, v) { return el.dataset.kind === v; });
  bindFilter('[data-project-filter]', 'data-project-filter', function () { return $$('[data-project-grid] .project-card'); },
    function (el, v) { return (el.dataset.tech || '').split('|').indexOf(v) !== -1; });

  // Touch: tap a skill card to reveal its details
  $$('.skill-card').forEach(function (card) {
    card.addEventListener('click', function () { card.classList.toggle('is-open'); });
  });

  /* ---------- GitHub fragment (lazy) ---------- */
  var gh = $('[data-github-src]');
  if (gh) {
    var loadGh = function () {
      fetch(gh.dataset.githubSrc, { headers: { 'Accept': 'text/html' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (html) { gh.innerHTML = html; gh.removeAttribute('aria-busy'); countUp(gh); })
        .catch(function () { gh.innerHTML = '<div class="gh-empty card"><p>GitHub activity could not be loaded right now.</p></div>'; gh.removeAttribute('aria-busy'); });
    };
    if ('IntersectionObserver' in window) {
      var ghObs = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { ghObs.disconnect(); loadGh(); } }, { rootMargin: '400px' });
      ghObs.observe(gh);
    } else loadGh();
  }
  function countUp(scope) {
    $$('[data-count]', scope).forEach(function (el) {
      var end = parseInt(el.dataset.count, 10) || 0;
      if (!motionOK() || end < 2) { el.textContent = end; return; }
      var t0 = performance.now(), dur = 1200;
      (function step(t) {
        var k = Math.min(1, (t - t0) / dur);
        el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
        if (k < 1) requestAnimationFrame(step);
      })(t0);
    });
  }

  /* ---------- Contact form ---------- */
  var form = $('[data-contact-form]');
  if (form) {
    var status = $('[data-form-status]', form), btn = $('[data-submit]', form);
    var setErr = function (name, msg) {
      var p = $('[data-error-for="' + name + '"]', form);
      if (p) { p.textContent = msg || ''; p.parentNode.classList.toggle('has-error', !!msg); }
    };
    var validate = function () {
      var ok = true, f = form.elements;
      var checks = {
        name: f.name.value.trim().length >= 2 ? '' : 'Please enter your name.',
        email: /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(f.email.value.trim()) ? '' : 'Please enter a valid email address.',
        message: f.message.value.trim().length >= 10 ? '' : 'Message should be at least 10 characters.'
      };
      Object.keys(checks).forEach(function (k) { setErr(k, checks[k]); if (checks[k]) ok = false; });
      setErr('subject', '');
      return ok;
    };
    $$('input, textarea', form).forEach(function (el) {
      el.addEventListener('blur', function () { if (form.dataset.touched) validate(); });
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      form.dataset.touched = '1';
      status.textContent = ''; status.className = 'form-status';
      if (!validate()) { var bad = $('.has-error input, .has-error textarea', form); if (bad) bad.focus(); return; }
      btn.disabled = true; btn.classList.add('is-loading'); $('.btn-label', btn).textContent = 'Sending...';
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
        .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'Unexpected response.' }; }); })
        .then(function (data) {
          if (data.ok) {
            form.reset(); delete form.dataset.touched;
            status.textContent = data.message; status.classList.add('is-success');
            var bot = $('[data-bot]'); if (bot) { bot.classList.add('is-happy'); setTimeout(function () { bot.classList.remove('is-happy'); }, 4000); }
          } else {
            if (data.fields) Object.keys(data.fields).forEach(function (k) { setErr(k, data.fields[k]); });
            status.textContent = data.error || 'Something went wrong. Please try again.'; status.classList.add('is-error');
          }
        })
        .catch(function () { status.textContent = 'Network error. Please check your connection and try again.'; status.classList.add('is-error'); })
        .finally(function () { btn.disabled = false; btn.classList.remove('is-loading'); $('.btn-label', btn).textContent = $('.btn-label', btn).dataset.label || 'Send message'; });
    });
  }

  /* ---------- Copy email ---------- */
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var done = function () { var l = b.getAttribute('aria-label'); b.setAttribute('aria-label', 'Copied!'); b.classList.add('is-copied'); setTimeout(function () { b.setAttribute('aria-label', l); b.classList.remove('is-copied'); }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.copy).then(done, function () {});
    });
  });

  /* ---------- Lightbox ---------- */
  var dlg = $('[data-lightbox-dialog]');
  if (dlg && dlg.showModal) {
    var shots = $$('[data-lightbox]'), cur = 0, img = $('[data-lb-img]', dlg), cap = $('[data-lb-cap]', dlg);
    var show = function (i) { cur = (i + shots.length) % shots.length; img.src = shots[cur].dataset.lightbox; img.alt = shots[cur].dataset.caption || ''; cap.textContent = shots[cur].dataset.caption || ''; };
    shots.forEach(function (s, i) { s.addEventListener('click', function () { show(i); dlg.showModal(); }); });
    $('[data-lb-close]', dlg).addEventListener('click', function () { dlg.close(); });
    $('[data-lb-prev]', dlg).addEventListener('click', function () { show(cur - 1); });
    $('[data-lb-next]', dlg).addEventListener('click', function () { show(cur + 1); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) { if (e.key === 'ArrowLeft') show(cur - 1); if (e.key === 'ArrowRight') show(cur + 1); });
    if (shots.length < 2) { $('[data-lb-prev]', dlg).hidden = true; $('[data-lb-next]', dlg).hidden = true; }
  }

  /* ---------- Page transitions for internal navigation ---------- */
  if (!body.classList.contains('transition-none')) {
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href]');
      if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 || a.target || a.hasAttribute('download')) return;
      var url = new URL(a.href, location.href);
      if (url.origin !== location.origin || (url.pathname === location.pathname && url.hash) || url.pathname.indexOf('/static/') === 0 || url.pathname === '/resume') return;
      if (!motionOK()) return;
      e.preventDefault();
      body.classList.add('is-leaving');
      setTimeout(function () { location.href = url.href; }, 230);
    });
    window.addEventListener('pageshow', function () { body.classList.remove('is-leaving'); });
  }

  /* ---------- Live design preview (admin Design Center iframe) ---------- */
  if (root.dataset.preview === 'true' && window.parent !== window) {
    window.addEventListener('message', function (e) {
      if (e.origin !== location.origin || e.source !== window.parent || !e.data || e.data.type !== 'pf-design') return;
      var d = e.data;
      var styleEl = $('#design-vars'); if (styleEl && typeof d.css === 'string') styleEl.textContent = d.css;
      if (d.fontUrl) { var fl = $('#design-fonts'); if (!fl) { fl = document.createElement('link'); fl.rel = 'stylesheet'; fl.id = 'design-fonts'; document.head.appendChild(fl); } if (fl.href !== d.fontUrl) fl.href = d.fontUrl; }
      if (typeof d.classes === 'string') {
        body.className.split(/\s+/).forEach(function (c) { if (/^(skin-|card-|nav-|avatar-|reveal-|transition-|no-motion|no-bg-fx|no-cursor-fx)/.test(c)) body.classList.remove(c); });
        d.classes.split(/\s+/).forEach(function (c) { if (c) body.classList.add(c); });
        $$('[data-reveal]').forEach(function (el) { el.classList.add('is-visible'); });
      }
      if (d.mode) { root.dataset.themeMode = d.mode; root.dataset.theme = d.mode === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : d.mode; }
      if (Array.isArray(d.sections)) {
        var main = $('#main'), ch = 0;
        d.sections.forEach(function (s) {
          var slot = $('[data-section-key="' + s.key + '"]');
          if (!slot) return;
          main.appendChild(slot);
          slot.hidden = !s.enabled;
          var t = $('[data-section-title]', slot); if (t) t.textContent = s.title;
          var st = $('[data-section-subtitle]', slot); if (st) { st.textContent = s.subtitle; st.hidden = !s.subtitle; }
          var c = $('.eyebrow .ch', slot); if (c && s.enabled) c.textContent = 'CH ' + (ch < 10 ? '0' : '') + ch;
          if (s.enabled) ch++;
          var li = $('[data-nav-key="' + s.key + '"]'); if (li) { li.hidden = !s.enabled; li.parentNode.appendChild(li); }
        });
      }
    });
    window.parent.postMessage({ type: 'pf-preview-ready' }, location.origin);
  }
})();
