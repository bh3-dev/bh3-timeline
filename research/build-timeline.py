"""Build the Chinese-server timeline and its readable research document.

Run: python research/build-timeline.py
No third-party dependencies. Source notes are curated, not scraped assertions.
"""

from pathlib import Path
import json
import re
from datetime import date

ROOT = Path(__file__).resolve().parent
CUTOFF = "2026-10-11"
DATE_INDEX = "https://www.taptap.cn/moment/549549965811125812"

# version | CN update date | title | person/armor/kind;... | major events |
# story / significant permanent feature | source URL | source kind
# Events are selections, not a complete list of every login/reward event.
EARLY = """
1.0|2016-10-14|开服版本|琪亚娜/女武神·白练/battlesuit;琪亚娜/圣女祈祷/battlesuit;琪亚娜/女武神·游侠/battlesuit;琪亚娜/白骑士·月光/battlesuit;芽衣/脉冲装·绯红/battlesuit;芽衣/女武神·强袭/battlesuit;芽衣/影舞冲击/battlesuit;芽衣/雷电女王的鬼铠/battlesuit;布洛妮娅/女武神·战车/battlesuit;布洛妮娅/驱动装·山吹/battlesuit;布洛妮娅/雪地狙击/battlesuit;布洛妮娅/次元边界突破/battlesuit|全平台公测|开服主线与初始战斗体系|https://www.18183.com/bh3rd/201610/713481.html|reprint
1.1|2016-11-15|封印之剑|姬子/战场疾风/battlesuit;姬子/融核装·深红/battlesuit|轩辕篇外传|姬子首次作为可获取角色登场|https://news.4399.com/bhsrd/zixun/m/697167.html|reprint
1.2|2017-01-05|诅咒之剑|姬子/女武神·凯旋/battlesuit;姬子/血色玫瑰/battlesuit|蚩尤篇外传|换装系统|https://news.17173.com/z/bh3/content/01052017/105519539.shtml|reprint
1.3|2017-02-23|舰团启航||永世回忆（黑轩辕与八重樱）；孤独王座|舰团系统；矩阵探索|https://news.4399.com/bhsrd/zixun/m/731809.html|reprint
1.4|2017-04-12|樱色轮回|八重樱/逆神巫女/battlesuit;八重樱/御神装·勿忘/battlesuit|樱色轮回|首个开放世界；灵魂觉醒；联机玩法测试|https://www.9game.cn/bhxy3/1666511.html|reprint
1.5|2017-05-25|德丽莎，出击！|德丽莎/女武神·誓约/battlesuit;德丽莎/处刑装·紫苑/battlesuit|永世回忆（德丽莎外传）；樱色轮回美食祭|联机关卡扩展|https://news.4399.com/bhsrd/zixun/m/758305.html|reprint
1.6|2017-07-06|盛夏重逢|德丽莎/樱火轮舞/battlesuit|夏日大作战|主线第5章雪原重逢|https://u.360.cn/bh3/article/244857|reprint
1.7|2017-08-24|银狼觉醒|布洛妮娅/银狼的黎明/battlesuit;布洛妮娅/异度黑核侵蚀/battlesuit|抉择梦境；一周年庆|外传抉择梦境|https://m.ali213.net/news/170825/80669.html|reprint
1.8|2017-10-12|赤染御魂|八重樱/真炎幸魂/battlesuit;德丽莎/神恩颂歌/battlesuit|天守魂座|记忆战场上线；新联机Raid|https://u.360.cn/bh3/article/257260/|reprint
1.9|2017-11-23|圣仪之复苏|卡莲/圣仪装·今样/battlesuit|卡莲幻想VII；天火出鞘|主线第6章巴比伦的囚徒|https://www.18183.com/bh3rd/201711/979693.html|reprint
2.0|2018-01-11|宿舍派对|符华/女武神·迅羽/battlesuit|乱斗竞速|宿舍系统上线|https://m.ali213.net/news/180111/92881.html|reprint
2.1|2018-02-08|月影逐龙|符华/影骑士·月轮/battlesuit|神州的新春；破灭暴雨|神之键阁|https://www.18183.com/bh3rd/201802/1035282.html|reprint
2.2|2018-03-29|千年之羽|符华/炽翎/battlesuit|遗忘之人|符华主题外传|https://moegirl.uk/index.php?title=崩坏3/运营公告/2.2版本更新公告&variant=zh-hans|archived-reprint
2.3|2018-05-10|天命之战|卡莲/第六夜想曲/battlesuit;符华/白夜执事/battlesuit||主线第8章；联机Raid扩展|https://www.9game.cn/bhxy3/2315625.html|reprint
2.4|2018-06-21|夏日回忆|德丽莎/月下初拥/battlesuit|夏日回忆|舰长线早期故事；海滨宿舍；编年史|https://shouyou.gamersky.com/gl/201806/1055880.shtml|reprint
2.5|2018-08-02|女王降临|琪亚娜/空之律者/battlesuit;姬子/极地战刃/battlesuit||天命总部开放世界；时序旋涡|https://www.taptap.cn/moment/15210656814859874|official
2.6|2018-09-13|重燃|卡莲/原罪猎人/battlesuit|Reburn二周年庆|主线第1章与第2章重制；跨服联机|https://www.taptap.cn/moment/15225944302160047|official
2.7|2018-11-01|真红之剑|姬子/真红骑士·月蚀/battlesuit;丽塔/黯蔷薇/battlesuit|神机档案|主线第9章通往明日的旅途；赫尔海姆；空岛巡猎|https://www.taptap.cn/moment/15213370131090884|official
2.8|2018-12-13|圣夜狂想|丽塔/猎袭装·影铁/battlesuit|圣诞狂想曲|主线第9章间章天穹的追猎者；迪拉克之海|https://m.ali213.net/news/181206/117721.html|reprint
2.9|2019-01-24|快雪迎春|丽塔/苍骑士·月魂/battlesuit;芽衣/破晓强袭/augment|年夜饭大作战；新春聊天室|增幅核心系统；主线第9章间章蛇从黑暗中行来|https://news.17173.com/z/bh3/content/01252019/224513941.shtml|reprint
3.0|2019-03-14|海渊迷影|布洛妮娅/彗星驱动/augment;赤鸢之翼/赤鸢之翼/elf;仿犹大/仿犹大/elf|海渊之眼|主线第10章深渊之下；武装人偶系统；等级突破至82级|https://game.xiaomi.com/viewpoint/1098264873_1552569742572_16|official
3.1|2019-04-25|逐梦双星|萝莎莉娅/樱桃炸弹/battlesuit;莉莉娅/蓝莓特攻/battlesuit|崩坏国记|编年史逐梦双星|https://www.taptap.cn/moment/15201397343518943|official
3.2|2019-06-05|幻海童谣|希儿/幻海梦蝶/battlesuit;晓月镇魂歌/晓月镇魂歌/elf||主线第11章直到深海的尽头；量子属性；量子奇点；悬赏委托|https://game.xiaomi.com/viewpoint/1098264873_1559728796936_14|official
3.3|2019-07-18|天使重构|布洛妮娅/理之律者/battlesuit;琪亚娜/天穹游侠/augment|奇异漂流|主线第11章间章虚空之穹 孤独之月；作战凭证|https://www.taptap.cn/moment/15221230902709746|official
3.4|2019-08-29|暮光裁决|德丽莎/暮光骑士·月煌/augment|三周年庆；圣芙蕾雅嘉年华|主线第12章光与影的彼岸；超限武器系统|https://game.xiaomi.com/viewpoint/1130882680_1567075502821_12|official
3.5|2019-10-17|彼岸双生|希儿/彼岸双生/battlesuit;符华/雾都迅羽/augment|花开彼岸|主线第13章长夜暗空；家园系统重构|https://game.xiaomi.com/viewpoint/1098264873_1571311649438_16|official
3.6|2019-11-28|绯夜霞隐|八重霞/夜隐重霞/battlesuit|霞隐散华抄|主线第14章黑暗破晓；SP角色体系|https://www.taptap.cn/moment/15218632959199648|official
3.7|2020-01-16|墨书华岁|符华/云墨丹心/battlesuit;苍玄之书/苍玄之书/elf|神州仙行记；春节活动||https://www.taptap.cn/moment/15227062100954122|official
3.8|2020-03-05|拂晓荣光|幽兰黛尔/女武神·荣光/battlesuit|后崩坏书|新开放世界后崩坏书；主线第15章迷途沙尘|https://www.taptap.cn/moment/15213841189175572|official
3.9|2020-04-16|逐暗星辉|幽兰黛尔/辉骑士·月魄/battlesuit|光辉的赞歌；崩坏国记·零|主线第16章暴雨将至|https://www.taptap.cn/moment/15209100509974421|official
4.0|2020-05-28|长夜孤星|观星/朔夜观星/battlesuit|星与你消失之日|主线第17章雷从长空|https://game.xiaomi.com/viewpoint/1098264873_1590656225303_16|official
4.1|2020-07-09|雷鸣彻空|芽衣/雷之律者/battlesuit;贝拉/贝拉/elf|双子：入侵 海渊乐园篇|主线第18章凝自冰霜|https://bh3.mihoyo.com/m/news/695/120765|official
4.2|2020-08-20|幻夜迷迭|丽塔/失落迷迭/battlesuit;芽衣/断罪影舞/augment|迷迭香的花语|主线第19章；超弦空间|https://news.4399.com/bhsrd/zixun/m/922509.html|reprint
4.3|2020-09-26|异色狂潮|萝莎莉娅/狂热蓝调Δ/augment;特斯拉Zero/特斯拉Zero/elf|崩坏冒险谭；四周年庆|主线第20章千年之羽|https://www.taptap.cn/moment/58895869373582043|official
4.4|2020-11-19|黄金荣典|幽兰黛尔/不灭星锚/battlesuit|星辉下的故事|主线第21章新生之翼|https://www.qieyou.com/content/74172|reprint
4.5|2020-12-24|明日福音|明日香/明日福音/battlesuit|自新世纪（EVA联动）||https://www.sohu.com/a/440280315_632941|official
4.6|2021-02-04|唯我独尊|识之律者/识之律者/battlesuit;若水/若水/elf|神州漂流记；春节活动||https://www.taptap.cn/moment/106364568816584784|official
4.7|2021-03-25|骇兔入侵|布朗尼/迷城骇兔/battlesuit|光锁迷城：天穹|主线第23章一人的剧场|https://www.taptap.cn/moment/124119020143119798|official
4.8|2021-04-29|剧场魅影|希儿/魇夜星渊/battlesuit|偶像决胜战；禁限超越|主线第24章千人的舞台；万象虚境|https://www.taptap.cn/moment/136798291718309770|official
4.9|2021-06-10|异世旅人|菲谢尔/断罪皇女！！/battlesuit;刻晴/活动限定可操作角色/event-only|异世行记（原神联动）|主线第25章|https://www.taptap.cn/moment/152007240532885847|official
5.0|2021-07-15|薪火传承|琪亚娜/薪炎之律者/battlesuit;西琳/西琳/elf||往世乐土首次开放|https://news.4399.com/bhsrd/zixun/m/945537.html|reprint
5.1|2021-08-19|无瑕乐土|爱莉希雅/粉色妖精小姐♪/battlesuit|秘藏宝库|往世乐土第二章；主线第25章间章|https://news.4399.com/bhsrd/zixun/m/947305.html|reprint
5.2|2021-09-23|无限命途|梅比乌斯/无限·噬界之蛇/battlesuit;渡鸦/午夜苦艾/battlesuit|女武神的餐厅；五周年庆|主线第26章悲剧的诞生|https://www.taptap.cn/moment/190059786174201989|official
5.3|2021-11-04|黄昏后书|卡萝尔/甜辣女孩/battlesuit|后崩坏书第二章序章 星坠之前；崩坏国记·零（复刻）；星与你消失之日（复刻）|主线第27章愚者的黄昏|https://www.taptap.cn/moment/205277779728535014|official
"""

