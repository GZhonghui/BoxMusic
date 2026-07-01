# Dropbox 音乐播放器 — 设计方案（精简版）

> 设计原则：**只读、简单、好维护**。Web 应用对 Dropbox **永远只读**，不写入任何文件；不做扫描。索引由用户在本地用脚本扫描后，上传到 Dropbox 的固定位置 `/metainfo/index.json`。

> 代码原则：功能不追求多，追求稳定安全，好维护（不要让我读你写的屎山代码），写代码之前想想是不是最简单最稳定最好维护的实现，不该写的代码就不要写。追求从简

## 一、整体架构

**纯前端 SPA**，无后端。所有逻辑跑在浏览器里，且**对 Dropbox 只读**。

```
浏览器 (Vue 应用)
  ├─ Dropbox API (OAuth token / files.download / get_temporary_link)   ← 只读
  ├─ localStorage (refresh_token、index 缓存、用户偏好)
  └─ <audio> 元素 (流式播放)

本地脚本（不在本仓库范围）
  └─ 扫描音乐目录 → 生成 index.json → 上传到 Dropbox 的 /metainfo/index.json
```

数据流：
- **凭证**：用户输入 refresh_token → 存 localStorage → 每次启动用它换 access_token（短时，存内存）
- **元数据**：Dropbox 上的 `/metainfo/index.json` 为权威源（由本地脚本维护），本地 localStorage 镜像一份做秒开
- **音频**：临时直链流式播放，不下载到本地

> ⚠️ Web 应用**不会**写 Dropbox、**不会**扫描文件夹。索引的生成与更新完全由本地脚本负责。

---

## 二、页面 UI 设计

只用一个单页，按区域划分。核心思路：**左侧是一栏带 Tab 切换的列表（文件夹浏览 / 播放队列，一次只显示一个），可折叠、有最小宽度；右侧是大面积的「沉浸区」——展示封面或歌词，吃掉剩余空间、内容自适应居中。** 建议布局（桌面优先，可响应式到手机）：

```
┌─────────────────────────────────────────────────────────────┐
│ 顶部栏                                                        │
│  Logo · 搜索框 ──────────────────────  状态指示 · 设置按钮      │
├──────────────────────┬──────────────────────────────────────┤
│ ‹ [浏览 | 队列]       │  右侧 — 沉浸区（吃掉剩余空间）         │
│  ┌ 面包屑 ──────────┐ │                                      │
│  │ Music/华语/周杰伦 │ │          ╭───────────────────╮        │
│  └────────────────┘ │          │                   │        │
│  📁 2000 七里香       │          │    封面图（大）     │        │
│  📁 2004 叶惠美       │          │  圆角+阴影+玻璃感   │        │
│  🎵 晴天        ▶    │          │                   │        │
│  🎵 稻香             │          ╰───────────────────╯        │
│  …（虚拟滚动）        │             歌名 · 歌手               │
│  〔最小宽度 / 可折叠〕 │           [ 封面 | 歌词 ] 切换         │
├──────────────────────┴──────────────────────────────────────┤
│ 底部播放器（固定）                                            │
│  小封面 · 歌名/歌手 · ◁ ▷▷ ▷ · 进度条 · 时长 · 音量 · 模式      │
└─────────────────────────────────────────────────────────────┘
```

左侧栏有**最小宽度**（约 `280px`），可点顶部的 `‹` 按钮**折叠**起来（折叠后右侧沉浸区铺满整个宽度）；右侧不设固定比例，**flex 吃掉剩余空间**，封面卡片在其中按可用空间自适应缩放并**水平+垂直居中**。窄屏（手机）改为上下堆叠或用底部 Tab 切「列表 / 正在播放」。

### 关键 UI 元素

**顶部栏**
- 搜索框：跨全部歌曲实时过滤（按歌名/歌手/路径），客户端搜索，无需请求
  - 搜索是「看全部」的入口：平时按文件夹浏览，想找具体歌就搜——所以不需要再单独做一个一万首的平铺列表
  - **结果直接在搜索框下方弹出一个浮层列表**（不开新页面、不用路由），随输入实时刷新；输入为空 / 失焦点空白处 / `Esc` 就收起
  - 结果列表里双击播放（把搜索结果设为队列）、单击选中；结果多时虚拟滚动 + 截断显示「前 N 条」
- 状态指示：显示「已加载 · 12,345 首」「正在加载索引…」「未登录」
- 设置按钮：弹出设置面板

**左侧栏**（单栏 + Tab 切换，可折叠，最小宽度 ~`280px`）
- 顶部一排 Tab：`浏览` · `队列`，**一次只显示一个**，旁边一个 `‹` 折叠按钮
- **Tab：浏览**（文件夹式，核心交互，避免上万首平铺）
  - 用 `index.json` 里每首歌的 `path` 在前端构建一棵目录树，按真实文件夹层级浏览
  - 顶部 **面包屑**：显示当前路径（`Music / 华语 / 周杰伦`），可点任一级跳回
  - 当前目录内容混排，文件夹在前、歌曲在后：
    - `📁 文件夹`：单击进入下一层（面包屑加一级）
    - `🎵 歌曲`：双击播放；鼠标悬停时行尾显示「＋」按钮，单击把该首追加到当前队列末尾（不打断正在播放）
  - 只渲染「当前这一层」的条目，单层通常几十条，虚拟滚动作为兜底
- **Tab：队列** — 当前播放队列，平铺列表，支持：
  - 拖拽 / 删除单曲、点歌跳播
  - 顶部「清空队列」按钮
  - 高亮当前播放项
- 单击歌曲 = 选中（右侧沉浸区随之更新）

