<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '../stores/player'
import { trackTitle, artistText, formatTime } from '../lib/display'

const player = usePlayerStore()

const track = computed(() => player.currentTrack)
const hasTrack = computed(() => !!track.value)

const MODE_LABEL = {
  order: { icon: '➡️', text: '顺序播放' },
  'repeat-one': { icon: '🔂', text: '单曲循环' },
  'repeat-all': { icon: '🔁', text: '列表循环' },
  shuffle: { icon: '🔀', text: '随机播放' },
}
const modeInfo = computed(() => MODE_LABEL[player.mode] || MODE_LABEL.order)

function onSeek(e) {
  player.seek(Number(e.target.value))
}
function onVolume(e) {
  player.setVolume(Number(e.target.value))
}
</script>

<template>
  <footer class="bar">
    <!-- 当前曲目信息 -->
    <div class="info">
      <span class="cover">🎵</span>
      <div class="text" v-if="hasTrack">
        <span class="title">{{ trackTitle(track) }}</span>
        <span class="artist">{{ artistText(track) || '未知歌手' }}</span>
      </div>
      <div class="text" v-else>
        <span class="title muted">未在播放</span>
      </div>
    </div>

    <!-- 控制 + 进度 -->
    <div class="center">
      <div class="controls">
        <button class="mode" :title="`播放模式：${modeInfo.text}（点击切换）`" @click="player.cycleMode()">
          {{ modeInfo.icon }}
        </button>
        <button :disabled="!hasTrack" @click="player.prev()" title="上一首">⏮</button>
        <button class="play" :disabled="!hasTrack" @click="player.togglePlay()">
          {{ player.isPlaying ? '⏸' : '▶' }}
        </button>
        <button :disabled="!hasTrack" @click="player.next()" title="下一首">⏭</button>
      </div>
      <div class="progress">
        <span class="t">{{ formatTime(player.progress) }}</span>
        <input
          type="range"
          min="0"
          :max="player.duration || 0"
          step="0.1"
          :value="player.progress"
          :disabled="!hasTrack || !player.duration"
          @input="onSeek"
        />
        <span class="t">{{ formatTime(player.duration) }}</span>
      </div>
    </div>

    <!-- 音量 -->
    <div class="volume">
      <span>🔊</span>
      <input type="range" min="0" max="1" step="0.01" :value="player.volume" @input="onVolume" />
    </div>
  </footer>
</template>

<style scoped>
.bar {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid #2a2c34;
  background: #1a1c22;
}

.info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.cover {
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #2a2c34;
  font-size: 18px;
}

.text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.text .title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.text .artist {
  color: var(--fg-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.muted {
  color: var(--fg-muted);
}

.center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.controls {
  display: flex;
  align-items: center;
  gap: 14px;
}

.controls button {
  border: none;
  background: transparent;
  color: var(--fg);
  font-size: 18px;
  cursor: pointer;
  line-height: 1;
}

.controls button.play {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #6366f1;
  color: #fff;
}

.controls button:disabled {
  opacity: 0.4;
  cursor: default;
}

.controls button.mode {
  font-size: 15px;
}

.progress {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.progress .t {
  flex: none;
  width: 40px;
  color: var(--fg-muted);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.progress .t:last-child {
  text-align: right;
}

.progress input {
  flex: 1;
}

.volume {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.volume input {
  width: 90px;
}

input[type='range'] {
  accent-color: #6366f1;
  cursor: pointer;
}
</style>
