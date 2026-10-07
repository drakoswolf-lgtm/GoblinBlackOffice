(() => {
  const advice = document.querySelector('[data-aeterna-advice]');
  const toggle = document.querySelector('[data-aeterna-toggle]');
  if (advice && toggle) {
    toggle.addEventListener('click', () => {
      const expanded = advice.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
  }

  const splash = document.querySelector('[data-gbo-splash]');
  if (!splash) return;

  const ring = splash.querySelector('[data-progress-ring]');
  const value = splash.querySelector('[data-progress-value]');
  const mode = splash.querySelector('[data-progress-mode]');
  const joke = splash.querySelector('[data-sticky-joke]');
  const linesNode = document.getElementById('gbo-sticky-lines');
  const lines = linesNode ? JSON.parse(linesNode.textContent || '[]') : [];
  const params = new URLSearchParams(window.location.search);
  const updating = params.get('updating') === '1';
  const forceSplash = params.get('splash') === '1' || updating;
  const sessionKey = 'gbo.startup.seen';
  let seenThisSession = false;

  try {
    seenThisSession = window.sessionStorage.getItem(sessionKey) === '1';
  } catch (_) {
    seenThisSession = false;
  }

  if (seenThisSession && !forceSplash) {
    splash.hidden = true;
    splash.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('splash-active');
    document.body.classList.add('gbo-entered');
    return;
  }

  const minMs = 5000;
  const start = performance.now();
  let progress = 0;
  let lastBand = -1;

  mode.textContent = updating ? 'UPDATING' : 'LOADING';
  splash.hidden = false;
  splash.setAttribute('aria-hidden', 'false');
  document.body.classList.add('splash-active');

  function weightedChoice(candidates) {
    if (!candidates.length) return null;
    const total = candidates.reduce((sum, item) => sum + Number(item.weight || 1), 0);
    let n = Math.random() * total;
    for (const item of candidates) {
      n -= Number(item.weight || 1);
      if (n <= 0) return item;
    }
    return candidates[candidates.length - 1];
  }

  function setJoke(p) {
    const band = p < 25 ? 0 : p < 50 ? 1 : p < 80 ? 2 : 3;
    if (band === lastBand) return;
    lastBand = band;
    const eligible = lines.filter(item => p >= item.min && p <= item.max);
    const picked = weightedChoice(eligible);
    if (picked) joke.textContent = picked.text;
  }

  function draw(p) {
    progress = Math.max(0, Math.min(100, p));
    value.textContent = Math.floor(progress) + '%';
    ring.style.setProperty('--progress', String(progress));
    splash.style.setProperty('--load', String(progress / 100));
    setJoke(progress);
  }

  function finish() {
    draw(100);
    try {
      window.sessionStorage.setItem(sessionKey, '1');
    } catch (_) {
      // Storage can be unavailable in hardened/private browser contexts.
    }
    splash.classList.add('is-breaching');
    window.setTimeout(() => splash.classList.add('is-door'), 450);
    window.setTimeout(() => splash.classList.add('is-opening'), 1050);
    window.setTimeout(() => splash.classList.add('is-whiteout'), 1850);
    window.setTimeout(() => {
      splash.hidden = true;
      splash.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('splash-active');
      document.body.classList.add('gbo-entered');
    }, 2350);
  }

  function tick(now) {
    const elapsed = now - start;
    const floorProgress = Math.min(96, (elapsed / minMs) * 96);
    draw(floorProgress);
    if (elapsed >= minMs) {
      finish();
      return;
    }
    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
})();
