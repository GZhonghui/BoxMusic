// LRC 歌词解析：文本 → 按时间升序的 [{ time, text }]（time 单位秒）。
// 支持一行多个时间标 `[mm:ss.xx][mm:ss.xx]词`，以及 `[offset:±毫秒]` 整体偏移。
// 解析不出任何带时间标的行时返回空数组（调用方可回退成纯文本展示）。

const TIME_RE = /\[(\d{1,2}):(\d{1,2}(?:[.:]\d{1,3})?)\]/g
const OFFSET_RE = /\[offset:\s*([+-]?\d+)\s*\]/i

export function parseLrc(text) {
  if (!text) return []

  // offset：正值让歌词整体提前（标准 LRC 约定）
  let offset = 0
  const om = text.match(OFFSET_RE)
  if (om) offset = parseInt(om[1], 10) / 1000

  const lines = []
  for (const raw of text.split(/\r?\n/)) {
    const times = []
    let m
    TIME_RE.lastIndex = 0
    while ((m = TIME_RE.exec(raw)) !== null) {
      const min = parseInt(m[1], 10)
      const sec = parseFloat(m[2].replace(':', '.')) // 个别 lrc 用 mm:ss:xx
      if (Number.isFinite(min) && Number.isFinite(sec)) times.push(min * 60 + sec)
    }
    if (!times.length) continue // 无时间标（元数据 / 空行）跳过

    const content = raw.replace(TIME_RE, '').trim()
    for (const t of times) lines.push({ time: Math.max(0, t - offset), text: content })
  }

  lines.sort((a, b) => a.time - b.time)
  return lines
}

// 二分找「最后一个 time <= t」的行下标；都还没到则返回 -1。
export function activeLineIndex(lines, t) {
  let lo = 0
  let hi = lines.length - 1
  let ans = -1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    if (lines[mid].time <= t) {
      ans = mid
      lo = mid + 1
    } else {
      hi = mid - 1
    }
  }
  return ans
}
