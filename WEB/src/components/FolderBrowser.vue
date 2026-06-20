<script setup>
import { ref, computed, nextTick } from 'vue'
import { RecycleScroller } from 'vue-virtual-scroller'
import { useLibraryStore } from '../stores/library'
import { usePlayerStore } from '../stores/player'
import { buildTree, nodeAt, listEntries } from '../lib/tree'
import { trackTitle, artistText } from '../lib/display'

const library = useLibraryStore()
const player = usePlayerStore()

// 当前所在目录的路径段（[] = 根）。文件夹浏览的唯一可变状态。
const currentPath = ref([])

// 选中的歌曲 path（单击选中；双击播放留到第 4 步）
const selectedPath = ref('')

// 虚拟列表实例 + 各层滚动位置记忆（scrollMemory[depth] = 该层 scrollTop）。
// 进子目录前存下当前层滚动，面包屑跳回时恢复；被退出的更深层位置丢弃。
const scroller = ref(null)
const scrollMemory = []

function scrollTop() {
  return scroller.value?.$el?.scrollTop || 0
}
function setScroll(pos) {
  nextTick(() => {
    if (scroller.value?.$el) scroller.value.$el.scrollTop = pos
  })
}

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
  scrollMemory[currentPath.value.length] = scrollTop() // 记住当前层滚动
  currentPath.value = [...currentPath.value, name]
  selectedPath.value = ''
  setScroll(0) // 进入的子目录从顶部看起
}

// 跳到面包屑第 depth 级（0 = 根）
function jumpTo(depth) {
  const pos = scrollMemory[depth] || 0
  scrollMemory.length = depth // 丢弃该层及更深层（已退出的目录）的滚动记忆
  currentPath.value = currentPath.value.slice(0, depth)
  selectedPath.value = ''
  setScroll(pos) // 恢复回到的那层之前的滚动
}

function selectSong(file) {
  selectedPath.value = file.path
}

// 双击歌曲：把当前目录（不递归）所有歌按显示顺序设为队列，从该首开始播
function playSong(file) {
  const songs = currentNode.value?.songs || []
  const start = songs.findIndex((s) => s.path === file.path)
  if (start >= 0) player.playList(songs, start)
}

// 点「＋」加入队列末尾（不打断当前播放）；按钮短暂变 ✓ 作为反馈
const justAdded = ref('')
let addTimer
function addToQueue(file) {
  player.enqueue(file)
  justAdded.value = file.path
  clearTimeout(addTimer)
  addTimer = setTimeout(() => {
    justAdded.value = ''
  }, 900)
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
      ref="scroller"
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
        :class="{
          selected: item.file.path === selectedPath,
          playing: item.file.path === player.currentTrack?.path,
        }"
        @click="selectSong(item.file)"
        @dblclick="playSong(item.file)"
        title="双击播放"
      >
        <span class="icon">{{ item.file.path === player.currentTrack?.path ? '🔊' : '🎵' }}</span>
        <div class="text">
          <span class="title">{{ trackTitle(item.file) }}</span>
          <span v-if="artistText(item.file)" class="artist">{{ artistText(item.file) }}</span>
        </div>
        <button
          class="add"
          :class="{ done: item.file.path === justAdded }"
          title="加入当前队列"
          @click.stop="addToQueue(item.file)"
        >
          {{ item.file.path === justAdded ? '✓' : '＋' }}
        </button>
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

.row.song.playing .title {
  color: #818cf8;
}

.icon {
  flex: none;
  font-size: 16px;
}

.title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 文件夹行：名称占满剩余宽度 */
.row.folder .title {
  flex: 1;
}

/* 歌曲行：标题 / 歌手两行，左对齐（同队列列表） */
.text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.text .title {
  font-size: 14px;
}

.text .artist {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--fg-muted);
  font-size: 12px;
}

.meta {
  flex: none;
  color: var(--fg-muted);
  font-size: 13px;
}

/* 加入队列按钮：默认隐藏，hover 行时显示（同 QueueList 删除按钮做法），无边框 */
.add {
  flex: none;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--fg-muted);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  opacity: 0;
}

.row.song:hover .add {
  opacity: 1;
}

.add:hover {
  color: #818cf8;
}

/* 刚加入：保持可见并显示成功色 */
.add.done {
  opacity: 1;
  color: #4ade80;
}

/* 触屏 / 窄屏没有 hover：按钮常显，保证可点 */
@media (max-width: 720px) {
  .add {
    opacity: 1;
  }
}

.empty {
  flex: 1;
  display: grid;
  place-items: center;
  margin: 0;
  color: var(--fg-muted);
}
</style>