# Recent dates, titles and primary links come from the official CN Steam feed.
# Character identity, major events, and story are curated from these announcements.
RECENT = """
5.4|布洛妮娅/次生银翼/battlesuit|后崩坏书第二章|主线第28章意志的彼岸
5.5|幽兰黛尔/天元骑英/battlesuit;丽塔/缭乱星棘/battlesuit;圣剑幽兰黛尔/圣剑幽兰黛尔/elf|神秘企划·阿拉哈托α；新春聊天室2022；春节活动|后崩坏书第二章持续更新
5.6|帕朵菲莉丝/空梦·掠集之兽/battlesuit|无星之夜；神州仙行记（复刻）|往世乐土大型更新
5.7|阿波尼亚/戒律·深罪之槛/battlesuit;伊甸/黄金·璀耀之歌/battlesuit|断界残篇；迷迭花语（复刻）|主线第29章来自乐土
5.8|格蕾修/繁星·绘世之卷/battlesuit|绘星的旅程；光锁迷城（复刻）|主线第30章英雄们的葬礼
5.9|维尔薇/螺旋·愚戏之匣/battlesuit|夏日生存狂想曲·A面|主线第31章致爱莉希雅
6.0|爱莉希雅/真我·人之律者/battlesuit|夏日生存狂想曲·13面|主线间章圣痕计划
6.1|李素裳/玉骑士·月痕/battlesuit|天穹夜行录；六周年庆|主线第32章世界的止境
6.2|爱衣·休伯利安Λ/时帆旅人/battlesuit|崩坏拯救日志|主线第33章以真理之名
6.3|布洛妮娅/真理之律者/battlesuit|喧闹假日交响曲𝄆|主线第34章月之始源与终焉
6.4|琪亚娜/终焉之律者/battlesuit;芽衣/始源之律者/battlesuit|喧闹假日交响曲𝄇；新春聊天室2023；春节活动|主线第35章然后，向着明天
6.5|苏莎娜/女武神·热砂/battlesuit|猫镇奇遇记；流光若水；畅游吼姆世界 狂欢赛|主线第36章启自长空；第一部1.5开启
6.6|米丝忒琳（羽兔）/织羽梦旌/battlesuit;普罗米修斯/终末协理0017/battlesuit|特丽丽的魔法奇旅|主线第37章盐雪沙痕
6.7|时雨绮罗/糖露星霜/battlesuit|☆完美演出☆|主线第38章孤塔凋星
6.8|希儿/死生之律者/battlesuit;重装小兔/重装小兔/elf|在长梦弥散之前|主线第39章海的女儿
6.9|西琳/奇迹☆魔法少女/battlesuit|当红月落幕之后；崩坏3×普罗米亚联动|主线第40章七常住果
7.0|月下/月下誓约·予爱以心/battlesuit|舰舰的牧场奇谭；七周年庆|主线第41章杂染相续
7.1|格蕾修/天行·绘星之卷/battlesuit|繁星旅航：反击战|主线第42章绝地天通
7.2|符华/浮生·渡尘之羽/battlesuit|寻鸢漫录；月所凝望之星；拓境战幕|第二部前的活动剧情月所凝望之星
7.3|希娜狄雅/深空定锚·曙光/battlesuit;赫丽娅/女武神·巡矢/battlesuit;科拉莉/女武神·重机/battlesuit;寻梦者/寻梦者/astralop;松雀/松雀/astralop|数海寻馔；新春聊天室2024|主线第二部第1章百年孤影；星之环与协同者系统
7.4|瑟莉姆/享乐狂宴·邀影/battlesuit|飞向瓯夏邀请赛|主线第二部第2章迷宫中的七术
7.5|灯/破弃孤光·逐影/battlesuit|夜光逐影|主线第二部第3章事先张扬的犯罪
7.6|松雀/瞒天乐游·曙影/battlesuit;瑟拉珮姆/瑟拉珮姆/astralop|天命工作指南|主线第二部第3章间章一个梦游者的苦痛
7.7|德丽莎/天命难逃/battlesuit|于梦中诞生|主线第二部第4章何人注视的迷岸
7.8|薇塔/孑遗千星/battlesuit|荒野育成手记；特丽丽的魔法奇旅（复刻）；八周年庆|主线第二部第5章最初与最后的战争
7.9|花火/诡戏千役「友情出演！」/battlesuit|崩坏：愚者牌揭秘（崩坏 星穹铁道联动）|主线第二部第6章悲鸣止于缄默之影
8.0|幽兰黛尔/天光驰彻/battlesuit|倒计时：好梦开场！|主线第二部第7章怀抱旧愿的花束
8.1|琪亚娜/咚！炽愿吉星/battlesuit;德丽莎·阿波卡利斯/德丽莎·阿波卡利斯/astralop|进行时：新愿游园~；新春聊天室2025|主线第二部第7章间章神明无处祈祷
8.2|李素裳/一客逍游/battlesuit|云津百味记|主线第二部第8章直至长路迈向湛空
8.3|赫丽娅/位面武器·失序时空/battlesuit|启程！祝福与心愿的访途|主线第二部第9章如果命运在今日终结
8.4|科拉莉/逆命魔龙·降临！/battlesuit;晨雪/晨雪/astralop|集合！沁夏友乐园|主线第二部第9章间章星星仍在闪烁
8.5|爱莉希雅/嗨♪爱愿妖精♥/battlesuit|偕行！青春畅想；九周年庆|主线第二部第10章于信仰之光下重逢
8.6|丽塔/窈窕谍影/battlesuit|特工丽影：晚宴疑云|主线第二部第11章无神论者的弥撒
8.7|芽衣/镇×偃月叩晓/battlesuit|正当时：年夜奇缘*；新春聊天室2026|主线第二部第11章间章光所梦寻之夜
8.8|白鹿游云/白鹿游云/astralop|数海计划·论文危机|主线第二部第12章与我不曾知晓的你；次生银翼推荐装备更新
8.9|希儿/愈生佑翎/battlesuit|极限时速：外卖行者|主线第二部第13章一朵玫瑰的屈膝礼
9.0|希娜狄雅/希娜狄雅/astralop|舰舰与许愿树秘闻；飞向瓯夏邀请赛（复刻）|主线第二部终章从此，拥抱未来；浮生·渡尘之羽推荐装备更新
9.1|寻梦者/时序之律者/battlesuit|相遇♪回忆玩具小屋；十周年庆|主线第二部后日谈海正用火的声音歌唱
"""

