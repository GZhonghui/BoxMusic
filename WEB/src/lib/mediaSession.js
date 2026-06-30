// Media Session：把当前曲目信息（歌名/歌手/封面）和播放控制喂给系统的媒体卡片
//（安卓通知栏 / iOS 锁屏 / macOS「正在播放」/ Windows 媒体浮窗）。
// 纯浏览器原生 API、无依赖；不支持的浏览器（无 navigator.mediaSession）全部静默跳过，
// 失败一律不抛错——最坏情况 = 系统回退到 favicon，与原有行为一致，无回归。

const supported = typeof navigator !== 'undefined' && 'mediaSession' in navigator

// 注册一次控制按钮回调（播放 / 暂停 / 上一首 / 下一首）。
// 个别浏览器不支持某个 action 时 setActionHandler 会抛错，逐个 try 掉即可。
export function setupMediaSession({ play, pause, prev, next }) {
  if (!supported) return
  const set = (action, handler) => {
    try {
      navigator.mediaSession.setActionHandler(action, handler)
    } catch {
      // 该浏览器不支持此动作，忽略
    }
  }
  set('play', play)
  set('pause', pause)
  set('previoustrack', prev)
  set('nexttrack', next)
}

// 更新元数据。artwork 为空则省略 artwork（系统回退到 favicon），但歌名/歌手仍更新。
// title 为空（无当前曲）→ 清空整张卡片。
// 不写 type：封面可能是 jpeg/png 等，type 只是选择提示、不参与解码，省略比写错诚实。
export function updateMediaMetadata({ title, artist, artwork }) {
  if (!supported) return
  if (!title) {
    navigator.mediaSession.metadata = null
    return
  }
  try {
    const art = artwork ? [{ src: artwork, sizes: '512x512' }] : []
    navigator.mediaSession.metadata = new MediaMetadata({
      title,
      artist: artist || '',
      artwork: art,
    })
  } catch {
    // MediaMetadata 构造失败（理论上不会）：留空，系统回退默认，不影响播放
  }
}

// 同步播放状态，让系统卡片的按钮显示正确图标（播放 / 暂停）
export function setPlaybackState(state) {
  if (!supported) return
  navigator.mediaSession.playbackState = state // 'playing' | 'paused' | 'none'
}
