import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRecords, filterRecords, displayDate, readState, relatedRecords, escapeHTML, safeLink } from '../src/timeline.js';

const read = async name => JSON.parse((await readFile(new URL(`../research/${name}`, import.meta.url), 'utf8')).replace(/^\uFEFF/, ''));
const versions = await read('timeline.zh-CN.json');
const videos = await read('bilibili-timeline.zh-CN.json');
const community = await read('community-timeline.zh-CN.json');
const records = createRecords(versions, videos, community);
const years = [...new Set(records.map(r => r.year))].sort();

test('all researched records are preserved and dated within the archive range', () => {
  assert.equal(records.length, 168);
  assert.equal(new Set(records.map(r => r.id)).size, records.length);
  assert.equal(filterRecords(records)[0].id, 'pre-registration');
  assert.ok(records.every(r => r.year >= '2016' && r.year <= '2026'));
  assert.equal(records.filter(r => r.type === 'version').length, 82);
  assert.equal(records.filter(r => r.type === 'video').length, 56);
  assert.equal(records.filter(r => r.type === 'community').length, 27);
});
test('search crosses title, characters, activities and creators; filters combine', () => {
  assert.ok(filterRecords(records, { query: '琪亚娜', type: 'version' }).some(r => r.version === '1.0'));
  assert.ok(filterRecords(records, { query: '十周年庆', type: 'version' }).some(r => r.version === '9.1'));
  assert.ok(filterRecords(records, { query: 'Scyrax', type: 'video' }).length >= 3);
  assert.ok(filterRecords(records, { query: '雷电 芽衣', type: 'video', year: '2016' }).some(r => r.id === 'mei-pv-2016'));
  assert.equal(filterRecords(records, { year: '2016', type: 'community' }).length, 0);
  assert.equal(filterRecords(records, { query: '不存在的随机关键词-1234567' }).length, 0);
});
test('month and period labels are not promoted to exact event days', () => {
  const pre = records.find(r => r.id === 'pre-registration');
  assert.equal(displayDate(pre), '2016.09');
  assert.ok(pre.description.includes('不是预登录首日'));
  for (const row of community.topics) assert.equal(displayDate(row), row.dateLabel);
  assert.equal(displayDate(records.find(r => r.id === 'white-river')), '2019年底（3.6期间）');
});
test('sorting reverses chronology and does not mutate the research data', () => {
  const asc = filterRecords(records), desc = filterRecords(records, { sort: 'desc' });
  assert.deepEqual(desc.map(r => r.id), asc.map(r => r.id).reverse());
  assert.equal(versions.versions[0].id, 'cn-1.0');
});
test('related events connect version archives to videos and community nodes', () => {
  const version = records.find(r => r.id === 'cn-1.0');
  assert.ok(relatedRecords(version, records).some(r => r.id === 'mei-pv-2016'));
  assert.ok(relatedRecords(records.find(r => r.id === 'mei-pv-2016'), records).some(r => r.id === 'cn-1.0'));
  for (const row of community.topics) assert.ok(row.sourceIds.every(id => community.sources.some(s => s.id === id)));
});
test('shared URLs restore filters safely and invalid state falls back', () => {
  assert.deepEqual(readState('?year=2026&type=video&q=十周年&sort=desc&event=cn-9.1', years), { year: '2026', type: 'video', query: '十周年', sort: 'desc', event: 'cn-9.1' });
  assert.deepEqual(readState('?year=1900&type=wrong&sort=bad', years), { year: '2016', type: 'all', query: '', sort: 'asc', event: null });
  assert.equal(safeLink('javascript:alert(1)'), '#');
  assert.equal(escapeHTML('<img onerror="alert(1)">'), '&lt;img onerror=&quot;alert(1)&quot;&gt;');
});