**播放与队列的关系**（只有一个「当前播放队列」，不做收藏夹、不做手动建歌单）
- 在某个文件夹里双击一首歌 → 把**该文件夹内（不递归）的所有歌曲**按显示顺序设为队列，并从双击那首开始播放
- 在搜索结果里双击一首歌 → 把搜索结果设为队列，从该首开始
- 队列会**持久化到 localStorage**：刷新 / 重开浏览器后恢复上次的队列与当前曲（恢复后停在当前曲、不自动播放），但仍**不固化成命名歌单**（只有唯一的临时队列，可随时增删/排序/清空）。失效项（索引里已不存在的歌）只在重新加载索引后清理，见 §八第 11 步

**右侧 — 沉浸区**（大面积视觉焦点，封面 / 歌词二选一）
- 顶部一个分段切换：`封面` | `歌词`
- **封面视图**：
  - 居中的大封面卡片，**圆角 + 柔和投影（drop shadow）+ 玻璃拟态（frosted glass / backdrop-blur）**
  - 背景：用封面图放大模糊后铺底，叠一层半透明渐变，营造氛围
  - **正在播放的那一首**顺带读取其内嵌封面（反正要访问这个文件）；读不到 / 无内嵌封面 / 跨域受限 → 回退 `settings.default_cover`（再无则占位渐变 + 歌名首字）。**不批量为全部文件提取封面**（违背只读/从简）。
  - 下方显示歌名 · 歌手
- **歌词视图**：
  - 若该曲在 `index.json` 里带 `lrc`，从 Dropbox 拉取并解析，逐行显示、当前行高亮、随播放进度滚动居中
  - 没有歌词时给出「暂无歌词」占位
- 切换在两个视图间做淡入淡出过渡

**底部播放器**（始终可见）
- 当前曲目信息（小封面 + 歌名/歌手）
- 控制：上一首 / 播放暂停 / 下一首
- 进度条：可拖动 seek
- 音量条
- 播放模式：顺序 / 单曲循环 / 列表循环 / 随机

**首次进入 / 未登录态**
- 全屏引导：「请粘贴你的 Dropbox refresh token」+ 输入框 + 帮助链接
- 帮助文档说明：如何在 Dropbox 开发者后台拿到 token、PKCE 流程注意事项

**索引加载**
- 启动时下载 `/metainfo/index.json`，显示「正在加载索引…」短暂态即可（一次下载，不是扫描）
- 如果 Dropbox 上不存在该文件 → 提示「索引尚未生成，请先在本地运行扫描脚本上传到 /metainfo/index.json」

**设置面板**
- 重新加载索引按钮（强制重新下载 `/metainfo/index.json`，忽略本地缓存）
- 清除凭证按钮（退出登录）
- 关于 / 版本号

> 注：没有「文件夹路径」设置（索引位置固定），也没有「重建索引」按钮（扫描在本地脚本里做）。

---

## 三、功能清单

### 必备
1. **登录**：输入并保存 refresh_token
2. **加载索引**：启动时从 `/metainfo/index.json` 下载，本地缓存做秒开
3. **文件夹浏览**：用路径构建目录树，按层级进入，面包屑导航（替代上万首平铺列表）
4. **搜索过滤**：跨全部歌曲实时搜索歌名/歌手/路径（找具体歌的入口）
5. **播放**：流式播放，支持 seek
6. **播放队列**：唯一的队列概念。双击文件夹内某首 = 把该文件夹（不递归）所有歌曲入队并从该首播；上一首/下一首、自动连播；可手动增删/排序/清空
7. **播放模式**：顺序/单曲循环/列表循环/随机
8. **设置**：重新加载索引、退出登录

### 加分项（按优先级）
1. **歌词显示**（如果 Dropbox 同目录有同名 .lrc 文件就一起拉）

### 不做
- **任何写入 Dropbox 的操作**（上传索引、删除文件等）
- **在应用内扫描 / 重建索引**（交给本地脚本）
- **增量同步 / cursor 机制**（索引整体替换即可）
- **收藏夹**
- **手动创建 / 命名歌单**（只保留一个临时播放队列）
- ID3 标签解析取歌名/歌手（这些由本地脚本从文件名解析；唯一例外：播放时为取内嵌封面读一次标签）

---

## 四、数据结构

### Dropbox 上的 `index.json`（固定路径 `/metainfo/index.json`）

由本地扫描脚本生成并上传，Web 应用只读取。

```jsonc
{
  "version": 1,
  "generated_at": "2026-06-18T10:00:00Z",   // 本地脚本生成时间
  "settings": {                              // 全局设置（由本地脚本写入）
    "default_cover": "/metainfo/default.jpg", // 歌曲没有专辑图时统一回退用这张
    "root_label": "Music"                     // 可选：面包屑根节点显示名
  },
  "files": [
    {
      "path": "/Music/周杰伦 - 晴天.mp3",  // App folder 内的相对路径，作唯一标识
      "name": "周杰伦 - 晴天.mp3",
      "artist": ["周杰伦"],           // 列表：0 到多个歌手，本地脚本按 , / ; / & 分割
      "title": "晴天",                // 本地脚本解析得到
      "lrc": "/Music/周杰伦 - 晴天.lrc"    // 可选：同目录同名歌词文件路径
    }
  ]
}
```

