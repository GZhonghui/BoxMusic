// 用 index.json 的 files[].path 在前端构建一棵目录树（启动时算一次）。
// path 形如 "/Music/华语/周杰伦 - 晴天.mp3"，最后一段是文件名，前面是各级目录。
// Web 应用只读，这棵树纯内存、纯展示用。

// 树节点：
//   { name, children: Map<name, node>, songs: [fileEntry] }
// 根节点 name 为空字符串，代表 App folder 根。
function makeNode(name) {
  return { name, children: new Map(), songs: [] }
}

// 由 files[] 构建目录树，返回根节点。
export function buildTree(files) {
  const root = makeNode('')
  for (const f of files) {
    if (!f || typeof f.path !== 'string') continue
    const parts = f.path.split('/').filter(Boolean) // 去掉开头的空段
    if (parts.length === 0) continue
    // 沿目录段下钻，最后一段是文件名不建目录
    let node = root
    for (let i = 0; i < parts.length - 1; i++) {
      const seg = parts[i]
      if (!node.children.has(seg)) node.children.set(seg, makeNode(seg))
      node = node.children.get(seg)
    }
    node.songs.push(f)
  }
  return root
}

// 按路径段数组从根定位节点；任一段不存在返回 null。
export function nodeAt(root, segments) {
  let node = root
  for (const seg of segments) {
    if (!node) return null
    node = node.children.get(seg)
  }
  return node || null
}

// 取某节点下用于展示的条目：文件夹在前（按名排序），歌曲在后（沿用 path 排序）。
// 返回扁平数组，每项带 type 便于虚拟列表统一渲染。
export function listEntries(node) {
  if (!node) return []
  const folders = [...node.children.values()]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((child) => ({
      type: 'folder',
      name: child.name,
      count: child.children.size + child.songs.length,
    }))
  const songs = node.songs.map((f) => ({ type: 'song', file: f }))
  return [...folders, ...songs]
}
