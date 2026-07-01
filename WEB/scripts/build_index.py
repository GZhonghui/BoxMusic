# 本地索引生成脚本（在本机跑，不在浏览器里跑）
# 用法：python3 build_index.py
#
# 思路沿用 CLI/update_manifest.py：遍历本机已同步的 Dropbox App folder，
# 把扫描结果写成 metainfo/index.json，由 Dropbox 桌面客户端自动同步上传。
# Web 应用只下载读取这个文件，永不写入、永不扫描（见 WEB/PLAN.md）。
#
# index.json 的字段定义见 PLAN.md「Dropbox 上的 index.json」一节。

import json
import os
import re
from datetime import datetime, timezone

# ——— 配置（按需改这里）———

# 本机已同步的 App folder 根目录（即 API 里的 "/"）
DROPBOX_PATH = os.path.expanduser('~/Dropbox/Apps/ZhonghuiPlayer/')

# 只收录这些扩展名的音频（小写，不带点）。沿用 CLI 的 mp3/flac/m4a。
AUDIO_EXTS = {'mp3', 'flac', 'm4a'}

# 扫描时忽略的文件名
IGNORE_FILES = {'.DS_Store'}

# 命名顺序例外：这些一级目录下文件名是「歌名 - 歌手」（反序）。
# 其余目录一律「歌手 - 歌名」。需要再加反序目录就往这个集合里塞名字。
REVERSED_ORDER_DIRS = {'视频'}

# 输出位置（App folder 内的相对路径）。固定 metainfo/index.json，应用内不可配置。
OUTPUT_REL = 'metainfo/index.json'

# 写进 settings 的全局项（Web 应用只读）
DEFAULT_COVER = '/metainfo/default_cover.jpg'  # 歌曲无封面时统一回退用这张
ROOT_LABEL = 'Music'                     # 面包屑根节点显示名


# ——— 实现 ———

def split_artists(s):
    """歌手字段按英文逗号 , / 分号 ; / 和号 & 分割成列表，
    每个歌手名去掉前后空格、去掉空项。解析不出歌手时返回空列表（长度 0 到任意）。"""
    return [a.strip() for a in re.split(r'[,;&]', s) if a.strip()]


def parse_name(stem, reversed_order=False):
    """从文件名（不含扩展名）解析 artist / title。
    默认约定 '歌手 - 歌名'；reversed_order=True 时为 '歌名 - 歌手'（见 REVERSED_ORDER_DIRS）。
    没有 ' - ' 分隔时 artist 为空列表、整名当 title。
    返回 (artists, title)，artists 是列表（按英文逗号可拆成多人）。"""
    if ' - ' in stem:
        left, right = (s.strip() for s in stem.split(' - ', 1))
        artist_str, title = (right, left) if reversed_order else (left, right)
        return split_artists(artist_str), title
    return [], stem.strip()


def is_reversed_order(app_path):
    """按一级目录判断该文件是否用反序命名。
    app_path 形如 /视频/xxx.mp3 → 一级目录是 '视频'。"""
    segs = app_path.split('/')  # ['', '视频', 'xxx.mp3']
    return len(segs) > 2 and segs[1] in REVERSED_ORDER_DIRS


def to_app_path(abs_path):
    """本机绝对路径 → App folder 内路径（以 / 开头、用正斜杠）。"""
    rel = os.path.relpath(abs_path, DROPBOX_PATH)
    return '/' + rel.replace(os.sep, '/')


def natural_sort_key(s):
    """自然排序键：把字符串按连续数字段切开，数字段转成 int 参与比较，
    其余文本段保持原样。这样位数不同的数字按数值大小排
    （1 < 2 < 10 < 100），而不是按字典序（'10' < '2' < '9'）。

    re.split 用捕获组切分，结果里偶数位恒为文本段、奇数位恒为数字段，
    因此两个键逐位比较时同一位置类型一致，不会出现 int 与 str 相比报错。"""
    return [int(part) if part.isdigit() else part
            for part in re.split(r'(\d+)', s)]


def scan_files():
    files = []
    for root, _dirs, names in os.walk(DROPBOX_PATH):
        name_set = set(names)  # 同目录文件名集合，用于查同名 .lrc
        for name in names:
            if name in IGNORE_FILES:
                continue
            stem, ext = os.path.splitext(name)
            if ext[1:].lower() not in AUDIO_EXTS:
                continue

            path = to_app_path(os.path.join(root, name))
            artists, title = parse_name(stem, reversed_order=is_reversed_order(path))
            entry = {
                'path': path,
                'name': name,
                'artist': artists,  # 列表：0 到多个歌手（按英文逗号分割）
                'title': title,
            }

            # 同目录同名 .lrc 存在则带上歌词路径（可选字段）
            lrc_name = stem + '.lrc'
            if lrc_name in name_set:
                entry['lrc'] = to_app_path(os.path.join(root, lrc_name))

            files.append(entry)

    # 按 path 自然排序：位数不同的数字按数值大小排（1 2 10 100，而非 1 10 100 2）。
    # 仍是确定性排序，输出稳定 → 内容没变时 Dropbox 的 rev 不会变，应用不会重复下载。
    files.sort(key=lambda e: natural_sort_key(e['path']))
    return files


def main():
    if not os.path.isdir(DROPBOX_PATH):
        raise SystemExit(f'找不到 App folder：{DROPBOX_PATH}（请确认 Dropbox 已同步该目录）')

    files = scan_files()
    index = {
        'version': 1,
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'settings': {
            'default_cover': DEFAULT_COVER,
            'root_label': ROOT_LABEL,
        },
        'files': files,
    }

    out_path = os.path.join(DROPBOX_PATH, OUTPUT_REL)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f'已写入 {out_path}')
    print(f'共 {len(files)} 首，Dropbox 客户端会自动同步上传。')


if __name__ == '__main__':
    main()