- **App folder 路径**：应用用 `App folder` 权限，API 里的 `/` 就是 App 文件夹根目录（无需也不要写 `/Apps/<AppName>/` 前缀）。`/metainfo` 即 App 根下的 metainfo 目录；音乐、`metainfo/`、`default_cover` 都放在 App 文件夹内；索引固定 `/metainfo/index.json`，应用内不可配置。
- **用 `path` 作唯一标识**：`get_temporary_link` / `download` 都支持按 path 调用。**不存 `id`**——本地扫的是 online-only 占位文件，文件系统里没有 Dropbox 的 `id`（那是 API 概念），拿不到。
- **`settings`**：全局配置区，由本地脚本维护。目前放 `default_cover`（封面图）等；后续要加全局项都往这里塞，Web 应用只读。
- **没有 `size`**：online-only 占位文件本地扫描读出的 size 是 0 不可靠，所以不存；应用也用不到。
- **没有 `cover`**：`index.json` 不单独存封面图、也不批量提取内嵌封面。Web 应用只对**正在播放的单首**顺带读其内嵌封面（`jsmediatags` 走 Range 只读标签字节，不整文件下载）；读不到 / 无内嵌封面 / 跨域受限就回退 `settings.default_cover`（无则占位渐变）。
- 不再需要 `cursor`（应用不做增量同步）。
- 文件名解析（artist / title）由本地脚本完成，Web 应用直接用现成字段。`artist` 是**列表**（0 到多个歌手，脚本按英文逗号 `,` / 分号 `;` / 和号 `&` 分割，每名去前后空格）；`/视频` 一级目录下命名为「歌名 - 歌手」（反序），其余目录「歌手 - 歌名」。

### localStorage 键

| key | 内容 |
|---|---|
| `dbx_refresh_token` | refresh token |
| `dbx_app_key` | app key |
| `dbx_app_secret` | app secret（刷新 token 需要） |
| `index_cache` | 本地 index.json 副本（用于秒开） |
| `index_cache_rev` | 远端 index 的 rev/版本号，判断要不要重拉 |
| `settings` | `{ play_mode, volume }` |
| `queue` | 播放队列快照 `{ items: [song...], index }`（刷新后恢复，见 §八第 11 步） |

> 注：`index_cache` 约 1–3MB（万级曲库），在 localStorage ~5MB 上限内没问题；若日后曲库涨到几万首接近上限，再换 IndexedDB。

### 内存状态（Pinia / ref）

- `accessToken` — 短时令牌
- `currentTrack` — 正在播放的曲目
- `queue` — 当前播放队列（变化时镜像写入 localStorage `queue`，启动时恢复）
- `currentIndex` — 队列中位置（随 `queue` 一并持久化 / 恢复）
- `isPlaying` / `progress` / `volume`

---

## 五、核心流程

### 流程 1：首次启动

```
1. 读 localStorage 看有没有 refresh_token
   ├─ 没有 → 显示登录引导页
   └─ 有 → 进入第 2 步
2. 用 refresh_token 换 access_token（POST /oauth2/token）
   ├─ 失败 → 清除 token，回到登录页，提示「凭证已过期」
   └─ 成功 → 进入第 3 步
3. 先用 localStorage 的 index_cache 渲染界面（秒开），同时后台校验/更新索引（流程 2）
   ├─ 没有缓存 → 直接走流程 2 拉取
```

### 流程 2：加载索引（只读）

```
1. 调 /files/get_metadata { path: "/metainfo/index.json" } 拿 rev
   ├─ 文件不存在 → 提示「索引尚未生成，请先在本地运行脚本上传到 /metainfo/index.json」
2. 比较 rev 与本地 index_cache_rev
   ├─ 相同 → 用本地缓存，结束
   └─ 不同或无缓存 → 进入第 3 步
3. 调 /files/download { path: "/metainfo/index.json" } 下载
4. 解析 JSON → 更新内存列表 → 刷新 UI
5. 写入 localStorage：index_cache + index_cache_rev
```

> 「重新加载索引」按钮 = 跳过 rev 比较，强制执行第 3 步。

### 流程 3：播放

```
1. 用户双击歌曲（或队列中切歌）
2. 调 /files/get_temporary_link { path: id_or_path }
3. 拿到 link（4 小时有效）→ 设给 <audio src>
4. 监听 audio 事件：
   - timeupdate → 更新进度
   - ended → 自动切下一首
   - error → 提示用户、跳下一首
5. seek 是浏览器自己做的 Range 请求，Dropbox 直链支持，无需我们处理
```

### 流程 4：access token 刷新

- access token 默认 4 小时过期
- 每次 API 调用前检查 expires_at，提前 5 分钟刷新
- 包一个 `fetchWithAuth` 拦截器统一处理

---

## 六、技术栈

| 用途 | 选型 | 理由 |
|---|---|---|
| 框架 | Vue 3 + `<script setup>` | 指定 |
| 构建 | Vite | 静态产物，部署到任何静态托管 |
| 状态 | Pinia | 比 vuex 简洁 |
| 虚拟滚动 | `vue-virtual-scroller` | 一万行必须有 |
| 样式 | Tailwind 或纯 CSS | 看偏好 |
| HTTP | 原生 fetch | 无需 axios |
| 图标 | `lucide-vue-next`（Vue 3 版）或直接内联 SVG | 轻量；图标少可省掉依赖 |

### 版本记录（截至 2026-06-19，本机环境 + 各包当时最新版）

本机运行时：

| 运行时 | 版本 |
|---|---|
| Node | v24.17.0（LTS: Krypton，nvm 默认） |
| npm | 11.13.0 |
| pnpm | 11.7.0 |

> 已从非 LTS 的 23.10.0 切到 **Node 24 LTS**，满足 Vite 8 的 Node `20.19+` / `22.12+` 要求。

依赖（锁版本，不带 `^`，提交 lockfile）：

| 包 | 版本 |
|---|---|
| vue | 3.5.38 |
| vite | 8.0.16 |
| @vitejs/plugin-vue | 6.0.7 |
| pinia | 3.0.4 |
| vue-virtual-scroller | 3.0.4 |
| tailwindcss | 4.3.1 |
| lucide-vue-next | 待定（用前 `npm view lucide-vue-next version` 核对当前版） |

