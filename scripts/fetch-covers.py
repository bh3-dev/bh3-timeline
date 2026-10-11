"""Cache original Bilibili video covers; research statistics remain unchanged."""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = json.loads((ROOT / 'research/bilibili-timeline.zh-CN.json').read_text(encoding='utf-8-sig'))['videos']
OUT = ROOT / 'assets/covers'
OUT.mkdir(parents=True, exist_ok=True)


def download(video):
    api = 'https://api.bilibili.com/x/web-interface/view?bvid=' + video['bvid']
    try:
        req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
        response = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if response['code'] != 0:
            raise ValueError(response['code'])
        url = response['data']['pic'].replace('http://', 'https://')
        content = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read()
        name = video['id'] + Path(url.split('?')[0]).suffix
        (OUT / name).write_bytes(content)
        return video['id'], {'path': 'assets/covers/' + name, 'source': url, 'api': api}
    except Exception as error:
        return video['id'], {'error': str(error), 'api': api}


with ThreadPoolExecutor(max_workers=4) as pool:
    manifest = dict(pool.map(download, VIDEOS))
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'cached': sum('path' in v for v in manifest.values()), 'total': len(manifest)}, ensure_ascii=False))
