# make sure the vlc is installed
# https://www.videolan.org/
import dropbox, vlc, os, time, subprocess
import message as m

music_format = ['mp3', 'flac', 'm4a']
manifest = list()
playlist = list()

def download(dbx, file_path: str):
    try:
        md, res = dbx.files_download(file_path)
    except dropbox.exceptions.HttpError as err:
        m.out('*** HTTP error' + str(err))
        return None
    return res.content

# generate manifest.txt: tree . > manifest.txt @ Apps/ZhonghuiPlayer/
def sync_manifest(dbx):
    manifest_path = '/manifest.txt'
    with open('./manifest.txt', 'wb') as file:
        data = download(dbx, manifest_path)
        if data: file.write(data)

    global manifest
    with open('./manifest.txt', 'r', encoding='utf-8') as file:
        manifest = file.readlines()
    manifest = [line.strip() for line in manifest]

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

def playlist_updated():
    m.out('playlist updated')

def print_menu():
    menu = '[P (id)] Play or Pause, [N] Next file, [S] Current status, '
    menu = menu + '[D] Delete from playlist, [I] Insert to playlist, '
    menu = menu + '[M id] Play mode (1: default, 2: repeat, 3: shuffle), [Q] Quit.'
    m.out(menu)

def main():
    global playlist
    tokens = ['', '']
    with open('token.txt', 'r', encoding='utf-8') as file:
        tokens[0] = file.read()
    token_dn_path = os.path.expanduser('~/Downloads/token.txt')
    if os.path.exists(token_dn_path) and os.path.isfile(token_dn_path):
        with open(token_dn_path, 'r', encoding='utf-8') as file:
            tokens[1] = file.read()
    token = tokens[0] if len(tokens[0]) > len(tokens[1]) else tokens[1]
    if token == '' or token == 'YOUR_ACCESS_TOKEN':
        m.out('There is no avaliable token!')
        return

    dbx = dropbox.Dropbox(token)
    m.out('You are already signed in dropbox')
    sync_manifest(dbx)
    m.out('Music Library manifest info synced completed')

    while True:
        print_menu()
        i = input().upper()
        if i == 'Q': break
        elif i.startswith('P'):
            if i == 'P': m.out('Pausing...')
            elif ' ' in i and i.split(' ')[1].isdigit():
                id = int(i.split(' ')[1])
                if id == 0: m.out('Resuming...')
                elif id >= 1 and id <= len(playlist):
                    m.out(f'Start play: id = {id}, name = [{playlist[id-1]}]')
                else: m.out('Id out of range!')
        elif i.startswith('I'):
            with open('./cache.txt', 'w', encoding='utf-8') as file:
                for l in manifest: file.write(f'-{l}\n')
            try:
                subprocess.run(["vim", "./cache.txt"], check=True)
                updated_contents = list()
                with open('./cache.txt', 'r', encoding='utf-8') as file:
                    updated_contents = file.readlines()
                updated_contents = [line.strip() for line in updated_contents]
                added_new_song_count = 0
                for l in updated_contents:
                    if l in manifest:
                        m.out(f'Add [{l}]')
                        if l.startswith('F') and l[1:] not in playlist:
                            playlist.append(l[1:])
                            added_new_song_count += 1
                        if l.startswith('D'):
                            for item in manifest:
                                if item.startswith('F') and item[1:].startswith(l[1:]):
                                    if item[1:] not in playlist:
                                        playlist.append(item[1:])
                                        added_new_song_count += 1
                m.out(f'{added_new_song_count} songs added to playlist')
                if added_new_song_count != 0: playlist_updated()
            except subprocess.CalledProcessError as e:
                m.out('No update to playlist')
        elif i.startswith('D'):
            with open('./cache.txt', 'w', encoding='utf-8') as file:
                for l in playlist: file.write(f'+{l}\n')
            try:
                subprocess.run(["vim", "./cache.txt"], check=True)
                updated_contents = list()
                with open('./cache.txt', 'r', encoding='utf-8') as file:
                    updated_contents = file.readlines()
                updated_contents = [line.strip() for line in updated_contents]
                new_list = list()
                for l in updated_contents:
                    if l.startswith('+') and l[1:] in playlist:
                        new_list.append(l[1:])
                if len(playlist) != len(new_list): playlist_updated()
                playlist = new_list
                m.out(f'New playlist size is {len(playlist)}')
            except subprocess.CalledProcessError as e:
                m.out('No update to playlist')
        else: m.out('Unexpected input!')
    m.out('Bye~')

if __name__ == '__main__':
    main()