> Tailwind 是 v4（配置方式与 v3 不同，用 CSS-first 配置，无 `tailwind.config.js` 也可）。若嫌重，纯 CSS 也够用。

**部署**：构建产物全是静态文件，可部署到 GitHub Pages / Cloudflare Pages / Vercel / 本地 file:// 直接打开都行（注意 file:// 协议下某些浏览器对 fetch 有限制，建议起个本地静态服务器）。

---

## 七、容易踩的坑

1. **Dropbox 速率限制**：免费账号有调用频率限制。命中 429 时按 `Retry-After` 退避（只读场景调用很少，基本不会撞到）。
2. **token 失效**：refresh_token 也可能被用户主动撤销，每次启动要处理 401 → 回登录页。
3. **索引不存在**：`/metainfo/index.json` 没生成时要给出清晰提示，引导用户去跑本地脚本，而不是报错卡死。
4. **CORS**：Dropbox API 都支持 CORS，但临时链接的域名是 `dl.dropboxusercontent.com`，浏览器播放时不需要 CORS 头（`<audio>` 不受 CORS 限制），但如果想画波形图就要了。
5. **虚拟滚动 + 搜索**：搜索过滤后列表变短，virtual scroller 需要 reset 滚动位置。
6. **iOS Safari 限制**：音频播放必须由用户手势触发第一次。自动连播没问题，但页面打开后不能自动开播。
7. **大 index.json**：一万首大概 1-3MB JSON。下载可接受。如需更小，可让本地脚本生成 `.json.gz`，前端解压。

---

## 八、建议的开发顺序

每一步都能独立验证，不会陷入「写了一周还没东西能跑」的状态。每步给出 TODO 和验证项（✅ = 这步算完成的判据）。

> **当前进度**（截至 2026-06-19）
> - [x] **第 1 步：登录 + token 刷新** —— 已完成并验证（commit `e0a4fbe`）
> - [x] **本地索引生成脚本** —— `scripts/build_index.py` 已就绪并实跑生成 `index.json`（第 2 步的前置）
> - [x] **第 2 步：下载并解析 `/metainfo/index.json`** —— 已完成并验证（实测加载 5242 首）
> - [x] **第 3 步：文件夹浏览器 + 面包屑导航** —— 已完成并验证
> - [x] **第 4 步：播放器 + 队列（MVP）** —— 已完成并验证
> - [x] **第 5 步：本地缓存 + rev 校验秒开** —— 已完成并验证
> - [x] **第 6 步：搜索（跨全部）+ 播放模式** —— 已完成并验证
> - [x] **第 7 步：设置面板 + 样式打磨** —— 已完成（左右布局 / 沉浸区封面卡 / 设置面板 / 折叠 + 窄屏响应式）
> - [x] **第 8 步：歌词显示（加分项）** —— 已完成（拉取并解析 `.lrc`，逐行高亮 + 平滑滚动居中，Apple Music 风格）
>
> 原计划 8 步已全部完成。后续按需追加的小功能：
> - [x] 第 9 步：文件夹视图——单曲加入当前队列（hover「＋」按钮）—— 已完成
> - [x] 第 10 步：搜索结果同样支持 hover「＋」加入队列 + 文件夹浏览滚动位置记忆 —— 已完成并验证
> - [x] 第 11 步：播放队列持久化到 localStorage + 重新加载索引后清理失效项 —— 已完成并验证
> - [x] 第 12 步：Media Session（系统媒体卡片：通知栏 / 锁屏显示封面 + 歌名歌手 + 播放控制）—— 已完成

### 1. 登录 + token 刷新机制（确保 API 能调通）✅ 已完成
实现说明：
- `src/stores/auth.js`：Pinia 鉴权 store。持久化 refresh_token/app_key/app_secret，access_token 只存内存；提前 5 分钟刷新；`login()` 先换 token 校验、成功才落盘；刷新失败/401 → `logout()` 回登录页。
- `src/dropbox/api.js`：`fetchWithAuth()` 拦截器，自动加 Authorization、401 清凭证。
- `src/components/LoginView.vue`：登录引导页（refresh_token / app_key / app_secret 三个输入框）。
- `src/App.vue`：按登录态切换；临时连接测试占位（第 3 步会被真正的应用骨架替换）。
- 凭证方案：改为机密客户端（key+secret，复用 rclone 同一套），见 §九取舍说明。

TODO 验证：
- ✅ 粘贴有效凭证 → 换到 access_token，连接测试返回根目录条目
- ✅ 粘贴无效凭证 → 报错并带 Dropbox 原文
- ✅ token 过期 → 下次调用自动刷新（提前 5 分钟）；401 回登录页

### 2. 下载并解析 `/metainfo/index.json`（核心数据有了）✅ 已完成
> 前置已完成：本地索引脚本 `scripts/build_index.py`（沿用 CLI/update_manifest.py 思路）。
> 扫描本机已同步的 App folder，生成 `metainfo/index.json` 由 Dropbox 客户端同步上传；
> 字段、`settings`、`path` 唯一标识、按 path 排序保证 rev 稳定，均按本节 schema 实现。
实现说明：
- `src/stores/library.js`：Pinia store，`loadIndex()` 走 content 域 `/files/download` 拉 `/metainfo/index.json`（参数放 `Dropbox-API-Arg` 头），`JSON.parse` 进 `files[]` + `settings`。
- 失败只落到 `status`/`error`，不抛错不白屏：409 + `not_found` → 「索引尚未生成」；JSON 解析失败 / 缺 `files` 列表 → 「索引损坏」；其它 → 带 HTTP 原文。
- `src/App.vue`：占位页加「加载索引」按钮显示结果，仅为本步验证（第 3 步会被真正骨架替换）。
- 暂不做 rev 比对 / `index_cache` 秒开缓存（属后续步骤，本步从简）。
TODO 验证：
- ✅ 有索引 → 控制台打出曲目总数（实测 5242 首，与脚本一致）
- ✅ 删掉/改名远端文件 → 出现「索引尚未生成」提示，不白屏
- ✅ 故意上传一个坏 JSON → 有「索引损坏」提示，不崩

