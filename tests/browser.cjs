const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'verification');
const base = 'http://127.0.0.1:5184';
const server = spawn(process.execPath, ['scripts/serve.mjs', '--dist'], { cwd: root, env: { ...process.env, PORT: '5184' }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
const ready = new Promise((resolve, reject) => {
  server.stdout.on('data', data => { if (data.toString().includes('Local:')) resolve(); });
  server.on('error', reject);
  server.on('exit', code => { if (code) reject(new Error('Preview server failed: ' + code)); });
});

(async () => {
  fs.mkdirSync(output, { recursive: true });
  await ready;
  const browser = await chromium.launch({ ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}), headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', permissions: ['clipboard-read', 'clipboard-write'] });
  const page = await context.newPage();
  const report = { checks: [], errors: [], missing: [] };
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('response', response => { if (response.status() >= 400 && response.url().startsWith(base)) report.missing.push({ url: response.url(), status: response.status() }); });
  const count = () => page.locator('#timeline .record-card').count();
  const check = name => { report.checks.push(name); console.log('PASS ' + name); };
  try {
    await page.goto(base);
    await page.waitForSelector('.record-card');
    assert.equal(await count(), 7);
    assert.equal(await page.locator('#version-count').textContent(), '82');
    assert.equal(await page.locator('#video-count').textContent(), '56');
    assert.equal(await page.locator('#total-count').textContent(), '168');
    check('Initial 2016 archive and research counts');
    await page.screenshot({ path: path.join(output, 'desktop.png') });
    await page.locator('#anniversary-jump').click();
    assert.equal(await count(), 10);
    await page.locator('[data-record="cn-9.1"]').click();
    await page.waitForSelector('#detail-dialog[open]');
    assert.ok((await page.locator('#detail-content').innerText()).includes('时序之律者'));
    assert.ok((await page.locator('#detail-content').innerText()).includes('十周年庆'));
    await page.locator('[data-copy="cn-9.1"]').click();
    const shared = await page.evaluate(() => navigator.clipboard.readText());
    assert.ok(shared.includes('event=cn-9.1'));
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#detail-dialog').getAttribute('open'), null);
    check('Anniversary jump, version details, share link and Escape');

    await page.locator('#search').fill('Scyrax');
    await page.waitForFunction(() => document.querySelector('#result-summary').innerText.includes('搜索结果'));
    assert.equal(await count(), 4);
    await page.locator('[data-type="video"]').click();
    assert.equal(await count(), 4);
    await page.locator('#sort').selectOption('desc');
    const beforeReload = await page.locator('#timeline .record-card').evaluateAll(nodes => nodes.map(n => n.dataset.record));
    await page.reload();
    await page.waitForSelector('.record-card');
    assert.equal(await page.locator('#search').inputValue(), 'Scyrax');
    assert.deepEqual(await page.locator('#timeline .record-card').evaluateAll(nodes => nodes.map(n => n.dataset.record)), beforeReload);
    check('Global creator search, combined filters, reverse sort and URL restoration');
    await page.locator('#reset-filters').click();
    assert.equal(await count(), 168);

    // Open every record to catch data-schema, source-link and relation rendering failures.
    const allIDs = await page.locator('#timeline .record-card').evaluateAll(nodes => nodes.map(n => n.dataset.record));
    for (const id of allIDs) {
      await page.locator(`#timeline [data-record="${id}"]`).dispatchEvent('click');
      assert.ok(await page.locator('#detail-dialog').getAttribute('open') !== null, id);
      assert.ok((await page.locator('#detail-title').textContent()).length > 0, id);
      assert.ok(await page.locator('#detail-dialog .source-link').count() > 0, id);
      assert.equal(await page.locator('#detail-dialog .source-link[href="#"]').count(), 0, id);
      assert.equal(await page.locator('#detail-dialog .discussion-card').count(), 3, id + ' community quotes');
      assert.equal(await page.locator('#detail-dialog .discussion-origin a').count(), 3, id + ' original comment links');
      assert.equal(await page.locator('#detail-dialog .discussion-origin a[href="#"]').count(), 0, id);
      assert.ok((await page.locator('#detail-dialog .discussion-intro').innerText()).includes('3 位用户'), id);
      await page.locator('#detail-dialog .close-dialog').dispatchEvent('click');
    }
    check('All 168 records open with valid sources, related content and three attributed user comments');

    await page.locator('#timeline [data-record="zoro-anniversary"]').dispatchEvent('click');
    await page.locator('.detail-discussions').scrollIntoViewIfNeeded();
    assert.ok((await page.locator('.discussion-list').innerText()).includes('不行不行300氵才能全服失忆'));
    assert.ok((await page.locator('.discussion-list').innerText()).includes('2018.09.30'));
    await page.screenshot({ path: path.join(output, 'discussions-desktop.png') });
    await page.keyboard.press('Escape');
    check('Original TapTap wording and Beijing dates render correctly');

    await page.locator('[data-year="2016"]').first().click();
    await page.locator('[data-type="community"]').click();
    assert.equal(await count(), 0);
    assert.ok(await page.locator('.empty-state').isVisible());
    await page.locator('#show-all').click();
    assert.equal(await count(), 168);
    await page.locator('#timeline [data-record="white-river"]').dispatchEvent('click');
    assert.ok((await page.locator('#detail-content').innerText()).includes('2019年底（3.6期间）'));
    assert.ok((await page.locator('#detail-content').innerText()).includes('未核验'));
    await page.screenshot({ path: path.join(output, 'community-details.png') });
    await page.keyboard.press('Escape');
    check('Empty filter recovery and original period/evidence labels');

    await page.locator('#timeline [data-record="mei-pv-2016"]').dispatchEvent('click');
    await page.locator('#detail-dialog [data-record="cn-1.0"]').click();
    assert.equal(await page.locator('.detail-character-list>div').count(), 12);
    await page.screenshot({ path: path.join(output, 'version-details.png') });
    await page.keyboard.press('Escape');
    check('Video-to-version navigation and full launch lineup');

    await page.locator('[data-about]').first().click();
    await page.locator('#open-glossary').click();
    assert.equal(await page.locator('.glossary-entry').count(), 12);
    assert.ok((await page.locator('#about-dialog').innerText()).includes('累计快照'));
    await page.keyboard.press('Escape');
    check('Source policies, glossary and accessible dialogs');

    await page.goto(shared);
    await page.waitForSelector('#detail-dialog[open]');
    assert.equal(await page.locator('#detail-title').textContent(), '时序照新');
    await page.keyboard.press('Escape');
    check('Shared deep link opens its exact record');

    for (const width of [320, 390, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 844 });
      await page.goto(base);
      await page.waitForSelector('.record-card');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'page overflow at ' + width);
      await page.locator('#timeline [data-record="cn-1.0"]').dispatchEvent('click');
      assert.equal(await page.locator('#detail-dialog').evaluate(node => node.scrollWidth > node.clientWidth), false, 'dialog overflow at ' + width);
      await page.locator('.detail-discussions').scrollIntoViewIfNeeded();
      assert.equal(await page.locator('.discussion-card').evaluateAll(nodes => nodes.some(node => node.scrollWidth > node.clientWidth)), false, 'quote overflow at ' + width);
      if (width === 390) await page.screenshot({ path: path.join(output, 'discussions-mobile.png') });
      await page.keyboard.press('Escape');
      if (width === 390) {
        await page.evaluate(() => scrollTo(0, 0));
        await page.screenshot({ path: path.join(output, 'mobile.png') });
        await page.locator('#archive').scrollIntoViewIfNeeded();
        await page.screenshot({ path: path.join(output, 'mobile-archive.png') });
      }
    }
    check('Page and record details fit 320, 390, 768, 1024 and 1440px screens');

    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(base);
    await page.waitForSelector('.record-card');
    await page.locator('.record-card').last().scrollIntoViewIfNeeded();
    await page.waitForFunction(() => [...document.querySelectorAll('#timeline img')].every(img => img.complete && img.naturalWidth > 0));
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(output, 'desktop-full.png'), fullPage: true });
    await page.evaluate(() => scrollTo(0, 700));
    await page.screenshot({ path: path.join(output, 'desktop-archive.png') });
    assert.equal((await context.request.get(base + '/research/community.md')).status(), 200);
    assert.equal((await context.request.get(base + '/research/discussions.md')).status(), 200);
    assert.equal(await page.locator('a[href="home/index.html"]').count(), 0);
    check('Original covers and research documents are in the standalone production build');
    await context.setOffline(true);
    await page.goto(pathToFileURL(path.join(root, 'dist/index.html')).href);
    await page.waitForSelector('.record-card');
    assert.equal(await count(), 7);
    await page.locator('#timeline [data-record="cn-1.0"]').dispatchEvent('click');
    assert.equal(await page.locator('.detail-character-list>div').count(), 12);
    assert.equal(await page.locator('.discussion-card').count(), 3);
    assert.ok((await page.locator('.discussion-list').innerText()).includes('公测'));
    await page.keyboard.press('Escape');
    await page.locator('#search').fill('爱莉希雅');
    await page.waitForFunction(() => document.querySelector('#result-summary').innerText.includes('搜索结果'));
    assert.ok(await count() > 5);
    await page.locator('#reset-filters').click();
    assert.equal(await count(), 168);
    await context.setOffline(false);
    check('Direct offline file opening, search, filters and record details');
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.missing, []);
    check('No JavaScript exceptions or missing local requests');
    fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.kill());
