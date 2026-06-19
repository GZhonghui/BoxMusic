<script setup>
import { watch } from 'vue'
import { useAuthStore } from './stores/auth'
import { useLibraryStore } from './stores/library'
import LoginView from './components/LoginView.vue'
import FolderBrowser from './components/FolderBrowser.vue'

const auth = useAuthStore()
const library = useLibraryStore()

// 进入已登录态就加载索引（流程 1）。rev 比对 / 秒开缓存留到第 5 步。
watch(
  () => auth.isAuthenticated,
  (ok) => {
    if (ok && library.status === 'idle') library.loadIndex()
  },
  { immediate: true },
)
</script>

<template>
  <LoginView v-if="!auth.isAuthenticated" />

  <div v-else class="app">
    <header class="topbar">
      <strong class="brand">BoxMusic</strong>
      <span class="status">
        <template v-if="library.status === 'loading'">正在加载索引…</template>
        <template v-else-if="library.status === 'ready'">已加载 · {{ library.files.length }} 首</template>
        <template v-else>索引未就绪</template>
      </span>
      <span class="spacer" />
      <button class="ghost" :disabled="library.status === 'loading'" @click="library.loadIndex()">
        重新加载索引
      </button>
      <button class="ghost" @click="auth.logout()">退出登录</button>
    </header>

    <main class="main">
      <FolderBrowser v-if="library.status === 'ready'" />

      <div v-else class="state">
        <p v-if="library.status === 'loading'">正在加载索引…</p>
        <template v-else>
          <p class="msg">{{ library.error || '索引尚未加载' }}</p>
          <button @click="library.loadIndex()">重试</button>
        </template>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 16px;
  border-bottom: 1px solid #2a2c34;
  background: #1a1c22;
}

.brand {
  font-size: 16px;
  letter-spacing: 0.5px;
}

.status {
  color: var(--fg-muted);
  font-size: 13px;
}

.spacer {
  flex: 1;
}

.main {
  flex: 1;
  min-height: 0;
}

.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  height: 100%;
  padding: 24px;
  text-align: center;
}

.msg {
  margin: 0;
  max-width: 480px;
  color: var(--fg-muted);
  line-height: 1.6;
}

button {
  padding: 8px 16px;
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
  padding: 7px 14px;
  background: transparent;
  border: 1px solid #33363f;
  color: var(--fg-muted);
  font-weight: 500;
}
</style>