### 3. 文件夹浏览器 + 面包屑导航（能按目录看到歌了）✅ 已完成
实现说明：
- `src/lib/tree.js`：纯函数 `buildTree`（由 `files[].path` 建树）/ `nodeAt`（按路径段定位）/ `listEntries`（文件夹在前按名排序、歌曲在后沿用 path 排序）。
  > **排序说明（易误解，勿改错方向）**：`listEntries` 里**文件夹**用 `name.localeCompare()` 排序；**歌曲不做任何 sort**，只原样保留 `node.songs` 的 push 顺序，即 `index.json` 里 `files[]` 的顺序。因本地脚本生成索引时**已按 `path` 排序**（见第 2 步前置说明），同目录内歌曲最终就呈现为 path（≈文件名）顺序——所以「歌曲沿用 path 排序」是靠上游 index.json 保证、而非 tree.js 自己排。展示标题用 `display.js` 的 `trackTitle = file.title || file.name`，与排序基准（path/文件名）不一定一致；若日后要改成「按显示标题排」，需在 `listEntries` 里对 `songs` 显式 `.sort()`，且先与使用者确认基准（title / name / path 是三回事）。
- `src/components/FolderBrowser.vue`：面包屑（根节点用 `settings.root_label`）可逐级跳回；当前目录用 `RecycleScroller` 虚拟滚动兜底；`📁` 单击进入、`🎵` 单击选中（双击播放留第 4 步）。
- `src/App.vue`：占位页换成真正壳子，进入已登录态自动 `loadIndex()`，按 loading / 未就绪 / ready 三态渲染，只有 ready 才显示浏览器。
TODO 验证：
- ✅ 能从根逐层点进到最深目录，再用面包屑跳回任意层
- ✅ 文件夹/歌曲数量与 Dropbox 实际目录一致
- ✅ 某层有几千条时滚动不卡

### 4. 播放器 + 队列（能听了，就是 MVP）✅ 已完成
实现说明：
- `src/stores/player.js`：唯一播放队列 + store 持有的常驻 `<audio>`（切 Tab 不中断）。`playList`/`playAt`/`next`/`prev`/`togglePlay`/`seek`/`setVolume`/`jumpTo`/`removeAt`/`moveItem`（拖拽换序）/`clear`。取直链走 `/files/get_temporary_link`；`ended` 自动下一首；取链失败或媒体 `error` → 提示并跳下一首，队列到底停下；切歌竞态防护。
- `src/components/PlayerBar.vue`：底部常驻播放器（信息 / 上下首 / 播放暂停 / 进度 seek / 音量）。
- `src/components/QueueList.vue`：队列 Tab，高亮当前、双击跳播、删除、原生拖拽换序、清空。
- `FolderBrowser.vue`：双击 = 当前目录（不递归）所有歌入队从该首播；播放中高亮。
- `src/lib/display.js`：标题 / 歌手 / 时间格式化，三组件共用。
- `App.vue`：加 `浏览/队列` Tab（浏览用 v-show 保留导航位置）、播放错误提示条、底部 PlayerBar。
- 播放模式（顺序/循环/随机）按计划留到第 6 步，本步只顺序播放。
TODO 验证：
- ✅ 双击能出声，进度条走动、可拖动 seek
- ✅ 一首放完自动接下一首；上一首/下一首正确
- ✅ 队列里删除当前项、清空、跳播行为正确
- ✅ 拔网/坏链接 → 提示并跳下一首，不卡死

### 5. 本地缓存 + rev 校验秒开（启动变快）✅ 已完成
实现说明：
- `src/stores/library.js` 重构为缓存优先：`load()` 有 `index_cache` 就立即渲染（秒开），再后台 `revalidate(false)`。
- `revalidate(force)`：`get_metadata` 拿远端 `rev` 与 `index_cache_rev` 比对——相同且有缓存则不下载；不同 / 无缓存 / `force` 才 `download()`；远端 `not_found` 清缓存并提示；校验请求失败时有缓存静默沿用、无缓存才报错。
- `download(rev)`：成功后 `writeCache(原文, rev)`；坏 JSON / 缺 files → 「索引损坏」；下载失败同样优先保留缓存。缓存读写全程 try/catch（localStorage 满/不可用不影响播放）。
- `reload()`（「重新加载索引」按钮）= `revalidate(true)` 跳过 rev 比对强制下载。
TODO 验证：
- ✅ 第二次打开「秒开」（先出列表，无网络等待）
- ✅ 本地脚本更新索引后 → 自动检测到 rev 变化并刷新列表
- ✅ rev 没变 → 不重复下载（看 network 面板无 download 请求）

