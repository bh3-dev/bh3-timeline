// Read the same public comments returned to an ordinary, logged-out browser.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('C:/Users/rick/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '..');
const cache = path.join(root, 'research/discussion-sources');
const targets = {
  'zoro-taptap': '15230156691996962',
  'wuxueyou-taptap': '15201143235805921',
  'big-card-taptap': '15214892420169954',
  'priarm-taptap': '15205923576349573',
  'welfare-taptap': '43422422782709419',
  'artbook-taptap': '301306665829925500',
  'stigma-plan-taptap': '316354104458741306',
  'captainverse-taptap': '445998079456313463',
  'cn-8.9-taptap': '806539256917921448',
  'history-taptap': '135017348426894330',
  'zero98-taptap': '178717392187166345',
  'anniversary-taptap': '851861380653911488',
  'first-year-taptap': '58672674116733023',
};
for (const version of JSON.parse(fs.readFileSync(path.join(root, 'research/timeline.zh-CN.json'), 'utf8').replace(/^\uFEFF/, '')).versions) {
  const url = version.sources.find(source => /taptap\.cn\/moment\/\d+/.test(source.url))?.url;
  if (url) targets[version.id + '-taptap'] = url.match(/moment\/(\d+)/)[1];
}
const textOf = node => typeof node.text === 'string' ? node.text : (node.children || []).map(textOf).join('');
const dateOf = seconds => new Date(seconds * 1000).toISOString();
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  try {
    for (const [key, moment] of Object.entries(targets)) {
      const filename = path.join(cache, key + '.json');
      if (fs.existsSync(filename)) continue;
      const page = await browser.newPage();
      const result = { platform: 'TapTap', url: 'https://www.taptap.cn/moment/' + moment, checkedAt: new Date().toISOString(), comments: [] };
      let resolveComments;
      const received = new Promise(resolve => { resolveComments = resolve; });
      page.on('response', async response => {
        if (!response.url().includes('/moment-comment/v1/by-moment') || !response.url().includes('moment_id=' + moment)) return;
        try {
          const payload = await response.json();
          for (const comment of payload.data?.list || []) {
            for (const item of [comment, ...(comment.child_posts || [])]) {
              const author = item.author || {};
              const text = (item.contents?.json || []).map(textOf).join('\n').trim();
              if (!text || result.comments.some(c => c.id === String(item.id))) continue;
              result.comments.push({ id: String(item.id), userId: String(author.id), username: author.name, publishedAt: dateOf(item.created_time), text, likes: item.ups || 0, replyTo: item.parent_post_id ? String(item.parent_post_id) : null, position: item.position || null, official: Boolean(author.verified || author.is_moderator), sourceURL: result.url });
            }
          }
          resolveComments();
        } catch (error) { result.error = error.message; }
      });
      try {
        await page.goto(result.url, { waitUntil: 'domcontentloaded', timeout: 40000 });
        await Promise.race([received, new Promise(resolve => setTimeout(resolve, 14000))]);
        result.title = await page.title();
        result.status = result.comments.length ? 'ok' : 'no-readable-comments';
      } catch (error) { result.status = 'unavailable'; result.error = error.message; }
      fs.writeFileSync(filename, JSON.stringify(result, null, 2));
      console.log(key + ': ' + result.status + ', ' + result.comments.length + ' comments');
      await page.close();
    }
  } finally { await browser.close(); }
})();
