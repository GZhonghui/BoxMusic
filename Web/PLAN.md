# Dropbox 音乐播放器 — 设计方案

## 一、整体架构

**纯前端 SPA**，无后端。所有逻辑跑在浏览器里。

```
浏览器 (Vue 应用)
  ├─ Dropbox API (OAuth token / files / download)
  ├─ localStorage (refresh_token、index 缓存、用户偏好)
  └─ <audio> 元素 (流式播放)
```

数据流：
- **凭证**：用户输入 refresh_token → 存 localStorage → 每次启动用它换 access_token（短时，存内存）
- **元数据**：Dropbox 上一份 `index.json` 为权威源，本地 localStorage 镜像一份做秒开
- **音频**：临时直链流式播放，不下载到本地

---

## 二、页面 UI 设计

只用一个单页，按区域划分。建议布局（桌面优先，可响应式到手机）：

```
┌─────────────────────────────────────────────────────┐
│ 顶部栏                                                │
│  Logo · 搜索框 ──────────────  状态指示 · 设置按钮     │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  左侧边栏     │   主内容区                            │
│              │                                      │
│  · 全部歌曲   │   [歌曲列表 / 当前歌手详情 / 设置面板]   │
│  · 按歌手     │                                      │
│  · 播放队列   │   表格列：序号 · 歌名 · 歌手 · 时长 · 操作│
│  · 收藏夹     │                                      │
│              │                                      │
├──────────────┴──────────────────────────────────────┤
│ 底部播放器（固定）                                     │
│  封面占位 · 歌名/歌手 · ◁ ▷▷ ▷ · 进度条 · 时长 · 音量 · 模式│
└─────────────────────────────────────────────────────┘
```

### 关键 UI 元素

**顶部栏**
- 搜索框：实时过滤（按歌名/歌手），客户端搜索，无需请求
- 状态指示：显示「已同步 · 12,345 首」「正在同步…」「未登录」
- 设置按钮：弹出设置面板

**左侧边栏**
- 全部歌曲（默认视图）
- 按歌手分组（点开展开该歌手所有歌曲）
- 播放队列（当前队列 + 历史）
- 收藏夹（可选，存 localStorage）

**主内容区 — 歌曲列表**
- 虚拟滚动（一万行 DOM 卡，必须用 `vue-virtual-scroller` 类库）
- 列：`#` · `歌名` · `歌手` · `时长`（可选）· `操作`（播放/加入队列/收藏）
- 双击行 = 立即播放并把整个当前列表设为队列
- 单击 = 选中

**底部播放器**（始终可见）
- 当前曲目信息
- 控制：上一首 / 播放暂停 / 下一首
- 进度条：可拖动 seek
- 音量条
- 播放模式：顺序 / 单曲循环 / 列表循环 / 随机
- 桌面：还能加键盘快捷键（空格暂停、左右切歌）

**首次进入 / 未登录态**
- 全屏引导：「请粘贴你的 Dropbox refresh token」+ 输入框 + 帮助链接
- 帮助文档说明：如何在 Dropbox 开发者后台拿到 token、PKCE 流程注意事项

**首次同步**
- 全屏进度：「正在建立音乐索引 1234 / ~10000」+ 旋转动画
- 完成后自动进入主界面

**设置面板**
- Dropbox 文件夹路径（默认 `/`，可改成 `/Music`）
- 重建索引按钮
- 清除凭证按钮（退出登录）
- 主题切换（深色/浅色）
- 关于 / 版本号

---

## 三、功能清单

### 必备
1. **登录**：输入并保存 refresh_token
2. **建立索引**：首次全量扫描，生成 index.json 存到 Dropbox
3. **增量同步**：之后每次启动用 cursor 拉差量
4. **歌曲列表展示**：虚拟滚动，按歌手/歌名排序切换
5. **搜索过滤**：实时搜索歌名/歌手
6. **播放**：流式播放，支持 seek
7. **队列**：上一首/下一首、自动连播
8. **播放模式**：顺序/单曲循环/列表循环/随机
9. **设置**：路径、重建索引、退出登录

### 加分项（按优先级）
1. **按歌手分组视图**
2. **收藏夹**（存 localStorage）
3. **键盘快捷键**
4. **Media Session API**：让锁屏 / 蓝牙耳机能控制播放
5. **歌词显示**（如果 Dropbox 同目录有同名 .lrc 文件就一起拉）
6. **深色模式**
7. **多设备同步**：把收藏 / 播放历史也写进 Dropbox

