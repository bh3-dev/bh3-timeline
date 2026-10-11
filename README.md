# 崩坏3 · 十年时光档案

从 2016 年 9 月预登录进行中到 2026 年 10 月 11 日，展示 `research/` 中的国服版本、B站视频与社区记忆。使用官网公开的十周年主视觉、标识与视频原稿封面，图片来源保存在 `assets/sources.json` 和 `assets/covers/manifest.json`。

## 本地开发

需要 Node.js 20 或更新版本，无需安装依赖。

```powershell
git clone https://github.com/bh3-dev/bh3-timeline.git
cd bh3-timeline
npm run dev
```

打开 <http://127.0.0.1:5173>。端口可通过环境变量 `PORT` 修改。

```powershell
npm test
npm run build
npm run preview
```

`dist/` 为可托管到任意静态服务器的完整网站，也可直接双击 `dist/index.html` 离线浏览，无需启动服务。构建会嵌入当前研究资料，并保留所有本地图片。外部视频与来源链接仍需网络。

源码首页通过 HTTP 加载 JSON，因此开发时请使用 `npm run dev`。预览命令同样使用 5173 端口，请先停止开发服务器。

## GitHub Pages 部署

网站地址：<https://bh3-dev.github.io/bh3-timeline/>。

推送到 `main` 后，`.github/workflows/pages.yml` 会先校验研究数据，再构建并部署 `dist/`。在仓库 Settings → Pages 中选择 **GitHub Actions** 作为发布来源，也可在 Actions 中手动运行部署。

所有站内资源均使用相对路径，支持 GitHub Pages 的 `/bh3-timeline/` 子目录。`dist/` 和本地截图不提交，由工作流生成发布产物。时间轴独立部署，不再打包旁边的 2016 年旧官网目录。

## 功能与数据

- 11 个年份的导航与全部年份浏览，正序／倒序。
- 82 个版本、3 个启航节点、56 条视频、27 个社区节点。
- 按版本、影像、社区筛选，全局搜索版本、角色、活动、作者或梗。
- 详情弹窗保留角色种类、日期口径、累计热度快照、证据状态和原始来源。
- 每个节点的「社区回声」展示 3 位不同署名用户的真实评论节选，共 504 段；保留平台、日期、原帖和同期／后来讨论的区分。
- 版本／影像／社区关联跳转，13 组影像话题与 12 个社区梗词条。
- 单条记忆分享链接，URL 保存年份、筛选、排序与关键词。
- 移动端布局、键盘操作、原生对话框与减少动画偏好。

首页默认从 2016 年开始。搜索自动展开全部年份；可再次选择年份缩小范围。

更新 `research/` 的三个时间轴 JSON 后，刷新即可使用新资料；重新构建更新发布产物。社区评论使用独立的 `research/discussions.zh-CN.json`，采集与节选方法见 [讨论资料说明](research/discussions.md)。图片封面可运行 `python scripts/fetch-covers.py` 更新，失败项会保留明确状态，网页会显示文字封面。脚本不会改写研究资料中的播放量快照。

这是玩家制作的纪念档案，非官方网站。游戏与官方图片版权归 miHoYo 所有，视频作品版权归原作者所有。
