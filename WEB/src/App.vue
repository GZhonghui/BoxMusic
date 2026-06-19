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
import ImmersiveView from './components/ImmersiveView.vue'
import SettingsPanel from './components/SettingsPanel.vue'

const auth = useAuthStore()
const library = useLibraryStore()
const player = usePlayerStore()

// 左侧栏 Tab：浏览 / 队列（见 PLAN.md 二）
const tab = ref('browse')
// 左侧栏折叠（折叠后右侧沉浸区铺满）
const collapsed = ref(false)
// 设置面板开关
const showSettings = ref(false)

// 进入已登录态就加载索引（流程 1：缓存秒开 + 后台 rev 校验）
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
      <button class="icon-btn" title="设置" @click="showSettings = true">⚙</button>
    </header>

    <div class="body">
      <template v-if="library.status === 'ready'">
        <!-- 折叠后停靠在左缘、用于重新展开 -->
        <button v-show="collapsed" class="expand" title="展开列表" @click="collapsed = false">›</button>

        <aside class="sidebar" :class="{ collapsed }">
          <div class="side-head">
            <nav class="tabs">
              <button :class="{ active: tab === 'browse' }" @click="tab = 'browse'">浏览</button>
              <button :class="{ active: tab === 'queue' }" @click="tab = 'queue'">
                队列<span v-if="player.queue.length"> · {{ player.queue.length }}</span>
              </button>
            </nav>
            <button class="collapse" title="折叠列表" @click="collapsed = true">‹</button>
          </div>
          <div class="side-body">
            <FolderBrowser v-show="tab === 'browse'" />
            <QueueList v-if="tab === 'queue'" />
          </div>
        </aside>

        <ImmersiveView class="immersive" />
      </template>

      <div v-else class="state">
        <p v-if="library.status === 'loading'">正在加载索引…</p>
        <template v-else>
          <p class="msg">{{ library.error || '索引尚未加载' }}</p>
          <button class="primary" @click="library.load()">重试</button>
        </template>
      </div>
    </div>

    <p v-if="player.error" class="player-error" @click="player.error = ''">{{ player.error }}</p>

    <PlayerBar />

    <SettingsPanel v-if="showSettings" @close="showSettings = false" />
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

.icon-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid #33363f;
  border-radius: 8px;
  background: transparent;
  color: var(--fg-muted);
  font-size: 16px;
  cursor: pointer;
}

.icon-btn:hover {
  background: #23252d;
  color: var(--fg);
}

/* 主体：左侧栏 + 右侧沉浸区 */
.body {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
}

.sidebar {
  flex: none;
  width: 340px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid #2a2c34;
}

.sidebar.collapsed {
  display: none;
}

.side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 8px 0 12px;
  border-bottom: 1px solid #2a2c34;
}

.tabs {
  display: flex;
  gap: 4px;
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

.collapse,
.expand {
  border: none;
  background: transparent;
  color: var(--fg-muted);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.collapse {
  padding: 4px 8px;
  border-radius: 6px;
}

.collapse:hover {
  background: #23252d;
  color: var(--fg);
}

.expand {
  position: absolute;
  top: 50%;
  left: 0;
  z-index: 10;
  transform: translateY(-50%);
  padding: 14px 6px;
  border-radius: 0 8px 8px 0;
  background: #23252d;
  border: 1px solid #2a2c34;
  border-left: none;
}

.expand:hover {
  color: var(--fg);
}

.side-body {
  flex: 1;
  min-height: 0;
}

.immersive {
  flex: 1;
  min-width: 0;
}

.state {
  flex: 1;
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

.primary {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #6366f1;
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

/* 窄屏：隐藏沉浸区，左侧栏铺满（始终展开） */
@media (max-width: 720px) {
  .immersive {
    display: none;
  }

  .sidebar {
    width: 100%;
    min-width: 0;
    border-right: none;
  }

  .sidebar.collapsed {
    display: flex;
  }

  .expand,
  .collapse {
    display: none;
  }
}
</style>
