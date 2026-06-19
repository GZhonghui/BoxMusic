<script setup>
import { ref } from 'vue'
import { usePlayerStore } from '../stores/player'
import { trackTitle, artistText } from '../lib/display'

const player = usePlayerStore()

// 拖拽换序：记下拖起的下标，drop 时交给 store 处理
const dragIndex = ref(-1)

function onDragStart(i) {
  dragIndex.value = i
}
function onDrop(i) {
  if (dragIndex.value >= 0) player.moveItem(dragIndex.value, i)
  dragIndex.value = -1
}
</script>

<template>
  <div class="queue">
    <div class="head">
      <span>播放队列 · {{ player.queue.length }}</span>
      <button class="clear" :disabled="!player.queue.length" @click="player.clear()">清空</button>
    </div>

    <div v-if="player.queue.length" class="list">
      <div
        v-for="(t, i) in player.queue"
        :key="t.path"
        class="row"
        :class="{ current: i === player.currentIndex }"
        draggable="true"
        @dragstart="onDragStart(i)"
        @dragover.prevent
        @drop="onDrop(i)"
        @dblclick="player.jumpTo(i)"
        title="双击跳播 · 拖拽换序"
      >
        <span class="idx">{{ i === player.currentIndex ? '▶' : i + 1 }}</span>
        <div class="text">
          <span class="title">{{ trackTitle(t) }}</span>
          <span v-if="artistText(t)" class="artist">{{ artistText(t) }}</span>
        </div>
        <button class="del" @click.stop="player.removeAt(i)" title="移除">✕</button>
      </div>
    </div>

    <p v-else class="empty">队列为空，在浏览里双击一首歌开始播放</p>
  </div>
</template>

<style scoped>
.queue {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #2a2c34;
  font-size: 14px;
  color: var(--fg-muted);
}

.clear {
  padding: 5px 12px;
  border: 1px solid #33363f;
  border-radius: 6px;
  background: transparent;
  color: var(--fg-muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.clear:disabled {
  opacity: 0.4;
  cursor: default;
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
  border-bottom: 1px solid #1f2127;
  cursor: grab;
}

.row:hover {
  background: #1e2027;
}

.row.current {
  background: #2a2540;
}

.idx {
  flex: none;
  width: 22px;
  text-align: center;
  color: var(--fg-muted);
  font-size: 13px;
}

.row.current .idx {
  color: #818cf8;
}

.text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artist {
  color: var(--fg-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.del {
  flex: none;
  border: none;
  background: transparent;
  color: var(--fg-muted);
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
}

.row:hover .del {
  opacity: 1;
}

.empty {
  flex: 1;
  display: grid;
  place-items: center;
  margin: 0;
  padding: 24px;
  text-align: center;
  color: var(--fg-muted);
}
</style>
