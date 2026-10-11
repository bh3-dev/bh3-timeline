"""Build the curated community layer without network access.

Run: python research/build-community.py
Check saved outputs: python research/build-community.py --check
"""

import argparse
import copy
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
CATEGORIES = {
    "meme": "梗与复读",
    "controversy": "运营与内容争议",
    "gameplay": "玩法与养成话题",
    "story-discussion": "剧情与角色讨论",
    "community-culture": "社区文化与回忆",
}
GRADES = {
    "documented": "事件可核对",
    "attested": "讨论有用例",
    "contextual": "背景定位，待补原帖",
}
ACCESS = {
    "full-text": "已读正文",
    "page-metadata": "页面标题与时间可读",
    "search-index-only": "仅搜索索引可读",
    "reference-unread": "原帖入口，正文未读",
}
BASES = {
    "reported-event": "同期报道或公告记载的事件日",
    "discussion-published": "代表性讨论或用例的发布时间",
    "official-response": "官方回应或处理节点",
    "announcement": "前瞻或活动公告节点",
    "version-context": "关联版本或剧情的背景时间",
    "approximate-period": "约略时期",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def index(rows, key="id"):
    result = {}
    for row in rows:
        require(row[key] not in result, f"Duplicate {key}: {row[key]}")
        result[row[key]] = row
    return result


def normalize_date(value):
    require(bool(re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value)), f"Invalid date: {value}")
    normalized = value + "-01" if len(value) == 7 else value
    date.fromisoformat(normalized)
    return normalized


def validate(data, official, bili):
    require(data["schemaVersion"] == 1, "Unsupported schema")
    cutoff = data["meta"]["asOf"]
    date.fromisoformat(cutoff)
    require(cutoff == official["meta"]["asOf"], "Community/official cutoff mismatch")
    sources = index(data["sources"])
    topics = index(data["topics"])
    versions = index(official["versions"], "version")
    videos = index(bili["videos"])
    all_rows = data["topics"] + data["glossary"] + data["candidates"]
    index(all_rows)
    require(len(set(s["url"] for s in sources.values())) == len(sources), "Duplicate source URLs")
    for source in sources.values():
        parts = urlparse(source["url"])
        require(parts.scheme == "https" and parts.netloc, f"Invalid source URL: {source['id']}")
        require(source["access"] in ACCESS, f"Unknown access: {source['id']}")
        require(source["checkedAt"] <= cutoff, f"Future source check: {source['id']}")
        if source["publicationDate"]:
            date.fromisoformat(source["publicationDate"])
            require(source["publicationDate"] <= cutoff, f"Future publication: {source['id']}")
    for row in all_rows:
        require(set(row["sourceIds"]) <= sources.keys(), f"Unknown source: {row['id']}")
        require(len(row["sourceIds"]) == len(set(row["sourceIds"])), f"Repeated source: {row['id']}")
    for row in topics.values():
        anchor = normalize_date(row["date"])
        require(data["meta"]["displayStart"] <= row["date"] <= cutoff, f"Outside range: {row['id']}")
        require(row["category"] in CATEGORIES, f"Unknown category: {row['id']}")
        require(row["evidenceGrade"] in GRADES, f"Unknown evidence grade: {row['id']}")
        require(row["dateBasis"] in BASES, f"Unknown date basis: {row['id']}")
        require(row["datePrecision"] in {"day", "month", "period"}, f"Unknown precision: {row['id']}")
        require(row["datePrecision"] != "day" or len(row["date"]) == 10, f"False day precision: {row['id']}")
        require(bool(row["dateNote"] and row["caveat"] and row["sourceIds"]), f"Missing evidence note: {row['id']}")
        require(any(sources[s]["access"] != "reference-unread" for s in row["sourceIds"]), f"Unread-only claim: {row['id']}")
        require(set(row["relatedVersions"]) <= versions.keys(), f"Unknown version: {row['id']}")
        require(set(row["relatedVideoIds"]) <= videos.keys(), f"Unknown video: {row['id']}")
        require(isinstance(row["featured"], bool), f"Invalid featured flag: {row['id']}")
        require(anchor <= cutoff, f"Future anchor: {row['id']}")
        if row["firstAppearance"]:
            normalize_date(row["firstAppearance"])
    for row in data["glossary"]:
        require(set(row["relatedTopicIds"]) <= topics.keys(), f"Unknown glossary topic: {row['id']}")
        if row["attestedBy"]:
            require(normalize_date(row["attestedBy"]) <= cutoff, f"Future glossary use: {row['id']}")
    return sources, versions, videos


