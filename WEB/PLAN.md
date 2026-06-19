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
    - `🎵 歌曲`：双击播放
  - 只渲染「当前这一层」的条目，单层通常几十条，虚拟滚动作为兜底
- **Tab：队列** — 当前播放队列，平铺列表，支持：
  - 拖拽 / 删除单曲、点歌跳播
  - 顶部「清空队列」按钮
  - 高亮当前播放项
- 单击歌曲 = 选中（右侧沉浸区随之更新）

**播放与队列的关系**（只有一个「当前播放队列」，不做收藏夹、不做手动建歌单）
- 在某个文件夹里双击一首歌 → 把**该文件夹内（不递归）的所有歌曲**按显示顺序设为队列，并从双击那首开始播放
- 在搜索结果里双击一首歌 → 把搜索结果设为队列，从该首开始
- 队列是临时的、可手动编辑（增删/排序/清空），不持久化成命名歌单

**右侧 — 沉浸区**（大面积视觉焦点，封面 / 歌词二选一）
- 顶部一个分段切换：`封面` | `歌词`
- **封面视图**：
  - 居中的大封面卡片，**圆角 + 柔和投影（drop shadow）+ 玻璃拟态（frosted glass / backdrop-blur）**
  - 背景：用封面图放大模糊后铺底，叠一层半透明渐变，营造氛围
  - 封面统一用 `index.json` 的 `settings.default_cover`（无则占位渐变 + 歌名首字）；内嵌封面不提取
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
- ID3 标签解析

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
      "artist": "周杰伦",             // 本地脚本解析得到
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
- **没有 `cover`**：封面只嵌在音频文件内部，不单独存图。Web 应用统一显示 `settings.default_cover`（无则占位渐变），不做内嵌封面提取。
- 不再需要 `cursor`（应用不做增量同步）。
- 文件名解析（artist / title）由本地脚本完成，Web 应用直接用现成字段。

### localStorage 键

| key | 内容 |
|---|---|
| `dbx_refresh_token` | refresh token |
| `dbx_app_key` | app key |
| `dbx_app_secret` | app secret（刷新 token 需要） |
| `index_cache` | 本地 index.json 副本（用于秒开） |
| `index_cache_rev` | 远端 index 的 rev/版本号，判断要不要重拉 |
| `settings` | `{ play_mode, volume }` |

> 注：`index_cache` 约 1–3MB（万级曲库），在 localStorage ~5MB 上限内没问题；若日后曲库涨到几万首接近上限，再换 IndexedDB。

### 内存状态（Pinia / ref）

- `accessToken` — 短时令牌
- `currentTrack` — 正在播放的曲目
- `queue` — 当前播放队列
- `currentIndex` — 队列中位置
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
> - [ ] 第 4 步：播放器 + 队列（MVP）← 下一步
> - [ ] 第 5~8 步：未开始

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
- `src/components/FolderBrowser.vue`：面包屑（根节点用 `settings.root_label`）可逐级跳回；当前目录用 `RecycleScroller` 虚拟滚动兜底；`📁` 单击进入、`🎵` 单击选中（双击播放留第 4 步）。
- `src/App.vue`：占位页换成真正壳子，进入已登录态自动 `loadIndex()`，按 loading / 未就绪 / ready 三态渲染，只有 ready 才显示浏览器。
TODO 验证：
- ✅ 能从根逐层点进到最深目录，再用面包屑跳回任意层
- ✅ 文件夹/歌曲数量与 Dropbox 实际目录一致
- ✅ 某层有几千条时滚动不卡

### 4. 播放器 + 队列（能听了，就是 MVP）
TODO：
- 双击歌曲 → `/files/get_temporary_link` 拿直链设给 `<audio>`
- 队列：双击 = 把**当前目录（不递归）**所有歌入队并从该首播；`ended` 自动下一首
- 底部播放器：播放/暂停、上一首/下一首、进度条 seek、音量
- 队列 Tab：列表、拖拽/删除/跳播、清空、高亮当前项
- `error` → 提示并跳下一首
TODO 验证：
- ✅ 双击能出声，进度条走动、可拖动 seek
- ✅ 一首放完自动接下一首；上一首/下一首正确
- ✅ 队列里删除当前项、清空、跳播行为正确
- ✅ 拔网/坏链接 → 提示并跳下一首，不卡死

### 5. 本地缓存 + rev 校验秒开（启动变快）
TODO：
- 索引下载后写 `index_cache` + `index_cache_rev`
- 启动：先用 `index_cache` 渲染，再后台 `/files/get_metadata` 比对 rev
- rev 相同 → 用缓存；不同/无缓存 → 重新下载并刷新
- 「重新加载索引」按钮 = 跳过 rev 比对强制下载
TODO 验证：
- ✅ 第二次打开「秒开」（先出列表，无网络等待）
- ✅ 本地脚本更新索引后 → 自动检测到 rev 变化并刷新列表
- ✅ rev 没变 → 不重复下载（看 network 面板无 download 请求）

### 6. 搜索（跨全部）+ 播放模式
TODO：
- 搜索框下方浮层列表：按歌名/歌手/路径实时过滤全部 `files`
- 空输入 / 失焦 / `Esc` 收起；结果多时虚拟滚动 + 截断「前 N 条」
- 浮层内双击 = 把搜索结果设为队列并播放
- 播放模式：顺序 / 单曲循环 / 列表循环 / 随机，存 `localStorage.settings`
TODO 验证：
- ✅ 输入关键词即时出结果，中文/大小写都能匹配
- ✅ 浮层双击播放后队列 = 搜索结果
- ✅ 四种播放模式行为正确，刷新后模式被记住

### 7. 设置面板 + 样式打磨
TODO：
- 设置面板：重新加载索引、清除凭证（清 token/缓存并 reload）、关于/版本号
- 右侧沉浸区封面卡：圆角 + 投影 + 玻璃感 + 模糊背景；`封面 | 歌词` 切换
- 左侧栏最小宽度 + 折叠；窄屏响应式
TODO 验证：
- ✅ 清除凭证后回到登录页，localStorage 相关 key 已清空
- ✅ 封面卡视觉达标，窗口缩放时自适应居中不变形
- ✅ 左侧栏可折叠/展开，手机宽度下布局不破

### 8. 歌词显示（加分项）
TODO：
- 歌曲带 `lrc` 字段 → 拉取并解析 `.lrc`
- 歌词视图逐行显示、当前行高亮、随进度滚动居中；无歌词显示占位
TODO 验证：
- ✅ 有歌词的歌切到歌词页能逐行高亮、滚动跟随
- ✅ 无 `lrc` 字段的歌显示「暂无歌词」，不报错

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
