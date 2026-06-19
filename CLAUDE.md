# CLAUDE.md

BoxMusic —— 一个把 Dropbox 当曲库的个人音乐播放器。仓库里有两个实现，共享同一套 Dropbox App folder（`/Apps/ZhonghuiPlayer/`）作为音乐源。

## 仓库结构

| 目录 | 是什么 | 状态 |
|---|---|---|
| `CLI/` | 早期的命令行版本（Python + VLC） | 已能用，基本不再大改 |
| `WEB/` | 当前在开发的网页版本（Vue 3 + Vite） | 开发中，重点在这里 |
| `WEB/PLAN.md` | 网页版的设计方案 / 开发计划 | **改 WEB 前先读，它是设计权威** |

## CLI（命令行版）

Python 3.8.10 / macOS，依赖本机装好 VLC（和 vim）。

- `main.py` —— 主程序：读 manifest、播放、播放模式（默认/单曲循环/随机）、后台线程预取下一首，支持音频和视频。
- `player.py` —— `AudioPlayer`，封装 python-vlc 的 `MediaPlayer`。
- `manager.py` —— `WorkerThread` 后台循环。
- `message.py` —— 带时间戳的日志输出。
- `update_manifest.py` —— **本地扫描脚本**：遍历本机 `~/Dropbox/Apps/ZhonghuiPlayer/`，生成 manifest（`D/目录`、`F/文件` 两类行）。WEB 版「本地脚本生成索引」的思路就源自这里。
- `convert_to_audio.py` —— 用 moviepy 从视频里提取音频。
- 依赖见 `CLI/requirements.txt`（`dropbox==12.0.2`、`python-vlc==3.0.21203`）。
- 运行：`cd CLI && python3 main.py`。

## WEB（网页版，当前重点）

纯前端 SPA，对 Dropbox **只读**；索引由本地脚本生成后上传到 Dropbox 固定位置 `/metainfo/index.json`，网页只下载读取、不写、不扫描。完整设计见 `WEB/PLAN.md`。

技术栈（精确锁版本，见 `WEB/package.json`）：Vue 3.5.38 + Vite 8.0.16 + Pinia 3.0.4 + vue-virtual-scroller 3.0.4。Node 24 LTS。

常用命令（在 `WEB/` 下）：

```bash
npm install      # 首次
npm run dev      # 本地开发 http://localhost:5173/
npm run build    # 产出静态文件到 dist/
npm run preview  # 预览构建产物
```

## 约定与注意

- **设计原则（从简）**：功能不追求多，追求稳定、安全、好维护。写代码前先想是不是最简单稳定的实现，不该写的别写。改 WEB 时不要擅自加 PLAN.md 里已砍掉的功能（收藏夹、命名歌单、深色模式、键盘快捷键等）。
- **Dropbox App folder**：两版共用 `/Apps/ZhonghuiPlayer/`，API 路径里的 `/` 即该目录根。WEB 用只读权限（`files.metadata.read` + `files.content.read`）。
- **密钥**：`CLI/token.txt` 是 Dropbox 凭证，已被 `CLI/.gitignore` 忽略，**不要提交**。
- **提交习惯**：只在用户明确要求时提交；提交信息用中文（与现有 git history 一致）。
- **`.gitignore` 分三份**：根目录只忽略 `.DS_Store`；`CLI/.gitignore` 面向 Python（含 `token.txt`、`Cache/`、`manifest.txt` 等）；`WEB/.gitignore` 面向 Node。
