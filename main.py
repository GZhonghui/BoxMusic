# make sure the vlc is installed
# https://www.videolan.org/
import dropbox, vlc, os, time

music_format = ['mp3', 'flac', 'm4a']
manifest = dict()

def download(dbx, file_path: str):
    try:
        md, res = dbx.files_download(file_path)
    except dropbox.exceptions.HttpError as err:
        print('*** HTTP error', err)
        return None
    return res.content

# generate manifest.txt: tree . > manifest.txt @ Apps/ZhonghuiPlayer/
def sync_manifest(dbx):
    manifest_path = '/manifest.txt'
    with open('./manifest.txt', 'wb') as file:
        file.write(download(dbx, manifest_path))

    global manifest

def sync_music(dbx, music_path: list):
    full_path = ''
    for sub in music_path: full_path += f'/{sub}'
    cache_path = f'./Cache{full_path}'
    if os.path.exists(cache_path) and os.path.isfile(cache_path):
        return cache_path

    data = download(dbx, full_path)
    if not data: return None

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as file:
        file.write(data)
    return cache_path

def play_music(dbx, music_path: list):
    cache_path = sync_music(dbx, music_path)
    if not cache_path: return None

    player = vlc.MediaPlayer(cache_path)
    player.play()

    time.sleep(1)
    while player.is_playing(): time.sleep(1)

def main():
    token = ''
    with open('token.txt', 'r', encoding='utf-8') as file:
        token = file.read()
    if token == '' or token == 'YOUR_ACCESS_TOKEN': return

    dbx = dropbox.Dropbox(token)
    sync_manifest(dbx)

    m_p = ['单曲', 'Vol. 01', 'G.E.M.邓紫棋 - If I Were A Boy.mp3']
    play_music(dbx, m_p)

if __name__ == '__main__':
    main()