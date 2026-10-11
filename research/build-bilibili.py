"""Join verified Bilibili snapshots, editorial notes and the existing CN timeline.

Run: python research/build-bilibili.py
Check saved outputs without writing: python research/build-bilibili.py --check
Uses only the Python standard library; no network requests.
"""

import argparse
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATEGORIES = {
    "official-animation": "官方动画／过场",
    "official-pv": "官方角色／版本PV",
    "official-song": "官方歌曲／演唱视频",
    "official-program": "官方节目／音乐会／纪录片",
    "render-mmd": "创作者MMD／渲染演示",
    "cv-song": "声优翻唱／原创曲",
    "fan-creation": "同人／鬼畜／MAD／手书",
    "community-program": "社区晚会",
}
OFFICIAL_MID = 27534330
CONTEXT_IDS = {"chuchusha-suoor", "mei-quit-original"}


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_index(rows, key):
    result = {}
    for row in rows:
        require(row[key] not in result, f"Duplicate {key}: {row[key]}")
        result[row[key]] = row
    return result


def build():
    timeline = read_json("timeline.zh-CN.json")
    editorial = read_json("bilibili-editorial.json")
    seeds = unique_index(read_json("bilibili-seeds.json"), "id")
    snapshots = unique_index(read_json("bilibili-metadata.json"), "seedId")
    entries = unique_index(editorial["videos"], "id")
    require(set(seeds) == set(entries) == set(snapshots), "Seeds, editorial and snapshots must contain the same IDs")
    versions = sorted(timeline["versions"], key=lambda row: row["date"])
    by_version = unique_index(versions, "version")
    cutoff = timeline["meta"]["asOf"]
    date.fromisoformat(cutoff)
    videos = []
    bvids = set()

    for seed_id, note in entries.items():
        raw = snapshots[seed_id]
        seed = seeds[seed_id]
        require(raw["status"] == "ok", f"Unverified video: {seed_id}")
        require(raw["bvid"] not in bvids, f"Duplicate BVID: {raw['bvid']}")
        bvids.add(raw["bvid"])
        require(seed.get("bvid", raw["bvid"]) == raw["bvid"], f"BVID mismatch: {seed_id}")
        require(seed.get("aid", raw["aid"]) == raw["aid"], f"AID mismatch: {seed_id}")
        published = datetime.fromisoformat(raw["publishedAt"])
        require(published.utcoffset().total_seconds() == 28800, f"Expected UTC+8: {seed_id}")
        require(published.date().isoformat() == raw["date"], f"Date mismatch: {seed_id}")
        require("2016-09-01" <= raw["date"] <= cutoff, f"Publication outside scope: {seed_id}")
        require(note["category"] in CATEGORIES, f"Unknown category: {seed_id}")
        require(not note["category"].startswith("official-") or raw["owner"]["mid"] == OFFICIAL_MID,
                f"Official category without official uploader: {seed_id}")
        require(raw["stats"]["view"] >= 0, f"Invalid views: {seed_id}")
        eligible = [version for version in versions if version["date"] <= raw["date"]]
        version_at_publication = None
        if eligible:
            current = eligible[-1]
            version_at_publication = {"id": current["id"], "version": current["version"], "date": current["date"]}
        related_versions = []
        for related in note.get("relatedVersions", []):
            version = by_version[related["version"]]
            related_versions.append({"id": version["id"], "version": version["version"],
                                     "date": version["date"], "relation": "editorial-content-link",
                                     "reason": related["reason"]})

        creator_kind = ("official" if raw["owner"]["mid"] == OFFICIAL_MID else
                        "render-creator" if note["category"] == "render-mmd" else
                        "voice-actor" if note["category"] == "cv-song" else "community-creator")
        sources = [
            {"url": raw["url"], "kind": "original-video", "supports": "原稿、简介、创作署名及内容依据"},
            {"url": raw["apiUrl"], "kind": "bilibili-public-metadata", "accessedAt": raw["fetchedAt"],
             "supports": "BV／AV、作者UID、发布时间、累计数据及可取得的历史排名"},
            *note.get("extraSources", []),
        ]
        heat = [{"kind": "cumulative-views", "value": raw["stats"]["view"], "asOf": raw["fetchedAt"]}]
        historical_rank = raw["stats"].get("his_rank", 0) or None
        if historical_rank:
            heat.append({"kind": "historical-highest-sitewide-rank", "value": historical_rank})
        if seed_id in {"judah-disco", "annals"}:
            heat.append({"kind": "official-contest-award", "value": "三周年影像大赏" +
                         ("一等奖" if seed_id == "judah-disco" else "特等奖"),
                         "sourceUrl": note["extraSources"][0]["url"]})

        video = {
            "id": seed_id, "date": raw["date"], "datePrecision": "day", "publishedAt": raw["publishedAt"],
            "title": raw["title"], "displayTitle": note["displayTitle"], "category": note["category"],
            "bvid": raw["bvid"], "aid": raw["aid"], "url": raw["url"],
            "creator": {**raw["owner"], "url": f"https://space.bilibili.com/{raw['owner']['mid']}", "kind": creator_kind},
            "durationSeconds": raw["durationSeconds"], "summary": note["summary"],
            "characters": note["characters"], "tags": note["tags"],
            "priority": "context" if seed_id in CONTEXT_IDS else "featured" if note.get("featured") else "standard",
            "versionAtPublication": version_at_publication, "relatedVersions": related_versions,
            "relatedVideoIds": note.get("relatedVideoIds", []),
            "statsSnapshot": {"asOf": raw["fetchedAt"], "views": raw["stats"]["view"],
                              "likes": raw["stats"]["like"], "coins": raw["stats"]["coin"],
                              "favorites": raw["stats"]["favorite"], "shares": raw["stats"]["share"],
                              "danmaku": raw["stats"]["danmaku"], "comments": raw["stats"]["reply"],
                              "historicalHighestSitewideRank": historical_rank},
            "heatEvidence": heat, "sources": sources,
        }
        for key in ("music", "creditNote", "eventDate"):
            if key in note:
                video[key] = note[key]
        if "eventDate" in video:
            date.fromisoformat(video["eventDate"])
            require(video["eventDate"] <= video["date"], f"Event after upload: {seed_id}")
        if creator_kind == "render-creator":
            video["creator"]["identityNote"] = "原稿确认Scyrax账号与渲染创作；媒体报道将该系列与时任技术总监贺甲关联，任职归属采用二手报道，不标为官号稿件。"
            video["creator"]["reportedIdentity"] = note["reportedIdentity"]
        for related_id in video["relatedVideoIds"]:
            require(related_id in entries and related_id != seed_id, f"Invalid related video: {seed_id}/{related_id}")
        videos.append(video)

    videos.sort(key=lambda row: (row["publishedAt"], row["id"]))
    by_id = unique_index(videos, "id")
    unique_index(editorial["topics"], "id")
    topics = []
    for topic in editorial["topics"]:
        require(topic["videoIds"] and len(set(topic["videoIds"])) == len(topic["videoIds"]), f"Invalid topic: {topic['id']}")
        require(all(key in by_id for key in topic["videoIds"]), f"Unknown topic video: {topic['id']}")
        anchors = sorted((by_id[key] for key in topic["videoIds"]), key=lambda row: (row["publishedAt"], row["id"]))
        topics.append({**topic, "anchorDate": anchors[0]["date"], "anchorVideoId": anchors[0]["id"],
                       "dateMeaning": "earliest-selected-video-publication-not-topic-origin"})

    snapshots_by_time = sorted(videos, key=lambda row: datetime.fromisoformat(row["statsSnapshot"]["asOf"]))
    return {
        "schemaVersion": 1,
        "meta": {
            "title": "崩坏3 B站视频与话题时间轴（精选）", "region": "CN", "timezone": "Asia/Shanghai",
            "displayStart": "2016-09", "asOf": cutoff, "status": "first-research-pass",
            "videoCount": len(videos), "topicCount": len(topics),
            "categoryCounts": dict(sorted(Counter(row["category"] for row in videos).items())),
            "categories": CATEGORIES, "versionTimelineFile": "timeline.zh-CN.json",
            "snapshotRange": {"earliest": snapshots_by_time[0]["statsSnapshot"]["asOf"],
                              "latest": snapshots_by_time[-1]["statsSnapshot"]["asOf"]},
            "scope": "2016年9月至截止日的官方动画、代表性PV／歌曲／节目、Scyrax渲染演示、声优歌曲及社区二创；精选而非全量排行。",
            "selectionNotes": [
                "优先原作者／官号原稿。兼顾累计播放、可取得的全站历史最高排名、官方获奖记录与话题代表性。",
                "context条目用于解释二创原作到声优翻唱的关系，不以当前播放量断言其独立成为热门。",
                "date／publishedAt来自原稿pubdate，按北京时间显示；eventDate仅在另有演出日期证据时填写。",
                "累计播放量是抓取时快照，不能当作发布当年的播放量、当年热度排行或唯一观众数。",
                "历史最高排名仅采用接口his_rank正值；0转换为null，表示本次未取得，不能断言从未上榜。",
                "versionAtPublication按既有国服更新日期推算；relatedVersions为人工内容关联，可能指向后来更新的版本。",
                "话题anchorDate是本资料所选代表视频中的最早发布时间，不是梗／话题首次出现日期。",
                "creator.kind区分发布账号；官号音乐可以由声优演唱，外邀歌手不自动归为角色CV。",
                "优先级、摘要、角色标签及话题编排属于编辑选择，不是B站官方分类或排行。",
            ],
            "knownGaps": [
                "尚未建立逐年同口径热门榜；2024—2026社区二创及更早的新春会／生日会仍可继续补选。",
                "Scyrax原稿与系列已核验；贺甲及任职归属仅采用媒体报道，尚未补入一手身份来源。",
                "未保存评论文本／逐日热榜，不据此断言梗的首创者、出圈首日或传播因果。",
            ],
            "refresh": "powershell -File research/collect-bilibili.ps1 -Refresh",
            "build": "python research/build-bilibili.py",
        },
        "videos": videos, "topics": topics,
    }


def escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def link(video):
    return f"[{escape(video['displayTitle'])}]({video['url']})"


def markdown(data):
    meta = data["meta"]
    by_id = unique_index(data["videos"], "id")
    lines = [
        "# 崩坏3 B站视频与话题时间轴（精选）", "",
        f"展示范围为 **2016年9月至{meta['asOf']}**。本轮整理 **{meta['videoCount']}条视频、{meta['topicCount']}组话题**，供十周年网页作为版本时间轴之外的视频与社区内容层。优先使用官号、声优或创作者原稿。", "",
        "配套数据：[网页时间轴JSON](bilibili-timeline.zh-CN.json)、[原稿元数据快照](bilibili-metadata.json)、[人工编辑信息](bilibili-editorial.json)。", "",
        "## 日期、热度与分类口径", "",
        "表内日期是B站原稿的北京时间发布时间。累计播放量取自各条抓取时快照；它不是当年播放量或当年热门榜。‘最高第N’仅表示接口可取得的全站历史最高排名；未取得排名时不写排名，不代表没有上过榜。具体抓取时间、点赞、投币、收藏等保存在JSON中。", "",
        "版本关系分为‘发布时国服版本’与‘内容关联版本’。例如《女王降临》在2.3期间发布，人物线可关联后来2.5上线的空之律者；版本PV也通常早于更新日。不能把视频发布时间改成装甲上线日。", "",
        "官方歌曲与声优歌曲按发布账号／创作性质区分，演唱者另外记录。周深、蔡健雅、黄龄、阿云嘎等外邀歌手不直接标成角色CV。Scyrax系列按作者MMD／渲染演示收录；[游戏葡萄的媒体报道（小米游戏中心转载）](https://game.xiaomi.com/viewpoint/1393220466_1678951710297_100)将该系列与时任米哈游技术总监贺甲关联。原稿作者、日期与数据已核验，任职归属标为二手来源。", "",
        "| 分类 | 条数 |", "| --- | ---: |",
    ]
    for category, label in CATEGORIES.items():
        lines.append(f"| {label} | {meta['categoryCounts'].get(category, 0)} |")
    lines += ["", "## 两条已核对的二创 → 声优翻唱关系", "",
              f"- **处处傻**：{link(by_id['chuchusha-suoor'])}（2020-02-07）→ {link(by_id['chuchusha-hualing'])}（2020-03-28）。花玲简介明确指向av87241880并感谢授权。原稿当前UP名为猫山王豆浆，简介署名邻家索尔；这是《处处吻》的二创填词翻唱。",
              f"- **芽衣什么的不干啦**：{link(by_id['mei-quit-original'])}（2020-03-02）→ {link(by_id['mei-quit-cv'])}（2020-03-15）。声优稿简介列出av93095741为本家；当前发布账号名为爆裂菊是也。", "",
              "## 按年排列的原稿", "",
              "★为建议主时间轴突出展示的条目；‘来源补充’为二创传播链原稿。其他条目可放在当年展开列表中。入选兼顾播放量、历史排名、获奖与时间轴叙事，并非同口径排名。", ""]
    current_year = None
    for video_index, video in enumerate(data["videos"]):
        year = video["date"][:4]
        if year != current_year:
            current_year = year
            lines += [f"### {year}年", "", "| 发布时间 | 视频／发布者 | 类别与记录理由 | 抓取时热度 | 版本关系 |",
                      "| --- | --- | --- | --- | --- |"]
        marker = "★ " if video["priority"] == "featured" else ""
        if video["priority"] == "context":
            marker = "来源补充："
        heat = f"{video['statsSnapshot']['views'] / 10000:.1f}万播放"
        if video["statsSnapshot"]["historicalHighestSitewideRank"]:
            heat += f"；最高第{video['statsSnapshot']['historicalHighestSitewideRank']}"
        current = video["versionAtPublication"]
        version_text = f"发布时{current['version']}" if current else "全平台公测前"
        if video["relatedVersions"]:
            version_text += "；关联" + "、".join(row["version"] for row in video["relatedVersions"])
        summary = video["summary"]
        if "eventDate" in video:
            summary += f" [演出日期依据]({video['sources'][-1]['url']})。"
        if video["id"] in {"judah-disco", "annals"}:
            summary += f" [获奖页]({video['sources'][-1]['url']})。"
        lines.append(f"| {video['date']} | {marker}{link(video)}<br>{escape(video['creator']['name'])} | "
                     f"{CATEGORIES[video['category']]}；{escape(summary)} | {heat} | {version_text} |")
        # Keep blank lines between consecutive year sections, including after the final one.
        next_index = video_index + 1
        if next_index == len(data["videos"]) or data["videos"][next_index]["date"][:4] != year:
            lines.append("")

    lines += ["## 可串联的话题", "",
              "下面的日期是**本资料所选代表视频中的最早发布时间**，供网页定位入口，不是话题／梗的起源日期。话题可以跨年，也可以共享一个视频。", ""]
    for topic in data["topics"]:
        lines += [f"### {topic['title']}", "", f"代表视频起点：{topic['anchorDate']}。{topic['summary']}", "",
                  " → ".join(link(by_id[key]) for key in topic["videoIds"]), ""]

    lines += ["## 网页数据接入与后续补录", "",
              "JSON的`videos`可直接按`publishedAt`排序，并用`category`、`characters`、`tags`过滤。`title`保留原稿标题，`displayTitle`用于卡片；`creator.mid`比账号昵称更适合关联改名后的作者。`priority`区分主节点、普通节点和来源补充。", "",
              "`versionAtPublication.id`与既有`timeline.zh-CN.json`的版本ID一致；`relatedVersions`只表示编辑内容关联，原因逐条保存。`relatedVideoIds`保存原作／翻唱、动画／歌曲、晚会／单品的关系。`topics.videoIds`复用视频，不需要复制视频卡片。", "",
              "`date`始终保持视频发布时间。若网页还展示演出发生日，使用可选的`eventDate`，例如星火流音为2021-10-05，而本稿`date`为2021-11-05。", "",
              "原稿简介完整保存在内部核验快照中；网页宜使用已编辑的摘要和外链。更新数据时先采集，再构建：", "",
              "```powershell", "powershell -File research/collect-bilibili.ps1 -Refresh", "python research/build-bilibili.py",
              "python research/build-bilibili.py --check", "```", "",
              "不带`-Refresh`时复用成功快照，只采集新增或失败条目。添加视频需同步编辑`bilibili-seeds.json`与`bilibili-editorial.json`；构建脚本检查重复BV、日期、作者类别、版本ID及话题引用，不允许未核实原稿混入成品。", "",
              "本轮仍有可补范围：逐年同口径热门榜、2024—2026更多社区二创、历年新春会／生日会，以及Scyrax任职身份的一手来源。未收集评论文本和逐日热榜，因此不标注梗的首创者、出圈首日或未经证实的传播因果。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate inputs and compare outputs without writing")
    args = parser.parse_args()
    data = build()
    outputs = {
        "bilibili-timeline.zh-CN.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        "bilibili.md": markdown(data),
    }
    for name, content in outputs.items():
        if args.check:
            require((ROOT / name).exists() and (ROOT / name).read_text(encoding="utf-8-sig") == content,
                    f"Output missing or stale: {name}; run the builder")
        else:
            (ROOT / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"{'Checked' if args.check else 'Built'} {len(data['videos'])} videos and {len(data['topics'])} topics")


if __name__ == "__main__":
    main()
