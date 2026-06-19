<script setup>
import { ref, computed, watch } from 'vue'
import { useLibraryStore } from '../stores/library'
import { usePlayerStore } from '../stores/player'
import { trackTitle, artistText } from '../lib/display'

const library = useLibraryStore()
const player = usePlayerStore()

// 沉浸区两个视图：封面 / 歌词（歌词功能在第 8 步实现，这里先占位）
const view = ref('cover')

// 沉浸区跟随「正在播放」的曲目
const track = computed(() => player.currentTrack)
// 封面优先用当前曲的内嵌封面，没有再回退到 settings.default_cover
const cover = computed(() => player.trackCover || library.coverUrl)

// 无封面图 / 加载失败时的占位：取歌名首字
const initial = computed(() => (trackTitle(track.value) || '♪').slice(0, 1))

// 封面图加载失败 → 回退到占位渐变
const coverFailed = ref(false)
watch(cover, () => { coverFailed.value = false })
const hasCover = computed(() => !!cover.value && !coverFailed.value)

const bgStyle = computed(() =>
  hasCover.value ? { backgroundImage: `url("${cover.value}")` } : {},
)
</script>

<template>
  <section class="iv">
    <!-- 背景：封面放大模糊铺底 + 半透明渐变 -->
    <div class="bg" :class="{ plain: !hasCover }" :style="bgStyle"></div>
    <div class="veil"></div>

    <div class="content">
      <!-- 封面 | 歌词 分段切换 -->
      <div class="seg">
        <button :class="{ active: view === 'cover' }" @click="view = 'cover'">封面</button>
        <button :class="{ active: view === 'lyrics' }" @click="view = 'lyrics'">歌词</button>
      </div>

      <transition name="fade" mode="out-in">
        <!-- 封面视图 -->
        <div v-if="view === 'cover'" key="cover" class="pane">
          <div class="card">
            <img v-if="hasCover" :src="cover" alt="封面" @error="coverFailed = true" />
            <div v-else class="placeholder">{{ initial }}</div>
          </div>
          <div class="meta">
            <template v-if="track">
              <div class="t">{{ trackTitle(track) }}</div>
              <div class="a">{{ artistText(track) || '未知歌手' }}</div>
            </template>
            <div v-else class="t muted">未在播放</div>
          </div>
        </div>

        <!-- 歌词视图（第 8 步实现，先占位） -->
        <div v-else key="lyrics" class="pane lyrics">
          <p class="hint">歌词功能即将推出</p>
        </div>
      </transition>
    </div>
  </section>
</template>

<style scoped>
.iv {
  position: relative;
  height: 100%;
  overflow: hidden;
  display: flex;
}

/* 模糊背景层 */
.bg {
  position: absolute;
  inset: -40px; /* 放大溢出，避免模糊出现透明边 */
  background-size: cover;
  background-position: center;
  filter: blur(48px) saturate(1.3);
  transform: scale(1.1);
}

.bg.plain {
  background: radial-gradient(circle at 30% 20%, #2b2f48, #16171d 70%);
  filter: none;
  transform: none;
}

.veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(22, 23, 29, 0.45), rgba(22, 23, 29, 0.8));
}

.content {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18px;
}

/* 分段切换：玻璃拟态 */
.seg {
  display: flex;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.seg button {
  padding: 6px 20px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--fg-muted);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.seg button.active {
  background: rgba(255, 255, 255, 0.16);
  color: var(--fg);
}

.pane {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 22px;
}

/* 封面卡：圆角 + 投影 + 玻璃边，按可用空间自适应缩放 */
.card {
  width: min(46vh, 80%, 420px);
  aspect-ratio: 1;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

.card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  font-size: clamp(48px, 18vh, 140px);
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  background: linear-gradient(135deg, #6366f1, #a855f7 60%, #ec4899);
}

.meta {
  text-align: center;
  max-width: 90%;
}

.meta .t {
  font-size: 20px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta .a {
  margin-top: 4px;
  color: var(--fg-muted);
  font-size: 14px;
}

.muted {
  color: var(--fg-muted);
}

.lyrics .hint {
  color: var(--fg-muted);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
