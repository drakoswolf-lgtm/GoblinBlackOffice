/* Runs in <head>: reserve the opening before the underlying login can appear. */
(() => {
  const key = 'gbo.audio.settings.v1';
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch (_) { /* private mode */ }
  const unit = value => typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : .12;
  const settings = {
    enabled: typeof stored.enabled === 'boolean' ? stored.enabled : true,
    muted: typeof stored.muted === 'boolean' ? stored.muted : false,
    volume: unit(stored.volume),
    splashSound: typeof stored.splashSound === 'boolean' ? stored.splashSound : true,
    splashVolume: unit(stored.splashVolume),
    motion: typeof stored.motion === 'boolean' ? stored.motion : true,
  };
  const films = new Set();
  window.GBOAudio = {
    settings,
    get filmActive() { return films.size > 0; },
    save(patch) {
      for (const name of ['enabled', 'muted', 'splashSound', 'motion']) {
        if (typeof patch[name] === 'boolean') settings[name] = patch[name];
      }
      for (const name of ['volume', 'splashVolume']) {
        if (typeof patch[name] === 'number') settings[name] = unit(patch[name]);
      }
      try { localStorage.setItem(key, JSON.stringify(settings)); } catch (_) { /* keep in memory */ }
      window.dispatchEvent(new Event('gbo:audio-settings'));
    },
    film(name, active) {
      if (active) films.add(name); else films.delete(name);
      window.dispatchEvent(new Event('gbo:film-state'));
    },
  };
  const params = new URLSearchParams(location.search);
  let seen = false;
  try { seen = sessionStorage.getItem('gbo.startup.seen') === '1'; } catch (_) { /* show entry */ }
  document.documentElement.dataset.gboLaunch = !seen || params.get('splash') === '1' || params.get('updating') === '1' ? 'pending' : 'complete';
})();
