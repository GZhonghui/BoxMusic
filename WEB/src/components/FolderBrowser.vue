<script setup>
import { ref, computed } from 'vue'
import { RecycleScroller } from 'vue-virtual-scroller'
import { useLibraryStore } from '../stores/library'
import { buildTree, nodeAt, listEntries } from '../lib/tree'

const library = useLibraryStore()

// 当前所在目录的路径段（[] = 根）。文件夹浏览的唯一可变状态。
const currentPath = ref([])

// 选中的歌曲 path（单击选中；双击播放留到第 4 步）
const selectedPath = ref('')

// 目录树：files 变了才重建（重新加载索引时）
const tree = computed(() => buildTree(library.files))

const currentNode = computed(() => nodeAt(tree.value, currentPath.value))

// 当前目录条目，补一个虚拟列表用的唯一 key
const entries = computed(() =>
  listEntries(currentNode.value).map((e) =>
    e.type === 'folder' ? { ...e, key: `d:${e.name}` } : { ...e, key: `f:${e.file.path}` },
  ),
)

// 面包屑：根节点名取 settings.root_label（无则「全部」）+ 逐级目录
const crumbs = computed(() => {
  const rootLabel = library.settings?.root_label || '全部'
  return [{ label: rootLabel, depth: 0 }, ...currentPath.value.map((seg, i) => ({ label: seg, depth: i + 1 }))]
})

function enterFolder(name) {
  currentPath.value = [...currentPath.value, name]
  selectedPath.value = ''
}

// 跳到面包屑第 depth 级（0 = 根）
function jumpTo(depth) {
  currentPath.value = currentPath.value.slice(0, depth)
  selectedPath.value = ''
}

function selectSong(file) {
  selectedPath.value = file.path
}

// 歌曲主标题：优先解析出的 title，没有就用文件名
function songTitle(file) {
  return file.title || file.name
}
</script>

<template>
  <div class="browser">
    <!-- 面包屑：可点任一级跳回 -->
    <nav class="crumbs">
      <template v-for="(c, i) in crumbs" :key="c.depth">
        <span v-if="i > 0" class="sep">/</span>
        <button
          class="crumb"
          :class="{ current: i === crumbs.length - 1 }"
          :disabled="i === crumbs.length - 1"
          @click="jumpTo(c.depth)"
        >
          {{ c.label }}
        </button>
      </template>
    </nav>

    <!-- 当前目录：文件夹在前、歌曲在后；单层几千条用虚拟滚动兜底 -->
    <RecycleScroller
      v-if="entries.length"
      class="list"
      :items="entries"
      :item-size="48"
      key-field="key"
      v-slot="{ item }"
    >
      <div
        v-if="item.type === 'folder'"
        class="row folder"
        @click="enterFolder(item.name)"
      >
        <span class="icon">📁</span>
        <span class="title">{{ item.name }}</span>
        <span class="meta">{{ item.count }}</span>
      </div>
      <div
        v-else
        class="row song"
        :class="{ selected: item.file.path === selectedPath }"
        @click="selectSong(item.file)"
      >
        <span class="icon">🎵</span>
        <span class="title">{{ songTitle(item.file) }}</span>
        <span v-if="item.file.artist" class="artist">{{ item.file.artist }}</span>
      </div>
    </RecycleScroller>

    <p v-else class="empty">这个文件夹是空的</p>
  </div>
</template>

<style scoped>
.browser {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.crumbs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  padding: 10px 12px;
  border-bottom: 1px solid #2a2c34;
  font-size: 14px;
}

.crumb {
  padding: 3px 6px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #818cf8;
  font: inherit;
  cursor: pointer;
}

.crumb:hover:not(:disabled) {
  background: #23252d;
}

.crumb.current {
  color: var(--fg);
  cursor: default;
}

.sep {
  color: var(--fg-muted);
}

.list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.row {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 14px;
  cursor: pointer;
  border-bottom: 1px solid #1f2127;
}

.row:hover {
  background: #1e2027;
}

.row.song.selected {
  background: #2a2540;
}

.icon {
  flex: none;
  font-size: 16px;
}

.title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta,
.artist {
  flex: none;
  color: var(--fg-muted);
  font-size: 13px;
}

.empty {
  flex: 1;
  display: grid;
  place-items: center;
  margin: 0;
  color: var(--fg-muted);
}
</style>
