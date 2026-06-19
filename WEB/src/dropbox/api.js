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
