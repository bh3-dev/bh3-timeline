export const TYPES = { milestone: '启航节点', version: '版本档案', video: '影像回忆', community: '社区记忆' };
export const YEAR_TITLES = { 2016: '初次启航', 2017: '旅程展开', 2018: '铭记这一刻', 2019: '走向更远的世界', 2020: '星与你的故事', 2021: '薪火与新生', 2022: '致那些闪耀的名字', 2023: '然后，向着明天', 2024: '翻开新的篇章', 2025: '相遇，依然继续', 2026: '十年，再次相聚' };

export function createRecords(versions, videos, community) {
  const rows = [
    ...versions.milestones.map(row => ({ ...row, type: 'milestone', summary: row.description })),
    ...versions.versions.map(row => ({ ...row, type: 'version', summary: row.storyAndFeatures.join(' · '), tags: row.characters.map(c => c.name) })),
    ...videos.videos.map(row => ({ ...row, type: 'video', title: row.displayTitle || row.title })),
    ...community.topics.map(row => ({ ...row, type: 'community' })),
  ];
  return rows.map(row => {
    const searchText = [row.title, row.version, row.summary, row.detail, row.creator?.name, ...(row.tags || []), ...(row.characters || []).map(c => typeof c === 'string' ? c : `${c.person} ${c.name}`), ...(row.majorEvents || []).map(e => e.title), ...(row.storyAndFeatures || []), row.categoryLabel, row.category].filter(Boolean).join(' ').toLowerCase();
    return { ...row, year: row.date.slice(0, 4), orderDate: row.sortDate || row.date, searchText };
  });
}

export function filterRecords(records, { year = 'all', type = 'all', query = '', sort = 'asc' } = {}) {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return records.filter(row => (year === 'all' || row.year === String(year)) && (type === 'all' || row.type === type) && terms.every(term => row.searchText.includes(term))).sort((a, b) => {
    const order = a.orderDate.localeCompare(b.orderDate) || a.type.localeCompare(b.type) || a.id.localeCompare(b.id);
    return sort === 'desc' ? -order : order;
  });
}

export function displayDate(row) {
  if (row.dateLabel) return row.dateLabel;
  return row.date.replaceAll('-', '.');
}

export function relatedRecords(record, records) {
  const versionIds = new Set((record.relatedVersions || []).map(v => v.id));
  const videoIds = new Set(record.relatedVideoIds || []);
  return records.filter(row => row.id !== record.id && (versionIds.has(row.id) || videoIds.has(row.id) || (record.type === 'version' && row.relatedVersions?.some(v => v.id === record.id))));
}

export function readState(search, years) {
  const params = new URLSearchParams(search);
  return {
    year: params.get('year') === 'all' || years.includes(params.get('year')) ? params.get('year') : '2016',
    type: ['all', 'version', 'video', 'community'].includes(params.get('type')) ? params.get('type') : 'all',
    query: (params.get('q') || '').slice(0, 200),
    sort: params.get('sort') === 'desc' ? 'desc' : 'asc',
    event: params.get('event'),
  };
}

export function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

export function safeLink(url) {
  try { const parsed = new URL(url); return ['https:', 'http:'].includes(parsed.protocol) ? escapeHTML(parsed.href) : '#'; } catch { return '#'; }
}
