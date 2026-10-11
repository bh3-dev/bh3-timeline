import { TYPES, YEAR_TITLES, createRecords, filterRecords, displayDate, relatedRecords, readState, escapeHTML as esc, safeLink } from './timeline.js';

const $ = selector => document.querySelector(selector);
const timeline = $('#timeline');
const detailDialog = $('#detail-dialog');
const aboutDialog = $('#about-dialog');
let records = [], years = [], state, data, covers = {}, searchTimer, toastTimer, embeddedData;
const icons = {
  milestone: '<path d="M12 3v18M3 12h18M5 5l14 14M5 19 19 5"/>',
  version: '<path d="m12 3 8 4v10l-8 4-8-4V7zM4 7l8 4 8-4M12 11v10"/>',
  video: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/>',
  community: '<path d="M20 11a8 8 0 0 1-8 8H5l-3 3V11a9 9 0 1 1 18 0ZM7 10h8M7 14h5"/>',
};
const icon = type => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[type]}</svg>`;
const tag = (text, cls = '') => `<span class="tag ${cls}">${esc(text)}</span>`;
const num = value => value >= 10000 ? `${(value / 10000).toFixed(1)}万` : new Intl.NumberFormat('zh-CN').format(value || 0);
const duration = seconds => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
const sourceNames = { official: '官方来源', reprint: '同期公告转载', 'official-archive': '官方存档', 'original-video': '视频原稿', 'bilibili-public-metadata': 'B站公开元数据', 'community-index': '社区版本索引' };
const accessNames = { 'full-text': '已核对全文', 'search-index-only': '仅搜索索引', 'reference-unread': '原帖未读', 'page-metadata': '页面元数据' };
const sourceLink = source => `<a class="source-link" href="${safeLink(source.url)}" target="_blank" rel="noopener noreferrer"><span>${esc(source.title || sourceNames[source.kind] || '参考来源')}<small>${esc(source.access ? accessNames[source.access] || source.access : new URL(source.url).hostname)}</small></span><b>↗</b></a>`;

function updateURL() {
  const params = new URLSearchParams();
  if (state.year !== '2016') params.set('year', state.year);
  if (state.type !== 'all') params.set('type', state.type);
  if (state.query) params.set('q', state.query);
  if (state.sort !== 'asc') params.set('sort', state.sort);
  if (state.event) params.set('event', state.event);
  history.replaceState(null, '', `${location.pathname}${params.size ? '?' + params : ''}${location.hash}`);
}

function selectYear(year) {
  state.year = year;
  state.event = null;
  render();
  updateURL();
  $('#archive').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function selectType(type, nav = false) {
  state.type = type;
  if (nav) state.year = 'all';
  render();
  updateURL();
}

function renderYears() {
  const matching = filterRecords(records, { ...state, year: 'all' });
  $('#year-nav').innerHTML = ['all', ...years].map(year => {
    const count = matching.filter(row => year === 'all' || row.year === year).length;
    const active = state.year === year;
    return `<button class="year-button ${active ? 'active' : ''}" data-year="${year}" ${active ? 'aria-current="date"' : ''}><span>${year === 'all' ? '全部年份' : year}</span><small>${String(count).padStart(2, '0')}</small><b aria-hidden="true">${active ? '→' : ''}</b></button>`;
  }).join('');
}

function renderCard(row, index) {
  const date = displayDate(row);
  let inside;
  if (row.type === 'version') {
    const people = row.characters.slice(0, 4).map(c => tag(`${c.person} · ${c.name}`, 'character')).join('');
    inside = `<div class="record-body"><div class="record-top">${tag('VER ' + row.version, 'version-label')}${row.majorEvents.some(e => e.kind === 'anniversary') ? tag('周年纪念', 'anniversary-label') : ''}<span class="record-kind">${TYPES[row.type]}</span></div><h4>${esc(row.title)}</h4><div class="character-tags">${people}${row.characters.length > 4 ? `<span class="more-tags">+${row.characters.length - 4}</span>` : ''}</div>${row.majorEvents.length ? `<p class="event-line"><span>活动</span> ${esc(row.majorEvents.map(e => e.title).join(' · '))}</p>` : ''}${row.summary ? `<p class="record-summary">${esc(row.summary)}</p>` : ''}<div class="record-bottom"><span>国服版本更新 · ${row.sources.length} 个来源</span><span class="record-action">翻阅档案 ↗</span></div></div>`;
  } else if (row.type === 'video') {
    const cover = covers[row.id]?.path;
    inside = `<div class="video-cover ${cover ? '' : 'cover-fallback'}">${cover ? `<img src="${esc(cover)}" alt="${esc(row.title)}视频原稿封面" loading="lazy" />` : `<span>${esc(row.title)}</span>`}<span class="play-icon">▶</span><span class="duration">${duration(row.durationSeconds)}</span></div><div class="record-body"><div class="record-top">${tag(data.videos.meta.categories[row.category] || TYPES.video, 'video-label')}<span class="record-kind">影像回忆</span></div><h4>${esc(row.title)}</h4><p class="record-summary">${esc(row.summary)}</p><div class="record-bottom"><span>${esc(row.creator.name)} <i>·</i> ${num(row.statsSnapshot.views)} 次累计播放</span><span class="record-action">重温影像 ↗</span></div></div>`;
  } else if (row.type === 'community') {
    inside = `<div class="record-body"><div class="record-top">${tag(row.categoryLabel, 'community-label')}<span class="record-kind">${esc(row.evidenceLabel)}</span></div><h4>${esc(row.title)}</h4><p class="record-summary">${esc(row.summary)}</p><div class="community-tags">${row.tags.slice(0, 4).map(t => tag(t)).join('')}</div><div class="record-bottom"><span>${esc(row.dateBasisLabel)}</span><span class="record-action">查看记忆 ↗</span></div></div>`;
  } else {
    inside = `<div class="record-body"><div class="record-top">${tag('起点 / PROLOGUE', 'milestone-label')}<span class="record-kind">${TYPES.milestone}</span></div><h4>${esc(row.title)}</h4><p class="record-summary">${esc(row.summary)}</p><div class="record-bottom"><span>${row.datePrecision === 'month' ? '月份节点 · 非首次开启日' : '启航纪事'}</span><span class="record-action">查看记录 ↗</span></div></div>`;
  }
  return `<article class="timeline-item type-${row.type}" style="--entry-index:${Math.min(index, 7)}"><div class="record-date"><time datetime="${esc(row.date)}">${esc(date)}</time><span>${row.datePrecision === 'month' ? '月份记录' : row.datePrecision === 'period' ? '时期记录' : row.type === 'community' ? '日期口径见详情' : row.type === 'video' ? '原稿发布' : '国服时间'}</span></div><div class="timeline-node">${icon(row.type)}</div><button class="record-card ${row.type === 'video' ? 'video-card' : ''}" data-record="${esc(row.id)}" aria-label="查看${esc(row.title)}的详情">${inside}</button></article>`;
}

function render() {
  const visible = filterRecords(records, state);
  renderYears();
  document.querySelectorAll('[data-type]').forEach(button => {
    const active = button.dataset.type === state.type;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', active);
  });
  document.querySelectorAll('[data-nav-type]').forEach(link => link.classList.toggle('active', link.dataset.navType === state.type));
  $('#search').value = state.query;
  $('#sort').value = state.sort;
  $('#timeline-year').innerHTML = state.year === 'all' ? `2016—2026<span>${state.query ? '寻找你的回忆' : '十年时光'}</span>` : `${state.year}<span>${YEAR_TITLES[state.year]}</span>`;
  $('#timeline-caption').textContent = state.query ? `在${state.year === 'all' ? '全部年份' : state.year + '年'}中搜索「${state.query}」` : state.year === '2016' ? '从九月的预登录开始，故事在这里写下第一行。' : `${state.year === 'all' ? '从初次启航到十周年相聚' : '这一年，我们一起走过'}，让记忆沿着时间再次展开。`;
  $('#result-summary').innerHTML = `<span>收录 <b>${visible.length}</b> 条${state.type === 'all' ? '记忆' : TYPES[state.type]}${state.query ? ' · 搜索结果' : ''}</span>${state.query || state.type !== 'all' ? '<button id="reset-filters">清除筛选 ×</button>' : '<span class="summary-hint">点击卡片，翻阅完整记录与来源 ↗</span>'}`;
  if (!visible.length) {
    timeline.innerHTML = `<div class="empty-state"><div>⌕</div><h4>这段回忆还没有被找到</h4><p>试试其他关键词，或展开全部年份。</p><button id="show-all" class="button button-dark">查看全部记忆 →</button></div>`;
  } else {
    let currentYear;
    timeline.innerHTML = visible.map((row, i) => {
      let heading = '';
      if (state.year === 'all' && row.year !== currentYear) {
        currentYear = row.year;
        heading = `<div class="timeline-year-divider"><b>${row.year}</b><span>${YEAR_TITLES[row.year]}</span></div>`;
      }
      return heading + renderCard(row, i);
    }).join('');
  }
  timeline.setAttribute('aria-busy', 'false');
  const position = years.indexOf(state.year);
  $('#year-pagination').innerHTML = position < 0 ? '' : `<button data-year="${years[position - 1] || ''}" ${position === 0 ? 'disabled' : ''}>← ${position === 0 ? '故事的起点' : years[position - 1] + ' 年'}</button><span>${position + 1} / ${years.length} <small>YEARS OF MEMORIES</small></span><button data-year="${years[position + 1] || ''}" ${position === years.length - 1 ? 'disabled' : ''}>${position === years.length - 1 ? '故事仍在继续' : years[position + 1] + ' 年'} →</button>`;
}

const detailSection = (title, content, cls = '') => content ? `<section class="detail-section ${cls}"><h3>${title}</h3>${content}</section>` : '';
const lines = values => values.map(value => `<li>${esc(value)}</li>`).join('');

function discussionSection(row) {
  const entry = data.discussions.nodes[row.id];
  if (!entry?.quotes?.length) return '';
  const dates = new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Shanghai' });
  const cards = entry.quotes.map(quote => {
    const source = data.discussions.sources[quote.sourceId];
    const stamp = dates.format(new Date(quote.publishedAt)).replaceAll('/', '.');
    const delta = (Date.parse(quote.publishedAt) - Date.parse(row.date.length === 7 ? row.date + '-01' : row.date)) / 86400000;
    const sameYear = stamp.slice(0, 4) === row.year;
    const period = row.type === 'community' ? (sameYear ? '同年留言' : stamp.slice(0, 4) > row.year ? '后来讨论' : '较早留言') : delta < -30 ? '较早留言' : delta < 0 ? '前瞻留言' : delta <= 70 ? '同期留言' : '后来讨论';
    const platform = source.platform === 'Bilibili' ? 'B站' : source.platform;
    return `<article class="discussion-card" data-comment-id="${esc(quote.id)}"><div class="discussion-author"><span class="discussion-avatar" aria-hidden="true">${esc(Array.from(quote.username)[0])}</span><div><b>${esc(quote.username)}</b><span>${esc(platform)} <i>·</i> <time datetime="${esc(quote.publishedAt)}" ${quote.dateBasis ? `title="${esc(quote.dateBasis)}"` : ''}>${esc(stamp)}</time>${quote.position ? ` <i>·</i> ${esc(quote.position)}${source.platform === 'TapTap' ? '楼' : ''}` : ''}</span></div><small class="discussion-period ${period === '后来讨论' ? 'later' : ''}">${period}</small></div><blockquote>${esc(quote.text)}${quote.excerpted ? '<span class="quote-ellipsis" aria-label="原文节选"> …</span>' : ''}</blockquote><div class="discussion-origin"><span title="${esc(source.title)}">${esc(source.title)}</span><a href="${safeLink(quote.url)}" target="_blank" rel="noopener noreferrer" aria-label="查看${esc(quote.username)}在${esc(source.title)}的原始留言">${quote.excerpted ? '读完整留言' : '查看原留言'} ↗</a></div></article>`;
  }).join('');
  return detailSection('社区回声', `<div class="discussion-intro"><span class="discussion-count">${entry.quotes.length} 位用户 · 原话摘录</span><p>${esc(entry.context)}</p></div><div class="discussion-list">${cards}</div><p class="discussion-policy">每条观点属于署名用户，节选不代表社区共识。留言日期按北京时间展示；更多上下文可在原帖阅读。<span>采集截至 ${esc(data.discussions.meta.asOf.replaceAll('-', '.'))}</span></p>`, 'detail-discussions');
}

function openRecord(id, syncURL = true) {
  const row = records.find(r => r.id === id);
  if (!row) return;
  if (aboutDialog.open) aboutDialog.close();
  let content = `<div class="detail-heading type-${row.type}"><div class="detail-metadata">${tag(TYPES[row.type])}${row.version ? tag('VER ' + row.version) : ''}<time datetime="${esc(row.date)}">${esc(displayDate(row))}</time></div><h2 id="detail-title">${esc(row.title)}</h2>${row.type !== 'version' ? `<p>${esc(row.summary)}</p>` : ''}</div>`;
  if (row.type === 'version') {
    content += detailSection('新增装甲与其他角色', row.characters.length ? `<div class="detail-character-list">${row.characters.map(c => `<div><span>${esc(c.person)}</span><b>${esc(c.name)}</b><small>${esc(data.versions.meta.characterKinds[c.kind] || c.kind)}</small></div>`).join('')}</div>` : '<p>本次整理未列新增装甲。</p>');
    content += detailSection('主题活动', row.majorEvents.length ? `<ul>${lines(row.majorEvents.map(e => e.title + (e.rerun ? '（复刻）' : '')))}</ul>` : '<p>本次精选未单列主题活动。</p>');
    content += detailSection('剧情与重要玩法', row.storyAndFeatures.length ? `<ul>${lines(row.storyAndFeatures)}</ul>` : '');
    content += detailSection('日期与内容说明', `<p>日期为中国大陆国服更新日，版本内容可能分周开放。</p>${row.notes?.length ? `<ul>${lines(row.notes)}</ul>` : ''}${row.verification?.date === 'community-index-needs-primary-date' ? '<p class="evidence-caveat">更新日采用玩家版本索引，仍需补充官方维护公告。</p>' : ''}`, 'detail-note');
  } else if (row.type === 'video') {
    if (covers[row.id]?.path) content += `<div class="detail-video-cover"><img src="${esc(covers[row.id].path)}" alt="${esc(row.title)}原稿封面" /><a href="${safeLink(row.url)}" target="_blank" rel="noopener noreferrer"><span>▶</span>在 B 站重温</a></div>`;
    content += detailSection('原稿档案', `<dl class="video-facts"><div><dt>发布账号</dt><dd><a href="${safeLink(row.creator.url)}" target="_blank" rel="noopener noreferrer">${esc(row.creator.name)} ↗</a></dd></div><div><dt>原稿发布时间 · 北京时间</dt><dd>${esc(row.publishedAt.replace('T', ' ').replace('+08:00', ''))}</dd></div><div><dt>视频时长</dt><dd>${duration(row.durationSeconds)}</dd></div><div><dt>BV 号</dt><dd>${esc(row.bvid)}</dd></div></dl><a class="button button-dark" href="${safeLink(row.url)}" target="_blank" rel="noopener noreferrer">打开视频原稿 <span>↗</span></a>`);
    const stats = row.statsSnapshot;
    content += detailSection('累计数据快照', `<div class="stats-grid"><div><b>${num(stats.views)}</b><span>播放</span></div><div><b>${num(stats.likes)}</b><span>点赞</span></div><div><b>${num(stats.coins)}</b><span>投币</span></div><div><b>${num(stats.favorites)}</b><span>收藏</span></div></div><p class="evidence-caveat">采集时间：${esc(stats.asOf.replace('T', ' ').split('.')[0].replace('+08:00', ''))}（北京时间）。累计数据不代表发布当年的热度或年度排名。${stats.historicalHighestSitewideRank ? `接口记录的全站历史最高排名为第 ${stats.historicalHighestSitewideRank} 名。` : '本次未取得全站历史最高排名。'}</p>`);
    const topics = data.videos.topics.filter(t => t.videoIds.includes(row.id));
    if (topics.length) content += detailSection('相关影像话题', topics.map(t => `<div class="video-topic"><b>${esc(t.title)}</b><p>${esc(t.summary)}</p><div class="related-links">${t.videoIds.filter(vid => vid !== row.id).map(vid => { const video = records.find(r => r.id === vid); return video ? `<button data-record="${esc(vid)}">${esc(video.title)} ↗</button>` : ''; }).join('')}</div><small>话题锚点为所选视频的最早发布日期，不代表话题起源。</small></div>`).join(''));
  } else if (row.type === 'community') {
    content += detailSection('这段记忆的背景', `<p>${esc(row.detail)}</p><p class="evidence-caveat">${esc(row.caveat)}</p>`);
    content += detailSection('日期与证据说明', `<dl class="video-facts"><div><dt>展示日期</dt><dd>${esc(row.dateLabel)}</dd></div><div><dt>日期依据</dt><dd>${esc(row.dateBasisLabel)}</dd></div><div><dt>证据状态</dt><dd>${esc(row.evidenceLabel)}</dd></div><div><dt>首次出现时间</dt><dd>${row.firstAppearance ? esc(row.firstAppearance) : '未核验'}</dd></div></dl><p>${esc(row.dateNote)}</p>`, 'detail-note');
    content += detailSection('记忆标签', `<div class="community-tags">${row.tags.map(t => tag(t)).join('')}</div>`);
  } else {
    content += detailSection('节点说明', `<p>${esc(row.description)}</p><p>展示精度：${row.datePrecision === 'month' ? '月份' : '具体日期'} · 北京时间</p>`, 'detail-note');
  }
  content += discussionSection(row);
  const related = relatedRecords(row, records);
  if (related.length) content += detailSection('在时间轴上相遇', `<div class="related-links">${related.map(r => `<button data-record="${esc(r.id)}"><small>${esc(displayDate(r))} · ${TYPES[r.type]}</small><span>${r.version ? esc(r.version) + ' ' : ''}${esc(r.title)} ↗</span></button>`).join('')}</div>`);
  const sources = row.type === 'community' ? row.sourceIds.map(id => data.community.sources.find(s => s.id === id)).filter(Boolean) : row.sources || [];
  content += detailSection('资料来源', `<div class="source-list">${sources.map(sourceLink).join('')}</div>`);
  content += `<div class="detail-footer"><span>每一段记忆，都值得被认真记录。</span><button class="share-button" data-copy="${esc(row.id)}">复制此条链接 ↗</button></div><div id="share-fallback" hidden></div>`;
  $('#detail-content').innerHTML = content;
  state.event = id;
  if (syncURL) updateURL();
  if (!detailDialog.open) detailDialog.showModal();
  detailDialog.scrollTop = 0;
}

function toast(text) {
  clearTimeout(toastTimer);
  $('#toast').textContent = text;
  $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3000);
}

document.addEventListener('click', async event => {
  const recordButton = event.target.closest('[data-record]');
  if (recordButton) { openRecord(recordButton.dataset.record); return; }
  const yearButton = event.target.closest('[data-year]');
  if (yearButton?.dataset.year) { selectYear(yearButton.dataset.year); return; }
  const typeButton = event.target.closest('[data-type]');
  if (typeButton && state) { selectType(typeButton.dataset.type); return; }
  const nav = event.target.closest('[data-nav-type]');
  if (nav && state) selectType(nav.dataset.navType, true);
  if (event.target.closest('[data-about]')) aboutDialog.showModal();
  if (event.target.closest('.close-dialog')) event.target.closest('dialog').close();
  if (event.target.closest('#reset-filters') || event.target.closest('#show-all')) {
    state = { ...state, query: '', type: 'all', year: 'all' };
    clearTimeout(searchTimer); render(); updateURL();
  }
  const share = event.target.closest('[data-copy]');
  if (share) {
    const url = new URL(location.href);
    url.searchParams.set('event', share.dataset.copy);
    url.hash = '';
    try { await navigator.clipboard.writeText(url.href); toast('这段回忆的链接已复制'); } catch {
      $('#share-fallback').hidden = false;
      $('#share-fallback').innerHTML = `<label>复制这个链接，分享这段回忆<input readonly value="${esc(url.href)}" /></label>`;
      $('#share-fallback input').select();
    }
  }
});

for (const dialog of document.querySelectorAll('dialog')) {
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => {
    document.body.classList.toggle('dialog-open', detailDialog.open || aboutDialog.open);
    if (dialog === detailDialog && state) { state.event = null; updateURL(); }
  });
  new MutationObserver(() => document.body.classList.toggle('dialog-open', detailDialog.open || aboutDialog.open)).observe(dialog, { attributes: true, attributeFilter: ['open'] });
}

$('#search').addEventListener('input', event => {
  clearTimeout(searchTimer);
  const query = event.target.value;
  searchTimer = setTimeout(() => { state.query = query.slice(0, 200); state.year = 'all'; render(); updateURL(); }, 160);
});
$('#sort').addEventListener('change', event => { state.sort = event.target.value; render(); updateURL(); });
$('#anniversary-jump').addEventListener('click', () => { state = { ...state, type: 'all', query: '', sort: 'asc' }; selectYear('2026'); });
$('#back-top').addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
document.addEventListener('keydown', event => {
  if (event.key === '/' && !detailDialog.open && !aboutDialog.open && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); $('#search').focus(); $('#archive').scrollIntoView({ behavior: 'smooth' }); }
});
window.addEventListener('scroll', () => { $('#back-top').hidden = window.scrollY < 750; }, { passive: true });
window.addEventListener('popstate', () => {
  if (!state) return;
  const incoming = readState(location.search, years);
  if (detailDialog.open) detailDialog.close();
  state = incoming;
  render();
  if (state.event) openRecord(state.event, false);
});

$('#open-glossary').addEventListener('click', () => {
  const target = $('#glossary');
  target.hidden = !target.hidden;
  $('#open-glossary').innerHTML = `${target.hidden ? '查看' : '收起'}社区梗词典 <span>${target.hidden ? '→' : '↑'}</span>`;
  if (!target.hidden) target.innerHTML = data.community.glossary.map(entry => `<article class="glossary-entry"><h3>${esc(entry.title)}</h3><p>${esc(entry.meaning)}</p><small>首创时间：${entry.firstAppearance ? esc(entry.firstAppearance) : '未核验'}${entry.attestedBy ? ' · 资料用例截至 ' + esc(entry.attestedBy) : ''}</small><p class="glossary-note">${esc(entry.attestationNote)}</p>${(entry.sourceIds || []).map(id => data.community.sources.find(s => s.id === id)).filter(Boolean).map(sourceLink).join('')}</article>`).join('');
});

async function loadJSON(url) {
  // The production build embeds a research snapshot for direct, offline opening.
  const snapshot = document.getElementById('archive-data');
  if (snapshot) {
    embeddedData ||= JSON.parse(snapshot.textContent);
    if (Object.hasOwn(embeddedData, url)) return embeddedData[url];
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

try {
  const [versions, videos, community, discussions, coverManifest] = await Promise.all([
    loadJSON('research/timeline.zh-CN.json'), loadJSON('research/bilibili-timeline.zh-CN.json'), loadJSON('research/community-timeline.zh-CN.json'), loadJSON('research/discussions.zh-CN.json'), loadJSON('assets/covers/manifest.json').catch(() => ({})),
  ]);
  data = { versions, videos, community, discussions };
  covers = coverManifest;
  records = createRecords(versions, videos, community);
  years = [...new Set(records.map(row => row.year))].sort();
  state = readState(location.search, years);
  $('#version-count').textContent = versions.versions.length;
  $('#video-count').textContent = videos.videos.length;
  $('#community-count').textContent = community.topics.length;
  $('#total-count').textContent = records.length;
  $('#data-cutoff').textContent = `资料截至 ${versions.meta.asOf.replaceAll('-', '.')}`;
  $('#about-cutoff').textContent = versions.meta.asOf.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1 年 $2 月 $3 日');
  render();
  if (state.event) openRecord(state.event, false);
} catch (error) {
  console.error('时光档案加载失败', error);
  timeline.setAttribute('aria-busy', 'false');
  timeline.innerHTML = '<div class="empty-state"><h4>档案暂时没有载入</h4><p>请刷新重试。若直接打开了 HTML 文件，请用 npm run dev 启动本地网页。</p><a class="button button-dark" href="research/README.md">阅读原始资料 ↗</a></div>';
  $('#result-summary').textContent = '资料加载失败';
}
