<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { usePlayerStore } from '../stores/player'
import { downloadText } from '../dropbox/api'
import { parseLrc, activeLineIndex } from '../lib/lrc'

const player = usePlayerStore()

// 'none' 无歌词 | 'loading' | 'ready' 已同步 | 'plain' 无时间标的纯文本 | 'error'
const state = ref('none')
const lines = ref([]) // 已同步歌词 [{time,text}]
const plain = ref('') // 纯文本歌词（无时间标时回退）
const scroller = ref(null)

const cache = new Map() // lrc path -> { lines, plain }
const track = computed(() => player.currentTrack)

// 当前行：随播放进度走（progress 每秒更新数次，二分足够）
const activeIndex = computed(() =>
  state.value === 'ready' ? activeLineIndex(lines.value, player.progress) : -1,
)

function apply(result) {
  if (result.lines.length) {
    lines.value = result.lines
    plain.value = ''
    state.value = 'ready'
  } else if (result.plain) {
    lines.value = []
    plain.value = result.plain
    state.value = 'plain'
  } else {
    lines.value = []
    plain.value = ''
    state.value = 'none'
  }
}

async function loadFor(t) {
  const path = t?.lrc
  if (!path) {
    apply({ lines: [], plain: '' })
    return
  }
  if (cache.has(path)) {
    apply(cache.get(path))
    return
  }
  state.value = 'loading'
  lines.value = []
  plain.value = ''
  try {
    const text = await downloadText(path)
    if (player.currentTrack?.lrc !== path) return // 期间已切歌，丢弃
    const parsed = parseLrc(text)
    const result = parsed.length ? { lines: parsed, plain: '' } : { lines: [], plain: text.trim() }
    cache.set(path, result)
    apply(result)
  } catch (e) {
    if (player.currentTrack?.lrc !== path) return
    // 歌词文件不存在视作「暂无歌词」，其它错误才报失败
    if (e.code === 'not_found') {
      cache.set(path, { lines: [], plain: '' })
      apply({ lines: [], plain: '' })
    } else {
      state.value = 'error'
    }
  }
}

watch(() => track.value?.lrc, () => loadFor(track.value), { immediate: true })

// 当前行变化 → 平滑滚动到容器垂直居中（从下往上的效果）
watch(activeIndex, async (i) => {
  if (i < 0) return
  await nextTick()
  const c = scroller.value
  const el = c?.querySelector(`[data-i="${i}"]`)
  if (!c || !el) return
  c.scrollTo({
    top: el.offsetTop - c.clientHeight / 2 + el.offsetHeight / 2,
    behavior: 'smooth',
  })
})
</script>

<template>
  <div class="lyrics-view">
    <div v-if="state === 'loading'" class="hint">歌词加载中…</div>
    <div v-else-if="state === 'error'" class="hint">歌词加载失败</div>
    <div v-else-if="state === 'none'" class="hint">暂无歌词</div>
    <pre v-else-if="state === 'plain'" class="plain">{{ plain }}</pre>

    <div v-else ref="scroller" class="scroller">
      <p
        v-for="(l, i) in lines"
        :key="i"
        :data-i="i"
        class="line"
        :class="{ active: i === activeIndex, past: i < activeIndex }"
      >
        {{ l.text || '♪' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.lyrics-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.hint {
  flex: 1;
  display: grid;
  place-items: center;
  color: var(--fg-muted);
}

.plain {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin: 0;
  padding: 16px;
  white-space: pre-wrap;
  font: inherit;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.75);
  text-align: center;
}

.scroller {
  position: relative; /* 作为 .line offsetTop 的参照，保证滚动居中算得准 */
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  /* 上下留白，让首尾行也能滚到正中 */
  padding: 45vh 24px;
  text-align: center;
  scrollbar-width: none;
  -webkit-mask-image: linear-gradient(180deg, transparent, #000 18%, #000 82%, transparent);
  mask-image: linear-gradient(180deg, transparent, #000 18%, #000 82%, transparent);
}

.scroller::-webkit-scrollbar {
  width: 0;
}

.line {
  margin: 0;
  padding: 11px 0;
  font-size: 23px;
  font-weight: 600;
  line-height: 1.32;
  color: rgba(255, 255, 255, 0.4);
  transform: scale(0.96);
  transform-origin: center;
  transition:
    color 0.3s ease,
    opacity 0.3s ease,
    transform 0.36s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.line.past {
  color: rgba(255, 255, 255, 0.28);
}

.line.active {
  color: #fff;
  font-weight: 800;
  transform: scale(1.08);
}
</style>
