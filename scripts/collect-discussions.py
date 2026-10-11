"""Read public community endpoints; cache auditable source text, never invent quotes."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'research/discussion-sources'
CACHE.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec='seconds')


def load(name):
    return json.loads((ROOT / 'research' / name).read_text(encoding='utf-8-sig'))


def request(url):
    time.sleep(0.2)
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20).read().decode('utf-8')


def wiki_version(version):
    url = 'https://wiki.biligame.com/bh3/api.php?' + urllib.parse.urlencode({'action': 'parse', 'page': version['version'] + 'PV', 'prop': 'wikitext', 'format': 'json'})
    key = version['id']
    filename = CACHE / (key + '-index.json')
    if filename.exists():
        return key, json.loads(filename.read_text(encoding='utf-8'))
    try:
        payload = json.loads(request(url))
        text = (payload.get('parse', {}).get('wikitext') or {}).get('*', '')
        bvids = re.findall(r'BV[0-9A-Za-z]{10}', text)
        aids = re.findall(r'(?:aid=|\|av)(\d+)', text)
        result = {'index': url, 'checkedAt': NOW, 'bvid': bvids[0] if bvids else None, 'aid': int(aids[0]) if aids else None, 'wikitext': text}
        if not result['bvid'] and not result['aid']:
            result['error'] = payload.get('error', {}).get('info', 'No embedded video')
    except Exception as error:
        result = {'index': url, 'checkedAt': NOW, 'error': str(error)}
    filename.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return key, result


def bilibili_source(item):
    key, hint = item
    filename = CACHE / (key + '.json')
    if filename.exists():
        return key, json.loads(filename.read_text(encoding='utf-8'))
    result = {'platform': 'Bilibili', 'checkedAt': NOW, 'sourceHint': hint, 'comments': []}
    try:
        article = hint.get('articleId')
        query = ('bvid=' + hint['bvid']) if hint.get('bvid') else ('aid=' + str(hint.get('aid', '')))
        metadata_url = ('https://api.bilibili.com/x/article/viewinfo?id=' + str(article)) if article else ('https://api.bilibili.com/x/web-interface/view?' + query)
        metadata = json.loads(request(metadata_url))
        if metadata.get('code') != 0:
            raise ValueError('Video API ' + str(metadata.get('code')))
        video = metadata['data']
        if article:
            result.update({'title': video['title'], 'articleId': article, 'author': video['author_name'], 'authorId': str(video['mid']), 'url': f'https://www.bilibili.com/read/cv{article}/', 'metadataURL': metadata_url})
        else:
            result.update({'title': video['title'], 'bvid': video['bvid'], 'aid': video['aid'], 'author': video['owner']['name'], 'authorId': str(video['owner']['mid']), 'url': 'https://www.bilibili.com/video/' + video['bvid'] + '/', 'publishedAt': dt.datetime.fromtimestamp(video['pubdate'], dt.timezone(dt.timedelta(hours=8))).isoformat(), 'metadataURL': metadata_url})
        reply_url = f"https://api.bilibili.com/x/v2/reply?type={12 if article else 1}&oid={article or video['aid']}&sort=2&pn=1"
        result['commentAPI'] = reply_url
        payload = json.loads(request(reply_url))
        if payload.get('code') != 0:
            raise ValueError('Reply API ' + str(payload.get('code')))
        data = payload.get('data') or {}
        result['page'] = data.get('page')
        seen = set()
        def add(reply, is_reply=False):
            if reply['rpid'] in seen:
                return
            seen.add(reply['rpid'])
            result['comments'].append({'id': str(reply['rpid']), 'userId': str(reply['member']['mid']), 'username': reply['member']['uname'], 'publishedAt': dt.datetime.fromtimestamp(reply['ctime'], dt.timezone(dt.timedelta(hours=8))).isoformat(), 'text': reply['content']['message'], 'likes': reply['like'], 'replyTo': str(reply.get('parent') or '') if is_reply else None, 'sourceURL': result['url'] + '#reply' + str(reply['rpid'])})
        for reply in (data.get('replies') or []) + (data.get('hots') or []) + [r for r in (data.get('top') or {}).values() if isinstance(r, dict) and 'rpid' in r]:
            add(reply)
            for child in reply.get('replies') or []:
                add(child, True)
        result['status'] = 'ok' if result['comments'] else 'no-readable-comments'
    except Exception as error:
        result['status'] = 'unavailable'
        result['error'] = str(error)
    filename.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return key, result


parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['versions', 'videos', 'extra'])
args = parser.parse_args()
if args.phase == 'versions':
    versions = load('timeline.zh-CN.json')['versions']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        indexes = dict(pool.map(wiki_version, versions))
    (ROOT / 'research/discussion-version-index.json').write_text(json.dumps(indexes, ensure_ascii=False, indent=2), encoding='utf-8')
    sources = [(key, item) for key, item in indexes.items() if item.get('bvid') or item.get('aid')]
elif args.phase == 'videos':
    sources = [(video['id'], {'bvid': video['bvid'], 'aid': video['aid']}) for video in load('bilibili-timeline.zh-CN.json')['videos']]
else:
    sources = list(load('discussion-extra-index.json').items())
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(bilibili_source, sources))
summary = {'phase': args.phase, 'sources': len(results), 'readable': sum(r.get('status') == 'ok' for r in results.values()), 'comments': sum(len(r['comments']) for r in results.values()), 'unavailable': {k: r.get('error', r.get('status')) for k, r in results.items() if r.get('status') != 'ok'}}
print(json.dumps(summary, ensure_ascii=False, indent=2))