def build():
    data = read_json("community-editorial.json")
    official = read_json("timeline.zh-CN.json")
    bili = read_json("bilibili-timeline.zh-CN.json")
    sources, versions, videos = validate(data, official, bili)
    output = copy.deepcopy(data)
    output["topics"].sort(key=lambda row: (normalize_date(row["date"]), row["id"]))
    for row in output["topics"]:
        row["sortDate"] = normalize_date(row["date"])
        row["sortDateNote"] = "仅用于排序；网页时间标签应使用dateLabel，结合dateBasis和dateNote。"
        row["categoryLabel"] = CATEGORIES[row["category"]]
        row["evidenceLabel"] = GRADES[row["evidenceGrade"]]
        row["dateBasisLabel"] = BASES[row["dateBasis"]]
        row["relatedVersions"] = [
            {"id": versions[v]["id"], "version": v, "date": versions[v]["date"]}
            for v in row["relatedVersions"]
        ]
        row["relatedVideos"] = [
            {"id": videos[v]["id"], "title": videos[v]["title"],
             "publishedAt": videos[v]["publishedAt"],
             "url": videos[v].get("url") or f"https://www.bilibili.com/video/{videos[v]['bvid']}/"}
            for v in row["relatedVideoIds"]
        ]
    output["meta"].update({
        "topicCount": len(output["topics"]),
        "glossaryCount": len(output["glossary"]),
        "candidateCount": len(output["candidates"]),
        "sourceCount": len(sources),
        "featuredCount": sum(t["featured"] for t in output["topics"]),
        "categoryCounts": dict(Counter(t["category"] for t in output["topics"])),
        "evidenceCounts": dict(Counter(t["evidenceGrade"] for t in output["topics"])),
        "sourceAccessCounts": dict(Counter(s["access"] for s in sources.values())),
        "yearCounts": dict(sorted(Counter(t["date"][:4] for t in output["topics"]).items())),
    })
    output["categories"] = [{"id": k, "label": v} for k, v in CATEGORIES.items()]
    output["evidenceGrades"] = [{"id": k, "label": v} for k, v in GRADES.items()]
    return output, render_markdown(output, sources)


def escape_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_links(ids, sources):
    links = []
    for key in ids:
        s = sources[key]
        suffix = "" if s["access"] == "full-text" else f"（{ACCESS[s['access']]}）"
        links.append(f"[{s['title']}]({s['url']}){suffix}")
    return "；".join(links)