### 不做（先砍掉）
- ID3 标签解析
- 在线音质转码
- 上传 / 删除文件
- 评论、社交

---

## 四、数据结构

### Dropbox 上的 `index.json`

```jsonc
{
  "version": 1,
  "cursor": "AAE_xxx",              // 用于增量同步
  "scanned_at": "2026-06-18T10:00:00Z",
  "root_path": "/Music",
  "files": [
    {
      "id": "id:abcdef123",          // Dropbox 稳定文件 ID
      "path": "/Music/周杰伦 - 晴天.mp3",
      "name": "周杰伦 - 晴天.mp3",
      "size": 5234123,
      "modified": "2024-03-12T...",
      "artist": "周杰伦",             // 文件名解析得到
      "title": "晴天"                 // 文件名解析得到
    }
  ]
}
```

存放位置：`/Apps/<你的App名>/index.json`，或就放在用户配置的音乐根目录里，比如 `/Music/.index.json`。

### localStorage 键

| key | 内容 |
|---|---|
| `dbx_refresh_token` | refresh token |
| `dbx_app_key` | app key（PKCE 流程，无 secret） |
| `index_cache` | 本地 index.json 副本（用于秒开） |
| `index_cache_etag` | 远端 index 的 rev/版本号，判断要不要重拉 |
| `settings` | `{ root_path, theme, play_mode, volume }` |
| `favorites` | 收藏的文件 ID 数组 |

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
3. 检查 Dropbox 上有没有 index.json
   ├─ 没有 → 触发「首次全量扫描」(流程 2)
   └─ 有 → 下载 index.json → 进入第 4 步
4. 同时做：
   a. 用 index 渲染界面（用户已经能看到列表）
   b. 后台跑「增量同步」(流程 3)
```

### 流程 2：全量扫描

```
1. 显示进度全屏
2. 调 /files/list_folder { path: root_path, recursive: true, limit: 2000 }
3. 过滤出音频扩展名（.mp3 / .flac / .m4a / .wav / .ogg / .opus）
4. 解析文件名：用正则 ^(.+?)\s*-\s*(.+)\.\w+$ 提取 artist 和 title
   - 不匹配的：artist = "未知"，title = 整个文件名
5. 如果 has_more === true，用 returned cursor 继续 /list_folder/continue
6. 全部拿完后：
   - 保存最后的 cursor
   - 组装 index.json
   - 用 /files/upload 写到 Dropbox（覆盖模式 mode = "overwrite"）
7. 同时写入 localStorage 缓存
```

进度计算：Dropbox 不告诉你总数，所以进度条只能显示「已扫描 N 个」。可以用伪进度条（先增长 90% 然后等真实完成）。

### 流程 3：增量同步

```
1. 拿本地 index 里的 cursor
2. 调 /files/list_folder/continue { cursor }
3. 返回的 entries 里：
   - .tag === "file" → 新增或修改 → 更新 index.files
   - .tag === "deleted" → 从 index.files 删除
4. 如果 has_more 继续翻页
5. 更新最终 cursor
6. 如果有变化：
   - 写回 Dropbox 上的 index.json
   - 写本地缓存
   - 通知 UI 刷新列表
