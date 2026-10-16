/* Native audio, a CSS projector, and explicit media state. No third-party player. */
(() => {
  const root = document.querySelector('[data-sound-projector]');
  const bus = window.GBOAudio;
  if (!root || !bus) return;
  const find = name => root.querySelector('[data-' + name + ']');
  const audio = find('office-audio');
  const play = find('sound-play'), mute = find('sound-mute');
  const select = find('sound-track'), volume = find('sound-volume');
  const seek = find('sound-seek'), status = find('sound-status');
  const indicator = find('sound-indicator'), title = find('sound-title');
  const splashVolume = find('splash-volume'), splashSound = find('splash-sound');
  const motion = find('projector-motion');
  const catalogue = JSON.parse(document.getElementById('gbo-soundtrack').textContent);
  const tracks = catalogue.tracks || [];
  const cursorKey = 'gbo.audio.cursor.v1';
  let cursor = {};
  try { cursor = JSON.parse(sessionStorage.getItem(cursorKey) || '{}') || {}; } catch (_) { /* private mode */ }
  let index = Math.max(0, tracks.findIndex(track => track.url === cursor.url));
  let position = typeof cursor.position === 'number' && Number.isFinite(cursor.position) ? Math.max(0, cursor.position) : 0;
  let loaded = false, blocked = false, failed = false, pending = false;
  let lastSaved = 0, requestId = 0;
  const inIntro = document.body.classList.contains('gbo-intro-body');
  const clock = seconds => {
    const value = Math.max(0, Math.floor(Number.isFinite(seconds) ? seconds : 0));
    return Math.floor(value / 60) + ':' + String(value % 60).padStart(2, '0');
  };

  function saveCursor() {
    if (!tracks.length) return;
    const current = loaded && Number.isFinite(audio.currentTime) ? audio.currentTime : position;
    try { sessionStorage.setItem(cursorKey, JSON.stringify({ url: tracks[index].url, position: current })); } catch (_) { /* keep playing */ }
  }
  function suspended() { return bus.filmActive || inIntro || document.hidden; }
  function render() {
    const settings = bus.settings;
    volume.value = String(Math.round(settings.volume * 100));
    find('sound-volume-label').textContent = volume.value + '%';
    splashVolume.value = String(Math.round(settings.splashVolume * 100));
    find('splash-volume-label').textContent = splashVolume.value + '%';
    splashSound.checked = settings.splashSound; motion.checked = settings.motion;
    root.classList.toggle('motion-paused', !settings.motion || document.hidden);
    const playing = !audio.paused && !failed;
    root.classList.toggle('is-playing', playing);
    play.textContent = playing || (settings.enabled && suspended()) ? 'Pause' : 'Play';
    play.setAttribute('aria-pressed', String(settings.enabled && tracks.length > 0));
    mute.textContent = settings.muted ? 'Unmute' : 'Mute';
    mute.setAttribute('aria-pressed', String(settings.muted));
    title.textContent = tracks.length ? tracks[index].title : 'Office soundtrack';
    if (tracks.length) select.value = String(index);
    let message = !tracks.length ? 'Tracks will appear here when added.'
      : failed ? 'This track is unavailable. Choose another track or try Play.'
      : !settings.enabled ? 'Music paused'
      : suspended() ? 'Music held during films or while this tab is hidden'
      : blocked ? 'Tap Play to enable sound'
      : playing ? (settings.muted ? 'Playing · muted' : 'Playing · ' + Math.round(settings.volume * 100) + '%')
      : pending ? 'Loading soundtrack…' : 'Ready';
    if (status.textContent !== message) status.textContent = message;
    indicator.textContent = !tracks.length ? 'Awaiting tracks' : playing ? (settings.muted ? 'Muted' : 'Playing') : blocked ? 'Tap to enable' : 'Standby';
    const duration = audio.duration;
    const known = Number.isFinite(duration) && duration > 0;
    seek.disabled = !known;
    if (known && document.activeElement !== seek) seek.value = String(100 * audio.currentTime / duration);
    find('sound-time').textContent = clock(audio.currentTime) + ' / ' + clock(duration);
  }
  function load() {
    if (!tracks.length || loaded) return;
    loaded = true;
    audio.src = tracks[index].url;
    audio.load();
  }
  async function attempt() {
    if (!tracks.length || !bus.settings.enabled || suspended()) { audio.pause(); render(); return; }
    if (pending || (!audio.paused && !failed)) { render(); return; }
    const id = ++requestId;
    if (failed) { loaded = false; failed = false; }
    load();
    pending = true;
    render();
    try {
      await audio.play();
      if (id !== requestId) return;
      if (!bus.settings.enabled || suspended()) audio.pause();
      else blocked = false;
    } catch (error) {
      if (id !== requestId || error.name === 'AbortError') return;
      blocked = error.name === 'NotAllowedError';
      failed = !blocked;
    } finally {
      if (id === requestId) pending = false;
      render();
    }
  }
  function changeTrack(next) {
    if (!tracks.length) return;
    ++requestId; pending = false;
    audio.pause();
    index = (next + tracks.length) % tracks.length;
    position = 0; loaded = false; failed = false; blocked = false;
    saveCursor();
    if (bus.settings.enabled) attempt(); else render();
  }
  function apply() {
    audio.volume = bus.settings.volume;
    audio.muted = bus.settings.muted;
    if (!bus.settings.enabled || suspended()) { ++requestId; pending = false; audio.pause(); }
    else attempt();
    render();
  }

  play.addEventListener('click', () => {
    if (!audio.paused || (bus.settings.enabled && suspended())) bus.save({enabled: false});
    else { blocked = false; failed = false; bus.save({enabled: true}); }
  });
  mute.addEventListener('click', () => bus.save({muted: !bus.settings.muted}));
  volume.addEventListener('input', () => bus.save({volume: Number(volume.value) / 100}));
  splashVolume.addEventListener('input', () => bus.save({splashVolume: Number(splashVolume.value) / 100}));
  splashSound.addEventListener('change', () => bus.save({splashSound: splashSound.checked}));
  motion.addEventListener('change', () => bus.save({motion: motion.checked}));
  select.addEventListener('change', () => changeTrack(Number(select.value)));
  find('sound-next').addEventListener('click', () => changeTrack(index + 1));
  find('sound-close').addEventListener('click', () => { root.open = false; root.querySelector('summary').focus(); });
  root.addEventListener('keydown', event => { if (event.key === 'Escape') { root.open = false; root.querySelector('summary').focus(); } });
  seek.addEventListener('input', () => {
    if (Number.isFinite(audio.duration)) audio.currentTime = audio.duration * Number(seek.value) / 100;
    saveCursor(); render();
  });
  audio.addEventListener('loadedmetadata', () => {
    if (position > 0 && Number.isFinite(audio.duration)) audio.currentTime = Math.min(position, Math.max(0, audio.duration - .1));
    position = 0; render();
  });
  audio.addEventListener('timeupdate', () => {
    if (performance.now() - lastSaved > 3000) { saveCursor(); lastSaved = performance.now(); }
    render();
  });
  audio.addEventListener('ended', () => changeTrack(index + 1));
  audio.addEventListener('error', () => { failed = true; pending = false; render(); });
  for (const event of ['playing', 'pause', 'volumechange']) audio.addEventListener(event, render);
  window.addEventListener('gbo:audio-settings', apply);
  window.addEventListener('gbo:film-state', apply);
  document.addEventListener('visibilitychange', () => { saveCursor(); apply(); });
  window.addEventListener('pagehide', () => { saveCursor(); audio.pause(); });
  // A first real gesture can unlock a remembered enabled preference. It never
  // changes a user's paused/off setting or steals a form/button's interaction.
  function unlock(event) {
    if (!event.isTrusted || !blocked || !bus.settings.enabled || suspended() || root.contains(event.target)) return;
    attempt();
  }
  document.addEventListener('pointerdown', unlock, {passive: true});
  document.addEventListener('keydown', unlock);
  apply();
})();
