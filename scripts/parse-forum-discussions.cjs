// Parse saved public HTML inertly: DOMParser does not run scripts or load images.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('C:/Users/rick/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const cache = path.resolve(__dirname, '../research/discussion-sources');
const sources = {
  'priarm-discussion': 'https://www.ptt.cc/bbs/miHoYo/M.1565282863.A.4B1.html',
  'elysia-ptt': 'https://www.ptt.cc/bbs/C_Chat/M.1757146843.A.409.html',
  'finale-ptt': 'https://www.ptt.cc/bbs/miHoYo/M.1783064047.A.1E1.html',
  'part2-forum': 'https://forum.gamer.com.tw/C.php?bsn=31066&snA=21616',
  'card-forum': 'https://forum.gamer.com.tw/C.php?bsn=31066&snA=10231',
  'finality-forum': 'https://forum.gamer.com.tw/C.php?bsn=31066&snA=20288',
};
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  try {
    const page = await browser.newPage();
    for (const [key, url] of Object.entries(sources)) {
      const html = fs.readFileSync(path.join(cache, key + '.html'), 'utf8');
      const result = await page.evaluate(({ html, url }) => {
        const d = new DOMParser().parseFromString(html, 'text/html');
        const txt = (element, selector) => element.querySelector(selector)?.textContent.trim() || '';
        const base = { title: d.title, url, comments: [] };
        if (url.includes('ptt.cc')) {
          base.platform = 'PTT';
          const meta = [...d.querySelectorAll('.article-meta-value')].map(e => e.textContent);
          const year = meta.join(' ').match(/20\d{2}/)?.[0];
          for (const [index, push] of [...d.querySelectorAll('.push')].entries()) {
            const username = txt(push, '.push-userid');
            const text = txt(push, '.push-content').replace(/^: ?/, '');
            const stamp = txt(push, '.push-ipdatetime').match(/(\d{2})\/(\d{2})\s+(\d{2}:\d{2})/);
            if (!username || !text || !stamp || !year) continue;
            const publishedAt = `${year}-${stamp[1]}-${stamp[2]}T${stamp[3]}:00+08:00`;
            const previous = base.comments.at(-1);
            if (previous?.username === username && previous.publishedAt === publishedAt) { previous.text += '\n' + text; previous.pushLines.push(index + 1); continue; }
            base.comments.push({ id: 'push-' + (index + 1), userId: username, username, text, publishedAt, dateBasis: '推文仅显示月日和时分；年份依原帖年份推定，秒数未提供。', pushLines: [index + 1], sourceURL: url });
          }
        } else {
          base.platform = '巴哈姆特';
          for (const [index, post] of [...d.querySelectorAll('.c-post')].entries()) {
            const author = post.querySelector('.c-post__header__author');
            const username = txt(author || post, '.username');
            const userId = txt(author || post, '.userid');
            const publishedAt = txt(post, '.c-post__header__info .edittime').match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)?.[0];
            const content = post.querySelector('.c-article__content');
            if (username && publishedAt && content) base.comments.push({ id: 'floor-' + (index + 1), userId, username, text: content.textContent.trim(), publishedAt: publishedAt.replace(' ', 'T') + '+08:00', dateBasis: '原帖显示时间；标注编辑的楼层可能为编辑时间。', position: txt(author || post, '.floor'), sourceURL: url });
            for (const reply of post.querySelectorAll('.c-reply__item')) {
              let metadata;
              try { metadata = JSON.parse(reply.getAttribute('data-comment') || '{}'); } catch { metadata = {}; }
              const user = reply.querySelector('.reply-content__user');
              const text = txt(reply, '.comment_content');
              const stamp = txt(reply, '.edittime').match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)?.[0];
              if (!user || !text || !stamp || !metadata.sn) continue;
              base.comments.push({ id: String(metadata.sn), userId: new URL(user.getAttribute('href'), url).searchParams.get('owner') || user.getAttribute('href'), username: user.textContent.trim(), text, publishedAt: stamp.replace(' ', 'T') + '+08:00', sourceURL: url, position: txt(reply, '.reply_time') || null });
            }
          }
          base.comments = base.comments.filter((c, index, all) => all.findIndex(other => other.id === c.id) === index);
        }
        base.status = base.comments.length ? 'ok' : 'no-readable-comments';
        return base;
      }, { html, url });
      result.checkedAt = new Date().toISOString();
      fs.writeFileSync(path.join(cache, key + '.json'), JSON.stringify(result, null, 2));
      console.log(key + ': ' + result.comments.length + ' comments');
    }
  } finally { await browser.close(); }
})();