KIND_LABEL = {"battlesuit": "装甲", "augment": "增幅", "astralop": "协同者", "elf": "人偶", "event-only": "活动限定"}
SOURCE_LABEL = {"official": "官方", "reprint": "公告转载", "archived-reprint": "公告存档", "community": "玩家索引", "official-archive": "旧官网存档"}

# These early dates have explicit update/maintenance-date evidence in the read source.
DATE_CONFIRMED = {"1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "2.0", "2.1", "2.6", "3.2", "3.5", "3.9", "4.1", "4.2", "4.3", "4.4", "4.5"}

def chars(value):
    result = []
    for token in value.split(";"):
        if not token:
            continue
        person, name, kind = token.split("/")
        result.append({"person": person, "name": name, "kind": kind})
    return result

def events(value):
    result = []
    for token in value.split("；"):
        if not token:
            continue
        kind = "anniversary" if "周年" in token else "collaboration" if "联动" in token else "seasonal" if "春节" in token or "新春聊天室" in token else "story-or-theme"
        result.append({"title": token, "kind": kind, "rerun": "复刻" in token})
    return result

def source(url, kind, supports):
    return {"url": url, "kind": kind, "supports": supports}

versions = []
for line in EARLY.strip().splitlines():
    v, released, title, cast, ev, highlights, url, source_kind = line.split("|")
    explicit = v in DATE_CONFIRMED
    sources = [source(url, source_kind, ["characters", "events", "highlights"])]
    if explicit:
        sources[0]["supports"].append("date")
    else:
        sources.append(source(DATE_INDEX, "community", ["date"]))
    versions.append({
        "id": "cn-" + v, "version": v, "date": released, "datePrecision": "day",
        "title": title, "titleType": "editorial" if v == "1.0" else "official",
        "characters": chars(cast), "majorEvents": events(ev),
        "storyAndFeatures": [x for x in highlights.split("；") if x],
        "sources": sources,
        "verification": {"date": "announcement-or-maintenance" if explicit else "community-index-needs-primary-date", "content": "official-announcement" if source_kind == "official" else "announcement-reprint"},
        "notes": []
    })

official_updates = json.loads((ROOT / "official-steam-updates.json").read_text(encoding="utf-8-sig"))
by_version = {}
for update in official_updates:
    matched = re.search(r"(\d+\.\d+)版本", update["title"])
    v = matched.group(1) if matched else "6.4" if "月之版本" in update["title"] else None
    if not v:
        raise ValueError(f"Unrecognized update: {update['title']}")
    by_version[v] = update

for line in RECENT.strip().splitlines():
    v, cast, ev, highlights = line.split("|")
    u = by_version[v]
    title = re.search(r"「([^」]+)」", u["title"]).group(1)
    versions.append({
        "id": "cn-" + v, "version": v, "date": u["announcementDate"], "datePrecision": "day",
        "title": title, "titleType": "official",
        "characters": chars(cast), "majorEvents": events(ev),
        "storyAndFeatures": [x for x in highlights.split("；") if x],
        "sources": [source(u["url"], "official", ["date", "characters", "events", "highlights"])],
        "verification": {"date": "official-cn-update-announcement", "content": "official-announcement"},
        "notes": []
    })

versions.sort(key=lambda r: tuple(map(int, r["version"].split("."))))
lookup = {v["version"]: v for v in versions}

def add_note(v, text):
    lookup[v]["notes"].append(text)

def add_source(v, url, kind, supports):
    existing = next((s for s in lookup[v]["sources"] if s["url"] == url), None)
    if existing:
        existing["supports"] = list(dict.fromkeys(existing["supports"] + supports))
    else:
        lookup[v]["sources"].append(source(url, kind, supports))

# Maintenance-date evidence from the final source pass. A reprint remains
# classified as a reprint; the community date index is replaced, not promoted.
DATE_SUPPLEMENTS = {
    "1.7": ("https://m.ali213.net/news/170822/80313.html", "reprint"),
    "1.8": ("https://www.yoyou.com/news/201710/1053070.html", "reprint"),
    "1.9": ("https://shouyou.3dmgame.com/gl/50773.html", "reprint"),
    "2.2": ("https://m.ali213.net/news/gl1803/226307.html", "reprint"),
    "2.3": ("https://www.9game.cn/bhxy3/2302577.html", "reprint"),
    "2.4": ("https://www.apk3.com/androidnews/html/227607.html", "reprint"),
    "2.5": ("https://www.cr173.com/gonglue/274106_1.html", "reprint"),
    "2.7": ("https://news.17173.com/z/bh3/content/10302018/225620034.shtml", "reprint"),
    "2.8": ("https://www.9game.cn/bhxy3/2697282.html", "reprint"),
    "2.9": ("https://news.4399.com/bhsrd/zixun/m/876993.html", "reprint"),
    "3.0": ("https://shouyou.3dmgame.com/gl/117165.html", "reprint"),
    "3.1": ("https://www.9game.cn/bhxy3/3066949.html", "reprint"),
    "3.3": ("https://m.ali213.net/news/gl1907/350047.html", "reprint"),
    "3.4": ("https://game.xiaomi.com/viewpoint/1098264873_1566974934564_14", "official"),
    "3.6": ("https://news.4399.com/bhsrd/zixun/m/905766.html", "reprint"),
    "3.7": ("https://news.17173.com/z/bh3/content/01162020/201115243.shtml", "reprint"),
    "3.8": ("https://game.xiaomi.com/viewpoint/1098264873_1583312338501_14", "official"),
    "4.0": ("https://news.17173.com/z/bh3pc/morelist/06032020/095913006.shtml", "reprint"),
    "4.6": ("https://ol.gamersky.com/netgame/56057/List_3.html", "reprint"),
    "4.7": ("https://m.ali213.net/news/gl2103/587917.html", "reprint"),
    "4.8": ("https://news.17173.com/z/bh3/content/04282021/173348543.shtml", "reprint"),
    "4.9": ("https://www.taptap.cn/moment/152007240532885847", "official"),
    "5.0": ("https://www.9game.cn/bhxy3/5276075.html", "reprint"),
    "5.1": ("https://shouyou.gamersky.com/news/202108/1416529.shtml", "reprint"),
    "5.2": ("https://www.9game.cn/bhxy3/5489300.html", "reprint"),
    "5.3": ("https://m.ali213.net/news/gl2111/720815.html", "reprint"),
}
for v, (url, kind) in DATE_SUPPLEMENTS.items():
    row = lookup[v]
    row["sources"] = [s for s in row["sources"] if s["url"] != DATE_INDEX]
    matching = next((s for s in row["sources"] if s["url"] == url), None)
    if matching:
        matching["supports"].append("date")
    else:
        add_source(v, url, kind, ["date"])
    row["verification"]["date"] = "announcement-or-maintenance"

# Content corrections from the same pass.
lookup["1.0"]["characters"][0]["name"] = "领域装·白练"
lookup["1.1"]["majorEvents"] += events("梦中的圣诞小镇")
lookup["2.3"]["storyAndFeatures"] = ["主线第8章女王降临", "编年史", "深渊与开放世界改版"]
lookup["2.4"]["storyAndFeatures"].remove("编年史")
lookup["5.0"]["majorEvents"] = events("盛夏海滨游乐园")
add_source("1.1", "https://wap.gamersky.com/sygl/Content-851632.html", "reprint", ["events"])
add_source("2.3", "https://www.9game.cn/bhxy3/2302577.html", "reprint", ["highlights"])
add_source("5.0", "https://www.taptap.cn/moment/164692059754595113", "official", ["characters", "events", "highlights"])

add_source("1.0", "https://web.archive.org/web/20160927090647/http://www.bh3.com/", "official-archive", ["characters"])
add_note("1.0", "日期为全平台公测日；iOS先行首发为2016-10-01。开服版本为编辑标签，并非确认过的官方版本副标题。角色是首发阵容，非当日同时首次公开。")
add_note("1.3", "永世回忆指当时矩阵探索中的黑轩辕与八重樱回忆关卡，与1.5的德丽莎外传同名。")
add_note("1.7", "一周年庆在本版本期间举办，不能把庆典日期当成1.7更新日期。")
add_source("2.6", "https://news.4399.com/bhsrd/zixun/m/862871.html", "reprint", ["date"])
add_source("3.2", "https://news.4399.com/bhsrd/zixun/m/889743.html", "reprint", ["date", "characters", "highlights"])
add_source("3.4", "https://news.17173.com/z/bh3/content/09232019/154803809.shtml", "reprint", ["events"])
add_note("3.4", "三周年圣芙蕾雅嘉年华从2019-09-26开启，属于3.4版本期间，非3.5。")
add_source("3.5", "https://bh3.mihoyo.com/m/news/695/120704", "official", ["date", "characters", "events", "highlights"])
add_note("3.8", "后崩坏书中的主角、芽衣和卡萝尔属于独立玩法的可操作角色，本表不把他们记作常规女武神装甲。")
add_note("4.0", "观星是德丽莎的平行世界角色；与本篇德丽莎分开标识。")
add_note("4.3", "公告明确版本更新日为2020-09-26，不采用部分汇总所列的9月24日。Δ是狂热蓝调的增幅形态。")
add_note("4.5", "版本更新日为2020-12-24，自新世纪联动活动于12月25日开启。")
add_note("4.6", "识之律者与符华共享外貌与部分游戏角色分类，但作为独立人物记录。")
add_note("4.9", "菲谢尔是常规可获取角色；刻晴只在联动活动中可操作，不能记作可永久获取的新装甲。")
add_note("6.4", "该版本更新公告使用月之版本·终焉归始这一名称；数据按连续编号记作6.4。")
add_note("6.7", "官方更新公告标题为歧路星语；不采用部分汇总中的歧路星羽。")
add_source("7.3", "https://bh3.mihoyo.com/news/693/122300", "official", ["characters", "events", "highlights"])
add_source("7.3", "https://www.taptap.cn/game-event/3132", "official", ["date"])
add_note("7.3", "国服第二部于2024-02-01随本版本开启。寻梦者与松雀均新增为协同者；此时寻梦者不是可获取的女武神装甲。")
add_source("7.6", "https://www.taptap.cn/moment/553267704149053099", "official", ["characters"])
add_note("7.6", "松雀在7.3是协同者，本版本新增可操作装甲瞒天乐游·曙影。")
add_note("7.9", "花火来自崩坏 星穹铁道；联动不等于该人物在崩坏3主线首次出现。")
add_note("8.8", "新增白鹿游云为协同者；公告中的次生银翼内容是推荐装备更新，不是新装甲。")
add_note("9.0", "新增希娜狄雅为协同者；她的装甲深空定锚·曙光已在7.3登场。浮生·渡尘之羽本次更新推荐装备。")
add_source("9.1", "https://bh3.mihoyo.com/gl/character/list?fullscreen=1&game_biz=bh3_cn&mode=fullscreen", "official", ["characters"])
add_note("9.1", "时序之律者按官方角色目录归于寻梦者。截止日期为2026-10-11，不收录9.2测试服或前瞻内容。")

MILESTONES = [
    {"id": "pre-registration", "date": "2016-09", "datePrecision": "month", "title": "预登录进行中", "description": "按网页展示范围从2016年9月开始。旧官网的预登录活动消息标注2016-08-09，因此本节点不是预登录首日。", "sources": [source("https://web.archive.org/web/20160927090647/http://www.bh3.com/", "official-archive", ["pre-registration-already-active"])], "localEvidence": "home/archive/text/index.html"},
    {"id": "android-non-reset-test", "date": "2016-09-14", "datePrecision": "day", "title": "安卓限号不删档测试", "description": "安卓平台限号不删档测试开启。9月17日是作战资格重新开放，不是预登录首次开启。", "sources": [source("https://bh3.mihoyo.com/news/693/119585", "official", ["date", "milestone"])]},
    {"id": "ios-launch", "date": "2016-10-01", "datePrecision": "day", "title": "iOS平台首发", "description": "iOS先行首发，与10月14日全平台公测分开展示。", "sources": [source("https://bh3.mihoyo.com/news/693/119590", "official", ["date", "milestone"])]}
]

data = {
    "schemaVersion": 1,
    "meta": {
        "title": "崩坏3国服十周年版本时间轴",
        "region": "CN", "regionLabel": "中国大陆国服", "timezone": "Asia/Shanghai",
        "displayStart": "2016-09", "asOf": CUTOFF, "versionCount": len(versions),
        "scope": "已上线的主要x.y版本，精选新装甲、增幅、协同者、大型主题活动、周年联动及重要主线与玩法。",
        "status": "first-research-pass",
        "selectionNotes": [
            "date为版本更新日，不是公告发表日、角色补给开启日或版本内活动开始日。",
            "majorEvents及storyAndFeatures为精选内容，不是完整活动或剧情更新目录；空数组不证明当版没有活动。",
            "characters以可获取装甲与增幅为主，并区分协同者、人偶、活动限定角色。武装人偶只收录已核对的代表节点，不是全量目录。",
            "person不是本次首次作为人物登场的断言；新装甲不等于新人物。服装、武器升级和剧情NPC不记为新装甲。",
            "版本内内容可能分周开放。本文不包含所有小补丁、常规登录、充值、皮肤与卡池轮换。",
            "community-index-needs-primary-date表示日期采用玩家版本索引，仍需补充官方维护公告；其内容来源另列。"
        ],
        "sourcePriority": ["国服官方更新或维护公告", "官方账号发布", "同期公告转载或存档", "玩家索引用于缺失日期"],
        "characterKinds": KIND_LABEL,
        "earlyDateIndex": DATE_INDEX,
        "refreshOfficialUpdates": "powershell -File research/collect-official.ps1",
        "build": "python research/build-timeline.py"
    },
    "milestones": MILESTONES,
    "versions": versions
}

def validate():
    expected = [f"{major}.{minor}" for major in range(1, 10) for minor in range(10) if (major, minor) <= (9, 1)]
    assert [v["version"] for v in versions] == expected, "Missing or duplicated version"
    assert len(versions) == 82
    assert len(by_version) == 38
    prior = "0000-00-00"
    for row in versions:
        date.fromisoformat(row["date"])
        assert prior < row["date"] <= CUTOFF, row["version"]
        prior = row["date"]
        assert row["title"] and row["sources"]
        assert any("date" in s["supports"] for s in row["sources"])
        assert len({s["url"] for s in row["sources"]}) == len(row["sources"])
        assert all(s["url"].startswith("https://") for s in row["sources"])
        assert all(c["kind"] in KIND_LABEL for c in row["characters"])
    assert lookup["7.3"]["date"] == "2024-02-01"
    assert not any(c["kind"] == "battlesuit" for c in lookup["8.8"]["characters"])
    assert not any(c["kind"] == "battlesuit" for c in lookup["9.0"]["characters"])
    assert lookup["9.1"]["characters"][0]["person"] == "寻梦者"
    assert "三周年庆" in [e["title"] for e in lookup["3.4"]["majorEvents"]]

def cast_text(row):
    pieces = []
    for c in row["characters"]:
        if c["kind"] == "battlesuit":
            pieces.append(f"{c['person']}「{c['name']}」")
        elif c["kind"] == "augment":
            pieces.append(f"{c['person']}「{c['name']}」（增幅）")
        elif c["kind"] == "event-only":
            pieces.append(f"{c['person']}（活动限定可操作）")
        else:
            pieces.append(f"{c['name']}（{KIND_LABEL[c['kind']]}）")
    return "；".join(pieces) if pieces else "未列新增装甲"

def markdown():
    pending = [v["version"] for v in versions if v["verification"]["date"] == "community-index-needs-primary-date"]
    lines = [
        "# 崩坏3国服十周年版本时间轴", "",
        f"时间范围为 **2016年9月至{CUTOFF}**，覆盖 **1.0至9.1共82个主要版本**。每版列出可获取的新装甲与增幅，以及大型主题活动、周年联动和重要剧情或玩法。国服与其他地区的版本日期不同，本表统一采用中国大陆国服时间。", "",
        "版本日期指更新日；角色补给和活动可能稍后开放。装甲是同一人物的不同可操作形态，不能直接换算为新增人物数。增幅、协同者、人偶及活动限定角色在表内单独注明。", "",
        (f"日期带 **†** 的 {len(pending)} 条记录采用[玩家版本索引]({DATE_INDEX})，仍需补充官方维护公告；每行另附内容来源。" if pending else "日期与内容来源逐版列出，优先采用官方公告；部分早期版本采用同期公告转载或存档。") + "空白活动栏写作‘—’，仅表示没有在本次精选中单列主题活动。人偶只列已核对的代表节点，不是全量人偶目录。", "",
        "## B站视频与话题资料", "",
        "第二层资料已整理为 [B站视频与话题时间轴](bilibili.md) 和 [网页JSON](bilibili-timeline.zh-CN.json)，包含官号动画／PV、Scyrax渲染演示、声优歌曲、鬼畜／手书及周年节目。每条保存原稿BV、作者、北京时间、热度快照与版本关联；累计数据不当作当年热榜。精选数量及采集与构建说明见该文档。", "",
        "## 预登录与开服", "",
        "| 日期 | 节点 | 说明与来源 |", "| --- | --- | --- |"
    ]
    for m in MILESTONES:
        s = m["sources"][0]
        lines.append(f"| {m['date']} | {m['title']} | {m['description']} [来源]({s['url']}) |")
    lines += [
        "| 2016-10-14 | 全平台公测 | 作为下表1.0的起点。[同期公告转载](https://www.18183.com/bh3rd/201610/713481.html) |", "",
        "旧官网保存的‘预登录活动火热进行中’消息标注为 **2016-08-09**。因此网页可以从9月展示‘预登录进行中’，但不能把9月17日写成预登录首日。可在项目的[旧官网文本](../home/archive/text/index.html)中查看这条消息。", ""
    ]
    current_year = None
    for row in versions:
        year = row["date"][:4]
        if year != current_year:
            current_year = year
            lines += ["", f"## {year}年", "", "| 国服更新日 | 版本 | 新增装甲与其他角色 | 大型活动 | 剧情与重要玩法 | 来源 |", "| --- | --- | --- | --- | --- | --- |"]
        suffix = "†" if row["version"] in pending else ""
        selected = [s for s in row["sources"] if s["kind"] != "community"]
        links = "、".join(f"[{SOURCE_LABEL[s['kind']]}{i + 1 if len(selected) > 1 else ''}]({s['url']})" for i, s in enumerate(selected))
        ev = "；".join(e["title"] for e in row["majorEvents"]) or "—"
        highlight = "；".join(row["storyAndFeatures"]) or "—"
        lines.append(f"| {row['date']}{suffix} | **{row['version']} {row['title']}** | {cast_text(row)} | {ev} | {highlight} | {links} |")
    lines += ["", "## 容易混淆的版本归属", ""]
    for v in ["1.0", "1.3", "3.4", "3.8", "4.3", "4.5", "4.9", "6.4", "6.7", "7.3", "7.6", "8.8", "9.0", "9.1"]:
        for note in lookup[v]["notes"]:
            lines.append(f"- **{v}**：{note}")
    lines += [
        "", "## 网页数据", "",
        "[timeline.zh-CN.json](timeline.zh-CN.json)保存预登录与开服节点、82条版本记录及逐条来源。主键采用cn加版本号，日期精度区分月份和日期；character.kind用于区分装甲、增幅、协同者、人偶与活动限定角色。", "",
        "[official-steam-updates.json](official-steam-updates.json)保存国服官方Steam公告的标题、时间和要点，用于核对5.4至9.1。Steam条目的国服应用ID为1668940。", "",
        "[build-timeline.py](build-timeline.py)生成本表与JSON，并检查连续版本、日期顺序、截止日期和分类。[collect-official.ps1](collect-official.ps1)可重新读取国服官方公告。", "",
        ""
    ]
    if pending:
        lines += ["## 日期待补官方维护公告", "", "以下日期已按版本索引归位，发布网页前可逐条补入当年的官方维护通知：", "", "、".join(pending) + "。", ""]
    return "\n".join(lines)

if __name__ == "__main__":
    validate()
    (ROOT / "timeline.zh-CN.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "README.md").write_text(markdown(), encoding="utf-8")
    print(json.dumps({"versions": len(versions), "milestones": len(MILESTONES), "officialRecent": len(by_version), "datesNeedingPrimary": sum(v["verification"]["date"] == "community-index-needs-primary-date" for v in versions), "first": versions[0]["date"], "last": versions[-1]["date"], "output": str(ROOT / "timeline.zh-CN.json")}, ensure_ascii=False))
