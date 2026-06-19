// 曲目展示用的小工具，浏览器 / 队列 / 播放器共用。

// 主标题：优先解析出的 title，没有就用文件名
export function trackTitle(file) {
  return file?.title || file?.name || ''
}

// 歌手：index.json 里是列表（0 到多个），多人用 / 连接。
// 兼容旧索引里 artist 仍是字符串的情况。
export function artistText(file) {
  const a = file?.artist
  return Array.isArray(a) ? a.join(' / ') : a || ''
}

// 秒数 → m:ss，用于进度/时长显示
export function formatTime(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00'
  const s = Math.floor(sec)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
