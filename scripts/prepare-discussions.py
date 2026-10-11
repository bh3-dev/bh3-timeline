"""Compile exact, attributed excerpts from public comment caches and reviewed selections."""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'research/discussion-sources'
SELECTIONS = ROOT / 'research/discussion-selections.json'
AS_OF = '2026-10-11'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

versions = load(ROOT / 'research/timeline.zh-CN.json')
videos = load(ROOT / 'research/bilibili-timeline.zh-CN.json')
community = load(ROOT / 'research/community-timeline.zh-CN.json')
records = versions['milestones'] + versions['versions'] + videos['videos'] + community['topics']
cache = {}
for file in CACHE.glob('*.json'):
    item = load(file)
    if isinstance(item, dict) and item.get('status') == 'ok' and item.get('comments'):
        cache[file.stem] = item

def visible(text):
    return re.sub(r'\[[^\]]*\]|https?://\S+|\s+', '', text)

def eligible(comment, source):
    text = html.unescape(comment['text'])
    return (comment.get('userId') != source.get('authorId')
            and not comment.get('official')
            and '注销' not in comment['username']
            and comment['publishedAt'][:10] <= AS_OF
            and len(visible(text)) >= 8
            and not re.search(r'兑换码|军功|抽奖|互填|求个三连|求三连|求关注|点赞.*置顶|死妈|没媽|妓女|绿帽龟|https?://', text)
            and len(re.findall(r'[A-Za-z]', visible(text))) < len(visible(text)) * .65)

def excerpt(text):
    text = html.unescape(text).strip()
    # Reply headers contain the addressee, not the words of the selected author.
    if text.startswith('回复 @') and (match := re.search(r'[:：]', text)):
        text = text[match.end():].lstrip()
    if len(text) <= 76:
        return text
    piece = text[:76]
    if piece.rfind('[') > piece.rfind(']'):
        piece = piece[:piece.rfind('[')].rstrip()
    boundary = max(piece.rfind(mark) for mark in ['。', '！', '？', '\n'])
    if boundary >= 24:
        return piece[:boundary + 1].rstrip()
    # The ellipsis is rendered outside the quote; the stored text is an exact substring.
    return piece.rstrip()

def choose(keys, record):
    candidates = []
    for key in keys:
        source = cache[key]
        for comment in source['comments']:
            if not eligible(comment, source):
                continue
            days = (dt.date.fromisoformat(comment['publishedAt'][:10]) - dt.date.fromisoformat(record['date'][:10] if len(record['date']) >= 10 else record['date'] + '-01')).days
            score = (45 if not comment.get('replyTo') else 0) + min(len(visible(comment['text'])), 65) / 4 + (25 if -21 <= days <= 70 else 0)
            candidates.append((score, key, comment))
    candidates.sort(key=lambda row: -row[0])
    chosen, users = [], set()
    for _, key, comment in candidates:
        identity = cache[key]['platform'] + ':' + comment['userId']
        if identity in users:
            continue
        users.add(identity)
        chosen.append({'source': key, 'comment': comment['id'], 'excerpt': excerpt(comment['text'])})
        if len(chosen) == 3:
            break
    return chosen

if '--draft' in sys.argv:
    selections = load(SELECTIONS) if SELECTIONS.exists() else {}
    for record in records:
        if record['id'] not in selections and record['id'] in cache:
            source = cache[record['id']]
            relation = '前瞻节目' if source.get('sourceHint', {}).get('relation') == 'version-program' else '宣传 PV'
            context = f"本版本{relation}评论区的玩家留言。" if record['id'].startswith('cn-') else '视频原稿评论区的用户留言。'
            selections[record['id']] = {'context': context, 'quotes': choose([record['id']], record)}
    SELECTIONS.write_text(json.dumps(selections, ensure_ascii=False, indent=2), encoding='utf-8')

selections = load(SELECTIONS)
sources, nodes = {}, {}
for record in records:
    selected = selections.get(record['id'])
    if not selected:
        continue
    quotes = []
    for pick in selected['quotes']:
        source = cache[pick['source']]
        comment = next(c for c in source['comments'] if c['id'] == pick['comment'])
        text = pick.get('excerpt') or excerpt(comment['text'])
        assert text in html.unescape(comment['text']), (record['id'], text)
        assert comment['publishedAt'][:10] <= AS_OF, record['id']
        source_id = pick['source']
        sources[source_id] = {k: source[k] for k in ['title', 'url', 'platform', 'checkedAt', 'publishedAt', 'author'] if k in source}
        sources[source_id]['cache'] = 'research/discussion-sources/' + source_id + '.json'
        quotes.append({
            'id': source['platform'] + ':' + comment['id'], 'sourceId': source_id,
            'username': comment['username'], 'userId': comment['userId'],
            'publishedAt': comment['publishedAt'], 'text': text,
            'excerpted': text != html.unescape(comment['text']).strip(),
            'url': comment['sourceURL'],
            **({'position': str(comment['position'])} if comment.get('position') else {}),
            **({'dateBasis': comment['dateBasis']} if comment.get('dateBasis') else {}),
        })
    assert len({sources[q['sourceId']]['platform'] + ':' + q['userId'] for q in quotes}) == len(quotes), record['id']
    nodes[record['id']] = {'context': selected['context'], 'quotes': quotes}

result = {
    'meta': {
        'asOf': AS_OF, 'recordCount': len(records), 'coveredCount': len(nodes),
        'quoteCount': sum(len(n['quotes']) for n in nodes.values()),
        'uniqueCommentCount': len({q['id'] for n in nodes.values() for q in n['quotes']}),
        'policy': '真实署名原文节选；不改写成用户口吻，不代表全体玩家意见。保留不同态度，按实际留言时间展示。同一原稿可关联多个节点，未作为多条独立证据统计。',
        'timeZone': 'Asia/Shanghai',
    }, 'sources': sources, 'nodes': nodes,
}
(ROOT / 'research/discussions.zh-CN.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
missing = [r['id'] for r in records if r['id'] not in nodes or len(nodes[r['id']]['quotes']) < 3]
print(json.dumps({'meta': result['meta'], 'incomplete': missing}, ensure_ascii=False, indent=2))
(ROOT / 'verification').mkdir(exist_ok=True)
(ROOT / 'verification/discussion-review.txt').write_text('\n\n'.join(record['id'] + ' ' + record['title'] + '\n' + '\n'.join(f"  {q['sourceId']} / {q['id']} / {q['username']} / {q['publishedAt'][:10]} / {q['text'].replace(chr(10), ' / ')}" for q in nodes.get(record['id'], {}).get('quotes', [])) for record in records), encoding='utf-8')
