<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from './stores/auth'
import { useLibraryStore } from './stores/library'
import { fetchWithAuth } from './dropbox/api'
import LoginView from './components/LoginView.vue'

const auth = useAuthStore()
const library = useLibraryStore()

// —— 临时占位：仅用于验证第 1 步「登录 + token 刷新机制」（确保 API 能调通）。
//    后续第 3 步会用真正的应用骨架替换整块已登录视图。
const testState = ref('idle') // idle | loading | ok | error
const testMsg = ref('')

const expiresText = computed(() => {
  if (!auth.expiresAt) return '尚未获取（首次调用时刷新）'
  return new Date(auth.expiresAt).toLocaleString()
})

async function testConnection() {
  testState.value = 'loading'
  testMsg.value = ''
  try {
    // App folder 根目录就是空字符串 path，列前几条验证读权限
    const res = await fetchWithAuth('https://api.dropboxapi.com/2/files/list_folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: '', limit: 5 }),
    })
    if (!res.ok) throw new Error(`API HTTP ${res.status}`)
    const data = await res.json()
    testState.value = 'ok'
    testMsg.value = `连接成功，App 根目录返回 ${data.entries.length} 个条目`
  } catch (e) {
    testState.value = 'error'
    testMsg.value = e.message
  }
}
</script>

<template>
  <LoginView v-if="!auth.isAuthenticated" />

  <div v-else class="placeholder">
    <h2>已登录 ✓</h2>
    <p class="hint">第 1 步占位页（待第 3 步替换）。access_token 过期时间：{{ expiresText }}</p>

    <div class="actions">
      <button @click="testConnection" :disabled="testState === 'loading'">
        {{ testState === 'loading' ? '测试中…' : '测试连接' }}
      </button>
      <button @click="library.loadIndex()" :disabled="library.status === 'loading'">
        {{ library.status === 'loading' ? '加载索引中…' : '加载索引' }}
      </button>
      <button class="ghost" @click="auth.logout()">退出登录</button>
    </div>

    <p v-if="testMsg" :class="['result', testState]">{{ testMsg }}</p>

    <p
      v-if="library.status !== 'idle' && library.status !== 'loading'"
      :class="['result', library.status === 'ready' ? 'ok' : 'error']"
    >
      <template v-if="library.status === 'ready'">索引加载成功，共 {{ library.files.length }} 首</template>
      <template v-else>{{ library.error }}</template>
    </p>
  </div>
</template>

<style scoped>
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  height: 100dvh;
  padding: 24px;
  text-align: center;
}

h2 {
  margin: 0;
}

.hint {
  margin: 0;
  color: var(--fg-muted);
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 12px;
}

button {
  padding: 9px 18px;
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

button.ghost {
  background: transparent;
  border: 1px solid #33363f;
  color: var(--fg-muted);
}

.result {
  margin: 0;
  font-size: 14px;
}

.result.ok {
  color: #4ade80;
}

.result.error {
  color: #f87171;
}
</style>
