<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const refreshTokenInput = ref(auth.refreshToken)
const appKeyInput = ref(auth.appKey)
const appSecretInput = ref(auth.appSecret)
const submitting = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!refreshTokenInput.value.trim() || !appKeyInput.value.trim() || !appSecretInput.value.trim()) {
    error.value = '请填写 Refresh token、App key 和 App secret'
    return
  }
  submitting.value = true
  try {
    await auth.login(refreshTokenInput.value, appKeyInput.value, appSecretInput.value)
  } catch (e) {
    error.value = `登录失败：${e.message}（请检查 Refresh token 与 App key 是否正确）`
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login">
    <div class="card">
      <h1>BoxMusic</h1>
      <p class="sub">把 Dropbox 当曲库的个人播放器</p>

      <p v-if="auth.notice" class="notice">{{ auth.notice }}</p>

      <form @submit.prevent="submit">
        <label>
          <span>Refresh token</span>
          <textarea
            v-model="refreshTokenInput"
            rows="3"
            spellcheck="false"
            autocomplete="off"
            placeholder="粘贴你的 Dropbox refresh token"
          />
        </label>

        <label>
          <span>App key</span>
          <input
            v-model="appKeyInput"
            type="text"
            spellcheck="false"
            autocomplete="off"
            placeholder="Dropbox App 的 App key"
          />
        </label>

        <label>
          <span>App secret</span>
          <input
            v-model="appSecretInput"
            type="password"
            spellcheck="false"
            autocomplete="off"
            placeholder="Dropbox App 的 App secret"
          />
        </label>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" :disabled="submitting">
          {{ submitting ? '正在登录…' : '登录' }}
        </button>
      </form>

      <details class="help">
        <summary>如何获取凭证？</summary>
        <ol>
          <li>
            在
            <a href="https://www.dropbox.com/developers/apps" target="_blank" rel="noopener">
              Dropbox App Console
            </a>
            的应用页面拿到 <b>App key</b> 和 <b>App secret</b>。
          </li>
          <li>
            用它们走一次 <code>token_access_type=offline</code> 授权，换取 <b>refresh token</b>
            （与 rclone 用的同一套即可）。本应用只读，不会写入 Dropbox。
          </li>
        </ol>
        <p class="tip">
          三个凭证都会明文存在本浏览器的 localStorage 里（个人本地使用风险可控）。
        </p>
      </details>
    </div>
  </div>
</template>

<style scoped>
.login {
  display: grid;
  place-items: center;
  height: 100dvh;
  padding: 24px;
}

.card {
  width: 100%;
  max-width: 420px;
  padding: 28px 28px 20px;
  border-radius: 16px;
  background: #1e2027;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}

h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0.5px;
}

.sub {
  margin: 4px 0 20px;
  color: var(--fg-muted);
  font-size: 14px;
}

.notice {
  margin: 0 0 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(234, 179, 8, 0.12);
  color: #fbbf24;
  font-size: 13px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--fg-muted);
}

textarea,
input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #33363f;
  border-radius: 8px;
  background: #16171d;
  color: var(--fg);
  font: inherit;
  font-size: 14px;
  resize: vertical;
}

textarea:focus,
input:focus {
  outline: none;
  border-color: #6366f1;
}

button {
  margin-top: 4px;
  padding: 11px;
  border: none;
  border-radius: 8px;
  background: #6366f1;
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: default;
}

.error {
  margin: 0;
  color: #f87171;
  font-size: 13px;
}

.help {
  margin-top: 20px;
  font-size: 13px;
  color: var(--fg-muted);
}

.help summary {
  cursor: pointer;
}

.help ol {
  margin: 10px 0 0;
  padding-left: 18px;
  line-height: 1.7;
}

.help code {
  padding: 1px 5px;
  border-radius: 4px;
  background: #16171d;
  font-size: 12px;
}

.help a {
  color: #818cf8;
}

.help .tip {
  margin: 12px 0 0;
  line-height: 1.6;
}
</style>
