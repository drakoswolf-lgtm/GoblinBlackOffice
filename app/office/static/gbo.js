(() => {
  // Passive command portrait. No speech, animation triggers or business commands
  // are inferred from this footage. The approved static portrait always remains.
  const portraits = document.querySelectorAll('[data-aeterna-ambient]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const dataSaver = navigator.connection && navigator.connection.saveData;
  if (!reducedMotion && !dataSaver) {
    for (const portrait of portraits) {
      let failed = false;
      let requested = false;
      const frame = portrait.parentElement;
      portrait.addEventListener('loadeddata', () => {
        portrait.classList.add('is-ready');
        frame.classList.add('has-ambient-video');
      });
      portrait.addEventListener('error', () => {
        failed = true;
        portrait.classList.remove('is-ready');
        frame.classList.remove('has-ambient-video');
      });
      const activate = () => {
        if (failed || document.hidden) return;
        if (!requested) {
          requested = true;
          portrait.load();
        }
        portrait.play().catch(() => {
          // Static canon portrait remains visible if autoplay is disallowed.
        });
      };
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) activate();
            else portrait.pause();
          }
        }, { threshold: 0.08 });
        observer.observe(portrait);
      } else {
        activate();
      }
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) portrait.pause();
        else if (portrait.getBoundingClientRect().height > 0) activate();
      });
    }
  }

  const advice = document.querySelector('[data-aeterna-advice]');
  const toggle = document.querySelector('[data-aeterna-toggle]');
  if (advice && toggle) {
    toggle.addEventListener('click', () => {
      const expanded = advice.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
  }

  const splash = document.querySelector('[data-gbo-splash]');
  const bus = window.GBOAudio;
  if (!splash) { document.documentElement.dataset.gboLaunch = 'complete'; return; }
  const film = splash.querySelector('[data-gbo-film]');
  const filmAudio = splash.querySelector('[data-gbo-film-audio]');
  const skip = splash.querySelector('[data-gbo-skip]');
  const ring = splash.querySelector('[data-progress-ring]');
  const value = splash.querySelector('[data-progress-value]');
  const mode = splash.querySelector('[data-progress-mode]');
  const joke = splash.querySelector('[data-sticky-joke]');
  const linesNode = document.getElementById('gbo-sticky-lines');
  let lines = [];
  try { lines = linesNode ? JSON.parse(linesNode.textContent || '[]') : []; } catch (_) { /* default note */ }
  const params = new URLSearchParams(window.location.search);
  const updating = params.get('updating') === '1';
  const forceSplash = params.get('splash') === '1' || params.get('updating') === '1';
  const sessionKey = 'gbo.startup.seen';
  let seenThisSession = false;
  try { seenThisSession = window.sessionStorage.getItem(sessionKey) === '1'; } catch (_) { /* private mode */ }
  if (seenThisSession && !forceSplash) {
    splash.hidden = true;
    document.documentElement.dataset.gboLaunch = 'complete';
    document.body.classList.add('gbo-entered');
    return;
  }

  const minMs = 5000;
  let start = performance.now(), lastBand = -1;
  let complete = false, legacyStarted = false, audioBlocked = false, filmGuard = null;
  const inertNodes = [];
  for (const child of document.body.children) {
    if (child.hasAttribute('data-gbo-launch-root') || ['SCRIPT', 'STYLE', 'LINK'].includes(child.tagName)) continue;
    inertNodes.push([child, child.inert]); child.inert = true;
  }
  mode.textContent = updating ? 'UPDATING' : 'LOADING';
  splash.hidden = false;
  splash.setAttribute('aria-hidden', 'false');
  document.body.classList.add('splash-active');
  bus?.film('splash', true);
  splash.focus({preventScroll: true});

  function leave() {
    if (complete) return;
    complete = true;
    clearTimeout(filmGuard);
    film?.pause();
    try { window.sessionStorage.setItem(sessionKey, '1'); } catch (_) { /* entry stays skippable */ }
    splash.hidden = true;
    splash.setAttribute('aria-hidden', 'true');
    document.documentElement.dataset.gboLaunch = 'complete';
    document.body.classList.remove('splash-active');
    document.body.classList.add('gbo-entered');
    for (const [node, wasInert] of inertNodes) node.inert = wasInert;
    bus?.film('splash', false);
    const first = document.querySelector('main input:not([type="hidden"]):not([disabled]), main a, main button');
    if (document.activeElement === splash || splash.contains(document.activeElement)) first?.focus({preventScroll: true});
    window.dispatchEvent(new Event('gbo:splash-complete'));
  }
  skip?.addEventListener('click', leave);
  splash.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); leave(); }
    if (event.key !== 'Tab') return;
    const buttons = [...splash.querySelectorAll('button')].filter(node => !node.hidden && !node.disabled);
    if (!buttons.length) return;
    if (event.shiftKey && (document.activeElement === buttons[0] || document.activeElement === splash)) {
      event.preventDefault(); buttons.at(-1).focus();
    } else if (!event.shiftKey && (document.activeElement === buttons.at(-1) || document.activeElement === splash)) {
      event.preventDefault(); buttons[0].focus();
    }
  });
  function draw(progress) {
    const p = Math.max(0, Math.min(100, progress));
    value.textContent = Math.floor(p) + '%'; ring.style.setProperty('--progress', String(p));
    splash.style.setProperty('--load', String(p / 100));
    const band = p < 25 ? 0 : p < 50 ? 1 : p < 80 ? 2 : 3;
    if (band === lastBand) return;
    lastBand = band;
    const eligible = lines.filter(item => p >= item.min && p <= item.max);
    let n = Math.random() * eligible.reduce((sum, item) => sum + Number(item.weight || 1), 0);
    for (const item of eligible) { n -= Number(item.weight || 1); if (n <= 0) { joke.textContent = item.text; break; } }
  }
  function tick(now) {
    if (complete) return;
    const elapsed = now - start;
    draw(Math.min(96, elapsed / minMs * 96));
    if (elapsed < minMs) { requestAnimationFrame(tick); return; }
    draw(100); splash.classList.add('is-breaching');
    setTimeout(() => splash.classList.add('is-door'), 450);
    setTimeout(() => splash.classList.add('is-opening'), 1050);
    setTimeout(() => splash.classList.add('is-whiteout'), 1850);
    setTimeout(leave, 2350);
  }
  function fallbackToLegacy() {
    if (legacyStarted || complete) return;
    legacyStarted = true; clearTimeout(filmGuard); film?.pause();
    splash.classList.remove('is-film');
    if (filmAudio) filmAudio.hidden = true;
    start = performance.now(); requestAnimationFrame(tick);
  }
  function soundState() {
    if (!film || !filmAudio) return;
    film.volume = bus?.settings.splashVolume ?? .12;
    film.muted = !(bus?.settings.splashSound ?? true) || audioBlocked;
    filmAudio.textContent = film.muted ? 'ENABLE SOUND' : 'MUTE SOUND';
    filmAudio.setAttribute('aria-pressed', String(!film.muted));
  }
  if (!film) { fallbackToLegacy(); return; }
  window.addEventListener('gbo:audio-settings', soundState);
  filmAudio.hidden = false;
  filmAudio.addEventListener('click', async () => {
    const enable = film.muted;
    audioBlocked = false;
    bus?.save({splashSound: enable});
    soundState();
    try { if (film.paused) await film.play(); } catch (error) {
      if (error.name === 'NotAllowedError') { audioBlocked = true; soundState(); }
      else fallbackToLegacy();
    }
  });
  film.addEventListener('ended', () => {
    if (legacyStarted || complete) return;
    splash.classList.add('is-film-ending'); setTimeout(leave, 220);
  }, {once: true});
  film.addEventListener('error', fallbackToLegacy, {once: true});
  splash.classList.add('is-film');
  soundState();
  // Try the owner's quiet sound-on preference. Blocked sound falls back to a
  // silent film and an honest sound button, without delaying the login screen.
  film.play().catch(async error => {
    if (complete || legacyStarted) return;
    if (error.name !== 'NotAllowedError') { fallbackToLegacy(); return; }
    audioBlocked = true; soundState();
    try { await film.play(); } catch (_) { fallbackToLegacy(); }
  });
  filmGuard = setTimeout(() => { if (!complete && !legacyStarted && film.paused) fallbackToLegacy(); }, 8000);
  window.addEventListener('pagehide', () => film.pause());
})();