### 6. 搜索（跨全部）+ 播放模式 ✅ 已完成
实现说明：
- `src/components/SearchBox.vue`（放进顶栏，索引就绪才显示）：实时过滤全部 `files`（歌名/文件名/路径/歌手，大小写不敏感），浮层结果用 `RecycleScroller` 虚拟滚动、截断前 200 条并提示总数；空输入 / `Esc` / 点浮层外部收起；结果双击 = 把当前展示的搜索结果设为队列并从该首播。
- `player.js`：`mode`（order/repeat-one/repeat-all/shuffle），`cycleMode()` 循环切换；`onEnded` 按模式分流（单曲重播 / 随机 / 顺序到底停 / 列表循环到头），`next`/`prev` 同样遵循模式；存 `localStorage.settings`（`{play_mode, volume}`，音量一并持久化），启动恢复。坏链顺延刻意保持线性，避免循环/随机模式下无限重试。
- `PlayerBar.vue`：播放器左侧加播放模式按钮（➡️/🔂/🔁/🔀），点击循环切换。
TODO 验证：
- ✅ 输入关键词即时出结果，中文/大小写都能匹配
- ✅ 浮层双击播放后队列 = 搜索结果
- ✅ 四种播放模式行为正确，刷新后模式被记住

### 7. 设置面板 + 样式打磨 ✅ 已完成
实现说明：
- `src/App.vue` 重构为 PLAN §二 的左右布局：顶栏（Logo / 搜索 / 状态 / 设置 ⚙）+ 主体（左侧栏 `width:340px min-width:280px` + 右侧沉浸区 `flex:1`）+ 底部常驻 PlayerBar。左侧栏用 class 控制折叠（`‹` 折叠、左缘 `›` 展开），折叠后沉浸区铺满；`@media(max-width:720px)` 隐藏沉浸区、左侧栏铺满且强制展开。
- `src/components/ImmersiveView.vue`（新）：右侧沉浸区，`封面 | 歌词` 玻璃拟态分段切换（淡入淡出过渡）。封面视图 = 模糊背景铺底 + 居中封面卡（圆角 + 投影 + 玻璃边，`min(46vh,80%,420px)` 自适应缩放居中）+ 歌名/歌手；封面优先用「正在播放」那首的**内嵌封面**（`src/lib/cover.js` 用 `jsmediatags` 对临时直链做 Range 读取，只读标签字节、不整文件下载，只此一首；player.js 持有 `trackCover` objectURL 并管理释放/竞态），读不到再回退 `settings.default_cover`，再无则渐变占位 + 歌名首字。沉浸区跟随「正在播放」曲目（底部 PlayerBar 小封面保持 🎵 占位，不放封面图）。歌词视图先占位（第 8 步实现）。
- `src/components/SettingsPanel.vue`（新）：模态设置面板。重新加载索引（`library.reload()`）、清除凭证（`confirm` 后 `removeItem` 全部 `dbx_*`/`index_cache`/`index_cache_rev`/`settings` 再 `location.reload()`，只删不读）、关于/版本号（读 `package.json` 的 `version`，已置 `0.7.0`）。
- `src/dropbox/api.js`：抽出共享 `getTemporaryLink(path)`，player.js 取直链与封面加载共用；`src/stores/library.js` 加 `coverUrl` + `loadCover()`（同一张图只解析一次，失败留空走占位）。
TODO 验证：
- ✅ 清除凭证后回到登录页，localStorage 相关 key 已清空
- ✅ 封面卡视觉达标，窗口缩放时自适应居中不变形
- ✅ 左侧栏可折叠/展开，手机宽度下布局不破

### 8. 歌词显示（加分项）✅ 已完成
实现说明：
- `src/dropbox/api.js`：加通用 `downloadText(path)`（content 域 `/files/download`，UTF-8 解码；`not_found` 抛 `code='not_found'` 由调用方当「无歌词」处理）。
- `src/lib/lrc.js`：`parseLrc()` 解析时间标（支持一行多标 `[mm:ss.xx]…` 与 `[offset:±ms]`，元数据/空行跳过，按时间升序）→ `[{time,text}]`；解析不出带时间标的行返回空数组（回退纯文本）。`activeLineIndex()` 二分定位当前行。
- `src/components/LyricsView.vue`：跟随 `player.currentTrack.lrc` 拉取解析（按 path 缓存、防切歌竞态）；当前行随 `player.progress` 走，变化时 `scrollTo` 平滑滚动到容器垂直居中（从下往上）。Apple Music 风格：当前行放大（`scale(1.08)`）+ 加粗 + 高亮，其余暗淡，上下渐隐遮罩。状态：无 `lrc`/文件缺失 → 「暂无歌词」；纯文本歌词 → 居中静态展示；加载中/失败有对应提示。
- `src/components/ImmersiveView.vue`：歌词页接入 `LyricsView`（铺满整块、内部自行滚动）。
TODO 验证：
- ✅ 有歌词的歌切到歌词页能逐行高亮、滚动跟随
- ✅ 无 `lrc` 字段的歌显示「暂无歌词」，不报错

### 9. 文件夹视图：单曲加入当前队列（hover「＋」按钮）
> 动机：现在浏览里双击一首 = 用「整个文件夹」替换队列。有时只想把某一首挑出来追加到正在播的队列末尾，而不打断当前播放，也不重置队列。

实现要点（沿用既有最简做法，不引新依赖）：
- `src/stores/player.js`：新增 `enqueue(song)` —— 把该 `song` 追加到 `queue` 末尾。已定两个边界：
  - **纯追加，永不自动播放**：即使队列为空 / 当前无播放（`currentIndex < 0`），点「＋」也只是入队，不动 `currentIndex`、不打断当前曲（要播去队列里双击，更符合直觉）。
  - **允许重复**：同一首点多次就入队多次，不去重（最简单可预测，与 QueueList 的删除/排序自洽）。
