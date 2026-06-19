<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RecycleScroller } from 'vue-virtual-scroller'
import { useLibraryStore } from '../stores/library'
import { usePlayerStore } from '../stores/player'
import { trackTitle, artistText } from '../lib/display'

const library = useLibraryStore()
const player = usePlayerStore()

const MAX = 200 // 结果多时只展示前 N 条

const query = ref('')
const open = ref(false)
const rootEl = ref(null)

// 跨全部 files 实时过滤：歌名 / 文件名 / 路径 / 歌手，大小写不敏感
const matches = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return { list: [], total: 0 }
  const list = []
  let total = 0
  for (const f of library.files) {
    const artists = Array.isArray(f.artist) ? f.artist.join(' ') : f.artist || ''
    const hay = `${f.title || ''} ${f.name || ''} ${f.path || ''} ${artists}`.toLowerCase()
    if (hay.includes(q)) {
      total++
      if (list.length < MAX) list.push(f)
    }
  }
  return { list, total }
})

const showPanel = computed(() => open.value && query.value.trim().length > 0)

// 浮层内双击 = 把搜索结果设为队列并从该首播
function playResult(file) {
  const list = matches.value.list
  const idx = list.findIndex((f) => f.path === file.path)
  if (idx >= 0) player.playList(list, idx)
  open.value = false
}

function onKeydown(e) {
  if (e.key === 'Escape') {
    open.value = false
    e.target.blur()
  }
}

// 点搜索框以外的地方收起浮层
function onDocMouseDown(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}
onMounted(() => window.addEventListener('mousedown', onDocMouseDown))
onUnmounted(() => window.removeEventListener('mousedown', onDocMouseDown))
</script>

<template>
  <div ref="rootEl" class="search">
    <input
      v-model="query"
      type="search"
      placeholder="搜索歌名 / 歌手 / 路径"
      spellcheck="false"
      @focus="open = true"
      @input="open = true"
      @keydown="onKeydown"
    />

    <div v-if="showPanel" class="panel">
      <template v-if="matches.list.length">
        <RecycleScroller
          class="results"
          :items="matches.list"
          :item-size="52"
          key-field="path"
          v-slot="{ item }"
        >
          <div class="result" @dblclick="playResult(item)" title="双击播放">
            <div class="title">{{ trackTitle(item) }}</div>
            <div class="sub">
              <span v-if="artistText(item)" class="artist">{{ artistText(item) }}</span>
              <span class="path">{{ item.path }}</span>
            </div>
          </div>
        </RecycleScroller>
        <p v-if="matches.total > matches.list.length" class="note">
          共 {{ matches.total }} 条，仅显示前 {{ matches.list.length }} 条，请细化关键词
        </p>
      </template>
      <p v-else class="empty">无匹配结果</p>
    </div>
  </div>
</template>

<style scoped>
.search {
  position: relative;
  flex: 1;
  max-width: 420px;
}

.search input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #33363f;
  border-radius: 8px;
  background: #16171d;
  color: var(--fg);
  font: inherit;
  font-size: 14px;
}

.search input:focus {
  outline: none;
  border-color: #6366f1;
}

.panel {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 50;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
  border: 1px solid #33363f;
  border-radius: 10px;
  background: #1e2027;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.results {
  max-height: calc(60vh - 30px);
  overflow-y: auto;
}

.result {
  height: 52px;
  padding: 6px 14px;
  border-bottom: 1px solid #1f2127;
  cursor: pointer;
}

.result:hover {
  background: #262830;
}

.result .title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.result .sub {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--fg-muted);
}

.result .artist {
  flex: none;
}

.result .path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  opacity: 0.7;
}

.note,
.empty {
  margin: 0;
  padding: 8px 14px;
  font-size: 12px;
  color: var(--fg-muted);
}
</style>
