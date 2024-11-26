# make sure the vlc is installed
# https://www.videolan.org/
import dropbox, vlc, os, time, random, subprocess, threading, manager
import message as m
import player as p

dbx = None

music_format = ['mp3', 'flac', 'm4a']
manifest = list()
playlist = list()

playmode = 1 # 1: default, 2: repeat, 3: shuffle

next_song_path = str()
next_song_path_lock = threading.Lock()

audio_player = p.AudioPlayer()
audio_manager = manager.WorkerThread()

need_help = True
def print_menu(detail = False):
    if detail:
        menu = '[P (id)] Play or Pause, [N] Next file, [S] Current status, '
        menu = menu + '[D] Delete from playlist, [I] Insert to playlist, '
        menu = menu + '[M id] Play mode (1: default, 2: repeat, 3: shuffle), [Q] Quit.'
        m.out(menu)
    else:
        m.out('Welcome! Please input your command, [H] for more help.')

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
    m.out(f'Download from [{full_path}]')
    if os.path.exists(cache_path) and os.path.isfile(cache_path):
        m.out(f'[{cache_path}] is alerady cached')
        return cache_path

    data = download(dbx, full_path)
    if not data: return None

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as file:
        file.write(data)
    return cache_path

def playlist_updated():
    m.out('playlist updated')

def play_song(dbx, path: str):
    m.out('Downloading file...')
    cache_path = sync_music(dbx, path.strip('/').split('/'))
    if not cache_path:
        m.out('Download failed!')
        return None

    m.out('Download completed')
    audio_player.play(cache_path)

# callback
def on_play_end(end_file_path):
    global dbx, playmode, playlist, next_song_path, next_song_path_lock
    if end_file_path: end_file_path = end_file_path[7:] # ./Cache
    m.out(f'[{end_file_path}] end')
    if len(playlist) == 0:
        m.out('Playlist is empty!')
        return
    if not end_file_path or end_file_path not in playlist:
        m.out('Play from the start of playlist')
        with next_song_path_lock:
            next_song_path = playlist[0]
        return
    idx = playlist.index(end_file_path) + 1
    if playmode == 1:
        if idx < len(playlist):
            m.out(f'Playing the next song (mode 1)... [{playlist[idx]}]')
            with next_song_path_lock:
                next_song_path = playlist[idx]
        else: m.out('Playlist end')
    elif playmode == 2:
        next_song = playlist[idx if idx < len(playlist) else 0]
        m.out(f'Playing the next song (mode 2)... [{next_song}]')
        with next_song_path_lock:
            next_song_path = next_song
    elif playmode == 3:
        with next_song_path_lock:
            next_song_path = random.choice(playlist)
            m.out(f'Random play: [{next_song_path}]')

audio_player.on_play_end_func = on_play_end

def manager_loop_func():
    global next_song_path, next_song_path_lock, dbx
    readed_path = None

    with next_song_path_lock:
        readed_path = next_song_path
        next_song_path = str()

    if not readed_path or len(readed_path) == 0: return
    m.out(f'Manager: start playing [{readed_path}]')
    play_song(dbx, readed_path)

audio_manager.loop_func = manager_loop_func

def main():
    global playlist, need_help, dbx, playmode, audio_manager

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

    audio_manager.start()
    while True:
        print_menu(need_help)
        need_help = False

        i = input().upper()
        if i == 'Q': break
        elif i.startswith('P'):
            if i == 'P':
                m.out('Pausing...')
                audio_player.pause()
            elif ' ' in i and i.split(' ')[1].isdigit():
                id = int(i.split(' ')[1])
                if id == 0:
                    m.out('Resuming...')
                    audio_player.resume()
                elif id >= 1 and id <= len(playlist):
                    m.out(f'Start play: id = {id}, name = [{playlist[id-1]}]')
                    global next_song_path, next_song_path_lock
                    with next_song_path_lock:
                        next_song_path = playlist[id-1]
                else: m.out('Id out of range!')
            else: m.out('No avaliable id!')
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
        elif i.startswith('S'):
            status = f'{"Playing" if audio_player.is_playing() else "Paused"}: '
            status = status + f'[{audio_player.current_file if audio_player.current_file else "NULL"}]; '
            current_time, total_length = audio_player.get_progress()
            status = status + f'({current_time//1000}s / {total_length//1000}s); '
            status = status + f'playmode = {playmode}'
            m.out(status)
        elif i.startswith('H'):
            need_help = True
        elif i.startswith('M') and ' ' in i and i.split(' ')[1] in ['1','2','3']:
            playmode = int(i.split(' ')[1])
            m.out(f'Changed playmode to {playmode}')
        else: m.out('Unexpected input!')
    m.out('Stopping manager threads...')
    audio_manager.stop()
    audio_manager.join()
    m.out('Bye~')

if __name__ == '__main__':
    main()