# Tested on MacOS (IMPORTANT!)
# python3 update_manifest.py

import os

ignore_files = ['.DS_Store']
dropbox_path = os.path.expanduser('~/Dropbox/Apps/ZhonghuiPlayer/')

def update_by_filter(files_filter: list, output_file: str):
    o = open(os.path.join(dropbox_path, output_file), 'w', encoding='utf-8')
    dl = len(dropbox_path)
    for root, dirs, files in os.walk(dropbox_path):
        o.write(f'D/{root[dl:]}\n')
        for dir_name in dirs:
            o.write(f'D/{os.path.join(root, dir_name)[dl:]}\n')
        for file_name in files:
            if file_name in ignore_files: continue
            if file_name.split('.')[-1] not in files_filter: continue
            o.write(f'F/{os.path.join(root, file_name)[dl:]}\n')
    o.close()

def main():
    update_by_filter(['mp3', 'flac', 'm4a'], 'manifest.txt')
    update_by_filter(['mp4', 'mkv'], 'manifest_video.txt')

if __name__ == '__main__':
    main()