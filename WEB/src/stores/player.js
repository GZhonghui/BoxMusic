import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTemporaryLink } from '../dropbox/api'
import { extractCover } from '../lib/cover'
import { trackTitle } from '../lib/display'

// 播放模式：顺序 / 单曲循环 / 列表循环 / 随机
export const MODES = ['order', 'repeat-one', 'repeat-all', 'shuffle']
const LS_SETTINGS = 'settings' // { play_mode, volume }

// 播放器 + 队列。只有一个「当前播放队列」（见 PLAN.md：不做收藏夹 / 命名歌单）。
// 第 4 步只做顺序播放；播放模式（循环/随机）留到第 6 步。
export const usePlayerStore = defineStore('player', () => {
  // 单个常驻 <audio>，由 store 持有，切 Tab 不中断
  const audio = new Audio()

  const queue = ref([])         // 队列：file 条目数组
  const currentIndex = ref(-1)  // 队列中位置，-1 = 空
  const isPlaying = ref(false)
  const progress = ref(0)       // 当前秒数
  const duration = ref(0)
  const volume = ref(1)
  const mode = ref('order')     // 播放模式，持久化到 localStorage.settings
  const error = ref('')         // 最近一次播放错误提示
  const trackCover = ref('')    // 当前曲内嵌封面的 objectURL，空 = 回退默认封面

  const currentTrack = computed(() => queue.value[currentIndex.value] || null)

  // 启动时恢复上次的播放模式 / 音量
  loadSettings()
  audio.volume = volume.value

  audio.addEventListener('timeupdate', () => { progress.value = audio.currentTime })
  audio.addEventListener('durationchange', () => { duration.value = audio.duration || 0 })
  audio.addEventListener('play', () => { isPlaying.value = true })
  audio.addEventListener('pause', () => { isPlaying.value = false })
  audio.addEventListener('ended', () => { onEnded() })
  // 媒体层错误（坏链 / 网络中断）→ 提示并跳下一首，不卡死
  audio.addEventListener('error', () => {
    if (currentIndex.value < 0 || !audio.src) return
    failCurrent(`播放出错，已跳过：${trackTitle(currentTrack.value)}`)
  })

  // 播放队列第 index 首
  async function playAt(index) {
    if (index < 0 || index >= queue.value.length) return
    currentIndex.value = index
    error.value = ''
    setTrackCover('') // 切歌先清空封面，提取完再填（期间走默认封面占位）
    const track = queue.value[index]
    try {
      const link = await getTemporaryLink(track.path)
      if (currentIndex.value !== index) return // 等待期间用户已切歌，丢弃这次
      audio.src = link
      audio.currentTime = 0
      // 播放被拒（如浏览器策略）由用户手动恢复；真正的媒体错误走 error 事件
      await audio.play().catch(() => {})
      loadTrackCover(link, track.path) // 顺手读内嵌封面（非阻塞，失败回退默认）
    } catch (e) {
      if (currentIndex.value !== index) return
      failCurrent(`无法播放《${trackTitle(track)}》：${e.message}`)
    }
  }

  // 替换当前曲封面 objectURL，释放上一个，避免内存泄漏
  function setTrackCover(url) {
    if (trackCover.value) URL.revokeObjectURL(trackCover.value)
    trackCover.value = url || ''
  }

  // 读正在播放这首的内嵌封面（只此一首，非阻塞）；期间已切歌则丢弃
  async function loadTrackCover(link, path) {
    const url = await extractCover(link)
    if (currentTrack.value?.path !== path) {
      if (url) URL.revokeObjectURL(url)
      return
    }
    setTrackCover(url)
  }

  // 当前曲失败：记下提示并「线性」顺延到下一首。
  // 刻意不按 mode（循环/随机），避免坏链在 repeat-all/shuffle 下无限重试。
  function failCurrent(msg) {
    error.value = msg
    if (currentIndex.value < queue.value.length - 1) {
      playAt(currentIndex.value + 1)
    } else {
      audio.pause()
      isPlaying.value = false
    }
  }

  // 随机一个与当前不同的下标
  function randomIndex() {
    const n = queue.value.length
    if (n <= 1) return 0
    let i = Math.floor(Math.random() * n)
    if (i === currentIndex.value) i = (i + 1) % n
    return i
  }

  // 自然播完一首：按 mode 决定下一步
  function onEnded() {
    if (mode.value === 'repeat-one') {
      audio.currentTime = 0
      audio.play().catch(() => {})
      return
    }
    if (mode.value === 'shuffle') {
      playAt(randomIndex())
      return
    }
    // order / repeat-all
    if (currentIndex.value < queue.value.length - 1) playAt(currentIndex.value + 1)
    else if (mode.value === 'repeat-all') playAt(0)
    else { audio.pause(); isPlaying.value = false } // 顺序到底，停
  }

  // 手动下一首：随机模式随机，否则顺延，列表循环到底回到头
  function next() {
    if (!queue.value.length) return
    if (mode.value === 'shuffle') { playAt(randomIndex()); return }
    if (currentIndex.value < queue.value.length - 1) playAt(currentIndex.value + 1)
    else if (mode.value === 'repeat-all') playAt(0)
    else { audio.pause(); isPlaying.value = false }
  }

  // 手动上一首：随机模式随机，否则回退，列表循环到头回到尾
  function prev() {
    if (!queue.value.length) return
    if (mode.value === 'shuffle') { playAt(randomIndex()); return }
    if (currentIndex.value > 0) playAt(currentIndex.value - 1)
    else if (mode.value === 'repeat-all') playAt(queue.value.length - 1)
  }

  // 用一组歌设为队列并从 startIndex 播（双击文件夹内某首时调用）
  function playList(songs, startIndex = 0) {
    if (!songs || !songs.length) return
    queue.value = [...songs]
    playAt(startIndex)
  }

  function jumpTo(index) {
    playAt(index)
  }

  function togglePlay() {
    if (!currentTrack.value) return
    if (audio.paused) audio.play().catch(() => {})
    else audio.pause()
  }

  function seek(sec) {
    if (currentTrack.value) audio.currentTime = sec
  }

  function setVolume(v) {
    volume.value = v
    audio.volume = v
    persistSettings()
  }

  // 切换播放模式（按 MODES 顺序循环），并持久化
  function cycleMode() {
    const i = MODES.indexOf(mode.value)
    mode.value = MODES[(i + 1) % MODES.length]
    persistSettings()
  }

  function loadSettings() {
    try {
      const s = JSON.parse(localStorage.getItem(LS_SETTINGS) || '{}')
      if (MODES.includes(s.play_mode)) mode.value = s.play_mode
      if (typeof s.volume === 'number' && s.volume >= 0 && s.volume <= 1) volume.value = s.volume
    } catch {
      // 设置损坏：用默认值即可，忽略
    }
  }

  function persistSettings() {
    try {
      localStorage.setItem(LS_SETTINGS, JSON.stringify({ play_mode: mode.value, volume: volume.value }))
    } catch (e) {
      console.warn('[BoxMusic] 保存播放设置失败：', e)
    }
  }

  // 从队列移除某项，并把 currentIndex 调到正确位置
  function removeAt(index) {
    if (index < 0 || index >= queue.value.length) return
    const wasCurrent = index === currentIndex.value
    queue.value.splice(index, 1)
    if (queue.value.length === 0) { clear(); return }
    if (wasCurrent) {
      // 删的是当前曲：原位现在是下一首，越界则停在最后一首
      playAt(Math.min(index, queue.value.length - 1))
    } else if (index < currentIndex.value) {
      currentIndex.value-- // 删的是前面的，下标左移
    }
  }

  // 队列内拖拽换序，currentIndex 跟随当前曲（path 唯一）
  function moveItem(from, to) {
    const len = queue.value.length
    if (from === to || from < 0 || to < 0 || from >= len || to >= len) return
    const cur = currentTrack.value
    const arr = queue.value.slice()
    const [item] = arr.splice(from, 1)
    arr.splice(to, 0, item)
    queue.value = arr
    if (cur) currentIndex.value = arr.findIndex((t) => t.path === cur.path)
  }

  function clear() {
    currentIndex.value = -1 // 先置空，避免清 src 触发的 error 被当成播放错误
    queue.value = []
    audio.pause()
    audio.removeAttribute('src')
    audio.load()
    isPlaying.value = false
    progress.value = 0
    duration.value = 0
    error.value = ''
    setTrackCover('')
  }

  return {
    queue,
    currentIndex,
    currentTrack,
    isPlaying,
    progress,
    duration,
    volume,
    mode,
    error,
    trackCover,
    playList,
    jumpTo,
    togglePlay,
    next,
    prev,
    seek,
    setVolume,
    cycleMode,
    removeAt,
    moveItem,
    clear,
  }
})