7. 如果 cursor 过期（API 报错）→ 降级到全量扫描
```

### 流程 4：播放

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

### 流程 5：access token 刷新

- access token 默认 4 小时过期
- 每次 API 调用前检查 expires_at，提前 5 分钟刷新
- 包一个 `fetchWithAuth` 拦截器统一处理

---

## 六、技术栈

| 用途 | 选型 | 理由 |
|---|---|---|
| 框架 | Vue 3 + `<script setup>` | 指定 |
| 构建 | Vite | 静态产物，部署到任何静态托管 |
| 路由 | Vue Router | 视图切换 |
| 状态 | Pinia | 比 vuex 简洁 |
| 虚拟滚动 | `vue-virtual-scroller` | 一万行必须有 |
| 样式 | Tailwind 或纯 CSS | 看偏好 |
| HTTP | 原生 fetch | 无需 axios |
| 图标 | lucide-vue | 轻量 |

**部署**：构建产物全是静态文件，可部署到 GitHub Pages / Cloudflare Pages / Vercel / 本地 file:// 直接打开都行（注意 file:// 协议下某些浏览器对 fetch 有限制，建议起个本地静态服务器）。

---

## 七、容易踩的坑

1. **Dropbox 速率限制**：免费账号有调用频率限制。全量扫描时如果命中 429，要按 `Retry-After` 退避。
2. **token 失效**：refresh_token 也可能被用户主动撤销，每次启动要处理 401 → 回登录页。
3. **文件名解析的边界情况**：
   - `Artist - Song - Remix.mp3` → 用 **第一个** `-` 作分隔
   - 没有 `-` → artist 设为「未知」
   - 多个空格、全角破折号 `—`、`–` → 正则要兼容
4. **CORS**：Dropbox API 都支持 CORS，但临时链接的域名是 `dl.dropboxusercontent.com`，浏览器播放时不需要 CORS 头（`<audio>` 不受 CORS 限制），但如果想画波形图就要了。
5. **index.json 上传冲突**：多设备同时改 index 会互相覆盖。低优先级问题，建议带 `client_modified` 时间戳，加载时谁新用谁。
6. **虚拟滚动 + 搜索**：搜索过滤后列表变短，virtual scroller 需要 reset 滚动位置。
7. **iOS Safari 限制**：音频播放必须由用户手势触发第一次。自动连播没问题，但页面打开后不能自动开播。
8. **大 index.json**：一万首大概 1-3MB JSON。上传/下载都可接受，但要 gzip。Dropbox 服务端不自动 gzip，可以考虑改用 `.json.gz` 自己压。

---

## 八、建议的开发顺序

1. **登录 + token 刷新机制**（确保 API 能调通）
2. **全量扫描 + 写 index.json**（核心数据有了）
3. **基础列表展示 + 虚拟滚动**（能看到歌了）
4. **播放器 + 队列**（能听了，就是 MVP）
5. **增量同步**（启动变快）
6. **搜索、按歌手分组**
7. **设置、收藏、键盘快捷键、Media Session**
8. **样式打磨、深色模式**

每一步都能独立验证，不会陷入「写了一周还没东西能跑」的状态。

---

## 九、凭证（refresh_token）安全方案

### 9.1 采用方案

**localStorage 明文存储 refresh_token**，配合多层防御措施降低风险。

完整方案：

1. refresh_token 明文存在 `localStorage['dbx_refresh_token']`
2. Dropbox App 配置为最小权限（见 9.3）
3. 部署位置不公开传播 URL（见 9.4）
4. 页面加 CSP 限制外联域名（见 9.5）
5. 设置面板提供「清除凭证」按钮（见 9.6）
6. 不引入非必要的 npm 依赖（见 9.7）

### 9.2 威胁模型 — 这套方案防什么、不防什么

| 威胁 | 是否防御 | 说明 |
|---|---|---|
| 陌生人偶然访问页面 URL | 防 | 不公开传播，URL 难被发现 |
| token 泄露后被攻击者乱用 Dropbox 全盘 | 防 | App folder 隔离，攻击者只能动音乐文件夹 |
| 恶意脚本把 token 偷偷发到外部域名 | 防 | CSP 拦截非 Dropbox 的 connect |
| 误装恶意 npm 包 / 供应链投毒 | 部分防 | CSP 兜底，但依赖越少越好 |
| **XSS 攻击（你自己页面有漏洞）** | **不防** | 纯前端无解，靠减少攻击面 |
| **物理访问你的电脑（已登录浏览器）** | **不防** | 别人能开 DevTools 看到 token |
| **同设备其他用户共享浏览器** | **不防** | 同上 |
| **恶意浏览器扩展** | **不防** | 扩展权限高于页面 JS |

> ⚠️ **重要认知**：纯静态网页中，**任何存储方式都无法防 XSS**。一旦页面跑了恶意 JS，token 无论怎么存都会被拿走。所以"存哪里"主要防的是**静态读取场景**（物理访问、陌生人开页面），而不是运行时窃取。

### 9.3 ⚠️ 必做 — Dropbox App 配置（比"存哪里"重要 10 倍）

去 [Dropbox App Console](https://www.dropbox.com/developers/apps) 创建应用时：

- ✅ **Access type 选 `App folder`**，**不要**选 `Full Dropbox`
  - 这样即使 token 完全泄露，攻击者也只能访问 `/Apps/<你的App名>/` 下的内容
  - 把音乐文件挪进这个目录
- ✅ **Permissions 只勾以下三项**：
  - `files.metadata.read` — 列出文件
  - `files.content.read` — 下载播放
  - `files.content.write` — 写 index.json
- ❌ **不要勾**：`account_info.read`、`sharing.*`、`file_requests.*`、任何 team 相关权限
- ✅ 生成 refresh_token 时使用 **PKCE 流程**，避免暴露 `app_secret`

> 💡 **这一步做完，安全等级提升远超任何存储方式的改动。** token 泄露的"爆炸半径"被物理隔离了。

### 9.4 ⚠️ 必做 — 部署位置

- ✅ 部署到 **Cloudflare Pages / GitHub Pages / Vercel** 等可控静态托管
- ✅ URL 不主动公开传播（不发推、不分享、不放 readme）
- ✅ 如果用 GitHub Pages，**仓库设为 private**（GitHub Pages 仍可正常 serve）
- ❌ **不要**部署到任何会被搜索引擎索引的位置
- ❌ **不要**嵌入到 iframe 或其他陌生站点

### 9.5 ⚠️ 必做 — CSP 内容安全策略

在部署配置里添加 HTTP header（Cloudflare Pages 用 `_headers` 文件，Vercel 用 `vercel.json`）：

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  connect-src 'self'
    https://api.dropbox.com
    https://api.dropboxapi.com
    https://content.dropboxapi.com
    https://*.dropboxusercontent.com;
  media-src https://*.dropboxusercontent.com;
  img-src 'self' data:;
  frame-ancestors 'none';
```

