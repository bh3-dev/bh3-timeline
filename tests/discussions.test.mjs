import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRecords, safeLink } from '../src/timeline.js';
const read = async name => JSON.parse((await readFile(new URL('../' + name, import.meta.url), 'utf8')).replace(/^\uFEFF/, ''));
const [versions, videos, community, discussions] = await Promise.all(['research/timeline.zh-CN.json', 'research/bilibili-timeline.zh-CN.json', 'research/community-timeline.zh-CN.json', 'research/discussions.zh-CN.json'].map(read));
const records = createRecords(versions, videos, community);
const snapshots = {};
for (const [id, source] of Object.entries(discussions.sources)) snapshots[id] = await read(source.cache);
const unescape = text => text.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');

test('Every timeline node has three comments by distinct platform users', () => {
  assert.equal(records.length, 168);
  assert.deepEqual(Object.keys(discussions.nodes).sort(), records.map(r => r.id).sort());
  for (const row of records) {
    const entry = discussions.nodes[row.id];
    assert.ok(entry.context.length > 8, row.id);
    assert.equal(entry.quotes.length, 3, row.id);
    assert.equal(new Set(entry.quotes.map(q => discussions.sources[q.sourceId].platform + ':' + q.userId)).size, 3, row.id);
  }
  assert.equal(discussions.meta.quoteCount, 504);
  assert.equal(discussions.meta.uniqueCommentCount, new Set(Object.values(discussions.nodes).flatMap(n => n.quotes.map(q => q.id))).size);
});

test('Every attributed excerpt matches its saved public source, user and timestamp', () => {
  for (const [id, entry] of Object.entries(discussions.nodes)) for (const quote of entry.quotes) {
    const snapshot = snapshots[quote.sourceId];
    const original = snapshot.comments.find(c => snapshot.platform + ':' + c.id === quote.id);
    assert.ok(original, id + ' ' + quote.id);
    assert.ok(unescape(original.text).includes(quote.text), id + ' exact excerpt');
    assert.equal(quote.username, original.username, id);
    assert.equal(quote.userId, original.userId, id);
    assert.equal(quote.publishedAt, original.publishedAt, id);
    assert.ok(Number.isFinite(Date.parse(quote.publishedAt)), id);
    assert.ok(quote.publishedAt.slice(0, 10) <= discussions.meta.asOf, id);
    assert.equal(quote.url, original.sourceURL, id);
    assert.notEqual(safeLink(quote.url), '#', id);
    assert.ok(!original.official, id + ' user, not official announcement');
  }
});

test('Version discussion sources identify the actual version or explicitly related posts', () => {
  for (const row of records.filter(r => r.type === 'version' && r.id !== 'cn-1.0')) {
    assert.ok(discussions.nodes[row.id].quotes.some(q => discussions.sources[q.sourceId].title.includes(row.title)), row.id);
  }
  assert.ok(discussions.nodes['pre-registration'].context.includes('未取得'));
  assert.ok(discussions.nodes['wuxueyou'].context.includes('未取得'));
  assert.ok(discussions.nodes['bunny-controversy'].context.includes('后来'));
  for (const node of ['ten-years-memory', 'cn-9.1']) {
    assert.ok(discussions.nodes[node].quotes.every(q => !/UID|回归码|\d{8,}/i.test(q.text)));
  }
});
