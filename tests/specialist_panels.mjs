import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);

const base = process.env.GBO_BASE_URL || 'http://127.0.0.1:8080';
const browser = await chromium.launch({ headless: true,
  ...(process.env.GBO_BROWSER_EXECUTABLE ? { executablePath: process.env.GBO_BROWSER_EXECUTABLE } : {}) });
const expected = ['ledgergut', 'signor', 'squarmish', 'packrat', 'patch', 'grimsnatch'];
await mkdir('artifacts/ui', { recursive: true });

// Validate mounted links, full artwork, content bounds and accessible descriptions.
async function checkPanels(page, { artwork = true } = {}) {
  const panels = page.locator('.specialist-glass-card');
  assert.equal(await panels.count(), 6);
  const result = await panels.evaluateAll(async (nodes, expected) => {
    const failures = [];
    for (const [i, node] of nodes.entries()) {
      const image = node.querySelector('.specialist-pane-art');
      image.loading = 'eager';
      try { await image.decode(); } catch (_) { /* checked below when required */ }
      const card = node.getBoundingClientRect();
      const copy = node.querySelector('.command-channel-copy, .office-scope-content');
      const rect = copy.getBoundingClientRect();
      const style = getComputedStyle(copy);
      const artStyle = getComputedStyle(image);
      if (node.dataset.specialist !== expected[i]) failures.push('Identity order');
      if (!image.src.endsWith('/' + expected[i] + '.png')) failures.push('Wrong art ' + expected[i]);
      if (artStyle.objectFit !== 'contain') failures.push('Artwork can crop or stretch');
      if (rect.left < card.left || rect.right > card.right + 1 || rect.top < card.top || rect.bottom > card.bottom + 1) failures.push('Content clipped ' + expected[i]);
      if (card.width < 44 || card.height < 44) failures.push('Touch target too small');
      if (card.right > innerWidth + 1) failures.push('Card exceeds viewport');
      if (style.marginLeft !== '0px') failures.push('Art displaces information');
      if (style.textAlign !== 'left') failures.push('Panel information is not left aligned');
      if (Number(style.zIndex) <= Number(getComputedStyle(node.querySelector('.specialist-glass-layer')).zIndex)) failures.push('Copy below art');
      for (const attr of ['aria-labelledby', 'aria-describedby']) {
        for (const id of node.getAttribute(attr).split(' ')) {
          if (!document.getElementById(id)?.textContent.trim()) failures.push('Missing accessible text ' + id);
        }
      }
      if (image.alt !== '' || image.parentElement.getAttribute('aria-hidden') !== 'true') failures.push('Decorative image exposed');
      if (node.querySelector('video,audio,button') || node.getAnimations().length) failures.push('Unexpected media or nested control');
      const href = node.getAttribute('href');
      if (href.startsWith('#') && !document.getElementById(href.slice(1))) failures.push('Dead project anchor');
    }
    return { failures, dimensions: nodes.map(n => { const i=n.querySelector('img'); return [i.naturalWidth,i.naturalHeight]; }) };
  }, expected);
  assert.deepEqual(result.failures, []);
  if (artwork) for (const dim of result.dimensions) assert.deepEqual(dim, [1536, 877]);
  for (let i = 0; i < 6; i++) {
    await panels.nth(i).focus();
    assert.equal(await panels.nth(i).evaluate(n => document.activeElement === n), true);
    assert.ok(await panels.nth(i).evaluate(n => parseFloat(getComputedStyle(n).outlineWidth) >= 2));
  }
}

try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(() => sessionStorage.setItem('gbo.startup.seen', '1'));
  // Create a real disposable project through the same endpoint as the UI.
  await page.goto(base + '/records');
  const clientName = 'Pane QA ' + Date.now();
  assert.ok((await page.request.post(base + '/records', { form: { kind: 'client', name: clientName } })).ok());
  await page.reload();
  const clientId = await page.locator('#project-client option').filter({ hasText: clientName }).getAttribute('value');
  const projectName = clientName + ' project';
  assert.ok((await page.request.post(base + '/records', { form: { kind: 'project', client_id: clientId, name: projectName } })).ok());
  await page.reload();
  const projectPath = await page.locator('.office-project-row').filter({ hasText: projectName }).getAttribute('href');

  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    for (const [name, path] of [['desk', '/'], ['project', projectPath]]) {
      assert.ok((await page.goto(base + path)).ok());
      await checkPanels(page);
      if (name === 'project' && [1440, 390].includes(width)) {
        await page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
        const audit = await page.evaluate(async () => axe.run({ include: [['.specialist-projection']] }, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } }));
        assert.deepEqual(audit.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), []);
      }
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), width + ' ' + name + ' overflow');
      if ([1440, 390].includes(width)) {
        await page.locator('.specialist-projection').screenshot({ path: `artifacts/ui/panes-${name}-${width}.png` });
      }
    }
  }
  // Large text must grow the cards, not crop the label or overlap the next row.
  await page.addStyleTag({ content: 'html { font-size:200% !important }' });
  await checkPanels(page);
  await page.locator('.specialist-projection').screenshot({ path: 'artifacts/ui/panes-large-text.png' });
  await page.reload();

  // Artwork is optional and has no say in business-content geometry.
  const geometry = () => page.locator('.office-scope-content').evaluateAll(nodes => nodes.map(n => {
    const r = n.getBoundingClientRect(); return [r.x, r.y, r.width, r.height];
  }));
  const before = await geometry();
  await page.addStyleTag({ content: '.specialist-glass-layer { display:none !important }' });
  assert.deepEqual(await geometry(), before);
  await checkPanels(page);
  await page.route('**/canon/characters/holographic-panes/*.png', route => route.abort());
  await page.reload();
  await checkPanels(page, { artwork: false });
  await page.locator('.specialist-projection').screenshot({ path: 'artifacts/ui/panes-missing-images.png' });
  await page.unroute('**/canon/characters/holographic-panes/*.png');

  await page.emulateMedia({ forcedColors: 'active' });
  await page.reload();
  await checkPanels(page);
  assert.equal(await page.locator('.specialist-glass-layer').first().evaluate(n => getComputedStyle(n).display), 'none');
  await page.locator('.specialist-projection').screenshot({ path: 'artifacts/ui/panes-forced-colors.png' });
  await page.emulateMedia({ forcedColors: 'none' });
  // Older Chromium lacks this emulateMedia option; CDP exercises the CSS feature.
  const cdp = await context.newCDPSession(page);
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-transparency', value: 'reduce' }] });
  await page.reload();
  assert.equal(await page.evaluate(() => matchMedia('(prefers-reduced-transparency: reduce)').matches), true);
  await checkPanels(page);
  assert.equal(await page.locator('.specialist-glass-layer').first().evaluate(n => getComputedStyle(n).display), 'none');
  assert.equal(await page.locator('.specialist-glass-identity').first().evaluate(n => getComputedStyle(n).zIndex), '2');
  await page.locator('.specialist-projection').screenshot({ path: 'artifacts/ui/panes-reduced-transparency.png' });
  assert.deepEqual(errors, []);
  await context.close();
  console.log('Specialist panes: 10 desktop/mobile surfaces, large text, focus, missing imagery, forced colors and reduced transparency passed.');
} finally { await browser.close(); }