- 作用：即使页面被注入恶意脚本，浏览器也会拒绝把 token 发往非 Dropbox 域名
- `frame-ancestors 'none'` 防止页面被嵌入 iframe（clickjacking 防御）

### 9.6 ⚠️ 必做 — 「清除凭证」按钮

设置面板里提供一键清除：

```js
localStorage.removeItem('dbx_refresh_token')
localStorage.removeItem('index_cache')
// ... 清掉所有相关 key
location.reload()
```

用途：
- 借给别人用电脑前清一下
- 怀疑泄露时立即清除
- 配合 [Dropbox connected apps 页面](https://www.dropbox.com/account/connected_apps) **撤销该 App**（这才是根治）

### 9.7 ⚠️ 必做 — 减少 XSS 攻击面

- ✅ 锁 lockfile（`package-lock.json` / `pnpm-lock.yaml`）提交到仓库
- ✅ 依赖版本不要带 `^` 自动升级
- ✅ 不引入任何分析 / 广告 / 第三方 CDN 脚本
- ✅ 用户输入（搜索框、文件名等）渲染时**不要**用 `v-html`
- ✅ npm 包能不装就不装，每个都是供应链风险点
- ❌ **不要**为了省事引入大型 UI 库，挑小而专的库

### 9.8 出问题怎么办（应急预案）

发现 token 可能泄露：

1. **立即**去 [dropbox.com/account/connected_apps](https://www.dropbox.com/account/connected_apps) 撤销该 App
2. 在 Dropbox App Console 重新生成 refresh_token
3. 检查 Dropbox 活动日志，看是否有异常下载
4. 因为 App folder 隔离，最坏情况也只是音乐文件夹被动过，不影响其他文件

### 9.9 升级路径（如果以后需要更高安全）

本方案的设计允许平滑升级，**无需重构**：

- **Level 2** — 密码加密：包一层 Web Crypto API，PBKDF2 + AES-GCM 加密后存 localStorage，启动时让用户输密码解密。防住物理访问场景。约 50 行代码。
- **Level 3** — WebAuthn PRF：用 Touch ID / 硬件密钥派生加密 key。最佳 UX + 安全平衡。需要现代浏览器和 authenticator。
- **Level 4** — 后端代理：加一个 Cloudflare Worker 保管 refresh_token，前端只拿短时 access_token。token 不再进入浏览器 JS，XSS 也偷不走。约 100 行 Worker 代码。

### 9.10 安全检查清单（开发完成前过一遍）

- [ ] Dropbox App 是 App folder 类型，不是 Full Dropbox
- [ ] Dropbox App 权限只有三项必需 scope
- [ ] 使用 PKCE 流程，没有把 `app_secret` 写进前端代码
- [ ] 部署位置 URL 未公开传播
- [ ] CSP header 已配置，`connect-src` 已限制
- [ ] 设置面板有「清除凭证」按钮
- [ ] 所有依赖都锁了版本
- [ ] 代码里没有 `v-html` 渲染用户/Dropbox 数据
- [ ] 没有引入任何第三方 CDN 脚本 / analytics
- [ ] 知道在哪里能撤销 token（已把 connected_apps URL 收藏）
