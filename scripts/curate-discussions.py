"""Reviewed selections; IDs resolve to the saved public source comments."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / 'research/discussion-selections.json'
selections = json.loads(path.read_text(encoding='utf-8'))

def set_node(node, context, source, ids):
    selections[node] = {'context': context, 'quotes': [
        {'source': key, 'comment': str(comment)} if isinstance(item, tuple)
        else {'source': source, 'comment': str(item)}
        for item in ids
        for key, comment in ([item] if isinstance(item, tuple) else [(source, item)])
    ]}

early = '开服前开场 CG 原稿下，玩家多年后重返起点的回忆。未取得本节点公告的可读用户留言，因此以关联影像补充，不作为同期反馈。'
for node in ['pre-registration', 'android-non-reset-test', 'ios-launch']:
    set_node(node, early, 'beta-pv', ['153745135440', '153786105664', '1129090494'])
set_node('cn-1.0', '早期公测宣传原稿下的同期留言，以及玩家对初版内容的回顾。', 'launch-2016', ['147363582', '147299753', ('cn-1.3', '207212000')])
set_node('zero-point-98', '概率争议回顾文章下的后来讨论。玩家对概率口径的解释仍有分歧，所引内容是个人意见，不用于认定事件事实。', 'community-zero98', ['120327293360', '141592148720', '184570402544'])
set_node('wuxueyou', '玩家俚语合集下，对角色简称、旧配装和「时代的眼泪」的补充。未取得「勿雪游」口号原帖的可读留言。', 'wuxueyou-taptap', ['41723909', '41718785', '41727471'])
set_node('bridge-interaction', '玩家保存旧互动画面的视频下，关于互动变更的同期讨论。', 'community-bridge-interaction', ['590435417', '591018463', '592361918'])
set_node('stigma-renaming', '圣痕改名整理视频下的同期意见与谐音玩梗。', 'community-stigma-renaming', ['599926624', '603058009', '602293529'])
set_node('stop-spending-new-s', '2.3 前瞻 PV 评论区中的停氪表态，以及玩家对退坑舆论的不同态度。未作为口号首创记录。', 'cn-2.3', ['765601494', '765566760', '765565946'])
set_node('zoro-anniversary', '二周年制作组说明原帖下的同期评论，保留批评、玩梗与期待。', 'zoro-taptap', ['29710100', '29706768', '29706825'])
set_node('big-month-card', '官方外挂处理说明与玩家专门讨论帖下的同期留言。', 'big-card-taptap', ['32298824', ('card-forum', 'floor-9'), ('card-forum', 'floor-13')])
set_node('level-break-priarm', '3.4 超限武器前瞻公告下的同期讨论，既有担忧，也有对旧角色得到出场机会的期待。', 'priarm-taptap', ['60443233', '60422275', ('priarm-discussion', 'push-2')])
set_node('white-river', '「白衣渡江」梗回顾视频下的玩家复读与怀旧，不作为最早截图的评论记录。', 'community-white-river', ['125487744480', '125495111616', '125485707088'])
set_node('guoji-zero', '国记零全剧情录像下，对阵营局势与舰长线的同期讨论。', 'community-guoji-zero', ['2816905338', '2816517163', '2817893938'])
set_node('raven-island', '渡鸦打滚剧情原声视频下的同期玩梗与动作讨论。', 'community-raven-original', ['2913461065', '2910310869', '2911679654'])
set_node('welfare-version-42', '4.2 直播回顾帖下，玩家对福利、肝度和深渊改动的同期意见。', 'welfare-taptap', ['128050809', '128188454', '128304457'])
set_node('aileen-fan', '官方小剧场原稿下，用户对「我是你的粉丝」台词的同期反应。', 'community-aileen-fan', ['3369187764', '3369254901', '3368934421'])
set_node('senti-memes', '4.6 宣传 PV 下，玩家围绕符华与识之律者的同期玩梗。', 'cn-4.6', ['4028319380', '4028370529', '4028657557'])
set_node('bunny-controversy', '4.8 PV 下的同期发言，以及海外周年剧情留档下的后来讨论。所引内容是个人意见，侧重玩家对事件和沟通方式的看法。', 'cn-4.8-corrected', ['4462828543', '4463060918', ('community-bunny-original', '233457334208')])
set_node('krishna-runover', '「创死他！克利希娜！」二创原稿下的同期谐音玩梗。', 'community-krishna', ['101213275328', '101214012864', '101214251216'])
set_node('artbook-race', '原画集限购总量上调说明下，玩家对名额、全勤与代币规划的同期讨论。', 'artbook-taptap', ['191255624', '191267066', '191300000'])
set_node('aimen', '「爱门」梗介绍视频下的玩家复读与回应，不作为梗首创记录。', 'community-aimen', ['132046973248', '132056895152', '132073465712'])
set_node('100-greater-than-175', '100SP＞175SP 梗介绍视频下，对渡鸦与李素裳的同期玩梗。', 'community-sp-meme', ['134659529744', '134661043328', '134661831040'])
set_node('stigma-plan-talk', '圣痕计划剧情解析帖下的同期提问和吐槽。玩家解读可能随剧情更新变化。', 'stigma-plan-taptap', ['194818575', '194928556', '194822852'])
set_node('finality-design-debate', '终焉设计与官方回复讨论帖中的同期发言，节选不同态度。', 'finality-forum', ['floor-6', 'floor-14', 'floor-12'])
set_node('captainverse-ending', '舰长线全剧情解析视频下，对摆渡人与结局的同期讨论。', 'community-captainverse', ['184341959280', '184165075392', '184134374784'])
set_node('part2-launch-debate', '第二部总评讨论帖下，对操作、角色与玩法的不同意见。来自台服社区，留言时间为 2024 年 4 月。', 'part2-forum', ['floor-9', 'floor-11', 'floor-16'])
set_node('vita-sama', '「薇塔大人」梗介绍视频下，对角色、周年庆与抽卡的同期讨论。', 'community-vita-sama', ['242504767921', '242612749248', '242618142256'])
set_node('elysia-return-banter', '「又在卖爱莉希雅」讨论帖下的同期回应，保留喜爱与立绘争议。', 'elysia-ptt', ['push-1', 'push-2', 'push-3'])
set_node('part2-finale-discussion', '第二部终章全流程视频下，对剧情与人物收束的同期讨论。包含剧透。', 'community-part2-finale', ['312541247184', '309231840449', '312501090704'])
set_node('ten-years-memory', '十周年祝福活动原帖下的玩家留言。节选祝福正文，不展示游戏 UID 或回归码。', 'anniversary-taptap', ['400663468', '400490230', '400487115'])

revisions = {
    'cn-1.3': ['207212000', '206889360', '2532841073'],
    'cn-1.5': ['263505556', '263510938', '263563099'],
    'cn-1.6': ['303155345', '303284332', '303363199'],
    'cn-2.0': ['572137679', '572151062', '572170317'],
    'cn-2.3': ['765548490', '765566760', '765555451'],
    'cn-2.5': [('cn-2.5-taptap', '25755394'), ('cn-2.5-taptap', '25756402'), ('cn-2.5-taptap', '25755589')],
    'cn-2.6': ['1056592293', '1057114660', ('cn-2.6-taptap', '28683634')],
    'cn-3.3': ['1758410799', '1758334489', '1758426066'],
    'cn-3.8': [('cn-3.8-taptap', '91449769'), ('cn-3.8-taptap', '91372863'), ('cn-3.8-taptap', '91400975')],
    'cn-4.1': ['3124806201', '3124826562', '3124960747'],
    'cn-4.3': ['3513332388', '3513403022', '3513301083'],
    'cn-5.1': ['5158774906', '5158568675', '5159486434'],
    'cn-5.5': ['99481447488', '99483369184', '99488430832'],
    'cn-7.4': ['213662191040', '213662432208', '213663011552'],
    'cn-7.8': ['242199027280', '242122953857', '242197881360'],
    'cn-8.6': ['281961703073', '283865271328', '281961775201'],
    'cn-8.8': ['296955618192', '296952109184', '296953262464'],
    'cn-9.1': ['317958035392', ('anniversary-taptap', '400490230'), ('anniversary-taptap', '400663468')],
}
for node, ids in revisions.items():
    set_node(node, '本版本宣传 PV、公告或相关同期帖子中的用户留言。' if any(isinstance(i, tuple) for i in ids) else '本版本宣传 PV 评论区的用户留言。', node, ids)
selections['cn-1.6']['context'] = '「盛夏重逢」PV 下，玩家以「学习使我快乐」段子调侃氪金的同期留言。'
selections['cn-9.1']['context'] = '本版本 PV 与十周年祝福活动中的同期意见和祝福。'
set_node('cn-4.8', '本版本宣传 PV 下的同期留言；该时期评论受到海外周年内容争议影响。', 'cn-4.8-corrected', ['4462828543', '4463060918', '4462152004'])
set_node('cn-6.4', '本版本日配宣传 PV 下，关于配音与终章的同期讨论。', 'cn-6.4-corrected', ['151673998256', '151702257920', '151676322320'])
video_revisions = {
    'scyrax-kiana': ['166247702', '196128297', '166765622'],
    'chuchusha-suoor': ['2633520944', '4061337932', '2342054030'],
    'moon-halo': ['4871908806', '4872313340', '163932745632'],
    'concert-2022': ['127682661968', '127679780464', '127683168160'],
    'concert-2023': ['177799951840', '177801548448', '177836756288'],
    'da-capo': ['154631254208', '154632147568', '154633692320'],
    'anniversary-10-program': ['314469137617', '314704813089', '314472296241'],
    'anniversary-10-fan': ['318467986880', '314945756545', '315077042689'],
}
for node, ids in video_revisions.items():
    set_node(node, '视频原稿评论区的用户留言。', node, ids)

# Contiguous passages from longer comments, reviewed in their original context.
excerpts = {
    ('cn-1.0', '207212000'): '1.0版本 刚刚开服，百废待兴。琪亚娜，芽衣，布洛尼亚3个女武神和12款女武神装甲，无限深渊。半成品游戏',
    ('cn-1.3', '207212000'): '1.3版本 舰团系统上线，新的舰团BOSS-八重樱和黑化姬轩辕加入，家园增加社交系统，新的武器、圣痕和皮肤。半成品游戏',
    ('cn-1.6', '303155345'): '我想买一套模拟题做一做\n只要168块',
    ('zero-point-98', '120327293360'): '他们把“0.98%概率出”和“0.98%概率（含保底）出”给搞混了',
    ('senti-memes', '4028319380'): '嗨符：第一次当律者，只要他们承认我是符华就算成功[呲牙]',
    ('bunny-controversy', '4462828543'): '其实兔女郎装扮对于一个二次元手游来说，真的不算什么，那些打着擦边球的手游人物比比皆是。',
    ('cn-4.8', '4462828543'): '其实兔女郎装扮对于一个二次元手游来说，真的不算什么，那些打着擦边球的手游人物比比皆是。',
    ('finality-design-debate', 'floor-14'): '當然造型本身也有缺點，遠遠看真的就很像螢火蟲skin，但動作本身至少從我以老玩家的角度看是有點欣慰的。',
    ('finality-design-debate', 'floor-12'): '一派客人說讚喔 一派客人說爛喔一邊講說伸懶腰很沒格調 一邊講說好棒棒好有涵義',
    ('part2-launch-debate', 'floor-11'): '原本是為了補劇情才玩的，但全部亂成一團，主線打到一半要我去玩櫻色輪迴，輪迴打到一半又要打後崩，原本想好好打第一部結果第二部一直插進來，',
    ('ten-years-memory', '400663468'): '崩坏三十周年快乐！愿我们未来还有一个又一个十周年',
    ('ten-years-memory', '400490230'): '我是崩坏三九周年入坑的，崩坏三，十周年快乐',
    ('ten-years-memory', '400487115'): '愿休伯利安的舰桥永远灯火通明，愿每一位舰长都还能在某个版本更新夜里，找回第一次抽到心头好时那种纯粹的开心',
    ('cn-9.1', '400490230'): '我是崩坏三九周年入坑的，崩坏三，十周年快乐',
    ('cn-9.1', '400663468'): '崩坏三十周年快乐！愿我们未来还有一个又一个十周年',
    ('cn-7.4', '213663011552'): '刚刚前瞻本来弹幕有气无力的老几样节奏已经让我有点提不起欢愉的劲儿了，但是猛然间看到一个特别顶级的：“你妹妹崩铁都在蹭芽衣的热度了，你还在这儿寻梦者。”',
}
for (node, comment), text in excerpts.items():
    for quote in selections[node]['quotes']:
        if quote['comment'] == comment:
            quote['excerpt'] = text

path.write_text(json.dumps(selections, ensure_ascii=False, indent=2), encoding='utf-8')