- `src/components/FolderBrowser.vue`：歌曲行尾加一个「＋」按钮，默认 `opacity:0`，`.row:hover` 时显示——与 `QueueList.vue` 删除按钮同款写法（纯 CSS `:hover`，`RecycleScroller` 复用 DOM 不受影响）。按钮 `@click.stop` 调 `player.enqueue(item.file)`，避免冒泡触发「选中 / 双击播放」。
- 触屏 / 窄屏无 hover：在 `@media (max-width:720px)` 下让「＋」常显，保证可点。
- 反馈（可选、从简）：点击后按钮短暂变 `✓` 再复原，或不做额外反馈（队列 Tab 的计数 `· N` 会变，本身就是反馈）。

不做：文件夹整体入队、跨文件夹多选入队、把入队做成右键菜单（保持单按钮、最简交互）。

TODO 验证：
- ✅ hover 出现「＋」，点击把该首加到队列末尾，不打断当前播放、不改变选中
- ✅ 队列 Tab 出现新增项，可正常跳播 / 删除 / 拖拽换序
- ✅ 队列为空时点「＋」只入队、不出声；同一首可重复加入
- ✅ 触屏 / 窄屏下「＋」可见可点

### 10. 搜索结果「＋」入队 + 文件夹浏览滚动位置记忆 ✅ 已完成
实现说明：
- `src/components/SearchBox.vue`：搜索浮层每条结果行尾加 hover「＋」按钮，与 `FolderBrowser` 同款（`@click.stop` 调 `player.enqueue`，点击短暂变 ✓，触屏/窄屏常显）。`@click.stop` 不触发双击播放、不收起浮层，可连续添加。
- `src/components/FolderBrowser.vue`：按层级记忆滚动位置。`scrollMemory[depth]` 存各层 `RecycleScroller` 的 `scrollTop`；进子目录前存当前层、新目录从顶部看起；面包屑跳回某层时恢复该层滚动，并 `scrollMemory.length = depth` 丢弃该层及更深层（已退出目录）的记忆——再次进入那些文件夹重新从头开始。

TODO 验证：
- ✅ 搜索结果 hover 出现「＋」，点击加入队列末尾、不打断当前播放、不收起浮层
- ✅ 长目录进子目录再用面包屑跳回，滚动位置保持
- ✅ 退出后再次进入该文件夹，从顶部开始（记忆已丢弃）

### 11. 播放队列持久化 + 索引更新后清理失效项 ✅ 已完成
> 动机：现在 `queue` / `currentIndex` 只在内存（Pinia），刷新或重开浏览器就清空。希望队列能跨刷新保留；同时在本地脚本更新过索引后，把队列里已不存在的歌（路径在新 `index.json` 里查不到）清掉，避免点了播不出来。

实现要点（沿用既有最简做法，不引新依赖）：

**持久化什么**
- 新增 localStorage key `queue`，存 `{ items: [song...], index }`：
  - `items`：队列里每首歌的**完整对象**（`{ path, name, artist, title, lrc }`，本就来自 `index.json`，小而自洽）。存整对象而非只存 `path`——恢复后无需依赖 library 加载顺序、可直接渲染队列，路径仍是后续清理 / 取直链的唯一标识。
  - `index`：`currentIndex`，用于恢复「当前曲」定位。
- **不持久化** `isPlaying` / `progress` / 临时直链：直链 4 小时会过期，且 iOS 首播必须用户手势。恢复后是「停在当前曲、未播放」状态，用户点播放或双击才出声（与第 9 步「enqueue 永不自动播放」一致）。

**写时机**
- `queue` / `currentIndex` 变化时写回（`playList` / `enqueue` / `removeAt` / `moveItem` / `clear` / 切歌都会改）。用一个 `persistQueue()` 收口，或对 `queue`+`currentIndex` 做深 `watch` 统一落盘。全程 `try/catch`（localStorage 满 / 不可用不影响播放，与 `index_cache` 写入同样处理）。

**恢复时机**
- player store 初始化时读 `queue`：填回 `queue` 与 `currentIndex`，并把 `currentTrack` 设为 `queue[index]`（**只设引用、不取直链、不播放**）。读不到 / 解析失败 → 当作空队列，不报错。

**清理失效项（核心诉求，只在「索引就绪后」做一次）**
- 触发点：`library` 成功拿到**非空** `files` 之后——即初次渲染（缓存或下载）以及每次 `revalidate` / `reload()` 取到新 `files`。
- **索引加载失败 / `files` 为空时绝不清理**（离线 / 远端临时不可用时保留队列，避免误清空）。
- 做法：用新 `files[].path` 建一个 `Set`，遍历 `queue` 把 path 不在 Set 里的项剔除；`currentIndex` **复用既有 `removeAt` 的下标调整规则**（删当前项后下一项顶上、删当前项之前的项 index 自减、删空则 index = -1），逐项或批量套用同款逻辑即可，不另写一套。
- **不打断正在播放的音频**：清理只动 `queue` 数组与 `currentIndex`；`<audio>` 已在流的那首即使被移出队列也放完当前（直链仍在内存），下一首 / 上一首按清理后的新队列走。

不做：跨设备同步队列、持久化播放进度 / 续播位置、把失效项做成「失效但保留灰显」（直接剔除最简单可预测）、在每次播放 / 每帧都做清理（只在索引更新这一个时机做）。

