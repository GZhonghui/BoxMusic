# Tested on MacOS
# python3 update_manifest.py

import os

ignore_files = ['.DS_Store']
files_filter = ['mp3', 'flac', 'm4a']

dropbox_path = os.path.expanduser('~/Dropbox/Apps/ZhonghuiPlayer/')
output_file = 'manifest.txt'

def main():
    o = open(os.path.join(dropbox_path, output_file), 'w', encoding='utf-8')
    dl = len(dropbox_path)
    for root, dirs, files in os.walk(dropbox_path):
        o.write(f'D/{root[dl:]}\n')
        for file_name in files:
            if file_name in ignore_files: continue
            if file_name.split('.')[-1] not in files_filter: continue
            o.write(f'F/{os.path.join(root, file_name)[dl:]}\n')
    o.close()

if __name__ == '__main__':
    main()