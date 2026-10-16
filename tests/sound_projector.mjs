import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { chromium } from 'playwright';
const require = createRequire(import.meta.url);
const base = process.env.GBO_BASE_URL || 'http://127.0.0.1:8080';
const browser = await chromium.launch({headless: true,
  ...(process.env.GBO_BROWSER_EXECUTABLE ? {executablePath: process.env.GBO_BROWSER_EXECUTABLE} : {})});
await mkdir('artifacts/ui', {recursive: true});

// A real 12-second PCM WAV exercises the browser media engine. It is intercepted
// only in this test and is never committed or offered as the owner's music.
const rate = 8000, frames = rate * 12;
const wav = Buffer.alloc(44 + frames * 2);
wav.write('RIFF'); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
wav.writeUInt32LE(rate, 24); wav.writeUInt32LE(rate * 2, 28);
wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34); wav.write('data', 36);
wav.writeUInt32LE(frames * 2, 40);
for (let i = 0; i < frames; i++) wav.writeInt16LE(Math.round(200 * Math.sin(i * 2 * Math.PI * 220 / rate)), 44 + 2 * i);
const catalogue = {artist: 'Test fixture', artist_url: '', tracks: [
  {title: 'Audio fixture A', url: '/static/audio/gbo-qa-a.wav'},
  {title: 'Audio fixture B', url: '/static/audio/gbo-qa-b.wav'},
]};

async function fixtures(context) {
  await context.route('**/*', async route => {
    const request = route.request();
    if (/\/static\/audio\/gbo-qa-[ab]\.wav$/.test(request.url())) {
      return route.fulfill({status: 200, contentType: 'audio/wav', body: wav});
    }
    if (!request.isNavigationRequest()) return route.continue();
    const response = await route.fetch();
    if (!response.headers()['content-type']?.includes('text/html')) return route.fulfill({response});
    const html = (await response.text()).replace(/(<script type="application\/json" id="gbo-soundtrack">)[\s\S]*?(<\/script>)/,
      (_, before, after) => before + JSON.stringify(catalogue) + after)
      .replace(/(data-sound-(?:play|next|track))\s+disabled\b/g, '$1')
      .replace(/(<select[^>]*data-sound-track[^>]*>)[\s\S]*?(<\/select>)/,
        (_, before, after) => before + '<option value="0">Audio fixture A</option><option value="1">Audio fixture B</option>' + after);
    return route.fulfill({response, body: html});
  });
}
async function noOverflow(page) {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  const bounds = await page.locator('.gbo-projector-panel').boundingBox();
  assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= (await page.viewportSize()).width + 1);
}

