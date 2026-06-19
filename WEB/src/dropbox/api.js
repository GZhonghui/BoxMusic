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
