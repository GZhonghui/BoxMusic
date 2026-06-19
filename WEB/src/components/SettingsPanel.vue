<script setup>
import { computed } from 'vue'
import { useLibraryStore } from '../stores/library'
import pkg from '../../package.json'

const emit = defineEmits(['close'])

const library = useLibraryStore()
const loading = computed(() => library.status === 'loading')

// 清除凭证：清掉本地全部凭证 + 索引缓存 + 偏好后刷新回登录页。
// 只做 removeItem（不读取任何值），见 PLAN.md 九.3。
const CLEARED_KEYS = [
  'dbx_refresh_token',
  'dbx_app_key',
  'dbx_app_secret',
  'index_cache',
  'index_cache_rev',
  'settings',
]

function clearCredentials() {
  if (!window.confirm('将清除本机保存的凭证与索引缓存并退出登录，确定吗？')) return
  for (const k of CLEARED_KEYS) localStorage.removeItem(k)
  location.reload()
}
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="panel" role="dialog" aria-label="设置">
      <header class="head">
        <strong>设置</strong>
        <button class="x" title="关闭" @click="emit('close')">✕</button>
      </header>

      <section class="row">
        <div class="text">
          <div class="t">重新加载索引</div>
          <div class="d">忽略本地缓存，强制从 Dropbox 重新下载索引</div>
        </div>
        <button class="action" :disabled="loading" @click="library.reload()">
          {{ loading ? '加载中…' : '重新加载' }}
        </button>
      </section>

      <section class="row">
        <div class="text">
          <div class="t">清除凭证</div>
          <div class="d">清掉本机凭证与索引缓存并退出登录</div>
        </div>
        <button class="action danger" @click="clearCredentials">清除并退出</button>
      </section>

      <footer class="about">
        BoxMusic · v{{ pkg.version }} —— 把 Dropbox 当曲库的个人播放器（只读）
      </footer>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}

.panel {
  width: min(440px, 92vw);
  border: 1px solid #33363f;
  border-radius: 14px;
  background: #1e2027;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #2a2c34;
  font-size: 15px;
}

.x {
  border: none;
  background: transparent;
  color: var(--fg-muted);
  font-size: 15px;
  cursor: pointer;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-bottom: 1px solid #23252d;
}

.text {
  min-width: 0;
}

.row .t {
  font-size: 14px;
}

.row .d {
  margin-top: 3px;
  color: var(--fg-muted);
  font-size: 12px;
}

.action {
  flex: none;
  padding: 8px 16px;
  border: 1px solid #33363f;
  border-radius: 8px;
  background: transparent;
  color: var(--fg);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.action:hover:not(:disabled) {
  background: #262830;
}

.action:disabled {
  opacity: 0.5;
  cursor: default;
}

.action.danger {
  border-color: rgba(248, 113, 113, 0.5);
  color: #f87171;
}

.action.danger:hover {
  background: rgba(248, 113, 113, 0.12);
}

.about {
  padding: 14px 18px;
  color: var(--fg-muted);
  font-size: 12px;
  line-height: 1.6;
}
</style>
