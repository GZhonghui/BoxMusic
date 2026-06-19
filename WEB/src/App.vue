<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import { useLibraryStore } from './stores/library'
import { usePlayerStore } from './stores/player'
import LoginView from './components/LoginView.vue'
import FolderBrowser from './components/FolderBrowser.vue'
import QueueList from './components/QueueList.vue'
import PlayerBar from './components/PlayerBar.vue'
import SearchBox from './components/SearchBox.vue'

const auth = useAuthStore()
const library = useLibraryStore()
const player = usePlayerStore()

// 左侧单栏 Tab：浏览 / 队列（见 PLAN.md 二）
const tab = ref('browse')

// 进入已登录态就加载索引（流程 1）。rev 比对 / 秒开缓存留到第 5 步。
watch(
  () => auth.isAuthenticated,
  (ok) => {
    if (ok && library.status === 'idle') library.load()
  },
  { immediate: true },
)
</script>

<template>
  <LoginView v-if="!auth.isAuthenticated" />

  <div v-else class="app">
    <header class="topbar">
      <strong class="brand">BoxMusic</strong>
      <SearchBox v-if="library.status === 'ready'" />
      <span class="spacer" />
      <span class="status">
        <template v-if="library.status === 'loading'">正在加载索引…</template>
        <template v-else-if="library.status === 'ready'">已加载 · {{ library.files.length }} 首</template>
        <template v-else>索引未就绪</template>
      </span>
      <button class="ghost" :disabled="library.status === 'loading'" @click="library.reload()">
        重新加载索引
      </button>
      <button class="ghost" @click="auth.logout()">退出登录</button>
    </header>

    <template v-if="library.status === 'ready'">
      <nav class="tabs">
        <button :class="{ active: tab === 'browse' }" @click="tab = 'browse'">浏览</button>
        <button :class="{ active: tab === 'queue' }" @click="tab = 'queue'">
          队列<span v-if="player.queue.length"> · {{ player.queue.length }}</span>
        </button>
      </nav>

      <main class="main">
        <FolderBrowser v-show="tab === 'browse'" />
        <QueueList v-if="tab === 'queue'" />
      </main>

      <p v-if="player.error" class="player-error" @click="player.error = ''">{{ player.error }}</p>

      <PlayerBar />
    </template>

    <main v-else class="main state">
      <p v-if="library.status === 'loading'">正在加载索引…</p>
      <template v-else>
        <p class="msg">{{ library.error || '索引尚未加载' }}</p>
        <button @click="library.load()">重试</button>
      </template>
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

.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 12px 0;
  border-bottom: 1px solid #2a2c34;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--fg-muted);
  font: inherit;
  cursor: pointer;
}

.tabs button.active {
  color: var(--fg);
  border-bottom-color: #6366f1;
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
  padding: 24px;
  text-align: center;
}

.msg {
  margin: 0;
  max-width: 480px;
  color: var(--fg-muted);
  line-height: 1.6;
}

.player-error {
  margin: 0;
  padding: 8px 16px;
  background: rgba(248, 113, 113, 0.12);
  color: #f87171;
  font-size: 13px;
  cursor: pointer;
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
