// 浏览器版 jsmediatags（包的 browser 字段指向了不存在的文件，直接引 dist 构建）
import jsmediatags from 'jsmediatags/dist/jsmediatags.min.js'

// 从音频直链里读「内嵌封面」，返回一个 objectURL；无封面 / 读失败 / 跨域受限都返回 ''。
// 只对「正在播放」的单首调用：jsmediatags 走 Range 请求，只读标签所需字节，不整文件下载。
// 失败一律静默回退（调用方会改用 default_cover），所以最坏情况 = 原有行为，无回归。
export function extractCover(url) {
  return new Promise((resolve) => {
    try {
      jsmediatags.read(url, {
        onSuccess(tag) {
          const pic = tag.tags && tag.tags.picture
          if (!pic || !pic.data || !pic.data.length) {
            resolve('')
            return
          }
          try {
            const bytes = new Uint8Array(pic.data)
            const blob = new Blob([bytes], { type: pic.format || 'image/jpeg' })
            resolve(URL.createObjectURL(blob))
          } catch {
            resolve('')
          }
        },
        onError() {
          resolve('')
        },
      })
    } catch {
      resolve('')
    }
  })
}
