# 社区回声 · 采集与节选说明

截至 2026 年 10 月 11 日，168 个节点各展示 3 位不同署名用户的发言，共 504 段节选。相同原稿可能关联版本、影像及社区事件，因此节选条数包含关联复用；独立评论数量以 `discussions.zh-CN.json` 的 `meta.uniqueCommentCount` 为准。

来源包括 B 站视频／专栏评论区、TapTap 帖子评论、巴哈姆特讨论楼层及 PTT 推文。逐条保存原文、公开署名、平台用户标识、留言日期、原帖链接和采集时间；正文只展示连续原文节选。省略号位于引文外，表示还有上下文可在原帖阅读。没有改写成玩家口吻，也没有生成用户发言。

评论是署名用户的个人意见，不用于证明争议指控或代表全体玩家态度。正面评价、批评、提问、玩梗和回忆均保留。采集的是目前能够公开阅读的页面片段，并非历史评论全集；不按当前热评推定当年舆论比例。

## 时间与关联

- 版本 PV 常早于更新日，标为前瞻留言；距离节点超过 70 天的较晚留言标为后来讨论。社区事件日期可能只有月份或时期，因此只按留言年份标为同年、后来或较早。
- 2016 年的三个启航节点未取得对应公告的可读用户留言，引用开场 CG 下玩家后来重返起点的回忆，并在详情明确说明关联。
- 「勿雪游」引用俚语合集中的角色简称与旧配装讨论，未作为口号原帖留言。「白衣渡江」「爱门」等梗的回顾视频评论也不作为首创时间证据。
- 巴哈姆特引用的是对应讨论帖楼层，部分时间可能为编辑时间。PTT 推文仅提供月日、时分，年份依原帖年份推定；页面只展示日期。
- 原画集活动、十周年祝福帖仅节选讨论或祝福正文，页面不展示游戏 UID、回归码或私人联系方式。
- 4.8 的 BWIKI 嵌入链接错误指向 5.2，6.4 的一条搜索候选误指《星穹铁道》OP。两者已排除，改用核验标题后的对应版本 PV。

## 本地取证与维护

`discussions.zh-CN.json` 是页面使用的精简数据；`discussion-selections.json` 保存逐节点选取的来源与评论 ID。采集快照位于源码项目的 `research/discussion-sources/`，不会随发布网站打包。

```powershell
python scripts/collect-discussions.py versions
python scripts/collect-discussions.py videos
python scripts/collect-discussions.py extra
node scripts/collect-forum-discussions.cjs
node scripts/parse-forum-discussions.cjs
python scripts/curate-discussions.py
python scripts/prepare-discussions.py
npm test
npm run build
```

采集脚本只读取公开可访问的页面和评论，缓存已取得的结果。新来源需要先阅读并核对原稿，再修改选取清单。重新生成时会校验节选确实包含在快照原文中，每个节点用户不重复。原文删除、署名变化或不可读时，应保留明确的来源状态并人工复核。
