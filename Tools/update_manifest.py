# Tested on MacOS (IMPORTANT!)
# python3 update_manifest.py

import os

ignore_files = ['.DS_Store']
dropbox_path = os.path.expanduser('~/Dropbox/Apps/ZhonghuiPlayer/')

def update_by_filter(files_filter: list, output_file: str, pre = None):
    o = open(os.path.join(dropbox_path, output_file), 'w', encoding='utf-8')
    dl = len(dropbox_path)
    for root, dirs, files in os.walk(dropbox_path):
        if not pre or root[dl:].startswith(pre):
            o.write(f'D/{root[dl:]}\n')
        for dir_name in dirs:
            full_dir = os.path.join(root, dir_name)[dl:]
            if not pre or full_dir.startswith(pre):
                o.write(f'D/{full_dir}\n')
        for file_name in files:
            if file_name in ignore_files: continue
            if file_name.split('.')[-1] not in files_filter: continue
            full_path = os.path.join(root, file_name)[dl:]
            if not pre or full_path.startswith(pre):
                o.write(f'F/{full_path}\n')
    o.close()

def main():
    update_by_filter(['mp3', 'flac', 'm4a'], 'manifest.txt')
    update_by_filter(['mp4', 'mkv'], 'manifest_v.txt', '视频/Video')

if __name__ == '__main__':
    main()