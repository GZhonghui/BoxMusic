import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchWithAuth, getTemporaryLink } from '../dropbox/api'
import { usePlayerStore } from './player'

// 索引固定路径（App folder 内），应用内不可配置（见 PLAN.md 四）
const INDEX_PATH = '/metainfo/index.json'
const DOWNLOAD_URL = 'https://content.dropboxapi.com/2/files/download'
const METADATA_URL = 'https://api.dropboxapi.com/2/files/get_metadata'

// localStorage 键（见 PLAN.md 四）
const LS_CACHE = 'index_cache'      // index.json 原文副本，用于秒开
const LS_REV = 'index_cache_rev'    // 远端 index 的 rev，判断要不要重拉

// 曲库索引：只读 /metainfo/index.json，解析进内存。
// 启动先用本地缓存秒开，再后台用 rev 校验是否需要重新下载（流程 1/2）。
// Web 应用永不写入、永不扫描；索引由本地脚本生成上传（见 scripts/build_index.py）。
export const useLibraryStore = defineStore('library', () => {
  const files = ref([])      // index.json 的 files[]，path 作唯一标识
  const settings = ref({})   // index.json 的 settings（default_cover / root_label 等）
  const coverUrl = ref('')   // settings.default_cover 解析出的临时直链（沉浸区封面用）

  // 'idle' 未加载 | 'loading' 加载中 | 'ready' 就绪 | 'empty' 索引未生成 | 'error' 下载/解析失败
  const status = ref('idle')
  const error = ref('')

  // —— 缓存读写（失败都不影响功能）——
  function readCache() {
    try {
      const raw = localStorage.getItem(LS_CACHE)
      if (!raw) return null
      const data = JSON.parse(raw)
      return data && Array.isArray(data.files) ? data : null
    } catch {
      return null
    }
  }

  function writeCache(text, rev) {
    try {
      localStorage.setItem(LS_CACHE, text)
      if (rev) localStorage.setItem(LS_REV, rev)
    } catch (e) {
      // localStorage 满 / 不可用：缓存失败不影响播放，忽略
      console.warn('[BoxMusic] 写索引缓存失败：', e)
    }
  }

  function clearCache() {
    localStorage.removeItem(LS_CACHE)
    localStorage.removeItem(LS_REV)
  }

  function applyData(data) {
    files.value = data.files
    settings.value = data.settings || {}
    loadCover()
    // 索引就绪后清理持久化队列里的失效项（仅在非空时，避免离线误清空）
    if (files.value.length) usePlayerStore().pruneToValid(files.value)
  }

  // 解析 settings.default_cover 的临时直链（同一张图只解析一次；失败留空走占位）
  let coverPathDone = ''
  async function loadCover() {
    const path = settings.value.default_cover
    if (!path) { coverUrl.value = ''; coverPathDone = ''; return }
    if (path === coverPathDone && coverUrl.value) return
    try {
      coverUrl.value = await getTemporaryLink(path)
      coverPathDone = path
    } catch (e) {
      console.warn('[BoxMusic] 封面加载失败：', e.message)
      coverUrl.value = ''
    }
  }

  // 把一段 index.json 原文解析并应用；坏 JSON / 缺 files → 标记损坏返回 false
  function parseAndApply(text) {
    let data
    try {
      data = JSON.parse(text)
    } catch {
      status.value = 'error'
      error.value = '索引损坏：index.json 不是合法 JSON，请在本地重新生成上传'
      return false
    }
    if (!data || !Array.isArray(data.files)) {
      status.value = 'error'
      error.value = '索引损坏：缺少 files 列表，请在本地重新生成上传'
      return false
    }
    applyData(data)
    status.value = 'ready'
    console.log(`[BoxMusic] 索引就绪，共 ${files.value.length} 首`)
    return true
  }

  // 入口：先用缓存秒开，再后台校验 rev（流程 1）
  async function load() {
    const cached = readCache()
    if (cached) {
      applyData(cached)
      status.value = 'ready'
    } else {
      status.value = 'loading'
    }
    await revalidate(false)
  }

  // 「重新加载索引」按钮：跳过 rev 比对，强制重新下载
  async function reload() {
    await revalidate(true)
  }

  // 取远端 rev，与缓存比对，决定是否下载（流程 2）
  async function revalidate(force) {
    let meta
    try {
      const res = await fetchWithAuth(METADATA_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: INDEX_PATH }),
      })
      if (!res.ok) {
        const detail = await res.text().catch(() => '')
        // 远端没有索引：清掉缓存，提示去本地生成
        if (res.status === 409 && detail.includes('not_found')) {
          clearCache()
          files.value = []
          settings.value = {}
          status.value = 'empty'
          error.value = '索引尚未生成，请先在本地运行扫描脚本上传到 /metainfo/index.json'
          return
        }
        throw new Error(`HTTP ${res.status}${detail ? `：${detail}` : ''}`)
      }
      meta = await res.json()
    } catch (e) {
      // 校验失败：有缓存就维持秒开内容（静默），无缓存才报错
      if (status.value === 'ready') {
        console.warn('[BoxMusic] 索引校验失败，沿用本地缓存：', e.message)
      } else {
        status.value = 'error'
        error.value = `加载索引失败：${e.message}`
      }
      return
    }

    const rev = meta.rev
    const haveCache = !!localStorage.getItem(LS_CACHE)
    // 非强制、且有缓存、且 rev 未变 → 秒开内容已是最新，不重复下载
    if (!force && haveCache && rev && rev === localStorage.getItem(LS_REV)) return

    await download(rev)
  }

  // 下载并解析索引，成功后写缓存
  async function download(rev) {
    if (status.value !== 'ready') status.value = 'loading'

    let res
    try {
      res = await fetchWithAuth(DOWNLOAD_URL, {
        method: 'POST',
        headers: { 'Dropbox-API-Arg': JSON.stringify({ path: INDEX_PATH }) },
      })
    } catch (e) {
      downloadFailed(e.message)
      return
    }

    if (!res.ok) {
      const detail = await res.text().catch(() => '')
      if (res.status === 409 && detail.includes('not_found')) {
        clearCache()
        files.value = []
        settings.value = {}
        status.value = 'empty'
        error.value = '索引尚未生成，请先在本地运行扫描脚本上传到 /metainfo/index.json'
      } else {
        downloadFailed(`HTTP ${res.status}${detail ? `：${detail}` : ''}`)
      }
      return
    }

    const text = await res.text()
    if (parseAndApply(text)) writeCache(text, rev)
  }

  // 下载失败：有缓存维持秒开内容（静默），无缓存才报错
  function downloadFailed(msg) {
    if (status.value === 'ready' && files.value.length) {
      console.warn('[BoxMusic] 索引下载失败，沿用本地缓存：', msg)
    } else {
      status.value = 'error'
      error.value = `加载索引失败：${msg}`
    }
  }

  return { files, settings, coverUrl, status, error, load, reload }
})