def render_markdown(data, sources):
    m = data["meta"]
    lines = [
        "# 崩坏3社区话题时间轴",
        "",
        f"展示范围为 **2016年9月至{m['asOf']}**。精选 **{m['topicCount']}个时间节点、{m['glossaryCount']}个长期梗词条**，覆盖贴吧、TapTap、巴哈、PTT、虎扑及其他玩家社区的梗、玩法黑话、运营争议和剧情讨论。与已有版本、B站资料互相关联。",
        "",
        "配套数据：[网页时间轴JSON](community-timeline.zh-CN.json)、[人工编辑与来源目录](community-editorial.json)。",
        "",
        "## 日期与证据口径",
        "",
        "事件日、官方回应日、代表帖发布时间和剧情上线期分别标注。月份或版本期只表示背景定位；它们不是梗的首创时间。长期昵称保留在词典，不回填到2016年。预登录阶段目前缺少能定位当时传播的原帖，因此有日期的精选节点从2017年开始。",
        "",
        "‘事件可核对’表示具体动作有公告或同期报道；‘讨论有用例’表示找到玩家表达，不代表全体玩家态度；‘背景定位，待补原帖’主要依赖回顾、百科或有限索引。原页无法读取的链接明确标注。这里未建立同口径的当年热度或参与人数统计。",
        "",
        "★为适合网页主轴突出展示的编辑选择；其余可放在年度展开项。待补证选题另列，不进入已收录节点计数。",
        "",
        "| 类别 | 节点数 |",
        "| --- | ---: |",
    ]
    for key, label in CATEGORIES.items():
        lines.append(f"| {label} | {m['categoryCounts'].get(key, 0)} |")
    lines += ["", "## 按年排列的社区话题", ""]
    year = None
    for row in data["topics"]:
        if row["date"][:4] != year:
            year = row["date"][:4]
            lines += [f"### {year}年", ""]
        star = "★ " if row["featured"] else ""
        lines += [
            f"#### {star}{row['title']}", "",
            f"**{row['dateLabel']} · {row['categoryLabel']} · {row['evidenceLabel']}**", "",
            row["summary"] + " " + row["detail"], "",
            f"时间定位：{row['dateNote']}", "",
            f"边界：{row['caveat']}", "",
            f"版本关联：{'、'.join(v['version'] for v in row['relatedVersions'])}。",
            "",
            f"来源：{source_links(row['sourceIds'], sources)}。", "",
        ]
        if row["relatedVideos"]:
            lines += ["关联B站内容：" + "；".join(f"[{v['title']}]({v['url']})" for v in row["relatedVideos"]) + "。", ""]
    lines += [
        "## 长期梗与玩法黑话", "",
        "下表的记录日期是资料或用例日期，不是梗诞生日；2019年合集可能持续编辑。它们适合做悬浮词典或标签入口。", "",
        "| 用语 | 含义 | 资料日期与来源 |",
        "| --- | --- | --- |",
    ]
    for row in data["glossary"]:
        when = row["attestedBy"] or "首发时间未核验"
        lines.append(f"| {escape_cell(row['title'])} | {escape_cell(row['meaning'])} | {when}；{escape_cell(source_links(row['sourceIds'], sources))} |")
    lines += ["", "## 待补证选题", ""]
    for row in data["candidates"]:
        evidence = " 线索：" + source_links(row["sourceIds"], sources) + "。" if row["sourceIds"] else ""
        lines += [f"- **{row['title']}**：{row['reason']}{evidence}"]
    lines += [
        "", "## 网页数据与维护", "",
        f"`topics`为{m['topicCount']}个已收录节点，`glossary`为长期用语，`candidates`为待补证线索。`sources`按ID去重；条目的`sourceIds`指向来源目录，来源保存发布时间、访问状态和证据说明。", "",
        "时间轴按`sortDate`排序，以`dateLabel`展示。`datePrecision`和`dateBasis`说明日期含义，`dateNote`保存细节；月份归一化到1日的`sortDate`仅为布局计算。`firstAppearance: null`表示首创时间未核验。`featured`为展示建议；`evidenceGrade`可用于筛选，不能用于计算玩家支持率。", "",
        "`relatedVersions`关联国服版本ID与更新日；`relatedVideoIds`及`relatedVideos`关联现有B站数据，不重复把视频列为社区事件。地区相关内容见正文，不把海外周年当国服周年。", "",
        "编辑`community-editorial.json`后运行：", "",
        "```powershell", "python research/build-community.py", "python research/build-community.py --check", "```", "",
        "构建使用Python标准库，无联网请求。检查唯一ID、日期范围、来源地址与访问状态、版本及视频引用，并核对保存的JSON和Markdown是否与编辑资料一致。", "",
        "## 来源目录", "",
        "以下日期为资料发布或页面编辑日期，具体区别见备注；不是统一的事件日期。", "",
        "| 来源 | 资料日期 | 可读状态 | 说明 |", "| --- | --- | --- | --- |",
    ]
    for s in data["sources"]:
        lines.append(f"| [{escape_cell(s['title'])}]({s['url']}) | {s['publicationDate'] or '未确定／持续编辑'} | {ACCESS[s['access']]} | {escape_cell(s['note'])} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output, markdown = build()
    files = {
        "community-timeline.zh-CN.json": json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        "community.md": markdown,
    }
    for name, content in files.items():
        path = ROOT / name
        if args.check:
            require(path.exists(), f"Missing output: {name}")
            require(path.read_text(encoding="utf-8") == content, f"Stale output: {name}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    action = "Checked" if args.check else "Built"
    print(f"{action} {output['meta']['topicCount']} topics, {output['meta']['glossaryCount']} glossary terms, {output['meta']['sourceCount']} sources.")


if __name__ == "__main__":
    main()
