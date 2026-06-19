import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// localStorage 键（见 PLAN.md 四）
const LS_REFRESH = 'dbx_refresh_token'
const LS_APPKEY = 'dbx_app_key'
const LS_SECRET = 'dbx_app_secret'

// Dropbox OAuth token 端点（机密客户端：用 app_key + app_secret 刷新，见 PLAN.md 九）
const TOKEN_URL = 'https://api.dropbox.com/oauth2/token'

// access_token 默认 4 小时过期，提前 5 分钟刷新
const REFRESH_SKEW_MS = 5 * 60 * 1000

// 用 refresh_token + key/secret 换一次 access_token。失败抛错，由调用方决定怎么处理。
async function exchangeToken(refreshToken, appKey, appSecret) {
  const res = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      client_id: appKey,
      client_secret: appSecret,
    }),
  })
  if (!res.ok) {
    // Dropbox 在 body 里给出具体原因（如 invalid_grant / invalid_client），带出来便于排查
    let detail = ''
    try {
      const err = await res.json()
      detail = err.error_description || err.error || ''
    } catch {
      detail = await res.text().catch(() => '')
    }
    throw new Error(`token 刷新失败 (HTTP ${res.status})${detail ? `：${detail}` : ''}`)
  }
  return res.json() // { access_token, expires_in, token_type }
}

export const useAuthStore = defineStore('auth', () => {
  // 持久化凭证（localStorage 明文，见 PLAN.md 九）
  const refreshToken = ref(localStorage.getItem(LS_REFRESH) || '')
  const appKey = ref(localStorage.getItem(LS_APPKEY) || '')
  const appSecret = ref(localStorage.getItem(LS_SECRET) || '')

  // 短时令牌，只存内存
  const accessToken = ref('')
  const expiresAt = ref(0) // epoch ms

  // 'login'：未登录 / 'ready'：已有凭证（access_token 懒加载）
  const status = ref(refreshToken.value && appKey.value && appSecret.value ? 'ready' : 'login')
  const isAuthenticated = computed(() => status.value === 'ready')

  // 回登录页时给用户的提示（如「凭证已过期」），登录成功后清空
  const notice = ref('')

  // 刷新 access_token；失败视为凭证失效 → 退出登录
  async function refreshAccessToken() {
    try {
      const data = await exchangeToken(refreshToken.value, appKey.value, appSecret.value)
      accessToken.value = data.access_token
      expiresAt.value = Date.now() + data.expires_in * 1000
    } catch (e) {
      logout('凭证已过期，请重新登录')
      throw e
    }
  }

  // 确保有未过期的 access_token（提前 5 分钟刷新），返回可用 token
  async function ensureFreshToken() {
    if (!accessToken.value || Date.now() >= expiresAt.value - REFRESH_SKEW_MS) {
      await refreshAccessToken()
    }
    return accessToken.value
  }

  // 登录：先换一次 token 做校验，成功才落盘
  async function login(newRefreshToken, newAppKey, newAppSecret) {
    const rt = newRefreshToken.trim()
    const key = newAppKey.trim()
    const secret = newAppSecret.trim()
    const data = await exchangeToken(rt, key, secret) // 凭证无效会在这里抛出，不落盘

    refreshToken.value = rt
    appKey.value = key
    appSecret.value = secret
    accessToken.value = data.access_token
    expiresAt.value = Date.now() + data.expires_in * 1000
    localStorage.setItem(LS_REFRESH, rt)
    localStorage.setItem(LS_APPKEY, key)
    localStorage.setItem(LS_SECRET, secret)
    notice.value = ''
    status.value = 'ready'
  }

  // 退出 / 凭证失效：清空内存 + localStorage，回登录页
  function logout(noticeText = '') {
    refreshToken.value = ''
    appKey.value = ''
    appSecret.value = ''
    accessToken.value = ''
    expiresAt.value = 0
    localStorage.removeItem(LS_REFRESH)
    localStorage.removeItem(LS_APPKEY)
    localStorage.removeItem(LS_SECRET)
    notice.value = noticeText
    status.value = 'login'
  }

  return {
    refreshToken,
    appKey,
    appSecret,
    accessToken,
    expiresAt,
    status,
    notice,
    isAuthenticated,
    refreshAccessToken,
    ensureFreshToken,
    login,
    logout,
  }
})
