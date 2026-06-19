import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchWithAuth } from '../dropbox/api'
import { trackTitle } from '../lib/display'

const TEMP_LINK_URL = 'https://api.dropboxapi.com/2/files/get_temporary_link'

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
  const error = ref('')         // 最近一次播放错误提示

  const currentTrack = computed(() => queue.value[currentIndex.value] || null)

  audio.volume = volume.value

  audio.addEventListener('timeupdate', () => { progress.value = audio.currentTime })
  audio.addEventListener('durationchange', () => { duration.value = audio.duration || 0 })
  audio.addEventListener('play', () => { isPlaying.value = true })
  audio.addEventListener('pause', () => { isPlaying.value = false })
  audio.addEventListener('ended', () => { next() })
  // 媒体层错误（坏链 / 网络中断）→ 提示并跳下一首，不卡死
  audio.addEventListener('error', () => {
    if (currentIndex.value < 0 || !audio.src) return
    failCurrent(`播放出错，已跳过：${trackTitle(currentTrack.value)}`)
  })

  // 取 4 小时有效直链
  async function getLink(path) {
    const res = await fetchWithAuth(TEMP_LINK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    })
    if (!res.ok) {
      const detail = await res.text().catch(() => '')
      throw new Error(`取直链失败 (HTTP ${res.status})${detail ? `：${detail}` : ''}`)
    }
    const data = await res.json()
    return data.link
  }

  // 播放队列第 index 首
  async function playAt(index) {
    if (index < 0 || index >= queue.value.length) return
    currentIndex.value = index
    error.value = ''
    const track = queue.value[index]
    try {
      const link = await getLink(track.path)
      if (currentIndex.value !== index) return // 等待期间用户已切歌，丢弃这次
      audio.src = link
      audio.currentTime = 0
      // 播放被拒（如浏览器策略）由用户手动恢复；真正的媒体错误走 error 事件
      await audio.play().catch(() => {})
    } catch (e) {
      if (currentIndex.value !== index) return
      failCurrent(`无法播放《${trackTitle(track)}》：${e.message}`)
    }
  }

  // 当前曲失败：记下提示并顺延到下一首
  function failCurrent(msg) {
    error.value = msg
    next()
  }

  function next() {
    if (currentIndex.value < queue.value.length - 1) {
      playAt(currentIndex.value + 1)
    } else {
      // 队列到底，停下（无循环模式）
      audio.pause()
      isPlaying.value = false
    }
  }

  function prev() {
    if (currentIndex.value > 0) playAt(currentIndex.value - 1)
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
  }

  return {
    queue,
    currentIndex,
    currentTrack,
    isPlaying,
    progress,
    duration,
    volume,
    error,
    playList,
    jumpTo,
    togglePlay,
    next,
    prev,
    seek,
    setVolume,
    removeAt,
    moveItem,
    clear,
  }
})