try {
  const context = await browser.newContext({reducedMotion: 'reduce'});
  const page = await context.newPage();
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await fixtures(context);
  // Deterministically emulate an autoplay-blocking browser while preserving real
  // audio decoding after the explicit Play action.
  await page.addInitScript(() => {
    const original = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
      if (this.tagName === 'AUDIO' && !window.__gboAudioAllowed) {
        return Promise.reject(new DOMException('Test autoplay policy', 'NotAllowedError'));
      }
      return original.call(this);
    };
  });
  await page.goto(base + '/login');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), true);
  assert.equal(await page.locator('main').evaluate(node => node.inert), true);
  const defaults = await page.evaluate(() => ({...GBOAudio.settings}));
  assert.equal(defaults.enabled, true); assert.equal(defaults.splashSound, true);
  assert.equal(defaults.volume, .12); assert.equal(defaults.splashVolume, .12);
  assert.equal(await page.locator('[data-gbo-film]').evaluate(n => n.volume), .12);
  assert.equal(await page.locator('[data-office-audio]').evaluate(n => n.paused), true);
  await page.getByRole('button', {name: 'Skip opening'}).click();
  assert.equal(await page.locator('main').evaluate(node => node.inert), false);
  assert.equal(await page.evaluate(() => sessionStorage.getItem('gbo.startup.seen')), '1');
  await page.waitForFunction(() => document.querySelector('[data-sound-indicator]').textContent === 'Tap to enable');
  await page.locator('[data-sound-projector] summary').click();
  await page.evaluate(() => { window.__gboAudioAllowed = true; });
  await page.getByRole('button', {name: 'Play', exact: true}).click();
  await page.waitForFunction(() => !document.querySelector('[data-office-audio]').paused);
  const audio = page.locator('[data-office-audio]');
  assert.equal(await audio.evaluate(n => n.volume), .12);
  assert.equal(await audio.evaluate(n => n.muted), false);
  assert.ok(await audio.evaluate(n => n.duration >= 11));
  await page.locator('[data-sound-volume]').fill('8');
  assert.equal(await audio.evaluate(n => n.volume), .08);
  await page.getByRole('button', {name: 'Mute', exact: true}).click();
  assert.equal(await audio.evaluate(n => n.muted), true);
  await page.getByRole('button', {name: 'Unmute', exact: true}).click();
  await page.getByRole('button', {name: 'Next', exact: true}).click();
  await page.waitForFunction(() => document.querySelector('[data-office-audio]').currentSrc.endsWith('gbo-qa-b.wav'));
  await page.waitForFunction(() => !document.querySelector('[data-office-audio]').paused);
  await page.evaluate(() => {
    const a = document.querySelector('[data-office-audio]'); a.currentTime = 4;
    a.dispatchEvent(new Event('timeupdate'));
  });
  // Film suspension does not overwrite the enabled preference.
  await page.evaluate(() => GBOAudio.film('test', true));
  assert.equal(await audio.evaluate(n => n.paused), true);
  assert.equal(await page.evaluate(() => GBOAudio.settings.enabled), true);
  await page.evaluate(() => GBOAudio.film('test', false));
  await page.waitForFunction(() => !document.querySelector('[data-office-audio]').paused);
  await page.getByRole('button', {name: 'Pause', exact: true}).click();
  assert.equal(await audio.evaluate(n => n.paused), true);
  await page.goto(base + '/ledgergut/');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), false);
  assert.equal(await page.evaluate(() => GBOAudio.settings.enabled), false);
  assert.equal(await audio.evaluate(n => n.paused), true);
  await page.locator('[data-sound-projector] summary').click();
  assert.equal(await page.locator('[data-sound-track]').inputValue(), '1');
  await page.evaluate(() => { window.__gboAudioAllowed = true; });
  await page.getByRole('button', {name: 'Play', exact: true}).click();
  await page.waitForFunction(() => document.querySelector('[data-office-audio]').currentTime >= 3.5);
  assert.equal(await audio.evaluate(n => n.volume), .08);
  // Avoid test tone playback while doing visual geometry checks.
  await page.getByRole('button', {name: 'Pause', exact: true}).click();
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({width, height: 900}); await noOverflow(page);
    await page.addScriptTag({path: require.resolve('axe-core/axe.min.js')});
    const violations = await page.evaluate(async () => (await axe.run({include: [['.gbo-projector']]}, {
      runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}
    })).violations.map(v => ({id: v.id, targets: v.nodes.map(n => n.target)})));
    assert.deepEqual(violations, []);
    assert.equal(await page.locator('.gbo-glyph').evaluate(n => getComputedStyle(n).animationName), 'none');
    if ([1440, 390].includes(width)) await page.screenshot({path: `artifacts/ui/audio-projector-${width}.png`});
  }
  await page.addStyleTag({content: 'html{font-size:200%!important}'}); await noOverflow(page);
  await page.emulateMedia({forcedColors: 'active'}); await noOverflow(page);
  await page.getByRole('button', {name: 'Close soundtrack controls'}).click();
  assert.equal(await page.locator('[data-sound-projector]').getAttribute('open'), null);
  assert.equal(await page.locator('[data-sound-projector] summary').evaluate(n => document.activeElement === n), true);
  const email = 'sound-qa-' + Date.now() + '@example.test';
  const password = 'sound-qa-only-password-123';
  const registered = await page.request.post(base + '/register', {form: {
    display_name: 'Sound QA', email, password, invite_code: 'qa-preview-only'
  }});
  assert.ok(registered.url().endsWith('/welcome'));
  await page.goto(base + '/welcome');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), false);
  assert.equal(await page.locator('[data-office-audio]').evaluate(n => n.paused), true);
  await page.request.post(base + '/welcome');
  await page.goto(base + '/onboarding');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), false);
  await page.request.post(base + '/onboarding', {form: {business_name: 'Sound QA Office', currency: 'CAD'}});
  await page.goto(base + '/');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), false);
  await page.request.post(base + '/logout');
  await page.request.post(base + '/login', {form: {email, password}});
  await page.goto(base + '/');
  assert.equal(await page.locator('[data-gbo-splash]').isVisible(), false);
  assert.deepEqual(errors, []);
  await context.close();

  // An empty catalogue has no broken audio URL and remains inspectable.
  const empty = await browser.newContext();
  const emptyPage = await empty.newPage();
  await emptyPage.addInitScript(() => sessionStorage.setItem('gbo.startup.seen', '1'));
  await emptyPage.goto(base + '/login');
  const available = await emptyPage.evaluate(() => JSON.parse(document.getElementById('gbo-soundtrack').textContent).tracks.length);
  if (!available) {
    assert.equal(await emptyPage.locator('[data-office-audio]').getAttribute('src'), null);
    await emptyPage.locator('[data-sound-projector] summary').click();
    assert.equal(await emptyPage.locator('[data-sound-play]').isDisabled(), true);
  } else {
    await emptyPage.locator('[data-sound-projector] summary').click();
    await emptyPage.waitForFunction(() => {
      const audio = document.querySelector('[data-office-audio]');
      return !audio.paused || document.querySelector('[data-sound-indicator]').textContent === 'Tap to enable';
    });
    if (await emptyPage.locator('[data-office-audio]').evaluate(n => n.paused)) {
      await emptyPage.getByRole('button', {name: 'Play', exact: true}).click();
    }
    for (let i = 0; i < available; i++) {
      await emptyPage.locator('[data-sound-track]').selectOption(String(i));
      await emptyPage.waitForFunction(() => {
        const audio = document.querySelector('[data-office-audio]');
        return (audio.readyState >= 2 && !audio.paused) || audio.error;
      });
      const track = await emptyPage.locator('[data-office-audio]').evaluate(n => ({
        error: n.error?.message || '', duration: n.duration, volume: n.volume, playing: !n.paused
      }));
      assert.equal(track.error, ''); assert.ok(track.duration > 0);
      assert.equal(track.volume, .12); assert.equal(track.playing, true);
    }
  }
  await empty.close();
  console.log('Sound projector: real audio decode/control, autoplay fallback, quiet defaults, pre-login splash, session/navigation restore, film priority, four widths, 200% text, scoped axe and display fallbacks passed.');
} finally { await browser.close(); }
