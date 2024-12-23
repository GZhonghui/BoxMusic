# make sure the vlc is installed
# https://www.videolan.org/
import dropbox, vlc, os, time, random, subprocess, threading, manager
import message as m
import player as p

dbx = None

music_format = ['mp3', 'flac', 'm4a']
video_format = ['mp4', 'mkv']
manifest = list()
manifest_v = list()
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

def save_playlist(save_file_path = './playlist.txt'):
    global playlist

    with open(save_file_path, 'w', encoding='utf-8') as file:
        for item in playlist:
            file.write(f'{item}\n')
    m.out(f'Playlist saved to {save_file_path}')

def load_playlist(load_file_path = './playlist.txt'):
    if not os.path.exists(load_file_path) or not os.path.isfile(load_file_path):
        return
    
    global playlist, manifest
    with open(load_file_path, 'r', encoding='utf-8') as file:
        playlist = file.readlines()
    playlist = [item.strip() for item in playlist if f'F{item.strip()}' in manifest]
    m.out(f'{len(playlist)} songs readed from {load_file_path}')

def download(dbx, file_path: str):
    try:
        md, res = dbx.files_download(file_path)
    except dropbox.exceptions.HttpError as err:
        m.out('*** HTTP error' + str(err))
        return None
    return res.content

# generate manifest.txt: tree . > manifest.txt @ Apps/ZhonghuiPlayer/
def sync_manifest(dbx):
    def sync_with_filename(filename: str):
        manifest_path = f'/{filename}'
        with open(f'./{filename}', 'wb') as file:
            data = download(dbx, manifest_path)
            if data: file.write(data)
        data_place = list()
        with open(f'./{filename}', 'r', encoding='utf-8') as file:
            data_place = file.readlines()
        data_place = [line.strip() for line in data_place]
        return data_place
    
    global manifest, manifest_v
    manifest = sync_with_filename('manifest.txt')
    manifest_v = sync_with_filename('manifest_v.txt')

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
    save_playlist()

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
    m.out(f'Manager: start playing [{readed_path}] ({playlist.index(readed_path) + 1} / {len(playlist)})')
    play_song(dbx, readed_path)

audio_manager.loop_func = manager_loop_func

def parse_token(file_content: str):
    if file_content and len(file_content) > 0 and file_content.startswith('{'):
        data = file_content.split('"')
        if 'access_token' in data:
            return data[data.index('access_token') + 2]
    return file_content

def main():
    global playlist, need_help, dbx, playmode, audio_manager

    tokens = ['', '']
    with open('token.txt', 'r', encoding='utf-8') as file:
        tokens[0] = parse_token(file.read())
    token_dn_path = os.path.expanduser('~/Downloads/token.txt')
    if os.path.exists(token_dn_path) and os.path.isfile(token_dn_path):
        with open(token_dn_path, 'r', encoding='utf-8') as file:
            tokens[1] = parse_token(file.read())
    token = tokens[0] if len(tokens[0]) > len(tokens[1]) else tokens[1]
    if token == '' or token == 'YOUR_ACCESS_TOKEN':
        m.out('There is no avaliable token!')
        return

    dbx = dropbox.Dropbox(token)
    m.out('You are already signed in dropbox')
    sync_manifest(dbx)
    m.out('Music Library manifest info synced completed')
    load_playlist()

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
        elif i.startswith('N'):
            m.out('Jumping to next file...')
            audio_player.seek_to_last_second()
        elif i.startswith('V'):
            if i == 'V':
                with open('./cache.txt', 'w', encoding='utf-8') as file:
                    for l in manifest_v: file.write(f'*{l}\n')
                try:
                    subprocess.run(["vim", "./cache.txt"], check=True)
                except subprocess.CalledProcessError as e:
                    m.out('No update to video lib')
            elif ' ' in i and i.split(' ')[1].isdigit():
                id = int(i.split(' ')[1])
                if id >= 1 and id <= len(manifest_v):
                    server_path = manifest_v[id - 1]
                    if server_path.startswith('F') and len(server_path) > 3 and server_path[-3:] in video_format:
                        server_path = server_path[1:]
                        local_path = f'./CacheVideo{server_path}'
                        m.out(f'Downloading video file: [{server_path}]')
                        m.out(f'Local path = [{local_path}]')
                        if os.path.exists(local_path) and os.path.isfile(local_path):
                            m.out(f'[{local_path}] is already cached!')
                        else:
                            data = download(dbx, server_path)
                            if data is None:
                                m.out(f'[{server_path}] download failed')
                            else:
                                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                                with open(local_path, 'wb') as file:
                                    file.write(data)
                                m.out(f'[{server_path}] download complated')
                    else:
                        m.out(f'[{server_path}] is not a video file')
                else: m.out('Video id out of range!')
            else: m.out('No avaliable video id!')
        else: m.out('Unexpected input!')

    save_playlist()
    m.out('Stopping manager threads...')
    audio_manager.stop()
    audio_manager.join()
    m.out('Bye~')

if __name__ == '__main__':
    main()