import { useAuthStore } from '../stores/auth'

// 统一的带鉴权请求：调用前确保 token 新鲜，自动加 Authorization 头；
// 命中 401 视为凭证失效，清凭证回登录页。
// 注意：refresh_token 刷新失败也会在 ensureFreshToken() 内部 logout 并抛出。
export async function fetchWithAuth(url, options = {}) {
  const auth = useAuthStore()
  const token = await auth.ensureFreshToken()

  const res = await fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  })

  if (res.status === 401) {
    auth.logout('凭证已过期，请重新登录')
    throw new Error('凭证已过期，请重新登录')
  }
  return res
}

const DOWNLOAD_URL = 'https://content.dropboxapi.com/2/files/download'

// Dropbox-API-Arg 头只能是 ASCII：把非 ASCII 字符（如中文路径）转成 \uXXXX 转义，
// 否则带中文路径的请求会因 HTTP 头含非法字符而失败。Dropbox 会把转义还原。
function apiArg(obj) {
  return JSON.stringify(obj).replace(/[\u007f-\uffff]/g, (c) =>
    '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'),
  )
}

// 下载某个文本文件（如 .lrc 歌词）的内容，按 UTF-8 解码返回。
// 文件不存在 → 抛出带 code='not_found' 的错误，调用方可据此当「无内容」处理。
export async function downloadText(path) {
  const res = await fetchWithAuth(DOWNLOAD_URL, {
    method: 'POST',
    headers: { 'Dropbox-API-Arg': apiArg({ path }) },
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    if (res.status === 409 && detail.includes('not_found')) {
      const e = new Error('not_found')
      e.code = 'not_found'
      throw e
    }
    throw new Error(`下载失败 (HTTP ${res.status})${detail ? `：${detail}` : ''}`)
  }
  return res.text()
}

const TEMP_LINK_URL = 'https://api.dropboxapi.com/2/files/get_temporary_link'

// 取某个文件 4 小时有效的临时直链（音频流式播放、封面图都用它）。失败抛错。
export async function getTemporaryLink(path) {
  const res = await fetchWithAuth(TEMP_LINK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`取直链失败 (HTTP ${res.status})${detail ? `：${detail}` : ''}`)
  }
  const data = await res.json()
  return data.link
}
