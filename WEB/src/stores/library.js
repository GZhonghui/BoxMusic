import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchWithAuth } from '../dropbox/api'

// 索引固定路径（App folder 内），应用内不可配置（见 PLAN.md 四）
const INDEX_PATH = '/metainfo/index.json'
const DOWNLOAD_URL = 'https://content.dropboxapi.com/2/files/download'

// 曲库索引：只读 /metainfo/index.json，解析进内存。
// Web 应用永不写入、永不扫描；索引由本地脚本生成上传（见 scripts/build_index.py）。
export const useLibraryStore = defineStore('library', () => {
  const files = ref([])      // index.json 的 files[]，path 作唯一标识
  const settings = ref({})   // index.json 的 settings（default_cover / root_label 等）

  // 'idle' 未加载 | 'loading' 加载中 | 'ready' 就绪 | 'empty' 索引未生成 | 'error' 下载/解析失败
  const status = ref('idle')
  const error = ref('')

  // 下载并解析索引。失败不抛错，只落到 status/error，由 UI 给出提示，绝不白屏/崩溃。
  async function loadIndex() {
    status.value = 'loading'
    error.value = ''

    let res
    try {
      // download 走 content 域；参数放 Dropbox-API-Arg 头，请求体为空
      res = await fetchWithAuth(DOWNLOAD_URL, {
        method: 'POST',
        headers: { 'Dropbox-API-Arg': JSON.stringify({ path: INDEX_PATH }) },
      })
    } catch (e) {
      // 网络错误，或 token 刷新/401 已在 fetchWithAuth 内 logout 并抛出
      status.value = 'error'
      error.value = `加载索引失败：${e.message}`
      return
    }

    if (!res.ok) {
      const detail = await res.text().catch(() => '')
      // 文件不存在：Dropbox 返回 409 + path/not_found → 索引尚未生成
      if (res.status === 409 && detail.includes('not_found')) {
        status.value = 'empty'
        error.value = '索引尚未生成，请先在本地运行扫描脚本上传到 /metainfo/index.json'
      } else {
        status.value = 'error'
        error.value = `加载索引失败（HTTP ${res.status}）${detail ? `：${detail}` : ''}`
      }
      return
    }

    const text = await res.text()
    let data
    try {
      data = JSON.parse(text)
    } catch {
      status.value = 'error'
      error.value = '索引损坏：index.json 不是合法 JSON，请在本地重新生成上传'
      return
    }

    // 最低限度结构校验：缺 files 列表视为损坏
    if (!data || !Array.isArray(data.files)) {
      status.value = 'error'
      error.value = '索引损坏：缺少 files 列表，请在本地重新生成上传'
      return
    }

    files.value = data.files
    settings.value = data.settings || {}
    status.value = 'ready'
    console.log(`[BoxMusic] 索引加载成功，共 ${files.value.length} 首`)
  }

  return { files, settings, status, error, loadIndex }
})