实现说明：
- `src/stores/player.js`：新增 LS key `queue`。`loadQueue()` 在 store 初始化时恢复 `queue` + `currentIndex`（坏快照当空队列），只设引用、不取直链、不播放；`persistQueue()` 由 `watch([queue, currentIndex], …, { deep: true })` 在队列 / 位置变化时落盘（深监听以捕获 `removeAt` 的原地 `splice`），`try/catch` 包裹不影响播放。`clear()` 一并把空队列写回。
- `src/stores/player.js` `pruneToValid(validFiles)`：用 `files[].path` 建 `Set`，一次遍历重建保留项数组；`currentIndex` 沿用 removeAt 规则（当前曲之前的失效项 → index 自减；当前曲本身失效 → 下一首顶上；队列清空 → -1）；无失效项时直接返回不改动；只动 `queue` / `currentIndex`，不触碰 `<audio>`，不打断已在流的当前曲。
- `src/stores/library.js`：`applyData()` 在拿到**非空** `files` 后调用 `usePlayerStore().pruneToValid(files.value)`；`not_found` / 加载失败分支不走 `applyData`，故离线 / 索引缺失时队列不被清理。`library` 单向依赖 `player`，无循环引用。

TODO 验证：
- ✅ 建好队列后刷新页面 → 队列与当前曲恢复，停在当前曲、不自动出声
- ✅ 关掉浏览器重开 → 队列仍在
- ✅ 本地脚本删掉队列里某首再更新索引 → 重新加载索引后该首从队列消失，其余顺序不变、currentIndex 正确
- ✅ 删的是当前正在播放那首 → 不打断当前播放，下一首走清理后的队列
- ✅ 断网 / 索引加载失败 → 队列**不被清空**
- ✅ localStorage 写入异常不影响播放

### 12. Media Session（系统媒体卡片）✅ 已完成
> 动机：之前没把曲目信息喂给系统，安卓通知栏 / iOS 锁屏 / macOS「正在播放」只能回退到 favicon（显示 Vite 图标）+ 网页标题。把已有的封面 + 歌名/歌手 多喂一份给浏览器原生的 `navigator.mediaSession`，系统卡片就能正确显示封面与信息，并支持从通知栏控制播放。

实现要点（纯浏览器原生 API，无新依赖，契合「从简」）：
- `src/lib/mediaSession.js`（新）：薄封装。`setupMediaSession({play,pause,prev,next})` 注册控制按钮回调；`updateMediaMetadata({title,artist,artwork})` 设 `navigator.mediaSession.metadata`（`MediaMetadata`）；`setPlaybackState()` 同步播放/暂停图标。全程特性检测 + try/catch，不支持的浏览器（无 `mediaSession`）静默跳过——最坏情况 = 原有行为（回退 favicon），无回归。
- `src/stores/player.js`：store 初始化时 `setupMediaSession`（play→`audio.play`、pause→`audio.pause`、prev/next 复用既有函数）；`watch([currentTrack, trackCover], syncMediaSession)` 在切歌 / 封面读出时刷新元数据；`audio` 的 `play`/`pause` 事件里 `setPlaybackState`。
- 封面优先级与沉浸区一致：内嵌封面（`trackCover` blob）→ 默认封面（`library.coverUrl` Dropbox 直链）→ 省略 artwork（系统回退 favicon）。读 `library.coverUrl` 用懒取（`useLibraryStore()` 在函数内调用），避免与 `library.js` 顶层循环依赖。
- 控制按钮范围：播放 / 暂停 / 上一首 / 下一首（最常用四个）。**未做** seek（`seekto`/`seekforward`/`seekbackward`）与 `setPositionState` 进度条，按需再加。
- **CSP 无需改动**：现有 `img-src 'self' data: blob: https://*.dropboxusercontent.com` 已同时放行 blob 内嵌封面与 Dropbox 直链默认封面；媒体卡片由系统取图，受 `img-src` 管辖。
- 前提：Media Session 需 HTTPS（或 localhost）；Vercel 部署是 HTTPS，满足。

TODO 验证（需真机 / 桌面 OS 媒体卡片观察）：
- 播放后安卓通知栏 / iOS 锁屏 / macOS「正在播放」显示正确歌名歌手 + 封面（不再是 Vite 图标）
- 通知栏的播放/暂停/上一首/下一首按钮生效，图标随播放状态切换
- 无内嵌封面的歌回退默认封面；都没有时只缺图、信息仍正确
- 不支持 Media Session 的浏览器照常播放，不报错

---

## 九、凭证（refresh_token）安全方案

**localStorage 明文存储 refresh_token + app_key + app_secret**，配合以下几条措施：

1. **Dropbox App 最小权限（只读）**：在 [App Console](https://www.dropbox.com/developers/apps) 创建应用，Access type 选 `App folder`，Permissions 只勾 `files.metadata.read` + `files.content.read`。刷新 access_token 走机密客户端方式（`refresh_token` + `app_key` + `app_secret`，与 rclone 同一套凭证），三者都存 localStorage。本地扫描脚本另用一套带写权限的凭证。
   > 取舍：原计划用 PKCE 不存 secret，但现成的 refresh_token 是带 secret 换的、无 secret 刷不动；为复用凭证、保持实现简单，改为存 secret。代价是 secret 明文落在本浏览器（个人本地使用，风险可控）。
2. **CSP 限制外联域名**：部署配置里加 header，`connect-src` 只允许 Dropbox 域名，`media-src` 只允许 `*.dropboxusercontent.com`，`frame-ancestors 'none'`。
   ```
   Content-Security-Policy:
     default-src 'self';
     script-src 'self';
     style-src 'self' 'unsafe-inline';
     connect-src 'self' https://api.dropbox.com https://api.dropboxapi.com https://content.dropboxapi.com https://*.dropboxusercontent.com;
     media-src https://*.dropboxusercontent.com;
     img-src 'self' data:;
     frame-ancestors 'none';
   ```
3. **「清除凭证」按钮**：设置面板里一键清掉 `dbx_refresh_token` / `index_cache` 等 localStorage key 并 reload。
4. **减少依赖**：锁 lockfile、不引第三方 CDN / analytics、不用 `v-html` 渲染用户或 Dropbox 数据。
